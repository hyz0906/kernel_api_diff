#!/usr/bin/env python3
# abi_impact_analyzer.py - ABI影响分析

class ABIImpactAnalyzer:
    def __init__(self, api_changes):
        self.api_changes = api_changes
        self.abi_breaking_changes = []
    
    def analyze_abi_impact(self):
        """分析ABI兼容性影响"""
        print("分析ABI影响...")
        
        # 检查结构体布局变化
        for struct in self.api_changes.get('structs', []):
            if struct['change_type'] == 'modified':
                impact = self._analyze_struct_abi_impact(struct)
                if impact:
                    self.abi_breaking_changes.append(impact)
        
        # 检查函数签名变化
        for func in self.api_changes.get('functions', []):
            if func['change_type'] == 'modified':
                impact = self._analyze_function_abi_impact(func)
                if impact:
                    self.abi_breaking_changes.append(impact)
        
        return self.abi_breaking_changes
    
    def _analyze_struct_abi_impact(self, struct):
        """分析结构体的ABI影响"""
        fc = struct.get('field_changes', {})
        
        # ABI破坏性变化
        breaking_reasons = []
        
        # 删除字段总是破坏ABI
        if fc.get('removed'):
            breaking_reasons.append('Fields removed')
        
        # 字段重排序可能破坏ABI
        if fc.get('modified'):
            breaking_reasons.append('Fields reordered')
        
        # 在中间添加字段破坏ABI
        if fc.get('added'):
            # 简化判断：任何字段添加都可能影响ABI
            breaking_reasons.append('Fields added (potential ABI break)')
        
        if breaking_reasons:
            return {
                'type': 'structure',
                'name': struct['name'],
                'file': struct['file'],
                'severity': 'high' if fc.get('removed') else 'medium',
                'reasons': breaking_reasons,
                'recommendation': 'Review all users of this structure'
            }
        
        return None
    
    def _analyze_function_abi_impact(self, func):
        """分析函数的ABI影响"""
        param_changes = func.get('parameter_changes', [])
        
        breaking_reasons = []
        
        # 参数数量变化
        count_changes = [p for p in param_changes if p['type'] == 'param_count_change']
        if count_changes:
            breaking_reasons.append('Parameter count changed')
        
        # 参数类型变化
        type_changes = [p for p in param_changes if p['type'] == 'param_type_change']
        if type_changes:
            breaking_reasons.append(f'{len(type_changes)} parameter type(s) changed')
        
        # 返回类型变化
        if func.get('return_type_changed'):
            breaking_reasons.append('Return type changed')
        
        if breaking_reasons:
            return {
                'type': 'function',
                'name': func['name'],
                'file': func['file'],
                'severity': 'high',
                'reasons': breaking_reasons,
                'recommendation': 'Update all callers'
            }
        
        return None
    
    def generate_abi_report(self):
        """生成ABI影响报告"""
        report = {
            'total_breaking_changes': len(self.abi_breaking_changes),
            'high_severity': len([c for c in self.abi_breaking_changes if c['severity'] == 'high']),
            'medium_severity': len([c for c in self.abi_breaking_changes if c['severity'] == 'medium']),
            'changes': self.abi_breaking_changes
        }
        
        return report