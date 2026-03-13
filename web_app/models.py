# -*- coding: utf-8 -*-
"""
鸣潮动作数据汇总 - 数据库模型
SQLAlchemy ORM Models
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class Gender(enum.Enum):
    """性别"""
    FEMALE = "女"
    MALE = "男"

class BodyType(enum.Enum):
    """体型"""
    LARGE = "大"
    MEDIUM = "中"
    SMALL_MEDIUM = "中小"
    SMALL = "小"

class Element(enum.Enum):
    """属性"""
    SPECTRO = "衍射"
    HAVOC = "湮灭"
    FUSION = "热熔"
    ELECTRO = "导电"
    AERO = "气动"
    GLACIO = "冷凝"

class WeaponType(enum.Enum):
    """武器类型"""
    SWORD = "长刃"
    BROADBLADE = "大刀"
    PISTOLS = "佩枪"
    GAUNTLETS = "臂铠"
    RECTIFIER = "音感仪"

class ActionType(enum.Enum):
    """动作类型"""
    NORMAL_ATTACK = "常态攻击"
    RESONANCE_SKILL = "共鸣技能"
    RESONANCE_CIRCUIT = "共鸣回路"
    RESONANCE_LIBERATION = "共鸣解放"
    INTRO_SKILL = "变奏技能"
    OUTRO_SKILL = "延奏技能"
    DODGE = "闪避"
    ECHO = "声骸"

class PositionState(enum.Enum):
    """位置状态"""
    GROUND = "地面"
    AIR = "空中"
    GROUND_TO_AIR = "地转空"
    AIR_TO_GROUND = "空转地"

# ==================== 角色表 ====================

class Character(Base):
    """角色"""
    __tablename__ = 'characters'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    gender = Column(Enum(Gender), nullable=False)
    body_type = Column(Enum(BodyType), nullable=False)
    element = Column(Enum(Element))
    weapon_type = Column(Enum(WeaponType))
    release_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    actions = relationship("Action", back_populates="character", cascade="all, delete-orphan")
    damage_configs = relationship("DamageConfig", back_populates="character", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Character({self.name}, {self.gender.value}, {self.body_type.value})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender.value if self.gender else None,
            'body_type': self.body_type.value if self.body_type else None,
            'element': self.element.value if self.element else None,
            'weapon_type': self.weapon_type.value if self.weapon_type else None,
            'action_count': len(self.actions)
        }

# ==================== 动作数据表 ====================

class Action(Base):
    """动作数据 - 核心表"""
    __tablename__ = 'actions'
    
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False, index=True)
    
    # 基础信息
    action_name = Column(String(100), nullable=False)
    action_type = Column(Enum(ActionType))
    notes = Column(Text)  # 备注/技能说明
    
    # 帧数数据
    start_frame = Column(Integer)  # 发生帧
    duration_frame = Column(Integer)  # 持续帧
    self_hitstop = Column(Float)  # 顿帧-自
    enemy_hitstop = Column(Float)  # 顿帧-敌
    invincible_start = Column(Integer)  # 无敌启动帧
    invincible_duration = Column(Integer)  # 无敌持续帧
    priority_change = Column(Integer)  # 优先级改变
    derive_frame = Column(Integer)  # 派生帧
    derive_duration = Column(Integer)  # 派生持续帧
    end_frame = Column(Integer)  # 动作结束帧
    
    # 特性标记
    can_parry = Column(Boolean, default=False)  # 可弹刀
    can_detach = Column(Boolean, default=False)  # 可脱手
    
    # 战斗数值
    poise_damage = Column(Float)  # 削韧值
    concerto_recovery = Column(Float)  # 协奏回收
    core_recovery = Column(Float)  # 核心回收
    hit_resistance_factor = Column(Float)  # 受击韧性系数
    interrupt_priority = Column(Integer)  # 中断优先级
    
    # 状态
    position_state = Column(Enum(PositionState))  # 位置状态
    state_transition_time = Column(Integer)  # 状态转换时间
    
    # 时间膨胀
    time_dilation_type = Column(String(50))  # 时间膨胀类型
    self_dilation_factor = Column(Float)  # 膨胀系数-自
    self_dilation_start = Column(Integer)  # 膨胀发生-自
    self_dilation_duration = Column(Integer)  # 膨胀持续-自
    enemy_dilation_factor = Column(Float)  # 膨胀系数-敌
    enemy_dilation_start = Column(Integer)  # 膨胀发生-敌
    enemy_dilation_duration = Column(Integer)  # 膨胀持续-敌
    ally_dilation_factor = Column(Float)  # 膨胀系数-友
    ally_dilation_start = Column(Integer)  # 膨胀发生-友
    ally_dilation_duration = Column(Integer)  # 膨胀持续-友
    
    # 命中与判定
    hit_type = Column(String(50))  # 命中类型
    position_reference = Column(String(50))  # 位置基准
    follow_bone = Column(String(50))  # 跟随骨骼
    unfollow_frame = Column(Integer)  # 解除跟随帧
    scale_factor = Column(Float)  # 缩放倍数
    hit_range = Column(String(200))  # 判定范围描述
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    character = relationship("Character", back_populates="actions")
    
    def __repr__(self):
        return f"<Action({self.action_name}, {self.character.name if self.character else None})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'character_id': self.character_id,
            'character_name': self.character.name if self.character else None,
            'action_name': self.action_name,
            'action_type': self.action_type.value if self.action_type else None,
            'notes': self.notes,
            'start_frame': self.start_frame,
            'duration_frame': self.duration_frame,
            'self_hitstop': self.self_hitstop,
            'enemy_hitstop': self.enemy_hitstop,
            'invincible_start': self.invincible_start,
            'invincible_duration': self.invincible_duration,
            'can_parry': self.can_parry,
            'can_detach': self.can_detach,
            'poise_damage': self.poise_damage,
            'concerto_recovery': self.concerto_recovery,
            'position_state': self.position_state.value if self.position_state else None,
        }

# ==================== 声骸表 ====================

class Echo(Base):
    """声骸"""
    __tablename__ = 'echoes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, index=True)
    action_name = Column(String(100))  # 动作名称
    
    # 帧数
    start_frame = Column(Integer)
    duration_frame = Column(Integer)
    self_hitstop = Column(Float)
    enemy_hitstop = Column(Float)
    end_frame = Column(Integer)
    
    # 特性
    can_parry = Column(Boolean, default=False)
    can_detach = Column(Boolean, default=False)
    
    # 数值
    poise_damage = Column(Float)
    concerto_recovery = Column(Float)
    core_recovery = Column(Float)
    
    # 技能信息
    skill_type = Column(String(20))  # 召唤/变身等
    cooldown = Column(Integer)  # 冷却时间
    single_cooldown = Column(Float)  # 单段冷却
    continuation_limit = Column(Integer)  # 接续时限
    
    # 状态
    position_state = Column(Enum(PositionState))
    state_transition_time = Column(Integer)
    
    # 时间膨胀
    time_dilation_type = Column(String(50))
    self_dilation_factor = Column(Float)
    enemy_dilation_factor = Column(Float)
    
    # 描述
    description = Column(Text)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Echo({self.name})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'action_name': self.action_name,
            'skill_type': self.skill_type,
            'cooldown': self.cooldown,
            'poise_damage': self.poise_damage,
            'concerto_recovery': self.concerto_recovery,
            'description': self.description,
        }

# ==================== 伤害配置表 ====================

class DamageConfig(Base):
    """伤害配置"""
    __tablename__ = 'damage_configs'
    
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    
    # 基础配置
    level = Column(Integer, default=90)
    chain_level = Column(Integer, default=0)  # 共鸣链等级
    
    # 武器
    weapon_name = Column(String(100))
    weapon_level = Column(Integer)
    weapon_rank = Column(Integer)  # 武器阶级
    
    # 面板数值
    base_hp = Column(Integer)
    base_atk = Column(Integer)
    base_def = Column(Integer)
    crit_rate = Column(Float)
    crit_dmg = Column(Float)
    resonance_efficiency = Column(Float)
    
    # 加成
    normal_bonus = Column(Float, default=0)
    heavy_bonus = Column(Float, default=0)
    skill_bonus = Column(Float, default=0)
    ult_bonus = Column(Float, default=0)
    element_bonus = Column(Float, default=0)
    damage_bonus = Column(Float, default=0)
    
    # 偏谐
    concerto_efficiency = Column(Float, default=1.0)
    harmony_break_bonus = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    character = relationship("Character", back_populates="damage_configs")
    
    def __repr__(self):
        return f"<DamageConfig({self.character.name if self.character else None}, Lv.{self.level})>"

# ==================== 敌人属性表 ====================

class Enemy(Base):
    """敌人属性"""
    __tablename__ = 'enemies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    enemy_type = Column(String(20))  # 全息/深渊/普通
    level = Column(Integer)
    
    # 属性
    hp = Column(Integer)
    atk = Column(Integer)
    defense = Column(Integer)
    
    # 抗性
    glacio_res = Column(Float, default=0.2)
    fusion_res = Column(Float, default=0.2)
    electro_res = Column(Float, default=0.2)
    aero_res = Column(Float, default=0.2)
    spectro_res = Column(Float, default=0.2)
    havoc_res = Column(Float, default=0.2)
    physical_res = Column(Float, default=0.2)
    
    # 偏谐
    resonance = Column(Integer)
    concerto = Column(Integer)
    
    def __repr__(self):
        return f"<Enemy({self.name}, Lv.{self.level})>"

# ==================== 数据库初始化 ====================

def init_db(db_path='wuwa_data.db'):
    """初始化数据库"""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    """获取数据库会话"""
    Session = sessionmaker(bind=engine)
    return Session()
