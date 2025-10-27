#!/usr/bin/env python3
# subsystem_analyzer.py - 子系统语义分析

import os
import re
from collections import defaultdict

class SubsystemAnalyzer:
    def __init__(self, old_kernel, new_kernel):
        self.old_kernel = old_kernel
        self.new_kernel = new_kernel
        self.subsystems = self._identify_subsystems()
        
    def _identify_subsystems(self):
        """识别内核子系统"""
        return {
            'mm': 'include/linux/mm*.h',
            'fs': 'include/linux/fs*.h',
            'net': 'include/linux/net*.h include/net/',
            'drivers': 'include/linux/device*.h include/linux/driver*.h',
            'sched': 'include/linux/sched*.h',
            'block': 'include/linux/blk*.h',
            'crypto': 'include/linux/crypto*.h include/crypto/',
        }
        
    def analyze_subsystem_changes(self, api_changes):
        """分析子系统级别的变化"""
        subsystem_changes = defaultdict(lambda: {
            'functions': [],
            'structs': [],
            'semantic_changes': []
        })
        
        for func_change in api_changes['functions']:
            subsys = self._categorize_file(func_change['file'])
            if subsys:
                subsystem_changes[subsys]['functions'].append(func_change)
                
        for struct_change in api_changes['structs']:
            subsys = self._categorize_file(struct_change['file'])
            if subsys:
                subsystem_changes[subsys]['structs'].append(struct_change)
                
        # 检测语义变化模式
        for subsys, changes in subsystem_changes.items():
            semantic = self._detect_semantic_patterns(subsys, changes)
            subsystem_changes[subsys]['semantic_changes'] = semantic
            
        return dict(subsystem_changes)
        
    def _categorize_file(self, file_path):
        """将文件归类到子系统"""
        for subsys, pattern in self.subsystems.items():
            if any(p in file_path for p in pattern.split()):
                return subsys
        return 'other'
        
    def _detect_semantic_patterns(self, subsys, changes):
        """检测语义变化模式"""
        patterns = []
        
        # 检测参数添加模式
        func_changes = changes['functions']
        param_additions = [f for f in func_changes 
                          if f.get('change_type') == 'modified' 
                          and any(p['type'] == 'param_added' 
                                 for p in f.get('parameter_changes', []))]
        
        if len(param_additions) > 5:
            patterns.append({
                'pattern': 'widespread_parameter_addition',
                'description': f'{len(param_additions)} functions had parameters added',
                'impact': 'API extension',
                'affected_functions': [f['name'] for f in param_additions]
            })
            
        # 检测结构体扩展模式
        struct_changes = changes['structs']
        extended_structs = [s for s in struct_changes
                           if s.get('change_type') == 'modified'
                           and len(s.get('field_changes', {}).get('added', [])) > 0]
        
        if len(extended_structs) > 3:
            patterns.append({
                'pattern': 'data_structure_evolution',
                'description': f'{len(extended_structs)} structures were extended',
                'impact': 'ABI potentially affected',
                'affected_structs': [s['name'] for s in extended_structs]
            })
            
        return patterns