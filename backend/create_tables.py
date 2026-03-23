#!/usr/bin/env python3
"""
手动创建数据库表结构
"""
import sys
sys.path.append('/root/ai/WutheringWavesDPS/backend')

from app.core.database import engine
from app.models.base import Base

# 导入所有模型以确保它们被注册
from app.models import user, spreadsheet, star, category, character, announcement, visit_stat, tieba, app_ranking, survey  # noqa: F401

print("开始创建数据库表结构...")

# 检查survey模块是否正确导入
print(f"Survey module imported: {hasattr(survey, 'Survey')}")
print(f"SurveyQuestion module imported: {hasattr(survey, 'SurveyQuestion')}")

# 打印所有已注册的表
print("\n已注册的表:")
for table in Base.metadata.tables.values():
    print(f"- {table.name}")

# 创建表
Base.metadata.create_all(bind=engine)
print("\n数据库表结构创建完成！")
