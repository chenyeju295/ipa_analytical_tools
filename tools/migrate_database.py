#!/usr/bin/env python3
"""
数据库迁移工具
将旧版词库数据库结构迁移到新版本
"""

import sqlite3
import os
import json
from pathlib import Path


def check_database_version(db_path):
    """检查数据库版本"""
    if not os.path.exists(db_path):
        return "not_exists"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(words)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'apps_list' in columns:
            version = "legacy"
        elif 'content_hash' in columns:
            version = "new"
        else:
            version = "unknown"
        
        conn.close()
        return version
        
    except Exception as e:
        print(f"检查数据库版本时出错: {e}")
        return "error"


def migrate_legacy_to_new(legacy_db_path, new_db_path=None):
    """将旧版数据库迁移到新版结构"""
    if new_db_path is None:
        new_db_path = legacy_db_path + ".new"
    
    print(f"开始迁移数据库: {legacy_db_path} -> {new_db_path}")
    
    # 连接旧数据库
    legacy_conn = sqlite3.connect(legacy_db_path)
    legacy_cursor = legacy_conn.cursor()
    
    # 创建新数据库
    new_conn = sqlite3.connect(new_db_path)
    new_cursor = new_conn.cursor()
    
    # 创建新的表结构
    create_new_tables(new_cursor)
    
    try:
        # 迁移应用数据
        print("迁移应用数据...")
        legacy_cursor.execute("SELECT * FROM apps")
        apps = legacy_cursor.fetchall()
        
        app_id_mapping = {}
        for app in apps:
            # 旧结构: id, app_name, bundle_id, version, analysis_time, file_path, file_hash
            old_id, app_name, bundle_id, version, analysis_time, file_path, file_hash = app
            
            new_cursor.execute("""
                INSERT INTO apps (app_name, bundle_id, version, analysis_time, file_path, file_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (app_name, bundle_id, version, analysis_time, file_path, file_hash))
            
            new_id = new_cursor.lastrowid
            app_id_mapping[old_id] = new_id
        
        # 迁移词汇数据
        print("迁移词汇数据...")
        legacy_cursor.execute("SELECT * FROM words")
        words = legacy_cursor.fetchall()
        
        word_id_mapping = {}
        for word in words:
            if len(word) >= 8:  # 新版本字段更多
                # 旧结构: id, word, category, frequency, first_seen, last_seen, apps_count, apps_list, word_hash
                old_id, content, category, frequency, first_seen, last_seen, apps_count, apps_list, word_hash = word[:9]
                
                # 计算content_hash（如果没有的话）
                if not word_hash:
                    import hashlib
                    word_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                
                new_cursor.execute("""
                    INSERT OR IGNORE INTO words (content, content_hash, category)
                    VALUES (?, ?, ?)
                """, (content, word_hash, category))
                
                new_cursor.execute("SELECT id FROM words WHERE content_hash = ?", (word_hash,))
                result = new_cursor.fetchone()
                if result:
                    new_id = result[0]
                    word_id_mapping[old_id] = new_id
                    
                    # 处理应用关联
                    if apps_list:
                        app_names = apps_list.split(',')
                        for app_name in app_names:
                            app_name = app_name.strip()
                            # 查找对应的app_id
                            new_cursor.execute("SELECT id FROM apps WHERE app_name = ?", (app_name,))
                            app_result = new_cursor.fetchone()
                            if app_result:
                                app_id = app_result[0]
                                new_cursor.execute("""
                                    INSERT OR IGNORE INTO word_app_relations (word_id, app_id)
                                    VALUES (?, ?)
                                """, (new_id, app_id))
        
        new_conn.commit()
        print(f"✅ 数据库迁移完成: {new_db_path}")
        
        # 验证迁移结果
        new_cursor.execute("SELECT COUNT(*) FROM apps")
        apps_count = new_cursor.fetchone()[0]
        
        new_cursor.execute("SELECT COUNT(*) FROM words")
        words_count = new_cursor.fetchone()[0]
        
        new_cursor.execute("SELECT COUNT(*) FROM word_app_relations")
        relations_count = new_cursor.fetchone()[0]
        
        print(f"迁移统计: {apps_count} 个应用, {words_count} 个词汇, {relations_count} 个关联")
        
    except Exception as e:
        print(f"迁移过程中出错: {e}")
        new_conn.rollback()
        raise
    
    finally:
        legacy_conn.close()
        new_conn.close()


def create_new_tables(cursor):
    """创建新版本的表结构"""
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


def backup_database(db_path):
    """备份数据库"""
    if not os.path.exists(db_path):
        return None
    
    backup_path = db_path + ".backup"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"数据库已备份到: {backup_path}")
    return backup_path


def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "word_library.db"
    
    print("🔄 数据库迁移工具")
    print("=" * 50)
    
    # 检查数据库版本
    version = check_database_version(str(db_path))
    
    if version == "not_exists":
        print("ℹ️  数据库不存在，无需迁移")
        return
    
    elif version == "new":
        print("✅ 数据库已经是新版本，无需迁移")
        return
    
    elif version == "legacy":
        print("🔍 检测到旧版数据库，开始迁移...")
        
        # 备份原数据库
        backup_path = backup_database(str(db_path))
        
        try:
            # 迁移到临时文件
            temp_db_path = str(db_path) + ".migrated"
            migrate_legacy_to_new(str(db_path), temp_db_path)
            
            # 替换原文件
            import shutil
            shutil.move(temp_db_path, str(db_path))
            
            print("✅ 迁移完成！数据库已更新到新版本")
            print(f"原数据库备份: {backup_path}")
            
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            if backup_path and os.path.exists(backup_path):
                import shutil
                shutil.copy2(backup_path, str(db_path))
                print("已恢复原数据库")
    
    elif version == "error":
        print("❌ 数据库检查失败")
    
    else:
        print(f"❓ 未知的数据库版本: {version}")


if __name__ == "__main__":
    main() 