"""
工具函数模块
提供通用的辅助功能
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict


def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 (md5, sha1, sha256)
        
    Returns:
        文件哈希值
    """
    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception:
        return ""


def format_bytes(bytes_value: int) -> str:
    """格式化字节数为可读格式
    
    Args:
        bytes_value: 字节数
        
    Returns:
        格式化的字符串
    """
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def validate_ipa_file(file_path: str) -> bool:
    """验证IPA文件是否有效
    
    Args:
        file_path: IPA文件路径
        
    Returns:
        是否为有效的IPA文件
    """
    if not os.path.exists(file_path):
        return False
    
    if not file_path.lower().endswith('.ipa'):
        return False
    
    try:
        import zipfile
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            # 检查是否包含Payload目录
            return any(f.startswith('Payload/') and f.endswith('.app/') for f in file_list)
    except Exception:
        return False


def clean_string(text: str) -> str:
    """清理字符串，移除特殊字符
    
    Args:
        text: 原始字符串
        
    Returns:
        清理后的字符串
    """
    if not text:
        return ""
    
    # 移除不可打印字符
    cleaned = ''.join(char for char in text if char.isprintable())
    
    # 移除多余空格
    cleaned = ' '.join(cleaned.split())
    
    return cleaned


def is_text_file(file_path: str) -> bool:
    """判断文件是否为文本文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为文本文件
    """
    text_extensions = {
        '.txt', '.md', '.json', '.xml', '.plist', '.strings',
        '.html', '.css', '.js', '.py', '.java', '.swift',
        '.h', '.m', '.mm', '.cpp', '.c', '.yaml', '.yml'
    }
    
    file_ext = Path(file_path).suffix.lower()
    return file_ext in text_extensions


def get_file_type_category(file_path: str) -> str:
    """获取文件类型分类
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件类型分类
    """
    file_ext = Path(file_path).suffix.lower()
    
    categories = {
        'images': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico'],
        'audio': ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.wma', '.flac'],
        'video': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'],
        'documents': ['.pdf', '.txt', '.rtf', '.doc', '.docx'],
        'data': ['.json', '.xml', '.plist', '.db', '.sqlite', '.realm'],
        'fonts': ['.ttf', '.otf', '.woff', '.woff2'],
        'code': ['.js', '.html', '.css', '.lua', '.py', '.swift', '.h', '.m'],
        'archives': ['.zip', '.tar', '.gz', '.7z'],
        'certificates': ['.cer', '.crt', '.pem', '.p12', '.mobileprovision']
    }
    
    for category, extensions in categories.items():
        if file_ext in extensions:
            return category
    
    return 'other'


def extract_urls_from_text(text: str) -> List[str]:
    """从文本中提取URL
    
    Args:
        text: 输入文本
        
    Returns:
        URL列表
    """
    import re
    
    url_pattern = re.compile(
        r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
        re.IGNORECASE
    )
    
    urls = url_pattern.findall(text)
    return list(set(urls))  # 去重


def is_binary_file(file_path: str) -> bool:
    """判断文件是否为二进制文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为二进制文件
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:
                return True
            
            # 检查非ASCII字符比例
            non_ascii_count = sum(1 for byte in chunk if byte > 127)
            return non_ascii_count / len(chunk) > 0.3 if chunk else False
            
    except Exception:
        return True


def safe_filename(filename: str) -> str:
    """生成安全的文件名
    
    Args:
        filename: 原始文件名
        
    Returns:
        安全的文件名
    """
    import re
    
    # 移除不安全字符
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 限制长度
    if len(safe_name) > 100:
        name_part = safe_name[:80]
        ext_part = safe_name[-20:] if '.' in safe_name else ''
        safe_name = name_part + ext_part
    
    return safe_name


def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """创建进度条字符串
    
    Args:
        current: 当前进度
        total: 总数
        width: 进度条宽度
        
    Returns:
        进度条字符串
    """
    if total == 0:
        return "[" + "=" * width + "]"
    
    progress = current / total
    filled_width = int(width * progress)
    
    bar = "[" + "=" * filled_width + "-" * (width - filled_width) + "]"
    percentage = f"{progress * 100:.1f}%"
    
    return f"{bar} {percentage} ({current}/{total})"


def estimate_processing_time(file_size: int) -> str:
    """估算处理时间
    
    Args:
        file_size: 文件大小（字节）
        
    Returns:
        估算的处理时间字符串
    """
    # 假设处理速度为 10MB/秒
    processing_speed = 10 * 1024 * 1024  # 10MB/s
    
    estimated_seconds = file_size / processing_speed
    
    if estimated_seconds < 60:
        return f"约 {estimated_seconds:.0f} 秒"
    elif estimated_seconds < 3600:
        return f"约 {estimated_seconds / 60:.1f} 分钟"
    else:
        return f"约 {estimated_seconds / 3600:.1f} 小时" 