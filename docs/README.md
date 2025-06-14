# IPA分析工具

一个用于分析iOS应用包(.ipa文件)的Python工具，可以提取字符串、资源信息，并进行应用间相似性比较。

## 🚀 快速开始

### 安装要求
- Python 3.6+
- macOS或Linux系统

### 使用方法

1. **分析IPA文件**
```bash
python3 main.py /path/to/your/app.ipa
```

2. **相似性分析和重复词检测**
```bash
python3 quick_analysis.py
```

## 📊 主要功能

- **字符串提取**: 提取应用中的所有字符串和文本
- **资源分析**: 分析应用包中的资源文件
- **相似性比较**: 计算应用间的相似度
- **重复词检测**: 找出多个应用中的共同词汇
- **分类统计**: 按类别统计词汇分布

## 📁 项目结构

```
ipa_analytical_tools/
├── main.py                    # 主分析脚本
├── quick_analysis.py          # 快速分析入口（推荐）
├── analyze_ipa_similarity.py  # 相似性分析核心
├── analysis_reports/          # 分析报告目录
├── word_library.db           # 词汇数据库
└── 使用说明.md               # 详细使用说明
```

## 📈 输出示例

```
🔍 IPA相似性分析
==================================================
📊 分析了 5 个应用，共 44,799 个词汇
📱 应用词汇范围: 5,631 - 21,820 (平均: 11,271)
🔄 出现在 5 个应用中的词汇: 1,040 个

🔍 应用相似度: 平均 10.0%
🎯 最相似应用对: App1 vs App2 (10.0%)

🔝 前十重复词汇:
 1. webView:requestDeviceOrientation...
    类别: uncategorized | 频率: 5 | 应用: 所有应用
```

## 💡 特性

- ✅ 支持大型IPA文件分析
- ✅ 智能词汇过滤，排除无意义字符
- ✅ 多维度相似性计算
- ✅ SQLite数据库存储，支持增量分析
- ✅ 清晰的命令行界面

## 📋 注意事项

- 第一次运行会创建词汇数据库，可能需要较长时间
- 支持的文件格式: .ipa
- 分析结果保存在 `analysis_reports/` 目录中

---

*详细使用说明请参考 [使用说明.md](使用说明.md)* 