#!/usr/bin/env python3
"""
IPA分析工具 - 快速启动脚本
提供简单易用的命令行界面
"""

import sys
import subprocess
from pathlib import Path


def show_usage():
    """显示使用说明"""
    print("""
🔍 IPA分析工具 - 快速启动

基本用法:
  python analyze.py <命令> [选项]

命令:
  single <ipa_file>              分析单个IPA文件
  batch <directory>              批量分析目录中的所有IPA文件
  multi <file1> <file2> ...      分析多个指定的IPA文件
  similarity                     对已分析的文件进行相似性分析
  
选项:
  --verbose                      显示详细输出
  --csv                          生成CSV报告
  --similarity                   同时执行相似性分析

示例:
  python analyze.py single app.ipa
  python analyze.py batch ipas/ --similarity
  python analyze.py multi app1.ipa app2.ipa --verbose
  python analyze.py similarity
    """)


def run_enhanced_main(args):
    """运行增强版主程序"""
    cmd = [sys.executable, "main_enhanced.py"] + args
    return subprocess.run(cmd)


def main():
    if len(sys.argv) < 2:
        show_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "single":
        if len(sys.argv) < 3:
            print("❌ 错误: 请指定IPA文件路径")
            print("用法: python analyze.py single <ipa_file>")
            sys.exit(1)
        
        ipa_file = sys.argv[2]
        extra_args = sys.argv[3:]
        
        args = [ipa_file] + extra_args
        print(f"📱 分析单个IPA文件: {ipa_file}")
        run_enhanced_main(args)
    
    elif command == "batch":
        if len(sys.argv) < 3:
            print("❌ 错误: 请指定包含IPA文件的目录")
            print("用法: python analyze.py batch <directory>")
            sys.exit(1)
        
        directory = sys.argv[2]
        extra_args = sys.argv[3:]
        
        args = ["--directory", directory] + extra_args
        print(f"📁 批量分析目录: {directory}")
        run_enhanced_main(args)
    
    elif command == "multi":
        if len(sys.argv) < 3:
            print("❌ 错误: 请指定至少一个IPA文件")
            print("用法: python analyze.py multi <file1> [file2] ...")
            sys.exit(1)
        
        ipa_files = []
        extra_args = []
        
        # 分离IPA文件和额外参数
        for arg in sys.argv[2:]:
            if arg.startswith("--"):
                extra_args.append(arg)
            elif arg.endswith(".ipa"):
                ipa_files.append(arg)
            else:
                extra_args.append(arg)
        
        if not ipa_files:
            print("❌ 错误: 未找到IPA文件")
            sys.exit(1)
        
        args = ipa_files + extra_args
        print(f"📱 分析多个IPA文件: {', '.join(ipa_files)}")
        run_enhanced_main(args)
    
    elif command == "similarity":
        print("🔍 执行相似性分析...")
        # 直接调用相似性分析
        args = ["--similarity"]
        
        # 检查是否有已分析的文件
        analysis_dir = Path("data/analysis_reports")
        if not analysis_dir.exists():
            print("❌ 错误: 未找到分析报告目录")
            print("请先分析一些IPA文件")
            sys.exit(1)
        
        json_files = list(analysis_dir.glob("*_analysis.json"))
        if not json_files:
            print("❌ 错误: 未找到分析文件")
            print("请先使用 single、batch 或 multi 命令分析IPA文件")
            sys.exit(1)
        
        print(f"找到 {len(json_files)} 个分析文件")
        
        # 使用新版相似性分析器
        try:
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
            
            from similarity_analyzer import SimilarityAnalyzer
            import json
            
            # 默认启用智能过滤
            analyzer = SimilarityAnalyzer(filter_common_words=True)
            
            if len(analyzer.apps_data) < 2:
                print("❌ 错误: 需要至少2个已分析的应用才能进行相似性分析")
                print("请先分析更多IPA文件")
                sys.exit(1)
            
            report = analyzer.generate_comprehensive_report()
            analyzer.print_similarity_summary(report)
            
            # 保存报告
            report_file = analysis_dir / "comprehensive_similarity_analysis.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n📊 详细报告已保存到: {report_file}")
            
        except Exception as e:
            print(f"❌ 相似性分析失败: {e}")
            if "--verbose" in sys.argv:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    elif command in ["help", "-h", "--help"]:
        show_usage()
    
    else:
        print(f"❌ 错误: 未知命令 '{command}'")
        show_usage()
        sys.exit(1)


if __name__ == "__main__":
    main() 