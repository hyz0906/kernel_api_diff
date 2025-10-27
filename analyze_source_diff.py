#!/usr/bin/env python3
# analyze_source_diff.py - 分析源码级别的差异

import re
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class FunctionChange:
    name: str
    old_signature: str
    new_signature: str
    param_changes: List[Dict]
    return_type_changed: bool
    file: str
    old_line: int
    new_line: int

@dataclass
class StructChange:
    name: str
    added_fields: List[str]
    removed_fields: List[str]
    modified_fields: List[Dict]
    file: str
    
@dataclass
class MacroChange:
    name: str
    old_definition: str
    new_definition: str
    semantic_change: str
    file: str

class SourceDiffAnalyzer:
    def __init__(self, old_kernel, new_kernel):
        self.old_kernel = Path(old_kernel)
        self.new_kernel = Path(new_kernel)
        
    def extract_function_signature(self, file_path, function_name, line_num):
        """从源文件提取完整函数签名"""
        try:
            with open(file_path, 'r', errors='ignore') as f:
                lines = f.readlines()
                
            # 从函数定义行开始，找到完整签名
            signature_lines = []
            brace_count = 0
            found_brace = False
            
            for i in range(max(0, line_num - 1), min(len(lines), line_num + 20)):
                line = lines[i].strip()
                signature_lines.append(line)
                
                if '{' in line:
                    found_brace = True
                    break
                if ';' in line:  # 函数声明
                    break
                    
            signature = ' '.join(signature_lines)
            # 清理签名
            signature = re.sub(r'\s+', ' ', signature)
            signature = signature.split('{')[0].strip()
            
            return signature
        except Exception as e:
            return ""
            
    def parse_function_parameters(self, signature):
        """解析函数参数"""
        # 提取参数部分
        match = re.search(r'\((.*?)\)', signature)
        if not match:
            return []
            
        params_str = match.group(1).strip()
        if not params_str or params_str == 'void':
            return []
            
        # 分割参数
        params = []
        depth = 0
        current_param = []
        
        for char in params_str + ',':
            if char == ',' and depth == 0:
                param = ''.join(current_param).strip()
                if param:
                    params.append(self._parse_single_param(param))
                current_param = []
            else:
                if char in '([{':
                    depth += 1
                elif char in ')]}':
                    depth -= 1
                current_param.append(char)
                
        return params
        
    def _parse_single_param(self, param):
        """解析单个参数"""
        # 移除多余空格
        param = re.sub(r'\s+', ' ', param.strip())
        
        # 尝试分离类型和名称
        parts = param.rsplit(None, 1)
        if len(parts) == 2:
            param_type, param_name = parts
            # 处理指针
            if param_name.startswith('*'):
                param_type += ' *'
                param_name = param_name.lstrip('*')
        else:
            param_type = param
            param_name = ''
            
        return {
            'type': param_type.strip(),
            'name': param_name.strip(),
            'full': param
        }
        
    def compare_function_parameters(self, old_params, new_params):
        """比较函数参数变化"""
        changes = []
        
        # 参数数量变化
        if len(old_params) != len(new_params):
            changes.append({
                'type': 'param_count_change',
                'old_count': len(old_params),
                'new_count': len(new_params)
            })
            
        # 逐个比较参数
        for i in range(min(len(old_params), len(new_params))):
            old_p = old_params[i]
            new_p = new_params[i]
            
            if old_p['type'] != new_p['type']:
                changes.append({
                    'type': 'param_type_change',
                    'position': i,
                    'old_type': old_p['type'],
                    'new_type': new_p['type'],
                    'param_name': new_p.get('name', old_p.get('name', f'param{i}'))
                })
                
            if old_p.get('name') and new_p.get('name') and old_p['name'] != new_p['name']:
                changes.append({
                    'type': 'param_name_change',
                    'position': i,
                    'old_name': old_p['name'],
                    'new_name': new_p['name']
                })
                
        # 新增参数
        if len(new_params) > len(old_params):
            for i in range(len(old_params), len(new_params)):
                changes.append({
                    'type': 'param_added',
                    'position': i,
                    'param': new_params[i]['full']
                })
                
        # 删除参数
        if len(old_params) > len(new_params):
            for i in range(len(new_params), len(old_params)):
                changes.append({
                    'type': 'param_removed',
                    'position': i,
                    'param': old_params[i]['full']
                })
                
        return changes
        
    def extract_struct_fields(self, file_path, struct_name, line_num):
        """提取结构体字段"""
        try:
            with open(file_path, 'r', errors='ignore') as f:
                lines = f.readlines()
                
            fields = []
            in_struct = False
            brace_count = 0
            
            for i in range(max(0, line_num - 1), min(len(lines), line_num + 500)):
                line = lines[i].strip()
                
                if 'struct' in line and struct_name in line and '{' in line:
                    in_struct = True
                    brace_count = 1
                    continue
                    
                if in_struct:
                    brace_count += line.count('{') - line.count('}')
                    
                    if brace_count == 0:
                        break
                        
                    # 解析字段
                    if ';' in line and not line.startswith('//'):
                        field = line.split(';')[0].strip()
                        if field and not field.startswith('/*'):
                            fields.append(field)
                            
            return fields
        except Exception as e:
            return []
            
    def compare_struct_fields(self, old_fields, new_fields):
        """比较结构体字段变化"""
        old_set = set(old_fields)
        new_set = set(new_fields)
        
        added = list(new_set - old_set)
        removed = list(old_set - new_set)
        
        # 检查字段修改（位置或类型变化）
        modified = []
        for i, (old_f, new_f) in enumerate(zip(old_fields, new_fields)):
            if old_f != new_f and old_f in new_set and new_f in old_set:
                modified.append({
                    'position': i,
                    'old': old_f,
                    'new': new_f,
                    'change': 'reordered'
                })
                
        return {
            'added': added,
            'removed': removed,
            'modified': modified
        }