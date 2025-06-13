"""
资源分析器
分析IPA包中的资源文件，包括图片、音频、本地化文件等
"""

import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import hashlib


class ResourceAnalyzer:
    """资源文件分析器"""
    
    def __init__(self):
        """初始化资源分析器"""
        self.resource_categories = {
            'images': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico'],
            'audio': ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.wma', '.flac'],
            'video': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'],
            'documents': ['.pdf', '.txt', '.rtf', '.doc', '.docx'],
            'data': ['.json', '.xml', '.plist', '.db', '.sqlite', '.realm'],
            'fonts': ['.ttf', '.otf', '.woff', '.woff2'],
            'certificates': ['.cer', '.crt', '.pem', '.p12', '.mobileprovision'],
            'archives': ['.zip', '.tar', '.gz', '.7z'],
            'code': ['.js', '.html', '.css', '.lua', '.py'],
            'config': ['.conf', '.ini', '.yaml', '.yml', '.toml']
        }
        
        # 特殊文件名模式
        self.special_files = {
            'app_icons': ['AppIcon', 'Icon', 'icon'],
            'launch_images': ['LaunchImage', 'Launch', 'Default'],
            'localization': ['Localizable.strings', '.lproj'],
            'storyboards': ['.storyboard', '.nib', '.xib'],
            'assets': ['Assets.car', '.car']
        }
    
    def analyze(self, app_directory: str) -> Dict:
        """分析应用目录中的资源文件
        
        Args:
            app_directory: 应用目录路径
            
        Returns:
            资源分析结果
        """
        app_path = Path(app_directory)
        
        # 查找.app目录
        app_dirs = list(app_path.glob('**/*.app'))
        if app_dirs:
            app_path = app_dirs[0]
        
        # 收集所有文件信息
        all_files = self._collect_files(app_path)
        
        # 按类型分类
        categorized_files = self._categorize_files(all_files)
        
        # 分析特殊文件
        special_files = self._analyze_special_files(all_files)
        
        # 计算统计信息
        statistics = self._calculate_statistics(all_files, categorized_files)
        
        # 查找重复文件
        duplicates = self._find_duplicate_files(all_files)
        
        return {
            'total_files': len(all_files),
            'total_size': sum(file_info['size'] for file_info in all_files),
            'categories': categorized_files,
            'special_files': special_files,
            'statistics': statistics,
            'duplicates': duplicates,
            'large_files': self._get_large_files(all_files, 1024*1024),  # >1MB
            'directory_structure': self._analyze_directory_structure(app_path)
        }
    
    def _collect_files(self, app_path: Path) -> List[Dict]:
        """收集应用目录中的所有文件信息"""
        files = []
        
        try:
            for root, dirs, file_names in os.walk(app_path):
                root_path = Path(root)
                
                for file_name in file_names:
                    file_path = root_path / file_name
                    
                    try:
                        file_stat = file_path.stat()
                        relative_path = file_path.relative_to(app_path)
                        
                        file_info = {
                            'name': file_name,
                            'path': str(relative_path),
                            'full_path': str(file_path),
                            'size': file_stat.st_size,
                            'extension': file_path.suffix.lower(),
                            'directory': str(relative_path.parent),
                            'modified_time': file_stat.st_mtime
                        }
                        
                        files.append(file_info)
                        
                    except (OSError, IOError) as e:
                        print(f"警告: 无法访问文件 {file_path}: {e}")
                        continue
                        
        except Exception as e:
            print(f"警告: 遍历目录时出错: {e}")
        
        return files
    
    def _categorize_files(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """按类型分类文件"""
        categories = defaultdict(list)
        uncategorized = []
        
        for file_info in files:
            extension = file_info['extension']
            categorized = False
            
            # 检查文件扩展名
            for category, extensions in self.resource_categories.items():
                if extension in extensions:
                    categories[category].append(file_info)
                    categorized = True
                    break
            
            if not categorized:
                uncategorized.append(file_info)
        
        # 添加未分类文件
        categories['uncategorized'] = uncategorized
        
        # 转换为普通字典并按大小排序
        result = {}
        for category, file_list in categories.items():
            result[category] = sorted(file_list, key=lambda x: x['size'], reverse=True)
        
        return result
    
    def _analyze_special_files(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """分析特殊文件"""
        special = defaultdict(list)
        
        for file_info in files:
            file_name = file_info['name']
            file_path = file_info['path']
            
            # 检查应用图标
            if any(icon_pattern in file_name for icon_pattern in self.special_files['app_icons']):
                special['app_icons'].append(file_info)
            
            # 检查启动图像
            elif any(launch_pattern in file_name for launch_pattern in self.special_files['launch_images']):
                special['launch_images'].append(file_info)
            
            # 检查本地化文件
            elif any(loc_pattern in file_path for loc_pattern in self.special_files['localization']):
                special['localization'].append(file_info)
            
            # 检查故事板文件
            elif any(sb_pattern in file_name for sb_pattern in self.special_files['storyboards']):
                special['storyboards'].append(file_info)
            
            # 检查资源包文件
            elif any(asset_pattern in file_name for asset_pattern in self.special_files['assets']):
                special['assets'].append(file_info)
        
        return dict(special)
    
    def _calculate_statistics(self, files: List[Dict], categorized: Dict[str, List[Dict]]) -> Dict:
        """计算统计信息"""
        if not files:
            return {}
        
        sizes = [file_info['size'] for file_info in files]
        
        # 按类别统计
        category_stats = {}
        for category, file_list in categorized.items():
            if file_list:
                category_sizes = [f['size'] for f in file_list]
                category_stats[category] = {
                    'count': len(file_list),
                    'total_size': sum(category_sizes),
                    'avg_size': sum(category_sizes) / len(category_sizes),
                    'largest_file': max(file_list, key=lambda x: x['size'])
                }
        
        # 扩展名统计
        extension_stats = defaultdict(lambda: {'count': 0, 'total_size': 0})
        for file_info in files:
            ext = file_info['extension'] or 'no_extension'
            extension_stats[ext]['count'] += 1
            extension_stats[ext]['total_size'] += file_info['size']
        
        # 转换为普通字典并排序
        extension_stats = dict(sorted(extension_stats.items(), 
                                    key=lambda x: x[1]['total_size'], reverse=True))
        
        return {
            'size_stats': {
                'min': min(sizes),
                'max': max(sizes),
                'avg': sum(sizes) / len(sizes),
                'total': sum(sizes)
            },
            'category_stats': category_stats,
            'extension_stats': dict(list(extension_stats.items())[:20])  # 前20个扩展名
        }
    
    def _find_duplicate_files(self, files: List[Dict]) -> Dict:
        """查找重复文件（基于文件大小和名称）"""
        # 按文件大小分组
        size_groups = defaultdict(list)
        for file_info in files:
            size_groups[file_info['size']].append(file_info)
        
        # 查找可能的重复文件
        potential_duplicates = []
        for size, file_list in size_groups.items():
            if len(file_list) > 1 and size > 0:  # 忽略空文件
                potential_duplicates.extend(file_list)
        
        # 按文件名分组查找同名文件
        name_groups = defaultdict(list)
        for file_info in files:
            name_groups[file_info['name']].append(file_info)
        
        same_name_files = []
        for name, file_list in name_groups.items():
            if len(file_list) > 1:
                same_name_files.extend(file_list)
        
        return {
            'by_size': self._group_by_size(potential_duplicates),
            'by_name': self._group_by_name(same_name_files),
            'potential_count': len(potential_duplicates),
            'same_name_count': len(same_name_files)
        }
    
    def _group_by_size(self, files: List[Dict]) -> Dict:
        """按文件大小分组"""
        groups = defaultdict(list)
        for file_info in files:
            groups[file_info['size']].append({
                'name': file_info['name'],
                'path': file_info['path'],
                'size': file_info['size']
            })
        
        # 只返回有多个文件的组
        return {size: file_list for size, file_list in groups.items() if len(file_list) > 1}
    
    def _group_by_name(self, files: List[Dict]) -> Dict:
        """按文件名分组"""
        groups = defaultdict(list)
        for file_info in files:
            groups[file_info['name']].append({
                'name': file_info['name'],
                'path': file_info['path'],
                'size': file_info['size']
            })
        
        # 只返回有多个文件的组
        return {name: file_list for name, file_list in groups.items() if len(file_list) > 1}
    
    def _get_large_files(self, files: List[Dict], threshold: int) -> List[Dict]:
        """获取大文件列表"""
        large_files = [f for f in files if f['size'] > threshold]
        return sorted(large_files, key=lambda x: x['size'], reverse=True)[:20]  # 前20个大文件
    
    def _analyze_directory_structure(self, app_path: Path) -> Dict:
        """分析目录结构"""
        structure = {}
        
        try:
            for item in app_path.iterdir():
                if item.is_dir():
                    dir_size = self._calculate_directory_size(item)
                    file_count = len(list(item.rglob('*')))
                    
                    structure[item.name] = {
                        'type': 'directory',
                        'size': dir_size,
                        'file_count': file_count
                    }
                else:
                    structure[item.name] = {
                        'type': 'file',
                        'size': item.stat().st_size if item.exists() else 0
                    }
        except Exception as e:
            print(f"警告: 分析目录结构时出错: {e}")
        
        return structure
    
    def _calculate_directory_size(self, directory: Path) -> int:
        """计算目录大小"""
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, IOError):
                        pass
        except Exception:
            pass
        
        return total_size 