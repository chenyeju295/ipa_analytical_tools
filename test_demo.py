#!/usr/bin/env python3
"""
IPA分析工具演示脚本
用于测试工具的基本功能
"""

import os
import sys
from pathlib import Path

# 添加当前目录到模块搜索路径
sys.path.insert(0, str(Path(__file__).parent))

from ipa_parser import IPAParser
from string_extractor import StringExtractor
from resource_analyzer import ResourceAnalyzer
from reporter import Reporter


def demo_analysis(ipa_file_path: str):
    """演示IPA分析功能"""
    print(f"开始分析IPA文件: {ipa_file_path}")
    
    try:
        # 1. 解析IPA文件
        print("\n步骤 1: 解析IPA文件...")
        parser = IPAParser(ipa_file_path)
        parser.extract()
        app_info = parser.get_app_info()
        print(f"应用名称: {app_info.get('name')}")
        print(f"Bundle ID: {app_info.get('bundle_id')}")
        print(f"版本: {app_info.get('version')}")
        
        # 2. 分析字符串
        print("\n步骤 2: 分析字符串...")
        string_extractor = StringExtractor(min_length=4)
        binary_path = parser.get_binary_path()
        strings_data = string_extractor.analyze(binary_path)
        print(f"总字符串数: {strings_data.get('total_strings')}")
        print(f"唯一字符串数: {strings_data.get('unique_strings')}")
        
        # 3. 分析资源
        print("\n步骤 3: 分析资源...")
        resource_analyzer = ResourceAnalyzer()
        resources_data = resource_analyzer.analyze(parser.temp_dir)
        print(f"总文件数: {resources_data.get('total_files')}")
        print(f"总大小: {resources_data.get('total_size')} 字节")
        
        # 4. 生成报告
        print("\n步骤 4: 生成报告...")
        analysis_result = {
            'app_info': app_info,
            'strings': strings_data,
            'resources': resources_data,
            'analysis_meta': {
                'tool_version': '1.0.0',
                'source_file': ipa_file_path
            }
        }
        
        reporter = Reporter(analysis_result)
        reporter.print_summary()
        
        # 生成JSON报告
        output_dir = Path("./demo_output")
        output_dir.mkdir(exist_ok=True)
        
        json_file = output_dir / f"{app_info.get('name', 'app')}_demo.json"
        reporter.generate_json(str(json_file))
        print(f"\nJSON报告已保存到: {json_file}")
        
        # 清理临时文件
        parser.cleanup()
        
        print("\n演示完成！")
        
    except Exception as e:
        print(f"演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python test_demo.py <ipa_file_path>")
        print("示例: python test_demo.py example.ipa")
        sys.exit(1)
    
    ipa_file = sys.argv[1]
    
    if not os.path.exists(ipa_file):
        print(f"错误: 文件不存在: {ipa_file}")
        sys.exit(1)
    
    if not ipa_file.lower().endswith('.ipa'):
        print(f"错误: 不是IPA文件: {ipa_file}")
        sys.exit(1)
    
    demo_analysis(ipa_file)


if __name__ == '__main__':
    main() 