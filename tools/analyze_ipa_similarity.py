#!/usr/bin/env python3
"""
IPA相似性分析 - 优化版本
简化输出，只显示关键结果
"""

import os
import json
import sqlite3
from datetime import datetime
from collections import defaultdict

class IPASimilarityAnalyzer:
    def __init__(self, db_path=None):
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(__file__))
        self.db_path = db_path or os.path.join(project_root, 'data', 'word_library.db')
        self.analysis_dir = os.path.join(project_root, 'data', 'analysis_reports')
        
        # 确保data目录存在
        os.makedirs(os.path.join(project_root, 'data'), exist_ok=True)
        os.makedirs(self.analysis_dir, exist_ok=True)
        
    def analyze_all(self):
        """执行完整分析并输出简化结果"""
        print("🔍 IPA相似性分析")
        print("=" * 50)
        
        # 确保词库是最新的
        self._update_word_library()
        
        # 获取统计信息
        stats = self._get_statistics()
        
        # 显示基本统计
        self._print_basic_stats(stats)
        
        # 显示应用相似性
        self._print_similarity_results()
        
        # 显示前十重复词
        self._print_top_common_words()
        
        print("\n✅ 分析完成")
    
    def _update_word_library(self):
        """静默更新词库"""
        for filename in os.listdir(self.analysis_dir):
            if filename.endswith('_analysis.json') and filename != 'similarity_analysis.json':
                filepath = os.path.join(self.analysis_dir, filename)
                self._add_to_library_silent(filepath)
    
    def _add_to_library_silent(self, filepath):
        """静默添加文件到词库"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建表（如果不存在）
            self._create_tables(cursor)
            
            # 检查是否已存在
            import hashlib
            with open(filepath, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            cursor.execute("SELECT id FROM apps WHERE file_hash = ?", (file_hash,))
            if cursor.fetchone():
                conn.close()
                return
            
            # 添加应用
            app_name = os.path.basename(filepath).replace('_analysis.json', '')
            app_info = data.get('app_info', {})
            
            cursor.execute("""
                INSERT INTO apps (app_name, bundle_id, version, analysis_time, file_path, file_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                app_name,
                app_info.get('bundle_id', ''),
                app_info.get('version', ''),
                datetime.now().isoformat(),
                filepath,
                file_hash
            ))
            
            app_id = cursor.lastrowid
            
            # 添加词汇
            strings_data = data.get('strings', {})
            if 'categories' in strings_data:
                strings_data = strings_data['categories']
            
            for category, strings_list in strings_data.items():
                if isinstance(strings_list, list):
                    for item in strings_list:
                        content = item if isinstance(item, str) else item.get('content', '') if isinstance(item, dict) else ''
                        if content and len(content) >= 3 and not content.isdigit():
                            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                            
                            cursor.execute("""
                                INSERT OR IGNORE INTO words (content, content_hash, category)
                                VALUES (?, ?, ?)
                            """, (content, content_hash, category))
                            
                            cursor.execute("SELECT id FROM words WHERE content_hash = ?", (content_hash,))
                            word_id = cursor.fetchone()[0]
                            
                            cursor.execute("""
                                INSERT OR IGNORE INTO word_app_relations (word_id, app_id)
                                VALUES (?, ?)
                            """, (word_id, app_id))
            
            conn.commit()
            conn.close()
            
        except Exception:
            pass
    
    def _create_tables(self, cursor):
        """创建数据库表"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS apps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                bundle_id TEXT NOT NULL,
                version TEXT NOT NULL,
                analysis_time TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                content_hash TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_app_relations (
                word_id INTEGER NOT NULL,
                app_id INTEGER NOT NULL,
                PRIMARY KEY (word_id, app_id),
                FOREIGN KEY (word_id) REFERENCES words(id),
                FOREIGN KEY (app_id) REFERENCES apps(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_word_hash ON words(content_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_word_app ON word_app_relations(word_id)")
    
    def _get_statistics(self):
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 基本统计
        cursor.execute("SELECT COUNT(*) FROM apps")
        total_apps = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM words")
        total_words = cursor.fetchone()[0]
        
        # 应用词汇统计（使用现有表结构）
        cursor.execute("SELECT app_name FROM apps")
        apps = cursor.fetchall()
        app_stats = []
        
        for (app_name,) in apps:
            cursor.execute("SELECT COUNT(*) FROM words WHERE apps_list LIKE ?", (f'%{app_name}%',))
            word_count = cursor.fetchone()[0]
            app_stats.append((app_name, word_count))
        
        app_stats.sort(key=lambda x: x[1], reverse=True)
        
        # 共同词汇统计（使用现有表结构）
        cursor.execute("""
            SELECT apps_count, COUNT(*) as word_count
            FROM words
            GROUP BY apps_count
            ORDER BY apps_count DESC
        """)
        frequency_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_apps': total_apps,
            'total_words': total_words,
            'app_stats': app_stats,
            'frequency_stats': frequency_stats
        }
    
    def _print_basic_stats(self, stats):
        """打印基本统计信息"""
        print(f"📊 分析了 {stats['total_apps']} 个应用，共 {stats['total_words']:,} 个词汇")
        
        if stats['app_stats']:
            max_words = max(count for _, count in stats['app_stats'])
            min_words = min(count for _, count in stats['app_stats'])
            avg_words = sum(count for _, count in stats['app_stats']) / len(stats['app_stats'])
            print(f"📱 应用词汇范围: {min_words:,} - {max_words:,} (平均: {avg_words:,.0f})")
        
        # 显示共同词汇统计
        if stats['frequency_stats']:
            for frequency, word_count in stats['frequency_stats']:
                if frequency > 1:
                    print(f"🔄 出现在 {frequency} 个应用中的词汇: {word_count:,} 个")
    
    def _print_similarity_results(self):
        """显示相似性结果"""
        similarity_file = os.path.join(self.analysis_dir, 'similarity_analysis.json')
        if os.path.exists(similarity_file):
            with open(similarity_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'pairwise_similarity' in data:
                pairwise = data['pairwise_similarity']
                avg_similarity = sum(s['overall_similarity'] for s in pairwise.values()) / len(pairwise)
                max_similarity = max(pairwise.items(), key=lambda x: x[1]['overall_similarity'])
                
                print(f"\n🔍 应用相似度: 平均 {avg_similarity:.1f}%")
                print(f"🎯 最相似应用对: {max_similarity[0].replace('_vs_', ' vs ')} ({max_similarity[1]['overall_similarity']}%)")
        else:
            print("\n🔍 正在计算相似度...")
            self._calculate_similarity()
            self._print_similarity_results()
    
    def _calculate_similarity(self):
        """计算相似性"""
        # 加载分析文件
        analyses = {}
        for filename in os.listdir(self.analysis_dir):
            if filename.endswith('_analysis.json') and filename != 'similarity_analysis.json':
                filepath = os.path.join(self.analysis_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    app_name = filename.replace('_analysis.json', '')
                    analyses[app_name] = data
                except Exception:
                    continue
        
        # 计算成对相似性
        pairwise_similarity = {}
        app_names = list(analyses.keys())
        
        for i, app1 in enumerate(app_names):
            for j, app2 in enumerate(app_names[i+1:], i+1):
                similarity = self._calculate_pairwise_similarity(
                    analyses[app1], analyses[app2]
                )
                pairwise_similarity[f'{app1}_vs_{app2}'] = similarity
        
        # 保存结果
        similarity_results = {
            'pairwise_similarity': pairwise_similarity,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_apps': len(analyses)
        }
        
        with open(os.path.join(self.analysis_dir, 'similarity_analysis.json'), 'w', encoding='utf-8') as f:
            json.dump(similarity_results, f, ensure_ascii=False, indent=2)
    
    def _calculate_pairwise_similarity(self, app1_data, app2_data):
        """计算成对相似性"""
        # 提取字符串
        strings1 = self._extract_strings(app1_data.get('strings', {}))
        strings2 = self._extract_strings(app2_data.get('strings', {}))
        
        # 字符串相似性
        common_strings = strings1.intersection(strings2)
        total_unique_strings = strings1.union(strings2)
        string_similarity = len(common_strings) / len(total_unique_strings) if total_unique_strings else 0
        
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
        
        # 综合相似性
        overall_similarity = (string_similarity * 0.7 + bundle_similarity * 0.3)
        
        return {
            'string_similarity': round(string_similarity * 100, 2),
            'bundle_similarity': round(bundle_similarity * 100, 2),
            'overall_similarity': round(overall_similarity * 100, 2)
        }
    
    def _extract_strings(self, strings_data):
        """提取字符串"""
        all_strings = set()
        
        # 处理不同的数据结构
        if 'categories' in strings_data:
            strings_data = strings_data['categories']
        
        for category, strings_list in strings_data.items():
            if isinstance(strings_list, list):
                for item in strings_list:
                    if isinstance(item, dict) and 'content' in item:
                        all_strings.add(item['content'])
                    elif isinstance(item, str):
                        all_strings.add(item)
        
        return all_strings
    
    def _print_top_common_words(self):
        """显示前十重复词"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取出现频率最高的有意义词汇
        cursor.execute("""
            SELECT word, category, apps_count, apps_list
            FROM words
            WHERE apps_count > 1 
            AND LENGTH(word) >= 3
            AND word NOT LIKE '%{%'
            AND word NOT LIKE '%}%'
            AND word NOT LIKE '%~%'
            AND word NOT LIKE '%Ȩ%'
            AND word NOT LIKE '%ȹ%'
            AND word NOT LIKE '%֧%'
            AND word NOT LIKE '%\\%'
            AND word NOT LIKE '%||%'
            AND (word LIKE '%.%' OR word LIKE '%com.%' OR 
                 category IN ('class_methods', 'ui_texts', 'errors', 'domains', 'urls', 'bundle_ids') OR
                 (LENGTH(word) >= 4 AND word GLOB '*[a-zA-Z]*'))
            ORDER BY apps_count DESC, frequency DESC, LENGTH(word) DESC
            LIMIT 15
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            print(f"\n🔝 前十重复词汇:")
            print("-" * 60)
            for i, (word, category, apps_count, apps_list) in enumerate(results, 1):
                # 限制显示长度
                display_word = word[:30] + '...' if len(word) > 30 else word
                app_list = apps_list.split(',') if apps_list else []
                app_display = ', '.join(app_list[:3])
                if len(app_list) > 3:
                    app_display += f' (等{len(app_list)}个应用)'
                
                print(f"{i:2d}. {display_word}")
                print(f"    类别: {category} | 频率: {apps_count} | 应用: {app_display}")
                print()
        else:
            print("\n❌ 未找到重复词汇")

def main():
    """主函数"""
    analyzer = IPASimilarityAnalyzer()
    analyzer.analyze_all()

if __name__ == '__main__':
    main() 