"""
相似性分析器
用于分析多个IPA文件之间的字符串和资源相似性/重复性
"""

import json
import os
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
from pathlib import Path
from difflib import SequenceMatcher
import hashlib


class SimilarityAnalyzer:
    """相似性分析器"""
    
    def __init__(self, analysis_dir: str = "data/analysis_reports", filter_common_words: bool = True, target_apps: List[str] = None):
        """初始化相似性分析器
        
        Args:
            analysis_dir: 分析报告目录
            filter_common_words: 是否过滤常见开发词汇
            target_apps: 指定要分析的应用列表，如果为None则分析所有应用
        """
        self.analysis_dir = Path(analysis_dir)
        self.filter_common_words = filter_common_words
        self.target_apps = target_apps
        self.apps_data = {}
        self._init_common_words_filter()
        self.load_analysis_data()
    
    def _init_common_words_filter(self):
        """初始化常见开发词汇过滤器"""
        # 编程通用词汇
        programming_words = {
            'main', 'error', 'com', 'index', 'app', 'application', 'system', 'data', 'info',
            'debug', 'config', 'settings', 'default', 'value', 'key', 'name', 'type', 'size',
            'count', 'number', 'string', 'text', 'file', 'path', 'url', 'http', 'https',
            'www', 'api', 'json', 'xml', 'html', 'css', 'js', 'javascript', 'true', 'false',
            'null', 'undefined', 'nil', 'empty', 'new', 'old', 'tmp', 'temp', 'cache',
            'log', 'logs', 'trace', 'warn', 'warning', 'fatal', 'exception', 'status',
            'state', 'flag', 'option', 'param', 'parameter', 'arg', 'argument', 'var',
            'variable', 'function', 'method', 'class', 'object', 'instance', 'property',
            'field', 'member', 'static', 'public', 'private', 'protected', 'internal'
        }
        
        # iOS/移动开发相关词汇
        ios_words = {
            'ios', 'iphone', 'ipad', 'apple', 'swift', 'objective', 'objc', 'xcode',
            'foundation', 'uikit', 'core', 'framework', 'library', 'bundle', 'plist',
            'nib', 'xib', 'storyboard', 'segue', 'view', 'controller', 'navigation',
            'tab', 'table', 'collection', 'scroll', 'button', 'label', 'image', 'icon',
            'background', 'foreground', 'animation', 'transition', 'gesture', 'touch',
            'delegate', 'datasource', 'protocol', 'notification', 'observer', 'target',
            'action', 'outlet', 'ibaction', 'iboutlet', 'autolayout', 'constraint',
            'margin', 'padding', 'frame', 'bounds', 'center', 'origin', 'width', 'height'
        }
        
        # 系统和框架词汇
        system_words = {
            'version', 'build', 'release', 'beta', 'alpha', 'production', 'development',
            'test', 'testing', 'unit', 'integration', 'mock', 'stub', 'fake', 'sample',
            'example', 'demo', 'tutorial', 'guide', 'help', 'support', 'documentation',
            'readme', 'license', 'copyright', 'author', 'created', 'updated', 'modified',
            'date', 'time', 'timestamp', 'uuid', 'identifier', 'id', 'uid', 'session',
            'token', 'auth', 'authentication', 'authorization', 'login', 'logout',
            'user', 'admin', 'guest', 'role', 'permission', 'access', 'security'
        }
        
        # 网络和数据相关
        network_words = {
            'network', 'internet', 'connection', 'request', 'response', 'client', 'server',
            'host', 'port', 'protocol', 'tcp', 'udp', 'socket', 'ssl', 'tls', 'certificate',
            'encryption', 'hash', 'md5', 'sha', 'base64', 'encoding', 'decoding', 'utf8',
            'ascii', 'unicode', 'locale', 'language', 'localization', 'internationalization',
            'database', 'sql', 'sqlite', 'mysql', 'postgres', 'mongodb', 'redis', 'cache'
        }
        
        # 通用技术词汇
        tech_words = {
            'algorithm', 'performance', 'optimization', 'memory', 'cpu', 'gpu', 'thread',
            'queue', 'stack', 'heap', 'garbage', 'collection', 'reference', 'pointer',
            'allocation', 'deallocation', 'leak', 'retain', 'release', 'autorelease',
            'weak', 'strong', 'copy', 'mutable', 'immutable', 'readonly', 'readwrite'
        }
        
        # 合并所有过滤词汇
        self.common_words = programming_words | ios_words | system_words | network_words | tech_words
        
        # 添加短字符串和数字模式
        self.min_meaningful_length = 3
        
        # 编译正则表达式用于过滤
        import re
        self.number_pattern = re.compile(r'^\d+$')
        self.version_pattern = re.compile(r'^\d+\.\d+(\.\d+)?$')
        self.hex_pattern = re.compile(r'^[0-9a-fA-F]{8,}$')
        self.uuid_pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        self.path_pattern = re.compile(r'^/[a-zA-Z0-9/_.-]*$')
        self.url_pattern = re.compile(r'^https?://')
        self.domain_pattern = re.compile(r'.*\.(com|org|net|edu|gov|mil|int|co\.|app)$')
        
        # 技术性字符串过滤模式
        self.swift_symbol_pattern = re.compile(r'^_\$s[A-Za-z0-9]+')  # Swift符号
        self.objc_method_pattern = re.compile(r'^[@v]\d+@\d+:\d+')  # Objective-C方法签名
        self.certificate_pattern = re.compile(r'Reliance on this certificate')  # 证书文本
        self.plist_pattern = re.compile(r'^<!DOCTYPE plist')  # plist文件头
        self.framework_pattern = re.compile(r'(WebView|WKWebView|UIKit|Foundation)')  # 框架相关
    
    def _should_filter_string(self, text: str) -> bool:
        """判断字符串是否应该被过滤
        
        Args:
            text: 要检查的字符串
            
        Returns:
            bool: True表示应该过滤掉
        """
        if not self.filter_common_words:
            return False
            
        # 去除空白字符
        text = text.strip()
        
        # 过滤空字符串和过短字符串
        if len(text) < self.min_meaningful_length:
            return True
        
        # 优先过滤技术性字符串（优先级最高）
        if self._is_technical_string(text):
            return True
        
        # 保留有意义的字符串
        if self._is_meaningful_string(text):
            return False
        
        # 转换为小写进行比较
        lower_text = text.lower()
        
        # 过滤常见词汇（单个词）
        if lower_text in self.common_words and len(text.split()) == 1:
            return True
        
        # 过滤纯数字
        if self.number_pattern.match(text):
            return True
        
        # 过滤版本号
        if self.version_pattern.match(text):
            return True
        
        # 过滤长十六进制字符串（可能是哈希值）
        if self.hex_pattern.match(text):
            return True
        
        # 过滤UUID
        if self.uuid_pattern.match(text):
            return True
        
        # 过滤文件路径
        if self.path_pattern.match(text):
            return True
        
        # 过滤URL
        if self.url_pattern.match(text):
            return True
        
        # 过滤域名
        if self.domain_pattern.match(lower_text):
            return True
        
        # 过滤只包含特殊字符的字符串
        if all(not c.isalnum() for c in text):
            return True
        
        # 过滤重复字符的字符串（如"aaaaa"）
        if len(set(text.lower())) <= 2 and len(text) > 4:
            return True
        
        return False
    
    def _is_technical_string(self, text: str) -> bool:
        """判断是否为技术性字符串（应该被过滤）
        
        Args:
            text: 要检查的字符串
            
        Returns:
            bool: True表示是技术性字符串
        """
        # Swift符号
        if self.swift_symbol_pattern.match(text):
            return True
        
        # Objective-C方法签名（任何以@"或v开头且包含数字的）
        if text.startswith(('@"', 'v')) and any(c.isdigit() for c in text[:10]):
            return True
        
        # 证书相关文本
        if self.certificate_pattern.search(text):
            return True
        
        # plist文件头或XML声明
        if text.startswith(('<!DOCTYPE', '<?xml')):
            return True
        
        # WebView相关的方法名（技术性API）
        webview_methods = ['webView:', 'WKWebView', 'WKNavigation', 'WKContext']
        if any(method in text for method in webview_methods):
            return True
        
        # 方法名模式（包含冒号的长字符串，通常是方法名）
        if ':' in text and len(text) > 20:
            return True
        
        # 包含大量下划线的技术字符串
        if text.count('_') > 2:
            return True
        
        # 全大写的长字符串（通常是常量或标识符）
        if text.isupper() and len(text) > 8:
            return True
        
        # 包含特殊符号组合的技术字符串
        technical_symbols = ['@"', '@0:', 'v48@', 'v40@', 'v56@', '$s', '_$', '16@']
        if any(symbol in text for symbol in technical_symbols):
            return True
        
        # 包含Foundation、Core等框架前缀的字符串
        framework_prefixes = ['Foundation', 'CoreData', 'CoreGraphics', 'UIKit', 'AVFoundation']
        if any(text.startswith(prefix) or f'.{prefix}' in text for prefix in framework_prefixes):
            return True
        
        # 框架路径和@rpath
        if text.startswith('@rpath/') or '.framework/' in text:
            return True
        
        # Swift内部符号
        if text.startswith('_swift_'):
            return True
        
        # plist键值对
        if text.startswith('<key>') and text.endswith('</key>'):
            return True
        
        # 证书相关文本
        if 'Certificate' in text or 'Developer Relations' in text:
            return True
        
        # iOS系统通知和常量
        ios_system_patterns = [
            '_UIApplication', '_NSNotification', 'UIApplicationMain',
            'com.apple.developer', '#com.apple', 'NSArray element',
            'Down-casted Array', 'Swift Array', 'failed to match'
        ]
        if any(pattern in text for pattern in ios_system_patterns):
            return True
        
        # Objective-C和Swift运行时函数
        runtime_patterns = [
            '_objc_', 'swift_task_', 'swift_retain', 'swift_release',
            'objc_msgSend', 'objc_retain', 'objc_autorelease'
        ]
        if any(pattern in text for pattern in runtime_patterns):
            return True
        
        # 系统错误消息模式
        system_error_patterns = [
            'failed to match', 'cannot throw', 'reported an error',
            'Thread Local Context', 'AutoreleasedReturnValue'
        ]
        if any(pattern in text for pattern in system_error_patterns):
            return True
        
        # UI系统常量和通知
        ui_system_patterns = [
            '_UIKeyboard', '_NSForeground', '_NSBackground', 'AttributeName',
            'LayoutDirection', 'StatusBarStyle', 'URLOptionsKey', 'ProxySettings',
            'OrientationProvider', 'TextLayout', '_CFNetwork'
        ]
        if any(pattern in text for pattern in ui_system_patterns):
            return True
        
        # Facebook SDK和第三方框架常量
        sdk_patterns = [
            '_FBSDK', 'AppEventParameterName', 'AppEventName', 'FacebookSDK'
        ]
        if any(pattern in text for pattern in sdk_patterns):
            return True
        
        # 系统通知模式（以_开头且包含Notification的）
        if text.startswith('_') and ('Notification' in text or 'WillShow' in text or 'WillHide' in text):
            return True
        
        # 系统库路径
        if text.startswith('/usr/lib/') or text.startswith('/System/Library/'):
            return True
        
        # plist和XML相关
        if text.startswith('<plist') or 'version="1.0"' in text or text.startswith('<?xml'):
            return True
        
        # 系统调试和错误相关
        system_debug_patterns = [
            'debugDescription', 'radr://', '.cxx_destruct', 
            'Apple Inc.', '_SKErrorDomain', 'radar://'
        ]
        if any(pattern in text for pattern in system_debug_patterns):
            return True
        
        # 系统默认管理器和中心
        system_managers = [
            'standardUserDefaults', 'defaultManager', 'defaultCenter',
            'sharedApplication', 'mainBundle', 'currentDevice'
        ]
        if any(manager in text for manager in system_managers):
            return True
        
        # 长度过长的技术字符串（通常是代码符号）
        if len(text) > 60 and not any(c in text for c in ' .,!?'):
            return True
        
        return False
    
    def _is_meaningful_string(self, text: str) -> bool:
        """判断字符串是否有意义（业务相关）
        
        Args:
            text: 要检查的字符串
            
        Returns:
            bool: True表示有意义，应该保留
        """
        lower_text = text.lower()
        
        # 错误和警告消息（必须是完整的消息，不是单个词，且不是系统内部错误）
        error_keywords = ['error', 'warning', 'fail', 'exception', 'invalid', 'missing', 'not found', 'denied']
        if (any(keyword in lower_text for keyword in error_keywords) and 
            len(text.split()) > 1 and
            not any(sys_pattern in text for sys_pattern in ['NSArray', 'Swift Array', 'Down-casted', 'swift_task'])):
            return True
        
        # 用户界面文本（包含常见UI词汇）
        ui_keywords = ['button', 'click', 'tap', 'swipe', 'loading', 'success', 'cancel', 'confirm', 'ok', 'yes', 'no']
        if any(keyword in lower_text for keyword in ui_keywords):
            return True
        
        # 包含冒号的消息（通常是状态或错误描述）
        if ':' in text and len(text) > 10:
            return True
        
        # 包含感叹号或问号的字符串（用户提示）
        if ('!' in text or '?' in text) and len(text) > 5:
            return True
        
        # 包含"请"、"您"等中文用户提示
        chinese_ui_chars = ['请', '您', '确认', '取消', '成功', '失败', '错误', '警告']
        if any(char in text for char in chinese_ui_chars):
            return True
        
        # 包含多个单词的描述性文本
        words = text.split()
        if len(words) >= 3 and len(text) > 15:
            # 检查是否包含有意义的动词或形容词
            meaningful_words = ['get', 'set', 'create', 'delete', 'update', 'load', 'save', 'send', 'receive', 
                              'connect', 'disconnect', 'start', 'stop', 'play', 'pause', 'open', 'close']
            if any(word.lower() in meaningful_words for word in words):
                return True
        
        return False
    
    def load_analysis_data(self):
        """加载分析数据"""
        if not self.analysis_dir.exists():
            return
        
        for file_path in self.analysis_dir.glob("*_analysis.json"):
            if file_path.name == "similarity_analysis.json" or file_path.name == "comprehensive_similarity_analysis.json":
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                app_name = data.get('app_info', {}).get('name', file_path.stem.replace('_analysis', ''))
                
                # 如果指定了目标应用列表，只加载指定的应用
                if self.target_apps is None or app_name in self.target_apps:
                    self.apps_data[app_name] = data
                
            except Exception as e:
                print(f"警告: 加载分析文件失败 {file_path}: {e}")
    
    def analyze_string_similarity(self) -> Dict:
        """分析字符串相似性"""
        if len(self.apps_data) < 2:
            return {"error": "需要至少2个应用才能进行相似性分析"}
        
        # 提取所有应用的字符串
        app_strings = {}
        for app_name, data in self.apps_data.items():
            strings = self._extract_all_strings(data)
            app_strings[app_name] = strings
        
        # 分析重复字符串
        duplicate_analysis = self._analyze_duplicates(app_strings)
        
        # 分析相似度
        similarity_matrix = self._calculate_similarity_matrix(app_strings)
        
        # 分析字符串分布
        category_analysis = self._analyze_string_categories(app_strings)
        
        return {
            'duplicate_analysis': duplicate_analysis,
            'similarity_matrix': similarity_matrix,
            'category_analysis': category_analysis,
            'apps_count': len(app_strings),
            'total_unique_strings': len(set().union(*app_strings.values()))
        }
    
    def analyze_resource_similarity(self) -> Dict:
        """分析资源相似性"""
        if len(self.apps_data) < 2:
            return {"error": "需要至少2个应用才能进行相似性分析"}
        
        # 提取资源信息
        app_resources = {}
        for app_name, data in self.apps_data.items():
            resources = self._extract_resources(data)
            app_resources[app_name] = resources
        
        # 分析重复资源
        duplicate_resources = self._analyze_resource_duplicates(app_resources)
        
        # 分析资源类型分布
        resource_type_analysis = self._analyze_resource_types(app_resources)
        
        return {
            'duplicate_resources': duplicate_resources,
            'resource_type_analysis': resource_type_analysis,
            'apps_count': len(app_resources)
        }
    
    def generate_comprehensive_report(self, include_filter_stats: bool = False) -> Dict:
        """生成综合相似性报告"""
        string_analysis = self.analyze_string_similarity()
        resource_analysis = self.analyze_resource_similarity()
        
        # 生成应用对比摘要
        app_comparison = self._generate_app_comparison()
        
        # 生成重复性统计
        duplication_stats = self._calculate_duplication_statistics(string_analysis)
        
        report = {
            'analysis_meta': {
                'generated_at': self._get_timestamp(),
                'apps_analyzed': list(self.apps_data.keys()),
                'apps_count': len(self.apps_data),
                'filter_enabled': self.filter_common_words
            },
            'string_analysis': string_analysis,
            'resource_analysis': resource_analysis,
            'app_comparison': app_comparison,
            'duplication_statistics': duplication_stats,
            'recommendations': self._generate_recommendations(string_analysis, resource_analysis)
        }
        
        # 只在需要时包含过滤统计信息
        if include_filter_stats:
            filter_stats = self._generate_filter_statistics()
            report['filter_statistics'] = filter_stats
        
        return report
    
    def _extract_all_strings(self, data: Dict) -> Set[str]:
        """提取应用的所有字符串"""
        strings = set()
        
        strings_data = data.get('strings', {})
        categories = strings_data.get('categories', {})
        
        for category, string_list in categories.items():
            # 跳过uncategorized、domains和class_methods类型的字符串
            if category.lower() in ['uncategorized', 'domains', 'class_methods']:
                continue
                
            if isinstance(string_list, list):
                for item in string_list:
                    string_content = None
                    if isinstance(item, str):
                        string_content = item
                    elif isinstance(item, dict) and 'content' in item:
                        string_content = item['content']
                    
                    # 应用过滤逻辑
                    if string_content and not self._should_filter_string(string_content):
                        strings.add(string_content)
        
        return strings
    
    def _extract_resources(self, data: Dict) -> List[Dict]:
        """提取应用的资源信息"""
        resources = []
        
        resources_data = data.get('resources', {})
        categories = resources_data.get('categories', {})
        
        for category, file_list in categories.items():
            if isinstance(file_list, list):
                for file_info in file_list:
                    if isinstance(file_info, dict):
                        resource = {
                            'name': file_info.get('name', ''),
                            'size': file_info.get('size', 0),
                            'category': category,
                            'path': file_info.get('path', '')
                        }
                        resources.append(resource)
        
        return resources
    
    def _analyze_duplicates(self, app_strings: Dict[str, Set[str]]) -> Dict:
        """分析重复字符串"""
        # 统计每个字符串出现在多少个应用中
        string_count = Counter()
        string_apps = defaultdict(list)
        
        for app_name, strings in app_strings.items():
            for string in strings:
                string_count[string] += 1
                string_apps[string].append(app_name)
        
        # 按重复次数分组
        duplicates = defaultdict(list)
        for string, count in string_count.items():
            if count > 1:
                duplicates[count].append({
                    'content': string,
                    'apps': string_apps[string],
                    'count': count
                })
        
        # 排序重复字符串
        for count in duplicates:
            duplicates[count].sort(key=lambda x: len(x['content']), reverse=True)
        
        # 统计信息
        total_strings = sum(len(strings) for strings in app_strings.values())
        unique_strings = len(string_count)
        duplicate_strings = sum(count - 1 for count in string_count.values() if count > 1)
        
        return {
            'duplicates_by_count': dict(duplicates),
            'statistics': {
                'total_strings': total_strings,
                'unique_strings': unique_strings,
                'duplicate_strings': duplicate_strings,
                'duplication_rate': duplicate_strings / total_strings * 100 if total_strings > 0 else 0
            },
            'top_duplicates': self._get_top_duplicates(duplicates, 20)
        }
    
    def _analyze_resource_duplicates(self, app_resources: Dict[str, List[Dict]]) -> Dict:
        """分析重复资源"""
        # 按文件名和大小分组
        resource_groups = defaultdict(list)
        
        for app_name, resources in app_resources.items():
            for resource in resources:
                key = (resource['name'], resource['size'])
                resource_groups[key].append({
                    'app': app_name,
                    'category': resource['category'],
                    'path': resource['path']
                })
        
        # 找出重复的资源
        duplicates = {}
        for (name, size), resources in resource_groups.items():
            if len(resources) > 1:
                duplicates[f"{name}_{size}"] = {
                    'name': name,
                    'size': size,
                    'apps': [r['app'] for r in resources],
                    'count': len(resources),
                    'category': resources[0]['category']
                }
        
        return {
            'duplicate_resources': duplicates,
            'count': len(duplicates),
            'total_size_saved': sum(
                (dup['count'] - 1) * dup['size'] 
                for dup in duplicates.values()
            )
        }
    
    def _calculate_similarity_matrix(self, app_strings: Dict[str, Set[str]]) -> Dict:
        """计算应用间相似度矩阵"""
        app_names = list(app_strings.keys())
        similarity_matrix = {}
        
        for i, app1 in enumerate(app_names):
            similarity_matrix[app1] = {}
            for j, app2 in enumerate(app_names):
                if i <= j:  # 只计算上三角矩阵
                    similarity = self._calculate_jaccard_similarity(
                        app_strings[app1], 
                        app_strings[app2]
                    )
                    similarity_matrix[app1][app2] = similarity
                    if app1 != app2:
                        if app2 not in similarity_matrix:
                            similarity_matrix[app2] = {}
                        similarity_matrix[app2][app1] = similarity
        
        return similarity_matrix
    
    def _calculate_jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """计算Jaccard相似度"""
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _analyze_string_categories(self, app_strings: Dict[str, Set[str]]) -> Dict:
        """分析字符串分类分布"""
        category_analysis = {}
        
        for app_name, data in self.apps_data.items():
            strings_data = data.get('strings', {})
            categories = strings_data.get('categories', {})
            
            category_stats = {}
            for category, string_list in categories.items():
                category_stats[category] = len(string_list) if isinstance(string_list, list) else 0
            
            category_analysis[app_name] = category_stats
        
        return category_analysis
    
    def _analyze_resource_types(self, app_resources: Dict[str, List[Dict]]) -> Dict:
        """分析资源类型分布"""
        type_analysis = {}
        
        for app_name, resources in app_resources.items():
            type_stats = defaultdict(int)
            for resource in resources:
                type_stats[resource['category']] += 1
            
            type_analysis[app_name] = dict(type_stats)
        
        return type_analysis
    
    def _generate_app_comparison(self) -> Dict:
        """生成应用对比"""
        comparison = {}
        
        for app_name, data in self.apps_data.items():
            app_info = data.get('app_info', {})
            strings_data = data.get('strings', {})
            resources_data = data.get('resources', {})
            
            comparison[app_name] = {
                'bundle_id': app_info.get('bundle_id', ''),
                'version': app_info.get('version', ''),
                'file_size': app_info.get('file_size', 0),
                'total_strings': strings_data.get('total_strings', 0),
                'unique_strings': strings_data.get('unique_strings', 0),
                'total_files': resources_data.get('total_files', 0),
                'total_resource_size': resources_data.get('total_size', 0)
            }
        
        return comparison
    
    def _calculate_duplication_statistics(self, string_analysis: Dict) -> Dict:
        """计算重复性统计"""
        if 'duplicate_analysis' not in string_analysis:
            return {}
        
        dup_analysis = string_analysis['duplicate_analysis']
        duplicates_by_count = dup_analysis.get('duplicates_by_count', {})
        
        stats = {
            'apps_with_high_similarity': [],
            'most_duplicated_strings': [],
            'duplication_distribution': {}
        }
        
        # 计算重复分布
        for count, items in duplicates_by_count.items():
            stats['duplication_distribution'][f"{count}_apps"] = len(items)
        
        # 找出最重复的字符串
        all_duplicates = []
        for count, items in duplicates_by_count.items():
            all_duplicates.extend([(int(count), item) for item in items])
        
        all_duplicates.sort(key=lambda x: x[0], reverse=True)
        stats['most_duplicated_strings'] = [
            {
                'content': item['content'],
                'count': count,
                'apps': item['apps']
            }
            for count, item in all_duplicates[:10]
        ]
        
        return stats
    
    def _generate_filter_statistics(self) -> Dict:
        """生成过滤统计信息"""
        if not self.filter_common_words:
            return {"filter_enabled": False}
        
        stats = {
            "filter_enabled": True,
            "common_words_count": len(self.common_words),
            "filter_criteria": {
                "min_length": self.min_meaningful_length,
                "filters_applied": [
                    "常见开发词汇",
                    "纯数字字符串",
                    "版本号",
                    "十六进制字符串",
                    "UUID",
                    "文件路径",
                    "URL链接",
                    "域名",
                    "特殊字符串",
                    "重复字符串"
                ]
            },
            "filtered_examples": []
        }
        
        # 收集一些被过滤的例子（用于调试和验证）
        sample_filtered = []
        for app_name, data in self.apps_data.items():
            strings_data = data.get('strings', {})
            categories = strings_data.get('categories', {})
            
            for category, string_list in categories.items():
                if isinstance(string_list, list):
                    for item in string_list[:20]:  # 只检查前20个
                        string_content = None
                        if isinstance(item, str):
                            string_content = item
                        elif isinstance(item, dict) and 'content' in item:
                            string_content = item['content']
                        
                        if string_content and self._should_filter_string(string_content):
                            sample_filtered.append(string_content)
                            if len(sample_filtered) >= 10:
                                break
                if len(sample_filtered) >= 10:
                    break
            if len(sample_filtered) >= 10:
                break
        
        stats["filtered_examples"] = sample_filtered[:10]
        return stats
    
    def _generate_recommendations(self, string_analysis: Dict, resource_analysis: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 字符串重复建议
        if 'duplicate_analysis' in string_analysis:
            dup_stats = string_analysis['duplicate_analysis']['statistics']
            dup_rate = dup_stats.get('duplication_rate', 0)
            
            if dup_rate > 50:
                recommendations.append(f"字符串重复率达到 {dup_rate:.1f}%，建议提取公共字符串资源")
            elif dup_rate > 30:
                recommendations.append(f"字符串重复率为 {dup_rate:.1f}%，可考虑优化公共字符串")
        
        # 资源重复建议
        if 'duplicate_resources' in resource_analysis:
            dup_resources = resource_analysis['duplicate_resources']
            saved_size = dup_resources.get('total_size_saved', 0)
            
            if saved_size > 1024 * 1024:  # 1MB
                size_mb = saved_size / 1024 / 1024
                recommendations.append(f"通过去除重复资源可节省约 {size_mb:.1f}MB 空间")
        
        # 相似度建议
        if 'similarity_matrix' in string_analysis:
            # 找出高相似度的应用对
            matrix = string_analysis['similarity_matrix']
            high_similarity_pairs = []
            
            for app1, similarities in matrix.items():
                for app2, similarity in similarities.items():
                    if app1 != app2 and similarity > 0.8:
                        high_similarity_pairs.append((app1, app2, similarity))
            
            if high_similarity_pairs:
                recommendations.append("发现高相似度应用，建议检查是否可以合并或提取公共组件")
        
        return recommendations
    
    def _get_top_duplicates(self, duplicates: Dict, limit: int = 20) -> List[Dict]:
        """获取最重复的字符串"""
        all_duplicates = []
        
        for count, items in duplicates.items():
            for item in items:
                all_duplicates.append((int(count), item))
        
        # 按重复次数和字符串长度排序
        all_duplicates.sort(key=lambda x: (x[0], len(x[1]['content'])), reverse=True)
        
        return [item for _, item in all_duplicates[:limit]]
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def print_similarity_summary(self, report: Dict, show_filter_info: bool = False):
        """打印相似性分析摘要"""
        print("\n" + "=" * 60)
        print("🔍 IPA相似性分析报告")
        print("=" * 60)
        
        meta = report.get('analysis_meta', {})
        print(f"分析应用数量: {meta.get('apps_count', 0)}")
        print(f"分析时间: {meta.get('generated_at', '')}")
        
        # 只在需要时显示过滤器状态
        if show_filter_info:
            filter_stats = report.get('filter_statistics', {})
            if filter_stats.get('filter_enabled', False):
                print(f"🔧 智能过滤: 已启用 (过滤 {filter_stats.get('common_words_count', 0)} 个常见词汇)")
                if filter_stats.get('filtered_examples'):
                    examples = filter_stats['filtered_examples'][:5]
                    print(f"   过滤示例: {', '.join(examples)}")
            else:
                print("🔧 智能过滤: 已禁用")
        
        # 字符串分析摘要
        string_analysis = report.get('string_analysis', {})
        if 'duplicate_analysis' in string_analysis:
            dup_stats = string_analysis['duplicate_analysis']['statistics']
            print(f"\n📝 字符串重复性分析:")
            print(f"   总字符串数: {dup_stats.get('total_strings', 0):,}")
            print(f"   唯一字符串数: {dup_stats.get('unique_strings', 0):,}")
            print(f"   重复字符串数: {dup_stats.get('duplicate_strings', 0):,}")
            print(f"   重复率: {dup_stats.get('duplication_rate', 0):.1f}%")
        
        # 资源分析摘要
        resource_analysis = report.get('resource_analysis', {})
        if 'duplicate_resources' in resource_analysis:
            dup_resources = resource_analysis['duplicate_resources']
            saved_size = dup_resources.get('total_size_saved', 0)
            print(f"\n📁 资源重复性分析:")
            print(f"   重复资源数: {dup_resources.get('count', 0)}")
            print(f"   可节省空间: {saved_size / 1024 / 1024:.1f}MB")
        
        # 显示最重复的字符串
        if 'duplicate_analysis' in string_analysis:
            top_duplicates = string_analysis['duplicate_analysis'].get('top_duplicates', [])
            if top_duplicates:
                print(f"\n🔄 前10个最重复字符串:")
                for i, dup in enumerate(top_duplicates[:10], 1):
                    content = dup['content']
                    if len(content) > 50:
                        content = content[:47] + "..."
                    print(f"   {i:2}. [{dup['count']}次] {content}")
        
        # 显示建议
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 优化建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("=" * 60) 