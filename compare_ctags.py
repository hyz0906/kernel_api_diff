#!/usr/bin/env python3

"""
Compares two kernel 'ctags' JSON output files to find API differences.

Generates a JSON report detailing added, removed, and modified symbols,
focusing on functions and their signatures.

'ctags' command to generate the input files (must be Universal Ctags):
ctags -R -o tags_v5.15.json --output-format=json --fields=+nS \
      --languages=C --kinds-C=+p \
      linux-5.15/include linux-5.15/drivers

ctags -R -o tags_v6.1.json --output-format=json --fields=+nS \
      --languages=C --kinds-C=+p \
      linux-6.1/include linux-6.1/drivers
"""

import json
import argparse
import sys
from pathlib import Path

def parse_ctags_json(filepath):
    """
    Parses a ctags JSON-lines file into a dictionary of symbols.

    Prioritizes definitions from header files (.h) as they represent
    the canonical API contract.
    """
    symbols = {}
    print(f"[+] Parsing {filepath}...", file=sys.stderr)
    try:
        with open(filepath, 'r') as f:
            for line in f:
                try:
                    tag = json.loads(line)
                except json.JSONDecodeError:
                    print(f"   - Warning: Skipping malformed JSON line: {line.strip()}", file=sys.stderr)
                    continue

                # We only care about actual tags, not pseudo-tags (metadata)
                if tag.get("_type") != "tag":
                    continue

                name = tag.get("name")
                if not name:
                    continue
                
                # Prioritization logic:
                # 1. If symbol not seen, add it.
                # 2. If symbol seen, but new one is in .h and old one wasn't, replace it.
                # 3. If symbol seen, and old one is in .h and new one isn't, keep old one.
                if name not in symbols:
                    symbols[name] = tag
                else:
                    current_path = symbols[name].get("path", "")
                    new_path = tag.get("path", "")
                    
                    is_current_header = current_path.endswith((".h", ".H"))
                    is_new_header = new_path.endswith((".h", ".H"))

                    if is_new_header and not is_current_header:
                        symbols[name] = tag  # Prioritize header definition
                    elif not is_new_header and is_current_header:
                        pass  # Keep existing header definition
                    else:
                        symbols[name] = tag  # Otherwise, last one wins
                        
    except FileNotFoundError:
        print(f"[!] Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error parsing file {filepath}: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"   - Found {len(symbols)} unique symbols.", file=sys.stderr)
    return symbols

def reconstruct_signature(tag):
    """
    Reconstructs a full C function signature from a ctags tag object.
    """
    if not tag:
        return "N/A (Symbol not present)"

    kind = tag.get("kind")
    name = tag.get("name", "Unnamed")

    # Handle functions
    if kind == "function" or kind == "prototype":
        # 'typeref' field looks like "typename:int"
        ret_type = tag.get("typeref", "void").replace("typename:", "").strip()
        # 'signature' field looks like "(int a, char *b)"
        args = tag.get("signature", "()")
        
        # Handle cases where ctags fails to find a return type
        if not ret_type:
            ret_type = "void" # Default assumption
            
        return f"{ret_type} {name}{args}"

    # Handle other types like macros, structs, etc.
    elif kind == "macro":
        return f"#define {name} ..." # Signature field is not reliable
    elif kind == "struct":
        return f"struct {name} {{...}}"
    elif kind == "typedef":
        return f"typedef ... {name};"
    else:
        return f"{kind} {name}"

def compare_tags(tag_a, tag_b, version_a_name, version_b_name):
    """
    Compares two tag objects for the same symbol and returns a diff dict.
    Returns None if no meaningful difference is found.
    """
    sig_a = reconstruct_signature(tag_a)
    sig_b = reconstruct_signature(tag_b)

    # If full signatures are identical, no change to report
    if sig_a == sig_b:
        return None

    change_entry = {
        "version_a_sig": sig_a,
        "version_b_sig": sig_b,
    }

    # Determine the type of change (this is a syntactic analysis)
    ret_a = tag_a.get("typeref", "").replace("typename:", "")
    ret_b = tag_b.get("typeref", "").replace("typename:", "")
    args_a = tag_a.get("signature", "")
    args_b = tag_b.get("signature", "")
    kind_a = tag_a.get("kind")
    kind_b = tag_b.get("kind")

    if kind_a != kind_b:
        change_entry["change_type"] = "kind_modified"
        change_entry["old_kind"] = kind_a
        change_entry["new_kind"] = kind_b
    elif ret_a != ret_b:
        change_entry["change_type"] = "return_type_modified"
    elif args_a != args_b:
        change_entry["change_type"] = "arguments_modified"
    else:
        # This can happen if reconstruct_signature has different defaults
        change_entry["change_type"] = "signature_modified_unknown"

    # Per your request: map to your specific output format
    # NOTE: The "sigce" field in your example is ambiguous.
    # I am interpreting it as "version where change was B".
    final_output = {
        "since": version_a_name,
        "until": version_b_name,
        "change_type": change_entry["change_type"],
        "old_signature": sig_a,
        "new_signature": sig_b,
        "semantic_change": change_entry["change_type"]
    }
    
    # Add extra context if kind changed
    if "old_kind" in change_entry:
        final_output["old_kind"] = change_entry["old_kind"]
        final_output["new_kind"] = change_entry["new_kind"]

    return final_output

def main():
    parser = argparse.ArgumentParser(description="Compare two ctags JSON files for API changes.")
    parser.add_argument("file_a", type=Path, help="Path to the first ctags JSON file (e.g., v5.15)")
    parser.add_argument("version_a", type=str, help="Version name for the first file (e.g., 'v5.15')")
    parser.add_argument("file_b", type=Path, help="Path to the second ctags JSON file (e.g., v6.1)")
    parser.add_argument("version_b", type=str, help="Version name for the second file (e.g., 'v6.1')")
    parser.add_argument("-o", "--output", type=Path, default="kernel_api_changes.json",
                        help="Output JSON file name (default: kernel_api_changes.json)")
    
    args = parser.parse_args()

    # Step 1: Parse both files
    symbols_a = parse_ctags_json(args.file_a)
    symbols_b = parse_ctags_json(args.file_b)

    # Step 2: Find all unique symbol names across both versions
    all_symbol_names = set(symbols_a.keys()) | set(symbols_b.keys())

    print(f"\n[+] Comparing {len(all_symbol_names)} total unique symbols...", file=sys.stderr)
    
    changes = {}

    # Step 3: Iterate and compare
    for name in sorted(all_symbol_names):
        tag_a = symbols_a.get(name)
        tag_b = symbols_b.get(name)

        # Normalize the name for the final JSON key (e.g., dma_map_single -> dma-map-single)
        json_key = name.replace("_", "-")
        
        change_detail = None

        if tag_a and not tag_b:
            # Symbol was removed
            change_detail = {
                "sigce": args.version_b,
                "change_type": "removed",
                "old_signature": reconstruct_signature(tag_a),
                "new_signature": "N/A (Symbol removed)",
                "semantic_change": "Symbol removal."
            }
        elif not tag_a and tag_b:
            # Symbol was added
            change_detail = {
                "sigce": args.version_b,
                "change_type": "added",
                "old_signature": "N/A (Symbol did not exist)",
                "new_signature": reconstruct_signature(tag_b),
                "semantic_change": "Added new symbol functionality."
            }
        elif tag_a and tag_b:
            # Symbol exists in both, check for modification
            change_detail = compare_tags(tag_a, tag_b, args.version_a, args.version_b)

        if change_detail:
            changes[json_key] = change_detail

    # Step 4: Write the final JSON report
    try:
        with open(args.output, 'w') as f:
            json.dump(changes, f, indent=4)
        
        print(f"\n[OK] Comparison complete. Report saved to: {args.output}", file=sys.stderr)
        print(f"   - Found {len(changes)} symbols with changes.", file=sys.stderr)

    except Exception as e:
        print(f"[!] Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()