#!/usr/bin/env python3
# comprehensive_analyzer.py - 综合分析脚本

import json
import sys
from pathlib import Path
from kernel_api_analyzer import KernelAPIAnalyzer
from subsystem_analyzer import SubsystemAnalyzer
from inline_function_analyzer import InlineFunctionAnalyzer
from abi_impact_analyzer import ABIImpactAnalyzer

def run_comprehensive_analysis(old_kernel, new_kernel, output_file='kernel_api_changes.json'):
    """运行完整的内核API变化分析"""
    
    print("="*60)
    print("Linux Kernel API 综合变化分析")
    print("="*60)
    print()
    
    # 步骤1: 基础API分析
    print("[1/5] 执行基础API分析...")
    api_analyzer = KernelAPIAnalyzer(old_kernel, new_kernel)
    changes = api_analyzer.analyze()
    
    # 步骤2: 子系统分析
    print("\n[2/5] 执行子系统语义分析...")
    subsys_analyzer = SubsystemAnalyzer(old_kernel, new_kernel)
    subsys_changes = subsys_analyzer.analyze_subsystem_changes(changes)
    changes['subsystem_analysis'] = subsys_changes
    
    # 步骤3: 内联函数分析
    print("\n[3/5] 执行内联函数语义分析...")
    inline_analyzer = InlineFunctionAnalyzer(old_kernel, new_kernel)
    inline_changes = inline_analyzer.analyze_inline_changes()
    changes['inline_functions'] = inline_changes
    
    # 步骤4: ABI影响分析
    print("\n[4/5] 执行ABI影响分析...")
    abi_analyzer = ABIImpactAnalyzer(changes)
    abi_impact = abi_analyzer.analyze_abi_impact()
    changes['abi_impact'] = abi_analyzer.generate_abi_report()
    
    # 步骤5: 保存结果
    print("\n[5/5] 保存分析结果...")
    with open(output_file, 'w') as f:
        json.dump(changes, f, indent=2, ensure_ascii=False)
    
    # 打印总结
    print("\n" + "="*60)
    print("分析完成!")
    print("="*60)
    print(f"\n结果文件: {output_file}")
    print(f"总变化数: {sum(s['total_changes'] for s in changes['summary'].values())}")
    print(f"ABI破坏性变化: {changes['abi_impact']['total_breaking_changes']}")
    print(f"  - 高严重性: {changes['abi_impact']['high_severity']}")
    print(f"  - 中严重性: {changes['abi_impact']['medium_severity']}")
    print(f"内联函数语义变化: {len(changes['inline_functions'])}")
    print(f"子系统分析: {len(changes['subsystem_analysis'])} 个子系统")
    
    return changes

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法: python3 comprehensive_analyzer.py <old_kernel_path> <new_kernel_path>")
        print("示例: python3 comprehensive_analyzer.py ~/kernel_analysis/linux-old ~/kernel_analysis/linux-new")
        sys.exit(1)
    
    old_kernel = sys.argv[1]
    new_kernel = sys.argv[2]
    
    run_comprehensive_analysis(old_kernel, new_kernel)