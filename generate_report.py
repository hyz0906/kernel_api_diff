#!/usr/bin/env python3
# generate_report.py - 生成HTML报告

import json
import sys
from datetime import datetime

def generate_html_report(changes_file):
    with open(changes_file, 'r') as f:
        data = json.load(f)
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Kernel API Changes Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px        }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .stat {{ display: inline-block; margin: 10px 20px; }}
        .added {{ color: #28a745; }}
        .removed {{ color: #dc3545; }}
        .modified {{ color: #ffc107; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th {{ background: #007bff; color: white; padding: 10px; text-align: left; }}
        td {{ border: 1px solid #ddd; padding: 8px; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .change-type {{ padding: 3px 8px; border-radius: 3px; font-size: 0.9em; }}
        .change-added {{ background: #d4edda; color: #155724; }}
        .change-removed {{ background: #f8d7da; color: #721c24; }}
        .change-modified {{ background: #fff3cd; color: #856404; }}
        .code {{ background: #f4f4f4; padding: 10px; border-left: 3px solid #007bff; 
                 font-family: monospace; margin: 10px 0; overflow-x: auto; }}
        .param-change {{ margin: 5px 0; padding: 5px; background: #fff; border-left: 2px solid #ffc107; }}
        .subsystem {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .semantic-pattern {{ background: #e7f3ff; padding: 10px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Linux Kernel API Changes Report</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Summary</h2>
"""
    
    # 添加统计摘要
    for category, stats in data.get('summary', {}).items():
        html += f"""
        <div class="stat">
            <strong>{category.upper()}</strong><br>
            <span class="added">+{stats['added']}</span> | 
            <span class="removed">-{stats['removed']}</span> | 
            <span class="modified">~{stats['modified']}</span>
        </div>
"""
    
    html += """
    </div>
"""
    
    # 函数变化
    html += generate_function_section(data.get('functions', []))
    
    # 结构体变化
    html += generate_struct_section(data.get('structs', []))
    
    # 宏变化
    html += generate_macro_section(data.get('macros', []))
    
    # 子系统分析
    if 'subsystem_analysis' in data:
        html += generate_subsystem_section(data['subsystem_analysis'])
    
    html += """
</body>
</html>
"""
    
    output_file = 'kernel_api_report.html'
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"HTML报告已生成: {output_file}")

def generate_function_section(functions):
    if not functions:
        return ""
    
    html = """
    <h2>Function Changes</h2>
    <table>
        <tr>
            <th>Function Name</th>
            <th>Change Type</th>
            <th>File</th>
            <th>Details</th>
        </tr>
"""
    
    for func in functions:
        change_type = func['change_type']
        change_class = f"change-{change_type}"
        
        details = ""
        if change_type == 'modified':
            details = f"""
                <div class="code">
                    <strong>Old:</strong> {func.get('old_signature', 'N/A')}<br>
                    <strong>New:</strong> {func.get('new_signature', 'N/A')}
                </div>
"""
            if func.get('parameter_changes'):
                details += "<strong>Parameter Changes:</strong><br>"
                for pchange in func['parameter_changes']:
                    details += f"<div class='param-change'>{format_param_change(pchange)}</div>"
            
            if func.get('return_type_changed'):
                details += f"""
                <div class='param-change'>
                    <strong>Return Type:</strong> {func.get('old_return_type')} → {func.get('new_return_type')}
                </div>
"""
        
        html += f"""
        <tr>
            <td><code>{func['name']}</code></td>
            <td><span class="change-type {change_class}">{change_type}</span></td>
            <td>{func.get('file', 'N/A')}</td>
            <td>{details}</td>
        </tr>
"""
    
    html += """
    </table>
"""
    return html

def format_param_change(pchange):
    ptype = pchange.get('type', '')
    
    if ptype == 'param_count_change':
        return f"Parameter count: {pchange['old_count']} → {pchange['new_count']}"
    elif ptype == 'param_type_change':
        return f"Param {pchange['position']} ({pchange['param_name']}): {pchange['old_type']} → {pchange['new_type']}"
    elif ptype == 'param_name_change':
        return f"Param {pchange['position']} renamed: {pchange['old_name']} → {pchange['new_name']}"
    elif ptype == 'param_added':
        return f"Added param {pchange['position']}: {pchange['param']}"
    elif ptype == 'param_removed':
        return f"Removed param {pchange['position']}: {pchange['param']}"
    else:
        return str(pchange)

def generate_struct_section(structs):
    if not structs:
        return ""
    
    html = """
    <h2>Structure Changes</h2>
    <table>
        <tr>
            <th>Structure Name</th>
            <th>Change Type</th>
            <th>File</th>
            <th>Field Changes</th>
        </tr>
"""
    
    for struct in structs:
        change_type = struct['change_type']
        change_class = f"change-{change_type}"
        
        details = ""
        if change_type == 'modified' and 'field_changes' in struct:
            fc = struct['field_changes']
            
            if fc.get('added'):
                details += "<strong>Added fields:</strong><br>"
                for field in fc['added']:
                    details += f"<div class='param-change'>+ {field}</div>"
            
            if fc.get('removed'):
                details += "<strong>Removed fields:</strong><br>"
                for field in fc['removed']:
                    details += f"<div class='param-change'>- {field}</div>"
            
            if fc.get('modified'):
                details += "<strong>Modified fields:</strong><br>"
                for mod in fc['modified']:
                    details += f"<div class='param-change'>~ Position {mod['position']}: {mod['change']}</div>"
        
        html += f"""
        <tr>
            <td><code>struct {struct['name']}</code></td>
            <td><span class="change-type {change_class}">{change_type}</span></td>
            <td>{struct.get('file', 'N/A')}</td>
            <td>{details}</td>
        </tr>
"""
    
    html += """
    </table>
"""
    return html

def generate_macro_section(macros):
    if not macros:
        return ""
    
    html = """
    <h2>Macro Changes</h2>
    <table>
        <tr>
            <th>Macro Name</th>
            <th>Change Type</th>
            <th>File</th>
            <th>Definition</th>
        </tr>
"""
    
    for macro in macros:
        change_type = macro['change_type']
        change_class = f"change-{change_type}"
        
        details = ""
        if change_type == 'modified':
            details = f"""
                <div class="code">
                    <strong>Old:</strong> {macro.get('old_definition', 'N/A')}<br>
                    <strong>New:</strong> {macro.get('new_definition', 'N/A')}
                </div>
"""
        
        html += f"""
        <tr>
            <td><code>{macro['name']}</code></td>
            <td><span class="change-type {change_class}">{change_type}</span></td>
            <td>{macro.get('file', 'N/A')}</td>
            <td>{details}</td>
        </tr>
"""
    
    html += """
    </table>
"""
    return html

def generate_subsystem_section(subsystems):
    html = """
    <h2>Subsystem Analysis</h2>
"""
    
    for subsys_name, subsys_data in subsystems.items():
        func_count = len(subsys_data.get('functions', []))
        struct_count = len(subsys_data.get('structs', []))
        
        html += f"""
    <div class="subsystem">
        <h3>{subsys_name.upper()} Subsystem</h3>
        <p>
            <strong>Changes:</strong> 
            {func_count} functions, {struct_count} structures
        </p>
"""
        
        # 语义变化模式
        patterns = subsys_data.get('semantic_changes', [])
        if patterns:
            html += "<h4>Detected Patterns:</h4>"
            for pattern in patterns:
                html += f"""
        <div class="semantic-pattern">
            <strong>{pattern['pattern'].replace('_', ' ').title()}</strong><br>
            {pattern['description']}<br>
            <em>Impact: {pattern['impact']}</em>
        </div>
"""
        
        html += """
    </div>
"""
    
    return html

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 generate_report.py kernel_api_changes.json")
        sys.exit(1)
    
    generate_html_report(sys.argv[1])