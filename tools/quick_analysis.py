#!/usr/bin/env python3
"""
IPA快速分析工具
简化的主入口脚本
"""

import os
import sys

# 添加tools目录到Python路径以导入analyze_ipa_similarity
sys.path.insert(0, os.path.dirname(__file__))

from analyze_ipa_similarity import IPASimilarityAnalyzer

def main():
    """主入口函数"""
    print("🚀 IPA快速分析工具")
    print("=" * 50)
    
    # 检查是否有分析文件
    analysis_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'analysis_reports')
    if not os.path.exists(analysis_dir):
        print("❌ 未找到分析报告目录")
        print("请先使用 tools/main.py 分析IPA文件")
        return
    
    # 统计分析文件数量
    analysis_files = [f for f in os.listdir(analysis_dir) 
                     if f.endswith('_analysis.json') and f != 'similarity_analysis.json']
    
    if not analysis_files:
        print("❌ 未找到IPA分析文件")
        print("请先使用 tools/main.py 分析IPA文件")
        return
    
    print(f"📁 找到 {len(analysis_files)} 个分析文件")
    
    # 执行分析
    analyzer = IPASimilarityAnalyzer()
    analyzer.analyze_all()

if __name__ == '__main__':
    main() 