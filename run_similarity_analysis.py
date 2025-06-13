#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPA相似性分析脚本
"""

import json
import os
from collections import defaultdict
from datetime import datetime

def load_analysis_files(analysis_dir):
    """加载分析文件"""
    analyses = {}
    for filename in os.listdir(analysis_dir):
        if filename.endswith('_analysis.json') and filename != 'similarity_analysis.json':
            app_name = filename.replace('_analysis.json', '')
            filepath = os.path.join(analysis_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    analyses[app_name] = data
                    print(f'✅ 加载分析文件: {app_name}')
            except Exception as e:
                print(f'❌ 加载文件失败 {filename}: {e}')
    return analyses

def extract_all_strings(strings_data):
    """提取所有字符串"""
    all_strings = set()
    for category, strings_list in strings_data.items():
        if isinstance(strings_list, list):
            for item in strings_list:
                if isinstance(item, dict) and 'content' in item:
                    all_strings.add(item['content'])
                elif isinstance(item, str):
                    all_strings.add(item)
    return all_strings

def extract_resource_names(resources_data):
    """提取资源文件名"""
    resource_names = set()
    files_list = resources_data.get('files', [])
    for file_info in files_list:
        if isinstance(file_info, dict) and 'name' in file_info:
            filename = os.path.basename(file_info['name'])
            resource_names.add(filename)
    return resource_names

def analyze_common_strings(analyses):
    """分析共同字符串"""
    string_frequency = defaultdict(list)
    
    for app_name, analysis in analyses.items():
        strings = extract_all_strings(analysis.get('strings', {}))
        for string in strings:
            string_frequency[string].append(app_name)
    
    common_strings = {}
    for string, apps in string_frequency.items():
        freq = len(apps)
        if freq > 1:
            if freq not in common_strings:
                common_strings[freq] = []
            common_strings[freq].append({
                'string': string,
                'apps': apps,
                'frequency': freq
            })
    
    for freq in common_strings:
        common_strings[freq].sort(key=lambda x: len(x['string']))
    
    return common_strings

def analyze_common_resources(analyses):
    """分析共同资源"""
    resource_frequency = defaultdict(list)
    
    for app_name, analysis in analyses.items():
        resources = extract_resource_names(analysis.get('resources', {}))
        for resource in resources:
            resource_frequency[resource].append(app_name)
    
    common_resources = {}
    for resource, apps in resource_frequency.items():
        freq = len(apps)
        if freq > 1:
            if freq not in common_resources:
                common_resources[freq] = []
            common_resources[freq].append({
                'resource': resource,
                'apps': apps,
                'frequency': freq
            })
    
    for freq in common_resources:
        common_resources[freq].sort(key=lambda x: x['resource'])
    
    return common_resources

def calculate_pairwise_similarity(app1_data, app2_data, app1_name, app2_name):
    """计算成对相似性"""
    # 字符串相似性
    strings1 = extract_all_strings(app1_data.get('strings', {}))
    strings2 = extract_all_strings(app2_data.get('strings', {}))
    
    common_strings = strings1.intersection(strings2)
    total_unique_strings = strings1.union(strings2)
    
    string_similarity = len(common_strings) / len(total_unique_strings) if total_unique_strings else 0
    
    # 资源相似性
    resources1 = extract_resource_names(app1_data.get('resources', {}))
    resources2 = extract_resource_names(app2_data.get('resources', {}))
    
    common_resources = resources1.intersection(resources2)
    total_unique_resources = resources1.union(resources2)
    
    resource_similarity = len(common_resources) / len(total_unique_resources) if total_unique_resources else 0
    
    # Bundle ID相似性
    bundle1 = app1_data.get('app_info', {}).get('bundle_id', '')
    bundle2 = app2_data.get('app_info', {}).get('bundle_id', '')
    
    if bundle1 and bundle2:
        parts1 = bundle1.split('.')
        parts2 = bundle2.split('.')
        
        common_prefix_length = 0
        for p1, p2 in zip(parts1, parts2):
            if p1 == p2:
                common_prefix_length += 1
            else:
                break
        
        max_parts = max(len(parts1), len(parts2))
        bundle_similarity = common_prefix_length / max_parts if max_parts > 0 else 0.0
    else:
        bundle_similarity = 0.0
    
    # 综合相似性得分
    overall_similarity = (string_similarity * 0.4 + resource_similarity * 0.3 + bundle_similarity * 0.3)
    
    return {
        'string_similarity': round(string_similarity * 100, 2),
        'resource_similarity': round(resource_similarity * 100, 2),
        'bundle_similarity': round(bundle_similarity * 100, 2),
        'overall_similarity': round(overall_similarity * 100, 2),
        'common_strings_count': len(common_strings),
        'common_resources_count': len(common_resources)
    }

def main():
    """主函数"""
    print('🔍 IPA相似性分析开始...')
    analyses = load_analysis_files('analysis_reports')

    if analyses:
        print(f'\n📊 已加载 {len(analyses)} 个应用的分析数据')
        
        # 成对相似性分析
        pairwise_similarity = {}
        app_names = list(analyses.keys())
        
        for i, app1 in enumerate(app_names):
            for j, app2 in enumerate(app_names[i+1:], i+1):
                similarity = calculate_pairwise_similarity(
                    analyses[app1], analyses[app2], app1, app2
                )
                pairwise_similarity[f'{app1}_vs_{app2}'] = similarity
        
        # 共同字符串分析
        common_strings = analyze_common_strings(analyses)
        
        # 共同资源分析
        common_resources = analyze_common_resources(analyses)
        
        # 显示结果
        print('\n🔍 应用间相似性对比:')
        print('=' * 80)
        for pair_name, similarity in sorted(pairwise_similarity.items(), 
                                           key=lambda x: x[1]['overall_similarity'], 
                                           reverse=True):
            apps = pair_name.replace('_vs_', ' vs ')
            print(f'{apps:30} | 整体: {similarity["overall_similarity"]:5.1f}% | '
                  f'字符串: {similarity["string_similarity"]:5.1f}% | '
                  f'资源: {similarity["resource_similarity"]:5.1f}% | '
                  f'Bundle: {similarity["bundle_similarity"]:5.1f}%')
        
        # 显示共同字符串
        total_common_strings = sum(len(strings) for strings in common_strings.values())
        print(f'\n🔤 共同字符串分析 (总计 {total_common_strings} 个):')
        print('=' * 50)
        
        for freq in sorted(common_strings.keys(), reverse=True):
            strings_list = common_strings[freq]
            print(f'\n在 {freq} 个应用中出现的字符串 ({len(strings_list)} 个):')
            for string_info in strings_list[:5]:  # 显示前5个
                apps_str = ', '.join(string_info['apps'])
                string_preview = string_info['string'][:40] + '...' if len(string_info['string']) > 40 else string_info['string']
                print(f'  - {string_preview} (应用: {apps_str})')
            if len(strings_list) > 5:
                print(f'  ... 还有 {len(strings_list) - 5} 个字符串')
        
        # 显示共同资源
        total_common_resources = sum(len(resources) for resources in common_resources.values())
        print(f'\n📁 共同资源分析 (总计 {total_common_resources} 个):')
        print('=' * 50)
        
        for freq in sorted(common_resources.keys(), reverse=True):
            resources_list = common_resources[freq]
            print(f'\n在 {freq} 个应用中出现的资源 ({len(resources_list)} 个):')
            for resource_info in resources_list[:10]:  # 显示前10个
                apps_str = ', '.join(resource_info['apps'])
                print(f'  - {resource_info["resource"]} (应用: {apps_str})')
            if len(resources_list) > 10:
                print(f'  ... 还有 {len(resources_list) - 10} 个资源')
        
        # Bundle ID模式分析
        print(f'\n🏷️ Bundle ID模式分析:')
        print('=' * 50)
        bundle_ids = []
        for app in app_names:
            app_info = analyses[app].get('app_info', {})
            bundle_id = app_info.get('bundle_id', 'N/A')
            bundle_ids.append(bundle_id)
        
        valid_bundle_ids = [bid for bid in bundle_ids if bid != 'N/A']
        if valid_bundle_ids:
            common_prefix = os.path.commonprefix(valid_bundle_ids)
            print(f'公共前缀: {common_prefix} (长度: {len(common_prefix)})')
        else:
            common_prefix = ''
            print('未找到有效的Bundle ID')
        
        for app_name, bundle_id in zip(app_names, bundle_ids):
            print(f'  {app_name}: {bundle_id}')
        
        # 保存详细结果
        similarity_results = {
            'pairwise_similarity': pairwise_similarity,
            'common_strings': common_strings,
            'common_resources': common_resources,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_apps': len(analyses)
        }
        
        # 保存到文件
        with open('analysis_reports/similarity_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(similarity_results, f, ensure_ascii=False, indent=2)
        
        print('\n✅ 相似性分析完成！详细结果已保存到 analysis_reports/similarity_analysis.json')
        
        # 显示总结
        highest_similarity = max(pairwise_similarity.items(), key=lambda x: x[1]['overall_similarity'])
        print(f'\n🎯 关键发现:')
        print(f'   - 最相似的应用对: {highest_similarity[0]} (相似度: {highest_similarity[1]["overall_similarity"]}%)')
        print(f'   - 共同字符串总数: {total_common_strings} 个')
        print(f'   - 共同资源总数: {total_common_resources} 个')
        print(f'   - Bundle ID公共前缀长度: {len(common_prefix)} 个字符')
        
    else:
        print('❌ 未找到可分析的文件')

if __name__ == '__main__':
    main() 