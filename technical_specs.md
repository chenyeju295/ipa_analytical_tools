# IPA 分析工具技术规格书

## 1. 核心技术实现要点

### 1.1 IPA 文件结构理解
```
app.ipa
└── Payload/
    └── AppName.app/
        ├── AppName (主二进制文件)
        ├── Info.plist (应用信息)
        ├── Assets.car (图片资源)
        ├── Frameworks/ (第三方框架)
        ├── PlugIns/ (插件)
        └── 其他资源文件
```

### 1.2 关键技术实现

#### 1.2.1 字符串提取算法
```python
def extract_strings_from_binary(binary_path: str, min_length: int = 4) -> List[str]:
    """
    从二进制文件中提取字符串
    - 扫描二进制文件中的可打印ASCII字符序列
    - 过滤掉长度小于min_length的字符串  
    - 处理UTF-8编码的字符串
    """
    strings = []
    # 实现细节：使用正则表达式匹配可打印字符序列
    # 或者使用系统strings命令
    return strings
```

#### 1.2.2 相似度计算
```python
def calculate_similarity(str1: str, str2: str) -> float:
    """
    计算两个字符串的相似度
    - Levenshtein距离
    - Jaccard相似度
    - 余弦相似度
    """
    # 多种算法组合使用
    pass
```

#### 1.2.3 Mach-O文件解析
```python
def parse_macho_file(binary_path: str) -> dict:
    """
    解析Mach-O文件结构
    - 读取加载命令
    - 提取符号表
    - 分析段信息
    """
    pass
```

## 2. 数据分类策略

### 2.1 字符串分类规则
```python
STRING_CATEGORIES = {
    'urls': r'https?://[^\s]+',
    'api_endpoints': r'/api/[^\s]+',
    'error_messages': r'error|failed|exception',
    'ui_texts': r'[A-Z][a-z\s]+',  # 首字母大写的文本
    'debug_info': r'debug|log|trace',
    'file_paths': r'[./][^\s]*\.[a-z]{2,4}',
    'bundle_ids': r'[a-z]+\.[a-z]+\.[a-z]+',
}
```

### 2.2 资源文件分类
```python
RESOURCE_CATEGORIES = {
    'images': ['.png', '.jpg', '.jpeg', '.gif', '.svg'],
    'sounds': ['.mp3', '.wav', '.m4a', '.aac'],
    'videos': ['.mp4', '.mov', '.avi'],
    'data': ['.json', '.xml', '.plist', '.db'],
    'fonts': ['.ttf', '.otf'],
    'documents': ['.pdf', '.txt', '.rtf'],
}
```

## 3. 性能优化策略

### 3.1 内存优化
- 使用生成器处理大文件
- 分块读取二进制文件
- 及时释放临时文件

### 3.2 并行处理
- 多进程处理多个IPA文件
- 多线程处理单个文件内的不同分析任务
- 使用asyncio处理I/O密集型操作

### 3.3 缓存策略
- 文件hash缓存避免重复分析
- 字符串提取结果缓存
- 相似度计算结果缓存

## 4. 输出格式设计

### 4.1 JSON格式
```json
{
  "analysis_info": {
    "timestamp": "2024-01-01T00:00:00Z",
    "tool_version": "1.0.0",
    "analyzed_files": ["app1.ipa", "app2.ipa"]
  },
  "apps": [
    {
      "name": "Example App",
      "bundle_id": "com.example.app",
      "version": "1.0.0",
      "file_size": 52428800,
      "strings": {
        "total": 1234,
        "unique": 987,
        "categories": {
          "urls": ["https://api.example.com"],
          "errors": ["Connection failed"]
        }
      }
    }
  ],
  "comparisons": {
    "duplicate_strings": {
      "NSString": ["app1.ipa", "app2.ipa"],
      "UILabel": ["app1.ipa"]
    },
    "similarity_matrix": [[1.0, 0.75], [0.75, 1.0]]
  }
}
```

### 4.2 HTML报告模板
```html
<!DOCTYPE html>
<html>
<head>
    <title>IPA Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>IPA Analysis Report</h1>
    <div id="similarity-heatmap"></div>
    <div id="wordcloud"></div>
    <table id="duplicate-strings">
        <!-- 重复字符串表格 -->
    </table>
</body>
</html>
```

## 5. 安全考虑

### 5.1 文件安全
- 验证IPA文件完整性
- 限制临时文件权限
- 自动清理临时文件

### 5.2 数据安全
- 不保存敏感信息
- 可选择性过滤敏感字符串
- 报告中脱敏处理

## 6. 兼容性考虑

### 6.1 iOS版本兼容性
- 支持iOS 9.0+ 的IPA文件
- 兼容不同的Mach-O格式
- 处理加密的二进制文件

### 6.2 平台兼容性
- macOS: 原生支持（推荐）
- Linux: 需要额外工具
- Windows: 需要WSL或虚拟机

## 7. 错误处理策略

### 7.1 常见错误类型
- 文件格式不正确
- 二进制文件损坏
- 内存不足
- 权限问题

### 7.2 处理策略
```python
class IPAAnalysisError(Exception):
    """自定义异常类"""
    pass

def safe_analyze_ipa(ipa_path: str) -> dict:
    """安全的IPA分析函数"""
    try:
        # 分析逻辑
        pass
    except FileNotFoundError:
        # 文件不存在处理
        pass
    except PermissionError:
        # 权限错误处理
        pass
    except MemoryError:
        # 内存错误处理
        pass
    except Exception as e:
        # 其他错误处理
        pass
```

## 8. 测试数据准备

### 8.1 测试用例设计
- 正常IPA文件
- 大型IPA文件（>500MB）
- 损坏的IPA文件
- 加密的IPA文件
- 不同iOS版本的IPA文件

### 8.2 性能基准
- 处理速度: 100MB/分钟
- 内存使用: 不超过2GB
- 准确率: 字符串提取准确率>95%

## 9. 部署和分发

### 9.1 打包方式
- PyPI包分发
- Docker容器
- 独立可执行文件

### 9.2 依赖管理
```python
# requirements.txt
macholib>=1.16
pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.4.0
seaborn>=0.11.0
wordcloud>=1.8.0
plotly>=5.0.0
jinja2>=3.0.0
click>=8.0.0
tqdm>=4.60.0
```

## 10. 维护和更新

### 10.1 版本管理
- 语义化版本控制
- 变更日志维护
- 向后兼容性保证

### 10.2 持续改进
- 用户反馈收集
- 性能监控
- 算法优化
- 新功能添加 