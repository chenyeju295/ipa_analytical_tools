"""
报告生成器
负责生成分析报告，支持JSON和CSV格式输出
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class Reporter:
    """报告生成器"""
    
    def __init__(self, analysis_data: Dict):
        """初始化报告生成器
        
        Args:
            analysis_data: 分析结果数据
        """
        self.data = analysis_data
        self.timestamp = datetime.now().isoformat()
    
    def print_summary(self):
        """打印命令行摘要"""
        print("\n" + "=" * 60)
        print("IPA 分析报告摘要")
        print("=" * 60)
        
        # 应用基本信息
        app_info = self.data.get('app_info', {})
        print(f"\n📱 应用信息:")
        print(f"   应用名称: {app_info.get('name', '未知')}")
        print(f"   Bundle ID: {app_info.get('bundle_id', '未知')}")
        print(f"   版本: {app_info.get('version', '未知')}")
        print(f"   构建版本: {app_info.get('build_version', '未知')}")
        print(f"   平台: {app_info.get('platform', '未知')}")
        print(f"   最低系统版本: {app_info.get('minimum_os_version', '未知')}")
        
        # 文件大小信息
        file_size = app_info.get('file_size', 0)
        app_size = app_info.get('app_size', 0)
        print(f"\n📦 大小信息:")
        print(f"   IPA文件大小: {self._format_size(file_size)}")
        print(f"   应用包大小: {self._format_size(app_size)}")
        
        # 字符串分析
        strings_data = self.data.get('strings', {})
        print(f"\n🔤 字符串分析:")
        print(f"   总字符串数: {strings_data.get('total_strings', 0):,}")
        print(f"   唯一字符串数: {strings_data.get('unique_strings', 0):,}")
        
        # 计算重复率
        total_strings = strings_data.get('total_strings', 0)
        unique_strings = strings_data.get('unique_strings', 0)
        if total_strings > 0:
            duplicate_rate = (total_strings - unique_strings) / total_strings * 100
            print(f"   重复率: {duplicate_rate:.1f}%")
        
        # 字符串分类统计
        categories = strings_data.get('categories', {})
        if categories:
            print(f"\n   字符串分类:")
            for category, strings_list in categories.items():
                if strings_list and len(strings_list) > 0:
                    print(f"     {category}: {len(strings_list)} 个")
        
        # 重复字符串
        duplicates = strings_data.get('duplicates', {})
        duplicate_count = duplicates.get('count', 0)
        if duplicate_count > 0:
            print(f"   重复字符串: {duplicate_count} 个")
        
        # 资源分析
        resources_data = self.data.get('resources', {})
        print(f"\n📁 资源分析:")
        print(f"   总文件数: {resources_data.get('total_files', 0):,}")
        print(f"   总资源大小: {self._format_size(resources_data.get('total_size', 0))}")
        
        # 资源分类统计
        resource_categories = resources_data.get('categories', {})
        if resource_categories:
            print(f"\n   资源分类:")
            for category, file_list in resource_categories.items():
                if file_list and len(file_list) > 0:
                    total_size = sum(f.get('size', 0) for f in file_list)
                    print(f"     {category}: {len(file_list)} 个文件 ({self._format_size(total_size)})")
        
        # 特殊文件
        special_files = resources_data.get('special_files', {})
        if special_files:
            print(f"\n   特殊文件:")
            for file_type, file_list in special_files.items():
                if file_list:
                    print(f"     {file_type}: {len(file_list)} 个")
        
        # 大文件
        large_files = resources_data.get('large_files', [])
        if large_files:
            print(f"\n   大文件 (>1MB):")
            for file_info in large_files[:5]:  # 显示前5个
                print(f"     {file_info['name']}: {self._format_size(file_info['size'])}")
        
        print("\n" + "=" * 60)
    
    def generate_json(self, output_path: str):
        """生成JSON格式报告
        
        Args:
            output_path: 输出文件路径
        """
        report_data = self._prepare_report_data()
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"生成JSON报告失败: {e}")
    
    def generate_csv(self, output_path: str):
        """生成CSV格式报告
        
        Args:
            output_path: 输出文件路径
        """
        try:
            # 创建输出目录
            output_path = Path(output_path)
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成多个CSV文件
            base_name = output_path.stem
            
            # 1. 应用基本信息
            self._generate_app_info_csv(output_dir / f"{base_name}_app_info.csv")
            
            # 2. 字符串统计
            self._generate_strings_csv(output_dir / f"{base_name}_strings.csv")
            
            # 3. 资源统计
            self._generate_resources_csv(output_dir / f"{base_name}_resources.csv")
            
            # 4. 重复文件
            self._generate_duplicates_csv(output_dir / f"{base_name}_duplicates.csv")
            
        except Exception as e:
            raise Exception(f"生成CSV报告失败: {e}")
    
    def _prepare_report_data(self) -> Dict:
        """准备报告数据"""
        report_data = {
            'report_info': {
                'generated_at': self.timestamp,
                'tool_version': self.data.get('analysis_meta', {}).get('tool_version', '1.0.0'),
                'source_file': self.data.get('analysis_meta', {}).get('source_file', '')
            },
            'app_info': self.data.get('app_info', {}),
            'strings_analysis': self.data.get('strings', {}),
            'resources_analysis': self.data.get('resources', {}),
            'summary': self._generate_summary()
        }
        
        return report_data
    
    def _generate_summary(self) -> Dict:
        """生成摘要信息"""
        app_info = self.data.get('app_info', {})
        strings_data = self.data.get('strings', {})
        resources_data = self.data.get('resources', {})
        
        summary = {
            'app_name': app_info.get('name', '未知'),
            'file_size_mb': round(app_info.get('file_size', 0) / 1024 / 1024, 2),
            'total_strings': strings_data.get('total_strings', 0),
            'unique_strings': strings_data.get('unique_strings', 0),
            'duplicate_rate': 0,
            'total_files': resources_data.get('total_files', 0),
            'total_resource_size_mb': round(resources_data.get('total_size', 0) / 1024 / 1024, 2)
        }
        
        # 计算重复率
        if summary['total_strings'] > 0:
            summary['duplicate_rate'] = round(
                (summary['total_strings'] - summary['unique_strings']) / summary['total_strings'] * 100, 2
            )
        
        return summary
    
    def _generate_app_info_csv(self, output_path: Path):
        """生成应用信息CSV"""
        app_info = self.data.get('app_info', {})
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['属性', '值'])
            
            for key, value in app_info.items():
                if key != 'plist_data':  # 排除完整的plist数据
                    if key.endswith('_size'):
                        value = self._format_size(value)
                    writer.writerow([key, str(value)])
    
    def _generate_strings_csv(self, output_path: Path):
        """生成字符串统计CSV"""
        strings_data = self.data.get('strings', {})
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['类别', '数量', '示例字符串'])
            
            categories = strings_data.get('categories', {})
            for category, strings_list in categories.items():
                if strings_list:
                    # 取前3个作为示例
                    examples = ', '.join(strings_list[:3])
                    if len(strings_list) > 3:
                        examples += f' ... (共{len(strings_list)}个)'
                    writer.writerow([category, len(strings_list), examples])
    
    def _generate_resources_csv(self, output_path: Path):
        """生成资源统计CSV"""
        resources_data = self.data.get('resources', {})
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['文件名', '路径', '大小', '类型', '扩展名'])
            
            categories = resources_data.get('categories', {})
            for category, file_list in categories.items():
                for file_info in file_list:
                    writer.writerow([
                        file_info.get('name', ''),
                        file_info.get('path', ''),
                        self._format_size(file_info.get('size', 0)),
                        category,
                        file_info.get('extension', '')
                    ])
    
    def _generate_duplicates_csv(self, output_path: Path):
        """生成重复文件CSV"""
        strings_data = self.data.get('strings', {})
        resources_data = self.data.get('resources', {})
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['类型', '内容', '出现次数', '说明'])
            
            # 重复字符串
            duplicates = strings_data.get('duplicates', {})
            duplicate_strings = duplicates.get('strings', {})
            for string, count in duplicate_strings.items():
                writer.writerow(['字符串', string, count, '重复字符串'])
            
            # 重复文件（按名称）
            resource_duplicates = resources_data.get('duplicates', {})
            name_duplicates = resource_duplicates.get('by_name', {})
            for name, file_list in name_duplicates.items():
                paths = [f['path'] for f in file_list]
                writer.writerow(['文件名', name, len(file_list), f"路径: {'; '.join(paths)}"])
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小
        
        Args:
            size_bytes: 字节数
            
        Returns:
            格式化的大小字符串
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}" 