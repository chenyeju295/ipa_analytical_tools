#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
词库管理工具
用于管理和查询IPA分析中提取的字符串词库
"""

import sqlite3
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Set, Optional
from collections import defaultdict, Counter


class WordLibraryManager:
    """词库管理器"""
    
    def __init__(self, db_path: str = "word_library.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建词库表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                apps_count INTEGER DEFAULT 1,
                apps_list TEXT NOT NULL,
                word_hash TEXT NOT NULL
            )
        ''')
        
        # 创建应用记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS apps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                bundle_id TEXT NOT NULL,
                version TEXT NOT NULL,
                analysis_time TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL
            )
        ''')
        
        # 创建单词-应用关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS word_app_relations (
                word_id INTEGER,
                app_id INTEGER,
                category TEXT,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (word_id, app_id),
                FOREIGN KEY (word_id) REFERENCES words (id),
                FOREIGN KEY (app_id) REFERENCES apps (id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_words_category ON words (category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_words_apps_count ON words (apps_count)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_words_frequency ON words (frequency)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_word_hash ON words (word_hash)')
        
        conn.commit()
        conn.close()
    
    def add_analysis_data(self, analysis_file: str) -> Optional[int]:
        """从分析文件添加数据到词库"""
        if not os.path.exists(analysis_file):
            print(f"❌ 分析文件不存在: {analysis_file}")
            return None
        
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
        except Exception as e:
            print(f"❌ 读取分析文件失败: {e}")
            return None
        
        app_info = analysis_data.get('app_info', {})
        # 尝试两种可能的字符串数据结构
        strings_data = analysis_data.get('strings', {})
        if not strings_data:
            strings_analysis = analysis_data.get('strings_analysis', {})
            strings_data = strings_analysis.get('categories', {})
        
        return self._add_app_data(app_info, strings_data, analysis_file)
    
    def _add_app_data(self, app_info: Dict, strings_data: Dict, file_path: str) -> Optional[int]:
        """添加应用数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算文件hash
        app_signature = f"{app_info.get('bundle_id', '')}{app_info.get('version', '')}"
        file_hash = hashlib.md5(app_signature.encode()).hexdigest()
        
        # 检查应用是否已存在
        cursor.execute('SELECT id FROM apps WHERE file_hash = ?', (file_hash,))
        existing_app = cursor.fetchone()
        
        if existing_app:
            app_id = existing_app[0]
            print(f"应用 {app_info.get('app_name', '')} 已存在于词库中 (ID: {app_id})")
            conn.close()
            return app_id
        
        # 添加新应用
        cursor.execute('''
            INSERT INTO apps (app_name, bundle_id, version, analysis_time, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            app_info.get('app_name', ''),
            app_info.get('bundle_id', ''),
            app_info.get('version', ''),
            datetime.now().isoformat(),
            file_path,
            file_hash
        ))
        app_id = cursor.lastrowid
        print(f"✅ 新应用 {app_info.get('app_name', '')} 已添加到词库 (ID: {app_id})")
        
        # 添加字符串数据
        word_count = 0
        for category, words_list in strings_data.items():
            if isinstance(words_list, list):
                for word_item in words_list:
                    # 处理不同的数据格式
                    if isinstance(word_item, dict) and 'content' in word_item:
                        word = word_item['content']
                    elif isinstance(word_item, str):
                        word = word_item
                    else:
                        continue
                    
                    # 过滤条件：长度>=3，不全是数字/符号
                    if len(word.strip()) >= 3 and not word.isdigit():
                        self._add_word(cursor, word, category, app_id)
                        word_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"  添加了 {word_count} 个字符串到词库")
        return app_id
    
    def _add_word(self, cursor, word: str, category: str, app_id: int):
        """添加单词到词库"""
        word_hash = hashlib.md5(word.encode()).hexdigest()
        
        # 检查单词是否已存在
        cursor.execute('SELECT id, frequency, apps_list FROM words WHERE word_hash = ?', (word_hash,))
        existing_word = cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if existing_word:
            word_id, frequency, apps_list = existing_word
            apps_set = set(apps_list.split(',')) if apps_list else set()
            apps_set.add(str(app_id))
            
            # 更新现有单词
            cursor.execute('''
                UPDATE words 
                SET frequency = frequency + 1, 
                    last_seen = ?, 
                    apps_count = ?, 
                    apps_list = ?
                WHERE id = ?
            ''', (now, len(apps_set), ','.join(apps_set), word_id))
        else:
            # 添加新单词
            cursor.execute('''
                INSERT INTO words (word, category, frequency, first_seen, last_seen, apps_count, apps_list, word_hash)
                VALUES (?, ?, 1, ?, ?, 1, ?, ?)
            ''', (word, category, now, now, str(app_id), word_hash))
            word_id = cursor.lastrowid
        
        # 添加或更新单词-应用关联
        cursor.execute('''
            INSERT OR REPLACE INTO word_app_relations (word_id, app_id, category, count)
            VALUES (?, ?, ?, COALESCE((SELECT count + 1 FROM word_app_relations WHERE word_id = ? AND app_id = ?), 1))
        ''', (word_id, app_id, category, word_id, app_id))
    
    def get_common_words(self, min_apps: int = 2, category: str = None, limit: int = 100) -> List[Dict]:
        """获取共同单词"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT w.word, w.category, w.apps_count, w.frequency, w.apps_list
            FROM words w
            WHERE w.apps_count >= ?
        '''
        params = [min_apps]
        
        if category:
            query += ' AND w.category = ?'
            params.append(category)
        
        query += ' ORDER BY w.apps_count DESC, w.frequency DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            word, cat, apps_count, frequency, apps_list = row
            results.append({
                'word': word,
                'category': cat,
                'apps_count': apps_count,
                'frequency': frequency,
                'apps_list': apps_list.split(',') if apps_list else []
            })
        
        conn.close()
        return results
    
    def search_words(self, pattern: str, category: str = None, limit: int = 50) -> List[Dict]:
        """搜索单词"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT w.word, w.category, w.apps_count, w.frequency
            FROM words w
            WHERE w.word LIKE ?
        '''
        params = [f'%{pattern}%']
        
        if category:
            query += ' AND w.category = ?'
            params.append(category)
        
        query += ' ORDER BY w.frequency DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            word, cat, apps_count, frequency = row
            results.append({
                'word': word,
                'category': cat,
                'apps_count': apps_count,
                'frequency': frequency
            })
        
        conn.close()
        return results
    
    def get_statistics(self) -> Dict:
        """获取词库统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 基本统计
        cursor.execute('SELECT COUNT(*) FROM apps')
        total_apps = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM words')
        total_words = cursor.fetchone()[0]
        
        # 按分类统计
        cursor.execute('SELECT category, COUNT(*) FROM words GROUP BY category ORDER BY COUNT(*) DESC')
        category_stats = dict(cursor.fetchall())
        
        # 共同单词统计
        cursor.execute('SELECT apps_count, COUNT(*) FROM words GROUP BY apps_count ORDER BY apps_count DESC')
        common_words_stats = dict(cursor.fetchall())
        
        # 最频繁的单词
        cursor.execute('SELECT word, frequency, apps_count FROM words ORDER BY frequency DESC LIMIT 10')
        top_frequent_words = [{'word': row[0], 'frequency': row[1], 'apps_count': row[2]} for row in cursor.fetchall()]
        
        # 应用信息
        cursor.execute('SELECT app_name, bundle_id, analysis_time FROM apps ORDER BY analysis_time DESC')
        apps_info = [{'name': row[0], 'bundle_id': row[1], 'time': row[2]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_apps': total_apps,
            'total_words': total_words,
            'category_stats': category_stats,
            'common_words_stats': common_words_stats,
            'top_frequent_words': top_frequent_words,
            'apps_info': apps_info
        }
    
    def export_common_words(self, output_file: str, min_apps: int = 2):
        """导出共同单词到CSV文件"""
        common_words = self.get_common_words(min_apps=min_apps, limit=1000)
        
        import csv
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['word', 'category', 'apps_count', 'frequency', 'apps_list']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for word_info in common_words:
                writer.writerow({
                    'word': word_info['word'],
                    'category': word_info['category'],
                    'apps_count': word_info['apps_count'],
                    'frequency': word_info['frequency'],
                    'apps_list': ','.join(word_info['apps_list'])
                })
        
        print(f"✅ 共同单词已导出到: {output_file}")
    
    def generate_word_cloud_data(self, min_apps: int = 2, category: str = None) -> Dict:
        """生成词云数据"""
        common_words = self.get_common_words(min_apps=min_apps, category=category, limit=200)
        
        word_cloud_data = {}
        for word_info in common_words:
            # 词云权重 = 出现频率 × 应用数量
            weight = word_info['frequency'] * word_info['apps_count']
            word_cloud_data[word_info['word']] = weight
        
        return word_cloud_data
    
    def analyze_app_similarity_by_words(self) -> Dict:
        """基于词库分析应用相似性"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有应用
        cursor.execute('SELECT id, app_name FROM apps')
        apps = dict(cursor.fetchall())
        
        app_similarity = {}
        app_ids = list(apps.keys())
        
        for i, app1_id in enumerate(app_ids):
            for app2_id in app_ids[i+1:]:
                # 获取两个应用的共同单词
                cursor.execute('''
                    SELECT COUNT(*) as common_words
                    FROM word_app_relations war1
                    JOIN word_app_relations war2 ON war1.word_id = war2.word_id
                    WHERE war1.app_id = ? AND war2.app_id = ?
                ''', (app1_id, app2_id))
                
                common_words_count = cursor.fetchone()[0]
                
                # 获取各自的总单词数
                cursor.execute('SELECT COUNT(*) FROM word_app_relations WHERE app_id = ?', (app1_id,))
                app1_words_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM word_app_relations WHERE app_id = ?', (app2_id,))
                app2_words_count = cursor.fetchone()[0]
                
                # 计算Jaccard相似度
                total_unique_words = app1_words_count + app2_words_count - common_words_count
                similarity = common_words_count / total_unique_words if total_unique_words > 0 else 0
                
                app1_name = apps[app1_id]
                app2_name = apps[app2_id]
                app_similarity[f"{app1_name}_vs_{app2_name}"] = {
                    'similarity': round(similarity * 100, 2),
                    'common_words': common_words_count,
                    'app1_words': app1_words_count,
                    'app2_words': app2_words_count
                }
        
        conn.close()
        return app_similarity


def main():
    """主函数 - 命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description='词库管理工具')
    parser.add_argument('--add', help='添加分析文件到词库')
    parser.add_argument('--add-dir', help='添加目录中的所有分析文件到词库')
    parser.add_argument('--stats', action='store_true', help='显示词库统计信息')
    parser.add_argument('--common', type=int, default=2, help='显示出现在N个以上应用中的共同单词')
    parser.add_argument('--search', help='搜索包含指定模式的单词')
    parser.add_argument('--category', help='按分类过滤')
    parser.add_argument('--export', help='导出共同单词到CSV文件')
    parser.add_argument('--similarity', action='store_true', help='分析应用相似性')
    
    args = parser.parse_args()
    
    wlm = WordLibraryManager()
    
    if args.add:
        wlm.add_analysis_data(args.add)
    
    elif args.add_dir:
        if os.path.exists(args.add_dir):
            for filename in os.listdir(args.add_dir):
                if filename.endswith('_analysis.json'):
                    filepath = os.path.join(args.add_dir, filename)
                    wlm.add_analysis_data(filepath)
        else:
            print(f"❌ 目录不存在: {args.add_dir}")
    
    elif args.stats:
        stats = wlm.get_statistics()
        print(f"📊 词库统计信息:")
        print(f"   总应用数: {stats['total_apps']}")
        print(f"   总单词数: {stats['total_words']}")
        print(f"\n📝 分类统计:")
        for category, count in stats['category_stats'].items():
            print(f"   {category}: {count}")
        print(f"\n🔄 共同单词统计:")
        for apps_count, words_count in stats['common_words_stats'].items():
            print(f"   出现在{apps_count}个应用中: {words_count}个单词")
    
    elif args.common:
        common_words = wlm.get_common_words(min_apps=args.common, category=args.category)
        print(f"📝 出现在{args.common}个以上应用中的共同单词 (共{len(common_words)}个):")
        for word_info in common_words[:20]:  # 显示前20个
            apps_str = ', '.join(word_info['apps_list'])
            print(f"   {word_info['word']} ({word_info['category']}) - 频率:{word_info['frequency']}, 应用:{apps_str}")
        if len(common_words) > 20:
            print(f"   ... 还有{len(common_words) - 20}个单词")
    
    elif args.search:
        results = wlm.search_words(args.search, category=args.category)
        print(f"🔍 搜索结果 (模式: '{args.search}', 共{len(results)}个):")
        for word_info in results:
            print(f"   {word_info['word']} ({word_info['category']}) - 频率:{word_info['frequency']}, 应用数:{word_info['apps_count']}")
    
    elif args.export:
        wlm.export_common_words(args.export, min_apps=args.common)
    
    elif args.similarity:
        similarity = wlm.analyze_app_similarity_by_words()
        print("🔍 基于词库的应用相似性分析:")
        for pair, data in sorted(similarity.items(), key=lambda x: x[1]['similarity'], reverse=True):
            print(f"   {pair}: {data['similarity']}% (共同单词:{data['common_words']})")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main() 