"""
字符串提取器
从二进制文件中提取字符串并进行分类分析
"""

import re
import os
from collections import Counter, defaultdict
from typing import List, Dict, Set


class StringExtractor:
    """字符串提取器"""
    
    def __init__(self, min_length: int = 4):
        """初始化字符串提取器
        
        Args:
            min_length: 最小字符串长度
        """
        self.min_length = min_length
        self.string_patterns = {
            'urls': re.compile(r'https?://[^\s\x00-\x1f\x7f-\x9f]+', re.IGNORECASE),
            'apis': re.compile(r'/api/[^\s\x00-\x1f\x7f-\x9f]*', re.IGNORECASE),
            'errors': re.compile(r'(?i)(error|failed|exception|invalid|warning|alert|fault)', re.IGNORECASE),
            'bundle_ids': re.compile(r'[a-zA-Z][a-zA-Z0-9]*\.[a-zA-Z][a-zA-Z0-9]*\.[a-zA-Z][a-zA-Z0-9]*'),
            'file_paths': re.compile(r'[./][^\s\x00-\x1f\x7f-\x9f]*\.(png|jpg|jpeg|gif|mp3|wav|m4a|json|plist|xml|txt|pdf)', re.IGNORECASE),
            'domains': re.compile(r'[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}'),
            'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            'version': re.compile(r'\d+\.\d+(\.\d+)?'),
            'coordinates': re.compile(r'-?\d+\.\d+,-?\d+\.\d+'),
            'numbers': re.compile(r'\b\d{4,}\b'),  # 4位及以上的数字
        }
    
    def analyze(self, binary_path: str) -> Dict:
        """分析二进制文件中的字符串
        
        Args:
            binary_path: 二进制文件路径
            
        Returns:
            字符串分析结果
        """
        # 提取字符串
        strings = self.extract_strings(binary_path)
        
        # 分类字符串
        categorized = self.categorize_strings(strings)
        
        # 统计信息
        stats = self.calculate_statistics(strings, categorized)
        
        # 查找重复
        duplicates = self.find_duplicates(strings)
        
        return {
            'total_strings': len(strings),
            'unique_strings': len(set(strings)),
            'statistics': stats,
            'categories': categorized,
            'duplicates': duplicates,
            'top_strings': self.get_top_strings(strings, 20),
            'binary_size': os.path.getsize(binary_path)
        }
    
    def extract_strings(self, binary_path: str) -> List[str]:
        """从二进制文件中提取字符串
        
        Args:
            binary_path: 二进制文件路径
            
        Returns:
            提取的字符串列表
        """
        strings = []
        
        try:
            with open(binary_path, 'rb') as f:
                data = f.read()
                
                # 提取ASCII字符串
                strings.extend(self._extract_ascii_strings(data))
                
                # 提取UTF-8字符串
                strings.extend(self._extract_utf8_strings(data))
                
        except Exception as e:
            print(f"警告: 读取二进制文件时出错: {e}")
        
        # 去重并过滤
        unique_strings = list(set(strings))
        filtered_strings = [s for s in unique_strings if len(s) >= self.min_length and self._is_valid_string(s)]
        
        return filtered_strings
    
    def _extract_ascii_strings(self, data: bytes) -> List[str]:
        """提取ASCII字符串"""
        strings = []
        current_string = ""
        
        for byte in data:
            if 32 <= byte <= 126:  # 可打印ASCII字符
                current_string += chr(byte)
            else:
                if len(current_string) >= self.min_length:
                    strings.append(current_string)
                current_string = ""
        
        # 处理最后一个字符串
        if len(current_string) >= self.min_length:
            strings.append(current_string)
        
        return strings
    
    def _extract_utf8_strings(self, data: bytes) -> List[str]:
        """提取UTF-8字符串"""
        strings = []
        
        try:
            # 尝试解码整个文件为UTF-8
            text = data.decode('utf-8', errors='ignore')
            
            # 使用正则表达式提取有意义的字符串
            pattern = re.compile(r'[\u0020-\u007E\u00A0-\uFFFF]{' + str(self.min_length) + ',}')
            utf8_strings = pattern.findall(text)
            
            strings.extend(utf8_strings)
            
        except Exception:
            pass  # 忽略UTF-8解码错误
        
        return strings
    
    def _is_valid_string(self, s: str) -> bool:
        """检查字符串是否有效"""
        # 排除全是重复字符的字符串
        if len(set(s)) == 1:
            return False
        
        # 排除过多非打印字符的字符串
        printable_count = sum(1 for c in s if c.isprintable())
        if printable_count / len(s) < 0.8:
            return False
        
        # 排除过长的字符串（可能是数据）
        if len(s) > 1000:
            return False
        
        return True
    
    def categorize_strings(self, strings: List[str]) -> Dict[str, List[str]]:
        """对字符串进行分类
        
        Args:
            strings: 字符串列表
            
        Returns:
            分类结果字典
        """
        categories = defaultdict(list)
        uncategorized = []
        
        for string in strings:
            categorized = False
            
            # 检查每个模式
            for category, pattern in self.string_patterns.items():
                if pattern.search(string):
                    categories[category].append(string)
                    categorized = True
                    break  # 只分配到第一个匹配的类别
            
            if not categorized:
                # 基于内容特征进行分类
                if self._is_ui_text(string):
                    categories['ui_texts'].append(string)
                elif self._is_debug_info(string):
                    categories['debug_info'].append(string)
                elif self._is_class_method(string):
                    categories['class_methods'].append(string)
                else:
                    uncategorized.append(string)
        
        # 添加未分类的字符串
        categories['uncategorized'] = uncategorized
        
        # 转换为普通字典并排序
        result = {}
        for category, strings_list in categories.items():
            result[category] = sorted(list(set(strings_list)))
        
        return result
    
    def _is_ui_text(self, s: str) -> bool:
        """判断是否为UI文本"""
        # 首字母大写，包含空格，长度适中
        if len(s) > 50:
            return False
        
        words = s.split()
        if len(words) < 2:
            return False
        
        # 检查是否像句子
        if s[0].isupper() and any(word.islower() for word in words):
            return True
        
        return False
    
    def _is_debug_info(self, s: str) -> bool:
        """判断是否为调试信息"""
        debug_keywords = ['debug', 'log', 'trace', 'dump', 'assert', 'warning']
        s_lower = s.lower()
        return any(keyword in s_lower for keyword in debug_keywords)
    
    def _is_class_method(self, s: str) -> bool:
        """判断是否为类或方法名"""
        # Objective-C方法名模式
        if '+[' in s or '-[' in s:
            return True
        
        # Swift类名模式
        if '.' in s and not s.startswith('/') and not s.startswith('http'):
            return True
        
        return False
    
    def calculate_statistics(self, strings: List[str], categorized: Dict[str, List[str]]) -> Dict:
        """计算字符串统计信息"""
        if not strings:
            return {}
        
        lengths = [len(s) for s in strings]
        
        stats = {
            'length_stats': {
                'min': min(lengths),
                'max': max(lengths),
                'avg': sum(lengths) / len(lengths),
                'total_chars': sum(lengths)
            },
            'category_counts': {category: len(strings_list) for category, strings_list in categorized.items()},
            'encoding_info': self._analyze_encoding(strings),
            'duplicate_rate': (len(strings) - len(set(strings))) / len(strings) if strings else 0
        }
        
        return stats
    
    def _analyze_encoding(self, strings: List[str]) -> Dict:
        """分析字符串编码信息"""
        ascii_count = 0
        unicode_count = 0
        
        for s in strings:
            try:
                s.encode('ascii')
                ascii_count += 1
            except UnicodeEncodeError:
                unicode_count += 1
        
        return {
            'ascii_strings': ascii_count,
            'unicode_strings': unicode_count,
            'ascii_percentage': ascii_count / len(strings) if strings else 0
        }
    
    def find_duplicates(self, strings: List[str]) -> Dict:
        """查找重复字符串"""
        counter = Counter(strings)
        duplicates = {string: count for string, count in counter.items() if count > 1}
        
        # 按出现次数排序
        sorted_duplicates = dict(sorted(duplicates.items(), key=lambda x: x[1], reverse=True))
        
        return {
            'count': len(duplicates),
            'strings': dict(list(sorted_duplicates.items())[:50])  # 限制返回前50个
        }
    
    def get_top_strings(self, strings: List[str], limit: int = 20) -> List[Dict]:
        """获取最常见的字符串"""
        counter = Counter(strings)
        top_strings = counter.most_common(limit)
        
        return [{'string': string, 'count': count} for string, count in top_strings] 