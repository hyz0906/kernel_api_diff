#!/usr/bin/env python3
# inline_function_analyzer.py - 内联函数语义分析

import re
from pathlib import Path

class InlineFunctionAnalyzer:
    def __init__(self, old_kernel, new_kernel):
        self.old_kernel = Path(old_kernel)
        self.new_kernel = Path(new_kernel)
    
    def find_inline_functions(self, kernel_path):
        """查找所有内联函数"""
        inline_funcs = {}
        
        # 遍历所有头文件
        for header in kernel_path.glob('include/**/*.h'):
            try:
                with open(header, 'r', errors='ignore') as f:
                    content = f.read()
                
                # 匹配内联函数定义
                pattern = r'(?:static\s+)?inline\s+\w+\s+(\w+)\s*\([^)]*\)\s*\{[^}]*\}'
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    func_name = match.group(1)
                    func_body = match.group(0)
                    
                    inline_funcs[func_name] = {
                        'file': str(header.relative_to(kernel_path)),
                        'definition': func_body,
                        'body_hash': hash(func_body)
                    }
            except Exception as e:
                continue
        
        return inline_funcs
    
    def analyze_inline_changes(self):
        """分析内联函数的语义变化"""
        print("分析内联函数变化...")
        
        old_inlines = self.find_inline_functions(self.old_kernel)
        new_inlines = self.find_inline_functions(self.new_kernel)
        
        changes = []
        
        # 检查修改的内联函数
        for name in set(old_inlines.keys()) & set(new_inlines.keys()):
            old_func = old_inlines[name]
            new_func = new_inlines[name]
            
            if old_func['body_hash'] != new_func['body_hash']:
                semantic_change = self._analyze_semantic_change(
                    old_func['definition'],
                    new_func['definition']
                )
                
                changes.append({
                    'name': name,
                    'file': new_func['file'],
                    'change_type': 'semantic_change',
                    'old_definition': old_func['definition'],
                    'new_definition': new_func['definition'],
                    'semantic_analysis': semantic_change
                })
        
        return changes
    
    def _analyze_semantic_change(self, old_def, new_def):
        """分析语义变化类型"""
        changes = []
        
        # 检查是否添加了新的函数调用
        old_calls = set(re.findall(r'\b(\w+)\s*\(', old_def))
        new_calls = set(re.findall(r'\b(\w+)\s*\(', new_def))
        
        added_calls = new_calls - old_calls
        removed_calls = old_calls - new_calls
        
        if added_calls:
            changes.append({
                'type': 'new_function_calls',
                'functions': list(added_calls)
            })
        
        if removed_calls:
            changes.append({
                'type': 'removed_function_calls',
                'functions': list(removed_calls)
            })
        
        # 检查返回值变化
        old_returns = re.findall(r'return\s+([^;]+);', old_def)
        new_returns = re.findall(r'return\s+([^;]+);', new_def)
        
        if old_returns != new_returns:
            changes.append({
                'type': 'return_value_logic_change',
                'details': 'Return statement modified'
            })
        
        # 检查条件逻辑变化
        old_ifs = len(re.findall(r'\bif\s*\(', old_def))
        new_ifs = len(re.findall(r'\bif\s*\(', new_def))
        
        if old_ifs != new_ifs:
            changes.append({
                'type': 'control_flow_change',
                'old_branches': old_ifs,
                'new_branches': new_ifs
            })
        
        return changes