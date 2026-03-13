# -*- coding: utf-8 -*-
"""测试数据导入"""

import sys
sys.path.insert(0, '.')

from data_import.excel_parser import MingchaoDataParser

parser = MingchaoDataParser(r'd:\素材\鸣潮动作数据汇总.xlsx')
characters = parser.parse_all_characters()

print(f'成功解析 {len(characters)} 个角色')

# 查找陆·赫斯
for char in characters:
    if '赫斯' in char['name']:
        print(f'\n角色: {char["name"]}')
        print(f'  等级: {char.get("level", "N/A")}')
        print(f'  共鸣链: {char.get("chain", "N/A")}')
        print(f'  基础攻击: {char.get("base_atk", "N/A")}')
        print(f'  基础生命: {char.get("base_hp", "N/A")}')
        print(f'  基础防御: {char.get("base_def", "N/A")}')
        print(f'  大招能量: {char.get("ult_energy", "N/A")}')
        print(f'  技能数量: {len(char.get("skills", []))}')
        break

print('\n\n所有角色列表:')
for char in characters:
    print(f"  - {char['name']}: {len(char.get('skills', []))}个技能")
