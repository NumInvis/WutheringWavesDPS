#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "wuwa_calc.db"

def migrate():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(app_info)")
    columns = [col[1] for col in cursor.fetchall()]

    print("当前app_info表列:", columns)

    if "itunes_id" not in columns:
        print("添加itunes_id列...")
        cursor.execute("ALTER TABLE app_info ADD COLUMN itunes_id VARCHAR(50)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_app_info_itunes_id ON app_info(itunes_id)")

    if "icon_url" not in columns:
        print("添加icon_url列...")
        cursor.execute("ALTER TABLE app_info ADD COLUMN icon_url VARCHAR(500)")

    if "developer" not in columns:
        print("添加developer列...")
        cursor.execute("ALTER TABLE app_info ADD COLUMN developer VARCHAR(100)")

    conn.commit()
    print("数据库迁移完成！")

