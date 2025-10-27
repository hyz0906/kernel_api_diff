#!/usr/bin/env python3
# kernel_api_analyzer.py - 主分析脚本

import json
import sys
from pathlib import Path
from parse_ctags import parse_kernel_tags
from analyze_source_diff import SourceDiffAnalyzer

class KernelAPIAnalyzer:
    def __init__(self, old_kernel, new_kernel):
        self.old_kernel = old_kernel
        self.new_kernel = new_kernel
        self.analyzer = SourceDiffAnalyzer(old_kernel, new_kernel)
        self.changes = {
            'functions': [],
            'structs': [],
            'macros': [],
            'typedefs': [],
            'enums': [],
            'summary': {}
        }
        
    def analyze(self):
        """执行完整分析"""
        print("步骤 1: 解析旧版本 ctags...")
        old_symbols = parse_kernel_tags(self.old_kernel)
        
        print("步骤 2: 解析新版本 ctags...")
        new_symbols = parse_kernel_tags(self.new_kernel)
        
        print("步骤 3: 分析函数变化...")
        self._analyze_functions(old_symbols['functions'], new_symbols['functions'])
        
        print("步骤 4: 分析结构体变化...")
        self._analyze_structs(old_symbols['structs'], new_symbols['structs'])
        
        print("步骤 5: 分析宏变化...")
        self._analyze_macros(old_symbols['macros'], new_symbols['macros'])
        
        print("步骤 6: 分析类型定义变化...")
        self._analyze_typedefs(old_symbols['typedefs'], new_symbols['typedefs'])
        
        print("步骤 7: 生成统计摘要...")
        self._generate_summary()
        
        return self.changes
        
    def _analyze_functions(self, old_funcs, new_funcs):
        """分析函数变化"""
        old_names = set(old_funcs.keys())
        new_names = set(new_funcs.keys())
        
        # 新增的函数
        for name in new_names - old_names:
            self.changes['functions'].append({
                'name': name,
                'change_type': 'added',
                'file': new_funcs[name]['file'],
                'line': new_funcs[name]['line'],
                'signature': new_funcs[name]['signature']
            })
            
        # 删除的函数
        for name in old_names - new_names:
            self.changes['functions'].append({
                'name': name,
                'change_type': 'removed',
                'file': old_funcs[name]['file'],
                'line': old_funcs[name]['line'],
                'signature': old_funcs[name]['signature']
            })
            
        # 可能修改的函数
        for name in old_names & new_names:
            old_func = old_funcs[name]
            new_func = new_funcs[name]
            
            # 提取完整签名
            old_file = Path(self.old_kernel) / old_func['file']
            new_file = Path(self.new_kernel) / new_func['file']
            
            old_sig = self.analyzer.extract_function_signature(
                old_file, name, old_func['line']
            )
            new_sig = self.analyzer.extract_function_signature(
                new_file, name, new_func['line']
            )
            
            if old_sig != new_sig:
                # 解析参数
                old_params = self.analyzer.parse_function_parameters(old_sig)
                new_params = self.analyzer.parse_function_parameters(new_sig)
                
                param_changes = self.analyzer.compare_function_parameters(
                    old_params, new_params
                )
                
                # 检查返回类型
                old_return = old_sig.split('(')[0].strip().split()[-1]
                new_return = new_sig.split('(')[0].strip().split()[-1]
                
                self.changes['functions'].append({
                    'name': name,
                    'change_type': 'modified',
                    'file': new_func['file'],
                    'old_signature': old_sig,
                    'new_signature': new_sig,
                    'old_line': old_func['line'],
                    'new_line': new_func['line'],
                    'return_type_changed': old_return != new_return,
                    'old_return_type': old_return,
                    'new_return_type': new_return,
                    'parameter_changes': param_changes
                })
                
    def _analyze_structs(self, old_structs, new_structs):
        """分析结构体变化"""
        old_names = set(old_structs.keys())
        new_names = set(new_structs.keys())
        
        # 新增结构体
        for name in new_names - old_names:
            self.changes['structs'].append({
                'name': name,
                'change_type': 'added',
                'file': new_structs[name]['file']
            })
            
        # 删除结构体
        for name in old_names - new_names:
            self.changes['structs'].append({
                'name': name,
                'change_type': 'removed',
                'file': old_structs[name]['file']
            })
            
        # 修改的结构体
        for name in old_names & new_names:
            old_struct = old_structs[name]
            new_struct = new_structs[name]
            
            old_file = Path(self.old_kernel) / old_struct['file']
            new_file = Path(self.new_kernel) / new_struct['file']
            
            old_fields = self.analyzer.extract_struct_fields(
                old_file, name, old_struct['line']
            )
            new_fields = self.analyzer.extract_struct_fields(
                new_file, name, new_struct['line']
            )
            
            if old_fields != new_fields:
                field_changes = self.analyzer.compare_struct_fields(
                    old_fields, new_fields
                )
                
                self.changes['structs'].append({
                    'name': name,
                    'change_type': 'modified',
                    'file': new_struct['file'],
                    'field_changes': field_changes
                })
                
    def _analyze_macros(self, old_macros, new_macros):
        """分析宏变化"""
        old_names = set(old_macros.keys())
        new_names = set(new_macros.keys())
        
        for name in new_names - old_names:
            self.changes['macros'].append({
                'name': name,
                'change_type': 'added',
                'file': new_macros[name]['file']
            })
            
        for name in old_names - new_names:
            self.changes['macros'].append({
                'name': name,
                'change_type': 'removed',
                'file': old_macros[name]['file']
            })
            
        for name in old_names & new_names:
            if old_macros[name]['signature'] != new_macros[name]['signature']:
                self.changes['macros'].append({
                    'name': name,
                    'change_type': 'modified',
                    'file': new_macros[name]['file'],
                    'old_definition': old_macros[name]['signature'],
                    'new_definition': new_macros[name]['signature']
                })
                
    def _analyze_typedefs(self, old_types, new_types):
        """分析typedef变化"""
        old_names = set(old_types.keys())
        new_names = set(new_types.keys())
        
        for name in new_names - old_names:
            self.changes['typedefs'].append({
                'name': name,
                'change_type': 'added',
                'file': new_types[name]['file']
            })
            
        for name in old_names - new_names:
            self.changes['typedefs'].append({
                'name': name,
                'change_type': 'removed',
                'file': old_types[name]['file']
            })
            
    def _generate_summary(self):
        """生成统计摘要"""
        for category in ['functions', 'structs', 'macros', 'typedefs']:
            items = self.changes[category]
            self.changes['summary'][category] = {
                'added': len([x for x in items if x['change_type'] == 'added']),
                'removed': len([x for x in items if x['change_type'] == 'removed']),
                'modified': len([x for x in items if x['change_type'] == 'modified']),
                'total_changes': len(items)
            }
            
    def save_results(self, output_file='kernel_api_changes.json'):
        """保存结果到JSON文件"""
        with open(output_file, 'w') as f:
            json.dump(self.changes, f, indent=2)
        print(f"\n分析完成! 结果已保存到: {output_file}")

def main():
    if len(sys.argv) != 3:
        print("用法: python3 kernel_api_analyzer.py <old_kernel_path> <new_kernel_path>")
        sys.exit(1)
        
    old_kernel = sys.argv[1]
    new_kernel = sys.argv[2]
    
    analyzer = KernelAPIAnalyzer(old_kernel, new_kernel)
    analyzer.analyze()
    analyzer.save_results()
    
    # 打印摘要
    print("\n=== 变化摘要 ===")
    for category, stats in analyzer.changes['summary'].items():
        print(f"\n{category.upper()}:")
        print(f"  新增: {stats['added']}")
        print(f"  删除: {stats['removed']}")
        print(f"  修改: {stats['modified']}")
        print(f"  总计: {stats['total_changes']}")

if __name__ == '__main__':
    main()