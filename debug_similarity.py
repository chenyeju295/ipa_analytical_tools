#!/usr/bin/env python3
"""
相似性分析调试工具
深入分析字符串重复情况
"""

import json
import sys
import os
from pathlib import Path
from collections import Counter, defaultdict

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from similarity_analyzer import SimilarityAnalyzer


def load_app_data(file_path):
    """加载应用分析数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_all_strings_detailed(data):
    """详细提取所有字符串，包含来源信息"""
    strings_with_source = []
    
    strings_data = data.get('strings', {})
    categories = strings_data.get('categories', {})
    
    for category, string_list in categories.items():
        if isinstance(string_list, list):
            for item in string_list:
                if isinstance(item, str):
                    strings_with_source.append({
                        'content': item,
                        'category': category,
                        'type': 'string'
                    })
                elif isinstance(item, dict) and 'content' in item:
                    strings_with_source.append({
                        'content': item['content'],
                        'category': category,
                        'type': 'dict'
                    })
    
    return strings_with_source


def analyze_specific_apps(app_files):
    """分析指定的应用文件"""
    apps_data = {}
    
    # 加载应用数据
    for app_file in app_files:
        if not os.path.exists(app_file):
            print(f"❌ 文件不存在: {app_file}")
            continue
        
        data = load_app_data(app_file)
        app_name = data.get('app_info', {}).get('name', os.path.basename(app_file).replace('_analysis.json', ''))
        apps_data[app_name] = data
        print(f"✅ 加载应用: {app_name}")
    
    if len(apps_data) < 2:
        print("❌ 需要至少2个应用文件进行比较")
        return
    
    print(f"\n📊 开始分析 {len(apps_data)} 个应用...")
    
    # 详细提取字符串
    apps_strings_detailed = {}
    for app_name, data in apps_data.items():
        strings_detailed = extract_all_strings_detailed(data)
        apps_strings_detailed[app_name] = strings_detailed
        print(f"   {app_name}: {len(strings_detailed)} 个字符串")
    
    # 分析重复字符串
    print(f"\n🔍 分析字符串重复情况...")
    
    # 收集所有字符串
    all_strings = {}
    string_to_apps = defaultdict(list)
    
    for app_name, strings_list in apps_strings_detailed.items():
        app_strings = set()
        for string_info in strings_list:
            content = string_info['content']
            app_strings.add(content)
            string_to_apps[content].append({
                'app': app_name,
                'category': string_info['category']
            })
        all_strings[app_name] = app_strings
    
    # 找出重复字符串
    duplicate_strings = {}
    for string_content, apps_info in string_to_apps.items():
        if len(apps_info) > 1:
            duplicate_strings[string_content] = apps_info
    
    print(f"总计重复字符串: {len(duplicate_strings)}")
    
    # 按重复次数分组
    duplicates_by_count = defaultdict(list)
    for string_content, apps_info in duplicate_strings.items():
        count = len(apps_info)
        duplicates_by_count[count].append({
            'content': string_content,
            'apps': [info['app'] for info in apps_info],
            'categories': [info['category'] for info in apps_info]
        })
    
    # 显示统计
    print(f"\n📈 重复字符串统计:")
    for count in sorted(duplicates_by_count.keys(), reverse=True):
        strings_list = duplicates_by_count[count]
        print(f"   出现在 {count} 个应用中: {len(strings_list)} 个字符串")
    
    # 显示前20个最重复的字符串
    print(f"\n🔄 前20个最重复的字符串:")
    all_duplicates = []
    for count, strings_list in duplicates_by_count.items():
        for string_info in strings_list:
            all_duplicates.append((count, string_info))
    
    # 按重复次数和字符串长度排序
    all_duplicates.sort(key=lambda x: (x[0], len(x[1]['content'])), reverse=True)
    
    for i, (count, string_info) in enumerate(all_duplicates[:20], 1):
        content = string_info['content']
        if len(content) > 60:
            content = content[:57] + "..."
        apps_str = ', '.join(string_info['apps'])
        categories_str = ', '.join(set(string_info['categories']))
        print(f"   {i:2}. [{count}次] {content}")
        print(f"       应用: {apps_str}")
        print(f"       类别: {categories_str}")
        print()
    
    # 计算总体统计
    total_strings = sum(len(strings) for strings in all_strings.values())
    unique_strings = len(set().union(*all_strings.values()))
    duplicate_count = sum(len(apps_info) - 1 for apps_info in duplicate_strings.values())
    
    print(f"📊 总体统计:")
    print(f"   总字符串数: {total_strings}")
    print(f"   唯一字符串数: {unique_strings}")
    print(f"   重复字符串数: {duplicate_count}")
    print(f"   重复率: {duplicate_count / total_strings * 100:.1f}%")
    
    # 分析不同类别的重复情况
    print(f"\n📂 按类别分析重复情况:")
    category_duplicates = defaultdict(int)
    for string_content, apps_info in duplicate_strings.items():
        for info in apps_info:
            category_duplicates[info['category']] += 1
    
    for category, count in sorted(category_duplicates.items(), key=lambda x: x[1], reverse=True):
        print(f"   {category}: {count} 个重复字符串")


def main():
    if len(sys.argv) < 3:
        print("用法: python debug_similarity.py <app1_analysis.json> <app2_analysis.json> [...]")
        print("示例: python debug_similarity.py data/analysis_reports/Mimip_analysis.json data/analysis_reports/Zeally_analysis.json")
        sys.exit(1)
    
    app_files = sys.argv[1:]
    analyze_specific_apps(app_files)


if __name__ == "__main__":
    main() 