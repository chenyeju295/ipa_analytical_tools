#!/usr/bin/env python3
"""
IPA分析工具使用示例
演示如何使用新的批量分析和相似性分析功能
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from similarity_analyzer import SimilarityAnalyzer
import json


def example_single_analysis():
    """示例1: 单个IPA文件分析"""
    print("=" * 60)
    print("示例1: 单个IPA文件分析")
    print("=" * 60)
    
    print("命令: python analyze.py single ipas/your_app.ipa")
    print("说明: 分析单个IPA文件，生成详细报告")
    print()


def example_batch_analysis():
    """示例2: 批量分析"""
    print("=" * 60)
    print("示例2: 批量分析")
    print("=" * 60)
    
    print("命令: python analyze.py batch ipas/ --similarity --verbose")
    print("说明: 分析目录中的所有IPA文件，并执行相似性分析")
    print()


def example_multi_analysis():
    """示例3: 多文件分析"""
    print("=" * 60)
    print("示例3: 多文件分析")
    print("=" * 60)
    
    print("命令: python analyze.py multi app1.ipa app2.ipa app3.ipa --csv")
    print("说明: 同时分析多个指定的IPA文件，生成CSV报告")
    print()


def example_similarity_only():
    """示例4: 仅相似性分析"""
    print("=" * 60)
    print("示例4: 仅相似性分析")
    print("=" * 60)
    
    print("命令: python analyze.py similarity")
    print("说明: 对已分析的文件执行相似性分析")
    print()


def example_programmatic_usage():
    """示例5: 程序化使用"""
    print("=" * 60)
    print("示例5: 程序化使用相似性分析器")
    print("=" * 60)
    
    # 检查是否有分析数据
    analysis_dir = Path("data/analysis_reports")
    if not analysis_dir.exists():
        print("⚠️  需要先运行一些分析来生成示例数据")
        print("请运行: python analyze.py batch ipas/")
        return
    
    # 创建相似性分析器
    analyzer = SimilarityAnalyzer()
    
    # 检查加载的应用数量
    if len(analyzer.apps_data) < 2:
        print("⚠️  需要至少2个已分析的应用才能进行相似性分析")
        print("请分析更多IPA文件")
        return
    
    print(f"✅ 已加载 {len(analyzer.apps_data)} 个应用的分析数据")
    print("应用列表:", list(analyzer.apps_data.keys()))
    
    # 执行字符串相似性分析
    print("\n📝 执行字符串相似性分析...")
    string_analysis = analyzer.analyze_string_similarity()
    
    if 'duplicate_analysis' in string_analysis:
        dup_stats = string_analysis['duplicate_analysis']['statistics']
        print(f"  重复率: {dup_stats.get('duplication_rate', 0):.1f}%")
        print(f"  重复字符串数: {dup_stats.get('duplicate_strings', 0)}")
    
    # 执行资源相似性分析
    print("\n📁 执行资源相似性分析...")
    resource_analysis = analyzer.analyze_resource_similarity()
    
    if 'duplicate_resources' in resource_analysis:
        dup_resources = resource_analysis['duplicate_resources']
        print(f"  重复资源数: {dup_resources.get('count', 0)}")
        saved_mb = dup_resources.get('total_size_saved', 0) / 1024 / 1024
        print(f"  可节省空间: {saved_mb:.1f}MB")
    
    # 生成综合报告
    print("\n📊 生成综合报告...")
    comprehensive_report = analyzer.generate_comprehensive_report()
    
    # 显示建议
    recommendations = comprehensive_report.get('recommendations', [])
    if recommendations:
        print("\n💡 优化建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    
    print("\n✅ 程序化分析完成")


def show_all_examples():
    """显示所有使用示例"""
    print("🔍 IPA分析工具 - 使用示例")
    print()
    
    example_single_analysis()
    example_batch_analysis()
    example_multi_analysis()
    example_similarity_only()
    example_programmatic_usage()
    
    print("=" * 60)
    print("💡 更多高级选项:")
    print("=" * 60)
    
    advanced_examples = [
        ("并行处理控制", "python main_enhanced.py ipas/*.ipa --max-workers 5"),
        ("指定输出目录", "python main_enhanced.py app.ipa -o custom_output/"),
        ("调整字符串长度", "python main_enhanced.py app.ipa --min-string-length 6"),
        ("生成详细报告", "python main_enhanced.py ipas/*.ipa --verbose --csv --similarity"),
        ("使用通配符", "python main_enhanced.py ipas/production_*.ipa"),
    ]
    
    for desc, cmd in advanced_examples:
        print(f"{desc}:")
        print(f"  {cmd}")
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "programmatic":
        example_programmatic_usage()
    else:
        show_all_examples() 