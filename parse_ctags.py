#!/usr/bin/env python3
# parse_ctags.py - 解析ctags JSON输出

import json
import re
from collections import defaultdict
from pathlib import Path

class CTagsParser:
    def __init__(self, tags_file):
        self.tags_file = tags_file
        self.functions = {}
        self.macros = {}
        self.structs = {}
        self.typedefs = {}
        self.enums = {}
        
    def parse(self):
        """解析ctags JSON输出"""
        with open(self.tags_file, 'r') as f:
            for line in f:
                try:
                    tag = json.loads(line.strip())
                    self._process_tag(tag)
                except json.JSONDecodeError:
                    continue
                    
    def _process_tag(self, tag):
        """处理单个tag条目"""
        name = tag.get('name')
        kind = tag.get('kind')
        path = tag.get('path')
        signature = tag.get('signature', '')
        line = tag.get('line', 0)
        
        # 过滤非头文件和内部实现
        if not self._is_public_api(path):
            return
            
        tag_info = {
            'name': name,
            'file': path,
            'line': line,
            'signature': signature,
            'scope': tag.get('scope', ''),
            'access': tag.get('access', 'public')
        }
        
        if kind == 'function':
            self.functions[name] = tag_info
        elif kind == 'macro':
            self.macros[name] = tag_info
        elif kind == 'struct':
            self.structs[name] = tag_info
        elif kind == 'typedef':
            self.typedefs[name] = tag_info
        elif kind == 'enum':
            self.enums[name] = tag_info
            
    def _is_public_api(self, path):
        """判断是否为公开API"""
        if not path:
            return False
        # 只分析include目录下的头文件
        return 'include/' in path and path.endswith('.h')
        
    def get_all_symbols(self):
        """获取所有符号"""
        return {
            'functions': self.functions,
            'macros': self.macros,
            'structs': self.structs,
            'typedefs': self.typedefs,
            'enums': self.enums
        }

def parse_kernel_tags(kernel_path):
    """解析内核tags"""
    tags_file = Path(kernel_path) / "tags.json"
    parser = CTagsParser(tags_file)
    parser.parse()
    return parser.get_all_symbols()