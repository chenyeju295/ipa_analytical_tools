# IPA 分析工具

专业的iOS应用包(.ipa)分析工具，用于提取字符串、分析资源并生成详细报告。

## 项目结构

```
ipa_analytical_tools/
├── src/                    # 核心模块
│   ├── ipa_parser.py      # IPA文件解析器
│   ├── string_extractor.py # 字符串提取器
│   ├── resource_analyzer.py # 资源分析器
│   ├── reporter.py        # 报告生成器
│   └── utils.py           # 工具函数
├── tools/                  # 工具脚本
│   ├── main.py            # 主分析工具
│   ├── quick_analysis.py  # 快速分析工具
│   └── analyze_ipa_similarity.py # 相似性分析
├── docs/                   # 文档目录
│   ├── README.md          # 原始README
│   └── 使用说明.md         # 详细使用说明
├── data/                   # 数据目录
│   ├── analysis_reports/   # 分析报告
│   └── word_library.db     # 词库数据库
└── ipas/                   # IPA文件存放目录
```

## 快速开始

### 🆕 增强版 - 推荐使用

1. **分析单个IPA文件**
   ```bash
   python3 analyze.py single ipas/your_app.ipa
   ```

2. **批量分析目录中的所有IPA文件**
   ```bash
   python3 analyze.py batch ipas/ --similarity
   ```

3. **分析多个指定的IPA文件**
   ```bash
   python3 analyze.py multi app1.ipa app2.ipa app3.ipa --verbose
   ```

4. **仅执行相似性分析**（需要先有分析数据）
   ```bash
   python3 analyze.py similarity
   ```

### 传统版本（兼容）

1. **基础分析**
   ```bash
   python3 main.py ipas/your_app.ipa
   ```

2. **快速分析**（需要先有分析数据）
   ```bash
   python3 tools/quick_analysis.py
   ```

3. **相似性分析**
   ```bash
   python3 tools/analyze_ipa_similarity.py
   ```

## 功能特性

### 🔧 核心分析功能
- ✅ 提取iOS应用中的字符串信息
- ✅ 分析应用资源文件结构
- ✅ 生成详细的JSON/CSV报告
- ✅ 智能词库管理系统
- ✅ 简化输出显示关键结果

### 🆕 增强功能
- ✅ **批量分析**: 支持单个或多个IPA文件同时分析
- ✅ **并行处理**: 多线程并行分析，提升处理速度
- ✅ **深度相似性分析**: 字符串和资源的重复性检测
- ✅ **智能重复检测**: 跨应用的字符串重复统计
- ✅ **相似度矩阵**: 应用间相似度量化分析
- ✅ **优化建议**: 基于分析结果的优化建议
- ✅ **灵活输入**: 支持文件路径、目录、通配符等多种输入方式

## 环境要求

- Python 3.7+
- 依赖库：见各模块导入

详细使用说明请参考 `docs/使用说明.md` 