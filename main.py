#!/usr/bin/env python3
"""
IPA 分析工具 - 主程序入口
用于分析iOS应用包(.ipa)文件中的字符串、资源等信息
"""

import argparse
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from ipa_parser import IPAParser
from string_extractor import StringExtractor
from resource_analyzer import ResourceAnalyzer
from reporter import Reporter
import json


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='IPA文件分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  python main.py app.ipa                    # 基础分析
  python main.py app.ipa -o output/        # 指定输出目录
  python main.py app.ipa --csv             # 生成CSV报告
  python main.py app.ipa -v                # 详细输出
        '''
    )
    
    parser.add_argument('ipa_file', help='IPA文件路径')
    parser.add_argument('-o', '--output', default='.', help='输出目录 (默认: 当前目录)')
    parser.add_argument('--csv', action='store_true', help='生成CSV格式报告')
    parser.add_argument('--json', action='store_true', help='生成JSON格式报告')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('--min-string-length', type=int, default=4, help='最小字符串长度 (默认: 4)')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    # 检查IPA文件是否存在
    if not os.path.exists(args.ipa_file):
        print(f"错误: IPA文件不存在: {args.ipa_file}")
        sys.exit(1)
    
    # 检查输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"正在分析IPA文件: {args.ipa_file}")
        
        # 1. 解析IPA文件
        if args.verbose:
            print("步骤 1/4: 解析IPA文件...")
        parser = IPAParser(args.ipa_file)
        parser.extract()
        app_info = parser.get_app_info()
        
        # 2. 提取字符串
        if args.verbose:
            print("步骤 2/4: 提取字符串...")
        string_extractor = StringExtractor(min_length=args.min_string_length)
        binary_path = parser.get_binary_path()
        strings_data = string_extractor.analyze(binary_path)
        
        # 3. 分析资源
        if args.verbose:
            print("步骤 3/4: 分析资源文件...")
        resource_analyzer = ResourceAnalyzer()
        resources_data = resource_analyzer.analyze(parser.temp_dir)
        
        # 4. 生成报告
        if args.verbose:
            print("步骤 4/4: 生成报告...")
        
        # 合并分析结果
        analysis_result = {
            'app_info': app_info,
            'strings': strings_data,
            'resources': resources_data,
            'analysis_meta': {
                'tool_version': '1.0.0',
                'source_file': args.ipa_file,
                'min_string_length': args.min_string_length
            }
        }
        
        # 生成报告
        reporter = Reporter(analysis_result)
        
        # 命令行摘要
        reporter.print_summary()
        
        # 生成文件报告
        if args.json:
            json_file = output_dir / f"{app_info.get('name', 'app')}_analysis.json"
            reporter.generate_json(str(json_file))
            print(f"JSON报告已保存到: {json_file}")
        
        if args.csv:
            csv_file = output_dir / f"{app_info.get('name', 'app')}_analysis.csv"
            reporter.generate_csv(str(csv_file))
            print(f"CSV报告已保存到: {csv_file}")
        
        # 如果没有指定输出格式，默认生成JSON
        if not args.json and not args.csv:
            json_file = output_dir / f"{app_info.get('name', 'app')}_analysis.json"
            reporter.generate_json(str(json_file))
            print(f"JSON报告已保存到: {json_file}")
        
    except Exception as e:
        print(f"分析过程中发生错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    finally:
        # 清理临时文件
        if 'parser' in locals():
            parser.cleanup()
    
    print("分析完成！")


if __name__ == '__main__':
    main() 