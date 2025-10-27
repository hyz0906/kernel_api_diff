#!/usr/bin/env python3

"""
Generates a CSV file and an HTML report from a kernel_api_changes.json file.

The input JSON is expected to have a structure like:
{
    "symbol-name": {
        "change_type": "...",
        "old_signature": "...",
        "new_signature": "...",
        "semantic_change": "..."
    },
    ...
}
"""

import json
import csv
import html
import argparse
import sys
import os
from datetime import datetime

def generate_csv_report(data, csv_filepath):
    """Converts the JSON data to a CSV file."""
    
    print(f"[+] Generating CSV report at: {csv_filepath}")
    
    # 1. 动态确定所有可能的表头
    # 我们总是希望 'symbol' 在第一位
    headers = set(['symbol'])
    for details in data.values():
        headers.update(details.keys())
        
    # 定义一个期望的顺序，不存在的键将不会被添加
    field_order = [
        'symbol', 'change_type', 'sigce', 'old_signature', 
        'new_signature', 'semantic_change', 'old_kind', 'new_kind'
    ]
    
    # 过滤，只保留数据中实际存在的表头
    final_headers = [h for h in field_order if h in headers]
    # 添加数据中存在但不在期望列表中的其他表头
    final_headers.extend(sorted(list(headers - set(final_headers))))

    try:
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=final_headers)
            writer.writeheader()
            
            for symbol, details in data.items():
                # 创建一个新字典，包含符号名称
                row_data = details.copy()
                row_data['symbol'] = symbol
                writer.writerow(row_data)
                
    except IOError as e:
        print(f"[!] Error writing CSV file: {e}", file=sys.stderr)
        return False
        
    print(f"    ... CSV report generated successfully.")
    return True


def generate_html_report(data, html_filepath, versions_info):
    """Converts the JSON data to a standalone HTML report file with improved column widths."""
    
    print(f"[+] Generating HTML report at: {html_filepath}")

    # 1. Define HTML and CSS template
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kernel API Change Report</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, 
                         Helvetica, Arial, sans-serif; 
            line-height: 1.6; 
            background-color: #f9f9f9;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        h1, h2 {{ 
            color: #111;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            background-color: #fff;
            table-layout: fixed; /* Crucial for controlling width */
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px 15px; 
            text-align: left;
            vertical-align: top;
            word-break: break-word;
        }}
        th {{ 
            background-color: #f2f2f2; 
            color: #333;
            font-weight: 600;
        }}
        
        /* --- Column Width Adjustments --- */
        /* Col 1: Symbol Name */
        table th:nth-child(1), table td:nth-child(1) {{ width: 15%; }}
        /* Col 2: Change Type (Narrower, as requested) */
        table th:nth-child(2), table td:nth-child(2) {{ width: 10%; }}
        /* Col 3: Old Signature */
        table th:nth-child(3), table td:nth-child(3) {{ width: 25%; }}
        /* Col 4: New Signature */
        table th:nth-child(4), table td:nth-child(4) {{ width: 25%; }}
        /* Col 5: Semantic Impact (Wider, as requested) */
        table th:nth-child(5), table td:nth-child(5) {{ width: 25%; }}
        /* -------------------------------- */
        
        tr:nth-child(even) {{ background-color: #fcfcfc; }}
        tr:hover {{ background-color: #f1f1f1; }}
        code {{ 
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
            background-color: #eee;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 0.9em;
            white-space: pre-wrap; /* Allows code to wrap */
        }}
        .symbol-name {{ font-weight: 700; }}
        
        /* Based on change type styles */
        .change-added {{ background-color: #e6ffed; }}
        .change-removed {{ background-color: #ffeef0; }}
        .change-modified {{ background-color: #fff8e1; }}
        .change-return_type_modified {{ background-color: #fff0e1; }}
        .change-arguments_modified {{ background-color: #f0f8ff; }}
        
        .change-added .change-type {{ color: #228B22; font-weight: 700; }}
        .change-removed .change-type {{ color: #D9534F; font-weight: 700; }}
        .change-modified .change-type {{ color: #F0AD4E; font-weight: 700; }}
        .change-return_type_modified .change-type {{ color: #E67E22; font-weight: 700; }}
        .change-arguments_modified .change-type {{ color: #3498DB; font-weight: 700; }}

        .todo {{ color: #D9534F; font-weight: 700; }}
    </style>
</head>
<body>
    <h1>Kernel API Change Report</h1>
    <h2>Comparison between {version_a} and {version_b}</h2>
    <p>Generated on: {generation_date}</p>
    
    <table>
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Change Type</th>
                <th>Old Signature / Value</th>
                <th>New Signature / Value</th>
                <th>Semantic Impact (Manual Analysis)</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
</body>
</html>
    """

    # 2. Generate table rows (same logic as before)
    table_rows = []
    
    for symbol, details in sorted(data.items(), key=lambda item: item[0]):
        change_type = html.escape(details.get('change_type', 'unknown'))
        semantic = html.escape(details.get("semantic_change", ""))
        if "TODO" in semantic:
            semantic = f'<span class="todo">{semantic}</span>'

        row_class = f"change-{change_type}"

        table_rows.append(f'            <tr class="{row_class}">')
        table_rows.append(f'                <td class="symbol-name">{html.escape(symbol)}</td>')
        table_rows.append(f'                <td class="change-type">{change_type.replace("_", " ").title()}</td>')
        table_rows.append(f'                <td><code>{html.escape(details.get("old_signature", "N/A"))}</code></td>')
        table_rows.append(f'                <td><code>{html.escape(details.get("new_signature", "N/A"))}</code></td>')
        table_rows.append(f'                <td>{semantic}</td>')
        table_rows.append('            </tr>')

    # 3. Fill template (same logic as before)
    final_html = html_template.format(
        version_a=html.escape(versions_info.get("version_a", "vA")),
        version_b=html.escape(versions_info.get("version_b", "vB")),
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        table_rows="\n".join(table_rows)
    )

    # 4. Write to file (same logic as before)
    try:
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(final_html)
    except IOError as e:
        print(f"[!] Error writing HTML file: {e}", file=sys.stderr)
        return False

    print(f"    ... HTML report generated successfully.")
    return True


def generate_html_report_bak(data, html_filepath, versions_info):
    """Converts the JSON data to a standalone HTML report file."""
    
    print(f"[+] Generating HTML report at: {html_filepath}")

    # 1. 定义HTML和CSS模板
    # CSS为不同类型的变更提供了视觉提示
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kernel API Change Report</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, 
                         Helvetica, Arial, sans-serif; 
            line-height: 1.6; 
            background-color: #f9f9f9;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        h1, h2 {{ 
            color: #111;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            background-color: #fff;
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px 15px; 
            text-align: left;
            vertical-align: top;
            word-break: break-word;
        }}
        th {{ 
            background-color: #f2f2f2; 
            color: #333;
            font-weight: 600;
        }}
        tr:nth-child(even) {{ background-color: #fcfcfc; }}
        tr:hover {{ background-color: #f1f1f1; }}
        code {{ 
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
            background-color: #eee;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 0.9em;
            white-space: pre-wrap; /* 允许代码换行 */
        }}
        .symbol-name {{ font-weight: 700; }}
        
        /* 基于变更类型的样式 */
        .change-added {{ background-color: #e6ffed; }}
        .change-removed {{ background-color: #ffeef0; }}
        .change-modified {{ background-color: #fff8e1; }}
        .change-return_type_modified {{ background-color: #fff0e1; }}
        .change-arguments_modified {{ background-color: #f0f8ff; }}
        
        .change-added .change-type {{ color: #228B22; font-weight: 700; }}
        .change-removed .change-type {{ color: #D9534F; font-weight: 700; }}
        .change-modified .change-type {{ color: #F0AD4E; font-weight: 700; }}
        .change-return_type_modified .change-type {{ color: #E67E22; font-weight: 700; }}
        .change-arguments_modified .change-type {{ color: #3498DB; font-weight: 700; }}

        .todo {{ color: #D9534F; font-weight: 700; }}
    </style>
</head>
<body>
    <h1>Kernel API Change Report</h1>
    <h2>Comparison between {version_a} and {version_b}</h2>
    <p>Generated on: {generation_date}</p>
    
    <table>
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Change Type</th>
                <th>Old Signature / Value</th>
                <th>New Signature / Value</th>
                <th>Semantic Impact (Manual Analysis)</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
</body>
</html>
    """

    # 2. 生成表格行
    table_rows = []
    
    # 按符号名称排序
    for symbol, details in sorted(data.items(), key=lambda item: item[0]):
        change_type = html.escape(details.get('change_type', 'unknown'))
        
        # 为包含 "TODO" 的语义添加特殊样式
        semantic = html.escape(details.get("semantic_change", ""))
        if "TODO" in semantic:
            semantic = f'<span class="todo">{semantic}</span>'

        # 为不同变更类型添加CSS类
        row_class = f"change-{change_type}"

        table_rows.append(f'            <tr class="{row_class}">')
        table_rows.append(f'                <td class="symbol-name">{html.escape(symbol)}</td>')
        table_rows.append(f'                <td class="change-type">{change_type.replace("_", " ").title()}</td>')
        table_rows.append(f'                <td><code>{html.escape(details.get("old_signature", "N/A"))}</code></td>')
        table_rows.append(f'                <td><code>{html.escape(details.get("new_signature", "N/A"))}</code></td>')
        table_rows.append(f'                <td>{semantic}</td>')
        table_rows.append('            </tr>')

    # 3. 填充模板
    final_html = html_template.format(
        version_a=html.escape(versions_info.get("version_a", "vA")),
        version_b=html.escape(versions_info.get("version_b", "vB")),
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        table_rows="\n".join(table_rows)
    )

    # 4. 写入文件
    try:
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(final_html)
    except IOError as e:
        print(f"[!] Error writing HTML file: {e}", file=sys.stderr)
        return False

    print(f"    ... HTML report generated successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Convert Kernel API Changes JSON to CSV and HTML reports.")
    parser.add_argument("input_json", 
                        help="Path to the input JSON file (e.g., kernel_api_changes.json)")
    parser.add_argument("-c", "--csv", 
                        default="api_changes_report.csv",
                        help="Path for the output CSV file (default: api_changes_report.csv)")
    parser.add_argument("-H", "--html", 
                        default="api_changes_report.html",
                        help="Path for the output HTML file (default: api_changes_report.html)")
    parser.add_argument("--vA", default="vA", help="Name of version A (for report title)")
    parser.add_argument("--vB", default="vB", help="Name of version B (for report title)")

    args = parser.parse_args()

    # 1. 检查输入文件
    if not os.path.exists(args.input_json):
        print(f"[!] Error: Input file not found: {args.input_json}", file=sys.stderr)
        sys.exit(1)

    # 2. 加载JSON数据
    try:
        with open(args.input_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[!] Error: Failed to parse JSON file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[!] An error occurred while reading the file: {e}", file=sys.stderr)
        sys.exit(1)

    # 检查JSON是否是我们期望的格式（字典）
    if not isinstance(data, dict):
        print(f"[!] Error: JSON file is not in the expected format (top-level dictionary).", file=sys.stderr)
        sys.exit(1)
        
    # 检查JSON是否包含顶层元数据
    # （这是我在第一个回答中建议的格式）
    report_data = data
    versions_info = {"version_a": args.vA, "version_b": args.vB}
    if "metadata" in data and "api_changes" in data:
        print("[i] Detected metadata in JSON. Using 'api_changes' list/dict.")
        # 兼容列表和字典两种格式
        api_changes = data["api_changes"]
        if isinstance(api_changes, list):
             # 转换列表为字典，假设 'element_name' 是key
            report_data = {item.get('element_name', f'unknown_{i}'): item for i, item in enumerate(api_changes)}
        elif isinstance(api_changes, dict):
            report_data = api_changes
        
        # 自动从元数据填充版本
        versions_info["version_a"] = data["metadata"].get("version_A", args.vA)
        versions_info["version_b"] = data["metadata"].get("version_B", args.vB)


    if not report_data:
        print("[w] Warning: No API changes found in the JSON data. Reports will be empty.")

    # 3. 生成报告
    csv_ok = generate_csv_report(report_data, args.csv)
    html_ok = generate_html_report(report_data, args.html, versions_info)

    if csv_ok and html_ok:
        print("\n[OK] All reports generated successfully.")
    else:
        print("\n[!] One or more reports failed to generate.")
        sys.exit(1)

if __name__ == "__main__":
    main()