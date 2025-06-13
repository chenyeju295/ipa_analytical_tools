"""
IPA文件解析器
负责解压IPA文件，提取应用基本信息和定位主二进制文件
"""

import zipfile
import tempfile
import shutil
import os
import plistlib
from pathlib import Path


class IPAParser:
    """IPA文件解析器"""
    
    def __init__(self, ipa_path: str):
        """初始化IPA解析器
        
        Args:
            ipa_path: IPA文件路径
        """
        self.ipa_path = ipa_path
        self.temp_dir = None
        self.app_info = {}
        self.app_path = None
        self.binary_path = None
        
    def extract(self) -> str:
        """解压IPA文件到临时目录
        
        Returns:
            临时目录路径
        """
        try:
            # 创建临时目录
            self.temp_dir = tempfile.mkdtemp(prefix='ipa_analysis_')
            
            # 解压IPA文件
            with zipfile.ZipFile(self.ipa_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # 查找Payload目录中的.app文件
            payload_dir = Path(self.temp_dir) / 'Payload'
            if not payload_dir.exists():
                raise ValueError("IPA文件格式错误: 找不到Payload目录")
            
            # 找到.app目录
            app_dirs = list(payload_dir.glob('*.app'))
            if not app_dirs:
                raise ValueError("IPA文件格式错误: 找不到.app目录")
            
            self.app_path = app_dirs[0]
            
            return self.temp_dir
            
        except Exception as e:
            self.cleanup()
            raise Exception(f"解压IPA文件失败: {e}")
    
    def get_app_info(self) -> dict:
        """获取应用基本信息
        
        Returns:
            应用信息字典
        """
        if not self.app_path:
            raise ValueError("请先调用extract()方法")
        
        try:
            # 读取Info.plist文件
            info_plist_path = self.app_path / 'Info.plist'
            if not info_plist_path.exists():
                raise ValueError("找不到Info.plist文件")
            
            with open(info_plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
            
            # 提取基本信息
            self.app_info = {
                'name': plist_data.get('CFBundleDisplayName') or plist_data.get('CFBundleName', '未知应用'),
                'bundle_id': plist_data.get('CFBundleIdentifier', '未知'),
                'version': plist_data.get('CFBundleShortVersionString', '未知'),
                'build_version': plist_data.get('CFBundleVersion', '未知'),
                'executable': plist_data.get('CFBundleExecutable', ''),
                'platform': plist_data.get('CFBundleSupportedPlatforms', ['未知'])[0] if plist_data.get('CFBundleSupportedPlatforms') else '未知',
                'minimum_os_version': plist_data.get('MinimumOSVersion', '未知'),
                'file_size': os.path.getsize(self.ipa_path),
                'plist_data': plist_data  # 保留完整的plist数据以备后用
            }
            
            # 计算应用目录大小
            self.app_info['app_size'] = self._calculate_directory_size(self.app_path)
            
            return self.app_info
            
        except Exception as e:
            raise Exception(f"读取应用信息失败: {e}")
    
    def get_binary_path(self) -> str:
        """获取主二进制文件路径
        
        Returns:
            二进制文件路径
        """
        if not self.app_info:
            self.get_app_info()
        
        executable_name = self.app_info.get('executable')
        if not executable_name:
            raise ValueError("无法确定主二进制文件名")
        
        self.binary_path = self.app_path / executable_name
        
        if not self.binary_path.exists():
            raise ValueError(f"找不到主二进制文件: {executable_name}")
        
        return str(self.binary_path)
    
    def get_resources_info(self) -> dict:
        """获取资源文件信息
        
        Returns:
            资源信息字典
        """
        if not self.app_path:
            raise ValueError("请先调用extract()方法")
        
        resources_info = {
            'total_files': 0,
            'total_size': 0,
            'directories': []
        }
        
        # 遍历应用目录
        for root, dirs, files in os.walk(self.app_path):
            resources_info['total_files'] += len(files)
            
            for file in files:
                file_path = Path(root) / file
                try:
                    resources_info['total_size'] += file_path.stat().st_size
                except (OSError, IOError):
                    pass  # 忽略无法访问的文件
        
        # 记录主要目录
        for item in self.app_path.iterdir():
            if item.is_dir():
                resources_info['directories'].append({
                    'name': item.name,
                    'size': self._calculate_directory_size(item)
                })
        
        return resources_info
    
    def _calculate_directory_size(self, directory: Path) -> int:
        """计算目录大小
        
        Args:
            directory: 目录路径
            
        Returns:
            目录大小（字节）
        """
        total_size = 0
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, IOError):
                        pass  # 忽略无法访问的文件
        except Exception:
            pass
        
        return total_size
    
    def cleanup(self):
        """清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except Exception as e:
                print(f"警告: 清理临时文件失败: {e}")
    
    def __del__(self):
        """析构函数，确保清理临时文件"""
        self.cleanup() 