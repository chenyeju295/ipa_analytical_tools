# IPA 分析工具简化需求文档

## 项目目标
开发一个轻量级的Python工具，用于快速解析.ipa文件并生成统计报告，专注于核心分析功能。

## 核心功能（今天完成）

### 1. IPA文件解析
- 解压.ipa文件到临时目录
- 提取应用基本信息（Info.plist）
- 定位主二进制文件
- 统计文件大小和结构

### 2. 基础信息提取
```python
# 提取内容
{
    "app_name": "应用名称",
    "bundle_id": "com.example.app",
    "version": "1.0.0",
    "file_size": 52428800,
    "binary_size": 15728640,
    "total_files": 1247
}
```

### 3. 字符串分析
- 从二进制文件提取所有字符串
- 基础分类（长度、字符集）
- 统计总数和去重后数量
- 检测常见模式（URL、错误信息等）

### 4. 资源统计
- 图片文件统计（数量、总大小）
- 音频文件统计
- 其他资源文件统计
- 本地化文件统计

### 5. 简单重复检测
- 完全相同的字符串统计
- 基础相似字符串检测
- 常见第三方库标识符识别

### 6. 输出格式
- JSON格式详细报告
- CSV格式统计表格
- 命令行输出摘要信息

## 技术实现方案

### 依赖库（最小化）
```txt
# requirements.txt
zipfile         # 内置，zip文件处理
plistlib        # 内置，plist文件解析
pathlib         # 内置，路径处理
json            # 内置，JSON输出
csv             # 内置，CSV输出
re              # 内置，正则表达式
collections     # 内置，数据统计
argparse        # 内置，命令行参数
```

### 项目结构（简化）
```
ipa_analyzer/
├── main.py                 # 主程序入口
├── ipa_parser.py          # IPA文件解析器
├── string_extractor.py    # 字符串提取器
├── resource_analyzer.py   # 资源分析器
├── reporter.py            # 报告生成器
└── utils.py               # 工具函数
```

## 今天的开发计划

### 第1阶段：基础框架 (1-2小时)
- [x] 创建项目结构
- [ ] 实现IPA文件解压功能
- [ ] 实现Info.plist解析
- [ ] 基础命令行接口

### 第2阶段：核心功能 (2-3小时)
- [ ] 实现字符串提取功能
- [ ] 实现资源文件统计
- [ ] 基础数据统计和分类

### 第3阶段：报告生成 (1-2小时)
- [ ] JSON格式输出
- [ ] CSV格式输出
- [ ] 命令行摘要显示

### 第4阶段：测试和完善 (1小时)
- [ ] 基础测试和错误处理
- [ ] 文档和使用说明

## 核心类设计

### IPA解析器
```python
class IPAParser:
    def __init__(self, ipa_path: str):
        self.ipa_path = ipa_path
        self.temp_dir = None
        self.app_info = {}
    
    def extract(self) -> str:
        """解压IPA文件"""
        pass
    
    def get_app_info(self) -> dict:
        """获取应用基本信息"""
        pass
    
    def get_binary_path(self) -> str:
        """获取主二进制文件路径"""
        pass
    
    def cleanup(self):
        """清理临时文件"""
        pass
```

### 字符串提取器
```python
class StringExtractor:
    def extract_from_binary(self, binary_path: str) -> list:
        """从二进制文件提取字符串"""
        pass
    
    def categorize_strings(self, strings: list) -> dict:
        """字符串分类统计"""
        pass
    
    def find_duplicates(self, strings: list) -> dict:
        """查找重复字符串"""
        pass
```

### 报告生成器
```python
class Reporter:
    def __init__(self, analysis_data: dict):
        self.data = analysis_data
    
    def generate_json(self, output_path: str):
        """生成JSON报告"""
        pass
    
    def generate_csv(self, output_path: str):
        """生成CSV报告"""
        pass
    
    def print_summary(self):
        """打印命令行摘要"""
        pass
```

## 使用方式

### 基本命令
```bash
# 分析单个IPA文件
python main.py app.ipa

# 指定输出目录
python main.py app.ipa -o ./output

# 生成CSV报告
python main.py app.ipa --csv

# 详细输出
python main.py app.ipa --verbose
```

### 输出示例
```bash
# 命令行输出
IPA Analysis Report
==================
App Name: Example App
Bundle ID: com.example.app
Version: 1.0.0
File Size: 50.0 MB
Binary Size: 15.0 MB

Strings Analysis:
- Total strings: 12,345
- Unique strings: 9,876
- Duplicate rate: 20.0%
- URLs found: 23
- Error messages: 45

Resources:
- Images: 156 files (8.5 MB)
- Audio: 12 files (2.1 MB)  
- Other: 89 files (1.2 MB)
```

## 预期成果

### 今天完成的功能
1. ✅ 完整的IPA文件解析
2. ✅ 基础信息提取和统计
3. ✅ 字符串提取和分类
4. ✅ 资源文件统计
5. ✅ JSON/CSV报告生成
6. ✅ 命令行工具

### 性能目标
- 处理50MB的IPA文件 < 30秒
- 内存使用 < 500MB
- 字符串提取准确率 > 90%

### 扩展计划（后续）
- 多文件批量处理
- 更高级的重复检测算法
- 数据库存储历史分析结果
- Web界面（可选）

## 技术细节

### 字符串提取方法
```python
def extract_strings_simple(binary_path: str, min_length: int = 4) -> list:
    """简单字符串提取实现"""
    strings = []
    with open(binary_path, 'rb') as f:
        data = f.read()
        # 查找ASCII字符串
        current_string = ""
        for byte in data:
            if 32 <= byte <= 126:  # 可打印ASCII字符
                current_string += chr(byte)
            else:
                if len(current_string) >= min_length:
                    strings.append(current_string)
                current_string = ""
    return strings
```

### 基础分类规则
```python
STRING_PATTERNS = {
    'urls': r'https?://[^\s]+',
    'apis': r'/api/[^\s]*',
    'errors': r'(?i)(error|failed|exception|invalid)',
    'bundle_ids': r'[a-z]+\.[a-z]+\.[a-z]+',
    'file_paths': r'[./][^\s]*\.(png|jpg|mp3|json|plist)'
}
```

这个简化版本专注于核心功能，去掉了复杂的图形界面和高级分析功能，可以在今天内完成基础实现。您觉得这个计划合适吗？需要我开始实现某个特定模块吗？ 