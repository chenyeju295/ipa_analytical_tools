#!/usr/bin/env python3
"""
IPA分析总结报告生成器
"""

import os
import json
import sqlite3
from datetime import datetime

def generate_summary_report():
    """生成综合总结报告"""
    
    print("🔍 生成IPA分析总结报告...")
    
    # 加载相似性分析结果
    similarity_file = 'analysis_reports/similarity_analysis.json'
    if os.path.exists(similarity_file):
        with open(similarity_file, 'r', encoding='utf-8') as f:
            similarity_data = json.load(f)
    else:
        similarity_data = {}
    
    # 连接词库数据库
    db_path = 'word_library.db'
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取应用统计
        cursor.execute("SELECT COUNT(*) FROM apps")
        total_apps = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM words")
        total_words = cursor.fetchone()[0]
        
        # 获取分类统计
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM words 
            GROUP BY category 
            ORDER BY count DESC
        """)
        category_stats = cursor.fetchall()
        
        # 获取共同单词统计
        cursor.execute("""
            SELECT frequency, COUNT(*) as word_count
            FROM (
                SELECT word_id, COUNT(*) as frequency
                FROM word_app_relations
                GROUP BY word_id
            ) AS freq_stats
            GROUP BY frequency
            ORDER BY frequency DESC
        """)
        frequency_stats = cursor.fetchall()
        
        # 获取应用信息
        cursor.execute("""
            SELECT a.app_name, COUNT(war.word_id) as word_count
            FROM apps a
            LEFT JOIN word_app_relations war ON a.id = war.app_id
            GROUP BY a.id, a.app_name
            ORDER BY word_count DESC
        """)
        app_stats = cursor.fetchall()
        
        conn.close()
    else:
        total_apps = 0
        total_words = 0
        category_stats = []
        frequency_stats = []
        app_stats = []
    
    # 生成报告
    report = []
    report.append("# IPA分析工具 - 综合总结报告")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 基本统计
    report.append("## 📊 基本统计信息")
    report.append(f"- **分析应用总数**: {total_apps}")
    report.append(f"- **词库总词汇数**: {total_words:,}")
    
    if app_stats:
        report.append(f"- **最大应用词汇数**: {max(count for _, count in app_stats):,}")
        report.append(f"- **最小应用词汇数**: {min(count for _, count in app_stats):,}")
        avg_words = sum(count for _, count in app_stats) / len(app_stats)
        report.append(f"- **平均词汇数**: {avg_words:,.0f}\n")
    
    # 应用分析
    if app_stats:
        report.append("## 📱 应用词汇统计")
        report.append("| 应用名称 | 词汇数量 | 占比 |")
        report.append("|----------|----------|------|")
        for app_name, word_count in app_stats:
            percentage = (word_count / total_words * 100) if total_words > 0 else 0
            report.append(f"| {app_name} | {word_count:,} | {percentage:.1f}% |")
        report.append("")
    
    # 分类统计
    if category_stats:
        report.append("## 🏷️ 词汇分类统计")
        report.append("| 分类 | 数量 | 占比 |")
        report.append("|------|------|------|")
        for category, count in category_stats:
            percentage = (count / total_words * 100) if total_words > 0 else 0
            report.append(f"| {category} | {count:,} | {percentage:.1f}% |")
        report.append("")
    
    # 共同词汇统计
    if frequency_stats:
        report.append("## 🔄 词汇共享分析")
        report.append("| 出现应用数 | 词汇数量 | 百分比 |")
        report.append("|------------|----------|--------|")
        total_unique_words = sum(count for _, count in frequency_stats)
        for frequency, word_count in frequency_stats:
            percentage = (word_count / total_unique_words * 100) if total_unique_words > 0 else 0
            report.append(f"| {frequency} | {word_count:,} | {percentage:.1f}% |")
        report.append("")
    
    # Bundle ID分析
    report.append("## 🏷️ Bundle ID分析")
    
    # 读取应用分析文件获取Bundle ID信息
    bundle_ids = []
    analysis_dir = 'analysis_reports'
    for filename in os.listdir(analysis_dir):
        if filename.endswith('_analysis.json') and filename != 'similarity_analysis.json':
            filepath = os.path.join(analysis_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    bundle_id = data.get('app_info', {}).get('bundle_id', 'N/A')
                    app_name = filename.replace('_analysis.json', '')
                    bundle_ids.append((app_name, bundle_id))
            except Exception:
                continue
    
    if bundle_ids:
        report.append("| 应用名称 | Bundle ID |")
        report.append("|----------|-----------|")
        for app_name, bundle_id in bundle_ids:
            report.append(f"| {app_name} | {bundle_id} |")
        
        # 分析共同前缀
        valid_bundle_ids = [bid for _, bid in bundle_ids if bid != 'N/A']
        if valid_bundle_ids:
            common_prefix = os.path.commonprefix(valid_bundle_ids)
            report.append(f"\n**公共前缀**: `{common_prefix}` (长度: {len(common_prefix)} 字符)")
        report.append("")
    
    # 关键发现
    report.append("## 🎯 关键发现")
    findings = []
    
    if frequency_stats:
        # 统计完全共同的词汇
        for frequency, word_count in frequency_stats:
            if frequency == total_apps and total_apps > 1:
                findings.append(f"- 所有 {total_apps} 个应用都包含 {word_count:,} 个共同词汇")
                break
    
    if category_stats:
        top_category = category_stats[0]
        findings.append(f"- 最大词汇分类是 '{top_category[0]}'，包含 {top_category[1]:,} 个词汇")
    
    if bundle_ids and len(bundle_ids) > 1:
        prefixes = set()
        for _, bundle_id in bundle_ids:
            if bundle_id != 'N/A' and '.' in bundle_id:
                prefixes.add(bundle_id.split('.')[0])
        if len(prefixes) == 1:
            findings.append(f"- 所有应用使用相同的Bundle ID前缀，可能来自同一开发者")
    
    if not findings:
        findings.append("- 应用具有较强的独立性，各自特征明显")
    
    for finding in findings:
        report.append(finding)
    
    report.append("")
    
    # 建议
    report.append("## 💡 分析建议")
    suggestions = [
        "- 关注高频共同词汇，这些可能代表常用的框架或库",
        "- Bundle ID模式可以帮助识别应用的开发来源和组织关系",
        "- 词汇分类统计有助于了解应用的功能重点和技术特征"
    ]
    
    for suggestion in suggestions:
        report.append(suggestion)
    
    # 保存报告
    report_content = '\n'.join(report)
    
    # 保存为Markdown文件
    with open('analysis_reports/综合分析报告.md', 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # 打印报告
    print(report_content)
    
    print(f"\n✅ 综合分析报告已保存到: analysis_reports/综合分析报告.md")

if __name__ == '__main__':
    generate_summary_report() 