# -*- coding: utf-8 -*-
"""
鸣潮DPS计算器 - 数据库模型
正确导入角色技能类型数据
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Character(db.Model):
    """角色表"""
    __tablename__ = 'characters'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    level = db.Column(db.Integer, default=90)
    chain = db.Column(db.Integer, default=0)  # 共鸣链
    skill_level = db.Column(db.Integer, default=10)
    passive_level = db.Column(db.Integer, default=2)
    
    # 基础属性
    base_hp = db.Column(db.Integer, default=0)
    base_atk = db.Column(db.Integer, default=0)
    base_def = db.Column(db.Integer, default=0)
    
    # 能量相关
    ult_energy = db.Column(db.Integer, default=125)  # 大招能量
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    skills = db.relationship('CharacterSkill', backref='character', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'level': self.level,
            'chain': self.chain,
            'skill_level': self.skill_level,
            'passive_level': self.passive_level,
            'base_hp': self.base_hp,
            'base_atk': self.base_atk,
            'base_def': self.base_def,
            'ult_energy': self.ult_energy,
            'skills': [s.to_dict() for s in self.skills]
        }


class CharacterSkill(db.Model):
    """角色技能表 - 对应角色技能类型sheet"""
    __tablename__ = 'character_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'))
    
    # 技能基本信息
    skill_code = db.Column(db.String(50))  # A1, A2-1, E, Q等
    element = db.Column(db.String(20))  # 湮灭/热熔/气动/导电/冷凝/衍射
    settlement_type = db.Column(db.String(20))  # 结算类型：伤害/治疗
    skill_type = db.Column(db.String(50))  # 技能类型：普攻/共鸣技能/闪避反击/变奏等
    damage_type = db.Column(db.String(50))  # 伤害类型：普攻伤害/技能伤害/解放伤害
    damage_subtype = db.Column(db.String(50))  # 伤害子类
    
    # 倍率信息
    multiplier_base = db.Column(db.String(20))  # 倍率关联：攻击/生命/防御
    multiplier = db.Column(db.Float, default=0)  # 倍率值（小数形式，如0.6253表示62.53%）
    
    # 能量相关
    ult_energy_cost = db.Column(db.Float, default=0)  # 大招能量消耗/回复
    resonance_energy1 = db.Column(db.Float, default=0)  # 协奏能量1
    resonance_energy2 = db.Column(db.Float, default=0)  # 协奏能量2
    
    def to_dict(self):
        return {
            'id': self.id,
            'skill_code': self.skill_code,
            'element': self.element,
            'settlement_type': self.settlement_type,
            'skill_type': self.skill_type,
            'damage_type': self.damage_type,
            'damage_subtype': self.damage_subtype,
            'multiplier_base': self.multiplier_base,
            'multiplier': self.multiplier,
            'multiplier_percent': round(self.multiplier * 100, 2) if self.multiplier else 0,
            'ult_energy_cost': self.ult_energy_cost,
            'resonance_energy1': self.resonance_energy1,
            'resonance_energy2': self.resonance_energy2
        }


class Echo(db.Model):
    """声骸表"""
    __tablename__ = 'echoes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    cost = db.Column(db.Integer, default=4)
    element = db.Column(db.String(20))
    set_effect = db.Column(db.Text)
    main_stat = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cost': self.cost,
            'element': self.element,
            'set_effect': self.set_effect,
            'main_stat': self.main_stat
        }


class Weapon(db.Model):
    """武器表"""
    __tablename__ = 'weapons'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    type = db.Column(db.String(20))  # 长刃/迅刀/佩刀/音感仪/臂铠
    base_atk = db.Column(db.Integer, default=500)
    sub_stat = db.Column(db.String(20))
    sub_stat_value = db.Column(db.Float, default=0)
    passive_desc = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'base_atk': self.base_atk,
            'sub_stat': self.sub_stat,
            'sub_stat_value': self.sub_stat_value,
            'passive_desc': self.passive_desc
        }


class CalculationConfig(db.Model):
    """计算配置表"""
    __tablename__ = 'calculation_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'))
    
    # 声骸配置
    echo_c3_count = db.Column(db.Integer, default=2)
    echo_c3_element_dmg = db.Column(db.Float, default=60.0)
    echo_set_bonus = db.Column(db.Float, default=20.0)
    echo_main_atk_pct = db.Column(db.Float, default=33.0)
    echo_fixed_atk = db.Column(db.Float, default=350.0)
    
    # 拐力配置
    support_atk_pct = db.Column(db.Float, default=61.5)
    support_element_dmg = db.Column(db.Float, default=12.0)
    support_all_amplify = db.Column(db.Float, default=35.0)
    support_e_amplify = db.Column(db.Float, default=25.0)
    support_q_amplify = db.Column(db.Float, default=32.0)
    support_crit_rate = db.Column(db.Float, default=12.5)
    support_crit_dmg = db.Column(db.Float, default=25.0)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'character_id': self.character_id,
            'echo_c3_count': self.echo_c3_count,
            'echo_c3_element_dmg': self.echo_c3_element_dmg,
            'echo_set_bonus': self.echo_set_bonus,
            'support_atk_pct': self.support_atk_pct,
            'support_element_dmg': self.support_element_dmg,
            'support_all_amplify': self.support_all_amplify,
            'support_e_amplify': self.support_e_amplify,
            'support_q_amplify': self.support_q_amplify,
            'support_crit_rate': self.support_crit_rate,
            'support_crit_dmg': self.support_crit_dmg
        }
