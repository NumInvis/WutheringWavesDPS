# -*- coding: utf-8 -*-
"""检查数据库中的数据"""

import sys
sys.path.insert(0, '.')

from app import app
from database.models import db, Character, CharacterSkill

with app.app_context():
    # 查询椿的技能
    char = Character.query.filter_by(name='椿').first()
    if char:
        print(f'角色: {char.name}')
        print(f'技能数量: {len(char.skills)}')
        print('\n前10个技能:')
        print('-' * 100)
        print(f"{'动作':<10} | {'属性':<6} | {'结算类型':<8} | {'技能类型':<10} | {'伤害类型':<10} | {'倍率关联':<8} | {'倍率':<8}")
        print('-' * 100)
        for skill in char.skills[:10]:
            print(f"{skill.skill_code:<10} | {skill.element:<6} | {skill.settlement_type:<8} | {skill.skill_type:<10} | {skill.damage_type:<10} | {skill.multiplier_base:<8} | {skill.multiplier*100:.2f}%")
    else:
        print('椿不在数据库中，请先导入数据')
        print('\n可用角色:')
        chars = Character.query.all()
        for c in chars[:10]:
            print(f'  - {c.name}')
