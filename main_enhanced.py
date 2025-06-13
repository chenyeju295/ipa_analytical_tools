#!/usr/bin/env python3
"""
IPA 分析工具 - 增强版主程序
支持单个或多个IPA文件分析，集成相似性分析功能
"""

import argparse
import sys
import os
import glob
from pathlib import Path
from typing import List, Dict
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from ipa_parser import IPAParser
from string_extractor import StringExtractor
from resource_analyzer import ResourceAnalyzer
from reporter import Reporter
from similarity_analyzer import SimilarityAnalyzer
from analyze_ipa_similarity import IPASimilarityAnalyzer


class BatchIPAAnalyzer:
    """批量IPA分析器"""
    
    def __init__(self, output_dir: str = "data/analysis_reports", verbose: bool = False):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.results = []
        
    def analyze_single_ipa(self, ipa_path: str, min_string_length: int = 4) -> Dict:
        """分析单个IPA文件"""
        if self.verbose:
            print(f"📱 正在分析: {ipa_path}")
        
        try:
            # 1. 解析IPA文件
            parser = IPAParser(ipa_path)
            parser.extract()
            app_info = parser.get_app_info()
            
            # 2. 提取字符串
            string_extractor = StringExtractor(min_length=min_string_length)
            binary_path = parser.get_binary_path()
            strings_data = string_extractor.analyze(binary_path)
            
            # 3. 分析资源
            resource_analyzer = ResourceAnalyzer()
            resources_data = resource_analyzer.analyze(parser.temp_dir)
            
            # 4. 合并分析结果
            analysis_result = {
                'app_info': app_info,
                'strings': strings_data,
                'resources': resources_data,
                'analysis_meta': {
                    'tool_version': '2.0.0',
                    'source_file': ipa_path,
                    'min_string_length': min_string_length,
                    'analyzed_at': datetime.now().isoformat()
                }
            }
            
            # 5. 生成报告
            app_name = app_info.get('name', 'unknown_app')
            json_file = self.output_dir / f"{app_name}_analysis.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            # 清理临时文件
            parser.cleanup()
            
            result = {
                'ipa_path': ipa_path,
                'app_name': app_name,
                'status': 'success',
                'output_file': str(json_file),
                'analysis_result': analysis_result
            }
            
            if self.verbose:
                print(f"✅ 完成分析: {app_name}")
            
            return result
            
        except Exception as e:
            error_result = {
                'ipa_path': ipa_path,
                'status': 'error',
                'error': str(e)
            }
            if self.verbose:
                print(f"❌ 分析失败: {ipa_path} - {e}")
            return error_result
    
    def analyze_multiple_ipas(self, ipa_paths: List[str], min_string_length: int = 4, max_workers: int = 3) -> List[Dict]:
        """并行分析多个IPA文件"""
        print(f"🚀 开始批量分析 {len(ipa_paths)} 个IPA文件")
        
        results = []
        
        # 使用线程池进行并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_ipa = {
                executor.submit(self.analyze_single_ipa, ipa_path, min_string_length): ipa_path 
                for ipa_path in ipa_paths
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_ipa):
                ipa_path = future_to_ipa[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    print(f"进度: {completed}/{len(ipa_paths)} - {ipa_path}")
                except Exception as e:
                    error_result = {
                        'ipa_path': ipa_path,
                        'status': 'error',
                        'error': str(e)
                    }
                    results.append(error_result)
                    print(f"❌ 处理失败: {ipa_path} - {e}")
        
        self.results = results
        return results
    
    def print_batch_summary(self, results: List[Dict]):
        """打印批量分析摘要"""
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']
        
        print("\n" + "=" * 60)
        print("批量分析摘要")
        print("=" * 60)
        print(f"总计: {len(results)} 个文件")
        print(f"成功: {len(successful)} 个")
        print(f"失败: {len(failed)} 个")
        
        if successful:
            print(f"\n✅ 成功分析的应用:")
            for result in successful:
                app_name = result.get('app_name', 'unknown')
                print(f"   • {app_name}")
        
        if failed:
            print(f"\n❌ 失败的文件:")
            for result in failed:
                print(f"   • {result['ipa_path']}: {result['error']}")
        
        print("=" * 60)
    
    def generate_similarity_analysis(self, target_apps: List[str] = None):
        """生成相似性分析"""
        print("\n🔍 开始相似性分析...")
        
        # 使用增强的相似性分析器，默认启用智能过滤
        similarity_analyzer = SimilarityAnalyzer(
            analysis_dir=str(self.output_dir), 
            filter_common_words=True,
            target_apps=target_apps
        )
        comprehensive_report = similarity_analyzer.generate_comprehensive_report()
        
        # 打印摘要
        similarity_analyzer.print_similarity_summary(comprehensive_report)
        
        # 保存详细报告
        report_file = self.output_dir / "comprehensive_similarity_analysis.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 详细相似性报告已保存到: {report_file}")
        
        # 兼容原有的相似性分析工具（如果数据库结构匹配）
        try:
            # 检查是否存在旧版数据库结构
            import sqlite3
            db_path = self.output_dir.parent / "data" / "word_library.db"
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                # 检查是否有apps_list列
                cursor.execute("PRAGMA table_info(words)")
                columns = [row[1] for row in cursor.fetchall()]
                conn.close()
                
                if 'apps_list' in columns:
                    legacy_analyzer = IPASimilarityAnalyzer()
                    legacy_analyzer.analyze_all()
                else:
                    print("ℹ️  数据库结构已更新，使用新版相似性分析器")
            else:
                print("ℹ️  未找到传统数据库，使用新版相似性分析器")
        except Exception as e:
            print(f"ℹ️  传统相似性分析不可用: {e}")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='IPA文件分析工具 - 增强版',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 单个文件分析
  python main_enhanced.py app.ipa
  
  # 多个文件分析
  python main_enhanced.py app1.ipa app2.ipa app3.ipa
  
  # 使用通配符
  python main_enhanced.py ipas/*.ipa
  
  # 指定目录中的所有IPA文件
  python main_enhanced.py --directory ipas/
  
  # 生成详细报告并执行相似性分析
  python main_enhanced.py ipas/*.ipa --similarity --verbose
        '''
    )
    
    parser.add_argument('ipa_files', nargs='*', help='IPA文件路径(支持多个)')
    parser.add_argument('-d', '--directory', help='包含IPA文件的目录')
    parser.add_argument('-o', '--output', default='data/analysis_reports', help='输出目录 (默认: data/analysis_reports)')
    parser.add_argument('--similarity', action='store_true', help='执行相似性分析')
    parser.add_argument('--csv', action='store_true', help='生成CSV格式报告')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('--min-string-length', type=int, default=4, help='最小字符串长度 (默认: 4)')
    parser.add_argument('--max-workers', type=int, default=3, help='并行处理的最大工作线程数 (默认: 3)')
    
    return parser.parse_args()


def collect_ipa_files(args) -> List[str]:
    """收集要分析的IPA文件"""
    ipa_files = []
    
    # 从命令行参数收集文件
    if args.ipa_files:
        for pattern in args.ipa_files:
            if '*' in pattern or '?' in pattern:
                # 通配符模式
                matched_files = glob.glob(pattern)
                ipa_files.extend(matched_files)
            else:
                # 直接文件路径
                ipa_files.append(pattern)
    
    # 从目录收集文件
    if args.directory:
        directory = Path(args.directory)
        if directory.exists() and directory.is_dir():
            ipa_files.extend(str(f) for f in directory.glob('*.ipa'))
        else:
            print(f"错误: 目录不存在: {args.directory}")
            sys.exit(1)
    
    # 验证文件存在性
    valid_files = []
    for file_path in ipa_files:
        if os.path.exists(file_path):
            valid_files.append(file_path)
        else:
            print(f"警告: 文件不存在，跳过: {file_path}")
    
    return valid_files


def main():
    """主函数"""
    args = parse_arguments()
    
    # 收集IPA文件
    ipa_files = collect_ipa_files(args)
    
    if not ipa_files:
        print("错误: 未找到要分析的IPA文件")
        print("请指定IPA文件路径或使用 --directory 指定包含IPA文件的目录")
        sys.exit(1)
    
    # 去重并排序
    ipa_files = sorted(list(set(ipa_files)))
    
    print(f"找到 {len(ipa_files)} 个IPA文件待分析")
    if args.verbose:
        for i, file_path in enumerate(ipa_files, 1):
            print(f"  {i}. {file_path}")
    
    # 创建批量分析器
    analyzer = BatchIPAAnalyzer(output_dir=args.output, verbose=args.verbose)
    
    try:
        if len(ipa_files) == 1:
            # 单文件分析
            result = analyzer.analyze_single_ipa(ipa_files[0], args.min_string_length)
            
            if result['status'] == 'success':
                # 打印单文件摘要
                reporter = Reporter(result['analysis_result'])
                reporter.print_summary()
                
                # 生成CSV报告（如果需要）
                if args.csv:
                    app_name = result['app_name']
                    csv_file = Path(args.output) / f"{app_name}_analysis.csv"
                    reporter.generate_csv(str(csv_file))
                    print(f"CSV报告已保存到: {csv_file}")
                
                print(f"JSON报告已保存到: {result['output_file']}")
            else:
                print(f"分析失败: {result['error']}")
                sys.exit(1)
        else:
            # 多文件分析
            results = analyzer.analyze_multiple_ipas(
                ipa_files, 
                args.min_string_length, 
                args.max_workers
            )
            
            # 打印批量摘要
            analyzer.print_batch_summary(results)
            
            # 生成CSV报告（如果需要）
            if args.csv:
                successful_results = [r for r in results if r['status'] == 'success']
                for result in successful_results:
                    try:
                        reporter = Reporter(result['analysis_result'])
                        app_name = result['app_name']
                        csv_file = Path(args.output) / f"{app_name}_analysis.csv"
                        reporter.generate_csv(str(csv_file))
                        if args.verbose:
                            print(f"CSV报告已生成: {csv_file}")
                    except Exception as e:
                        print(f"生成CSV报告失败 {result['app_name']}: {e}")
        
        # 执行相似性分析
        if args.similarity:
            # 收集当前批次成功分析的应用名称
            if len(ipa_files) == 1:
                # 单文件分析
                if result['status'] == 'success':
                    target_apps = [result['app_name']]
                else:
                    target_apps = None
            else:
                # 多文件分析
                target_apps = [r['app_name'] for r in results if r['status'] == 'success']
            
            analyzer.generate_similarity_analysis(target_apps)
        
    except KeyboardInterrupt:
        print("\n用户中断了分析过程")
        sys.exit(1)
    except Exception as e:
        print(f"分析过程中发生错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    print("\n🎉 所有分析任务完成！")


if __name__ == '__main__':
    main() 