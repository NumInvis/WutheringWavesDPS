# -*- coding: utf-8 -*-
"""
数据模型定义
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum
import copy


class SkillType(Enum):
    """动作类型"""
    NORMAL = "a"      # 普攻
    SKILL = "e"       # 技能
    ULTIMATE = "q"    # 大招
    VARIATION = "bz"  # 变奏
    ECHO = "s"        # 声骸
    OTHER = "other"


@dataclass
class Skill:
    """
    动作/技能数据
    
    支持实时计算和叠层联动
    """
    # 基础信息
    name: str = "新动作"
    skill_type: str = "a"
    count: int = 1
    
    # 输入值（用户编辑）
    multiplier_input: float = 0  # 倍率输入值(%)
    panel_atk_input: float = 0   # 面板攻击输入值
    
    # 乘区（基础值）
    atk_zone: float = 1.0        # 攻击区
    bonus_zone: float = 1.0      # 加成区
    crit_zone: float = 1.0       # 双爆区
    amplify_zone: float = 0      # 加深区（0表示无加深）
    defense_zone: float = 0.5    # 防御区
    resistance_zone: float = 0.8 # 抗性区
    
    # 特殊乘区
    multiplier_boost: float = 0  # 倍率提升
    vulnerable_zone: float = 0   # 易伤区
    independent_zone: float = 1.0 # 独立乘区
    
    # 叠层影响（由LayerSystem填充）
    layer_effects: Dict[str, float] = field(default_factory=dict)
    
    # 计算结果
    _multiplier: float = 0       # 实际倍率（含叠层影响）
    _panel_atk: float = 0        # 实际面板攻击
    damage: float = 0            # 单次伤害
    total_damage: float = 0      # 总伤害
    
    # 其他
    echo: int = 0                # 余响
    overflow: int = 0            # 溢出
    note: str = ""               # 备注
    
    def __post_init__(self):
        self._update_calculated_values()
    
    def _update_calculated_values(self):
        """更新计算值（应用叠层效果）"""
        # 应用叠层到倍率
        self._multiplier = self.multiplier_input
        if 'multiplier_add' in self.layer_effects:
            self._multiplier += self.layer_effects['multiplier_add']
        if 'multiplier_multiply' in self.layer_effects:
            self._multiplier *= (1 + self.layer_effects['multiplier_multiply'])
        
        # 应用叠层到面板攻击
        self._panel_atk = self.panel_atk_input
        if 'panel_atk_add' in self.layer_effects:
            self._panel_atk += self.layer_effects['panel_atk_add']
        if 'panel_atk_multiply' in self.layer_effects:
            self._panel_atk *= (1 + self.layer_effects['panel_atk_multiply'])
    
    def calculate(self) -> float:
        """
        计算伤害
        
        公式: 面板攻击 × 倍率 × 攻击区 × 加成区 × 双爆区 × (1+加深区) × 防御区 × 抗性区 × (1+倍率提升) × (1+易伤区) × 独立乘区
        """
        self._update_calculated_values()
        
        # 应用叠层到各乘区
        atk_zone = self.atk_zone * (1 + self.layer_effects.get('atk_zone', 0))
        bonus_zone = self.bonus_zone * (1 + self.layer_effects.get('bonus_zone', 0))
        crit_zone = self.crit_zone * (1 + self.layer_effects.get('crit_zone', 0))
        amplify_zone = self.amplify_zone + self.layer_effects.get('amplify_zone', 0)
        
        self.damage = (
            self._panel_atk *
            (self._multiplier / 100) *
            atk_zone *
            bonus_zone *
            crit_zone *
            (1 + amplify_zone) *
            self.defense_zone *
            self.resistance_zone *
            (1 + self.multiplier_boost) *
            (1 + self.vulnerable_zone) *
            self.independent_zone
        )
        
        self.total_damage = self.damage * self.count
        return self.damage
    
    def clone(self) -> 'Skill':
        """克隆动作"""
        return copy.deepcopy(self)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'skill_type': self.skill_type,
            'count': self.count,
            'multiplier_input': self.multiplier_input,
            'panel_atk_input': self.panel_atk_input,
            'atk_zone': self.atk_zone,
            'bonus_zone': self.bonus_zone,
            'crit_zone': self.crit_zone,
            'amplify_zone': self.amplify_zone,
            'defense_zone': self.defense_zone,
            'resistance_zone': self.resistance_zone,
            'multiplier_boost': self.multiplier_boost,
            'vulnerable_zone': self.vulnerable_zone,
            'independent_zone': self.independent_zone,
            'echo': self.echo,
            'overflow': self.overflow,
            'note': self.note
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Skill':
        """从字典创建"""
        return cls(**data)


@dataclass
class SpecialLayer:
    """
    特殊叠层
    
    例如：奥古斯塔叠层、弗洛洛叠层、西格莉卡叠层
    """
    name: str = "叠层"           # 叠层名称
    current: int = 0             # 当前层数
    max_layers: int = 10         # 最大层数
    
    # 每层效果
    per_layer_atk_zone: float = 0
    per_layer_bonus_zone: float = 0
    per_layer_crit_zone: float = 0
    per_layer_amplify_zone: float = 0
    per_layer_multiplier: float = 0  # 每层增加的倍率
    per_layer_crit_dmg: float = 0    # 每层增加的爆伤
    
    def get_effects(self) -> Dict[str, float]:
        """获取当前层数的效果"""
        return {
            'atk_zone': self.per_layer_atk_zone * self.current,
            'bonus_zone': self.per_layer_bonus_zone * self.current,
            'crit_zone': self.per_layer_crit_zone * self.current,
            'amplify_zone': self.per_layer_amplify_zone * self.current,
            'multiplier_add': self.per_layer_multiplier * self.current,
            'crit_dmg_add': self.per_layer_crit_dmg * self.current
        }


@dataclass
class CharacterStats:
    """
    角色属性面板
    
    完整的攻击/加成/暴击/爆伤/加深/副词条区域
    """
    # 角色主类型
    main_type: str = "e"  # e/q/a等
    cost_3c_count: int = 2  # 3C属伤数
    
    # 攻击区
    base_atk: float = 1024  # 白值
    weapon_atk_percent: float = 24.0  # 固有武器%
    echo_atk_percent: float = 61.8  # 主副词条%
    self_atk_buff: float = 0  # 自拐攻击%
    received_atk_buff: float = 61.5  # 被拐攻击%
    fixed_atk: float = 350  # 声骸固定攻击
    extra_fixed_atk: float = 0  # 额外固定攻击
    
    # 加成区
    echo_3c_bonus: float = 60.0  # 3C声骸%
    set_first_bonus: float = 22.0  # 套装首位%
    self_element_buff: float = 0  # 自拐属伤%
    received_element_buff: float = 12.0  # 被拐属伤%
    other_element_buff: float = 0  # 其他属伤%
    e_bonus: float = 49.0  # e加成%
    q_bonus: float = 55.0  # q加成%
    
    # 暴击区
    base_crit_rate: float = 13.0  # 基础与固有%
    weapon_crit_rate: float = 24.3  # 武器%
    set_crit_rate: float = 20.0  # 套装%
    echo_crit_rate: float = 40.5  # 主副词条%
    chain_crit_rate: float = 0  # 共鸣链%
    teammate_crit_rate: float = 12.5  # 队友%
    
    # 爆伤区
    base_crit_dmg: float = 150.0  # 基础与固有%
    weapon_crit_dmg: float = 0  # 武器%
    set_crit_dmg: float = 0  # 套装%
    echo_crit_dmg: float = 125.0  # 主副词条%
    chain_crit_dmg: float = 0  # 共鸣链%
    teammate_crit_dmg: float = 25.0  # 队友%
    
    # 加深区
    universal_amplify: float = 35.0  # 全加深%
    e_amplify: float = 25.0  # e加深%
    q_amplify: float = 32.0  # q加深%
    
    # 副词条
    atk_substat: float = 25.8  # 大攻击%
    skill_dmg_substat: float = 17.2  # 共技伤害%
    crit_rate_substat: float = 40.5  # 暴击%
    crit_dmg_substat: float = 81.0  # 爆伤%
    
    def get_panel_atk(self) -> float:
        """计算面板攻击"""
        base = self.base_atk
        multiplier = 1 + (self.weapon_atk_percent + self.echo_atk_percent + 
                         self.self_atk_buff + self.received_atk_buff) / 100
        fixed = self.fixed_atk + self.extra_fixed_atk
        return base * multiplier + fixed
    
    def get_atk_zone(self) -> float:
        """计算攻击区"""
        return 1 + (self.self_atk_buff + self.received_atk_buff) / 100
    
    def get_bonus_zone(self, skill_type: str = "e") -> float:
        """计算加成区"""
        bonus = (self.echo_3c_bonus + self.set_first_bonus + 
                self.self_element_buff + self.received_element_buff + 
                self.other_element_buff) / 100
        
        # 根据技能类型添加对应加成
        if skill_type == "e":
            bonus += self.e_bonus / 100
        elif skill_type == "q":
            bonus += self.q_bonus / 100
        
        return 1 + bonus
    
    def get_crit_rate(self) -> float:
        """计算暴击率"""
        crit = (self.base_crit_rate + self.weapon_crit_rate + self.set_crit_rate +
               self.echo_crit_rate + self.chain_crit_rate + self.teammate_crit_rate) / 100
        return min(crit, 1.0)  # 最高100%
    
    def get_crit_dmg(self) -> float:
        """计算爆伤"""
        return (self.base_crit_dmg + self.weapon_crit_dmg + self.set_crit_dmg +
               self.echo_crit_dmg + self.chain_crit_dmg + self.teammate_crit_dmg) / 100
    
    def get_crit_zone(self) -> float:
        """计算双爆区"""
        crit_rate = self.get_crit_rate()
        crit_dmg = self.get_crit_dmg()
        return 1 + crit_rate * (crit_dmg - 1)
    
    def get_amplify_zone(self, skill_type: str = "e") -> float:
        """计算加深区"""
        amplify = self.universal_amplify / 100
        if skill_type == "e":
            amplify += self.e_amplify / 100
        elif skill_type == "q":
            amplify += self.q_amplify / 100
        return amplify


@dataclass
class Character:
    """
    角色
    
    包含动作列表、属性面板和特殊叠层
    """
    name: str = "新角色"
    stats: CharacterStats = field(default_factory=CharacterStats)
    skills: List[Skill] = field(default_factory=list)
    special_layers: List[SpecialLayer] = field(default_factory=list)
    
    # 回调函数
    on_skill_changed: Optional[Callable] = None
    
    def add_skill(self, skill: Skill = None, index: int = None) -> Skill:
        """添加动作"""
        if skill is None:
            skill = Skill(name=f"动作{len(self.skills) + 1}")
        
        if index is None:
            self.skills.append(skill)
        else:
            self.skills.insert(index, skill)
        
        self._notify_change()
        return skill
    
    def remove_skills(self, indices: List[int]):
        """批量删除动作"""
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.skills):
                del self.skills[idx]
        self._notify_change()
    
    def clone_skills(self, indices: List[int]) -> List[Skill]:
        """批量克隆动作"""
        return [self.skills[idx].clone() for idx in indices if 0 <= idx < len(self.skills)]
    
    def paste_skills(self, skills: List[Skill], index: int = None):
        """粘贴动作"""
        if index is None:
            self.skills.extend(skills)
        else:
            for i, skill in enumerate(skills):
                self.skills.insert(index + i, skill)
        self._notify_change()
    
    def get_total_damage(self) -> float:
        """获取角色总伤害"""
        return sum(s.total_damage for s in self.skills)
    
    def calculate_all(self):
        """计算所有动作"""
        # 获取叠层效果
        layer_effects = {}
        for layer in self.special_layers:
            effects = layer.get_effects()
            for key, value in effects.items():
                layer_effects[key] = layer_effects.get(key, 0) + value
        
        # 应用到所有动作并计算
        for skill in self.skills:
            skill.layer_effects = layer_effects
            skill.calculate()
    
    def _notify_change(self):
        """通知变更"""
        if self.on_skill_changed:
            self.on_skill_changed()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'skills': [s.to_dict() for s in self.skills],
            'special_layers': [
                {
                    'name': l.name,
                    'current': l.current,
                    'max_layers': l.max_layers,
                    'per_layer_atk_zone': l.per_layer_atk_zone,
                    'per_layer_bonus_zone': l.per_layer_bonus_zone,
                    'per_layer_crit_zone': l.per_layer_crit_zone,
                    'per_layer_amplify_zone': l.per_layer_amplify_zone,
                    'per_layer_multiplier': l.per_layer_multiplier,
                    'per_layer_crit_dmg': l.per_layer_crit_dmg
                }
                for l in self.special_layers
            ]
        }


@dataclass
class Environment:
    """环境设置"""
    name: str = "默认环境"
    enemy_level: int = 100
    resistance_zone: float = 0.8
    
    def get_defense_zone(self, def_shred: float = 0, def_ignore: float = 0) -> float:
        """
        计算防御区
        
        公式: 1520 / (1520 + (792 + 8*怪物等级) * (1-减防%) * (1-无视防御%))
        """
        numerator = 1520
        denominator = 1520 + (792 + 8 * self.enemy_level) * (1 - def_shred) * (1 - def_ignore)
        return numerator / denominator


@dataclass
class Team:
    """队伍"""
    name: str = ""
    characters: List[Character] = field(default_factory=list)
    environment: Environment = field(default_factory=Environment)
    time_seconds: float = 25.0
    
    def add_character(self, char: Character = None) -> Character:
        """添加角色"""
        if char is None:
            char = Character(name=f"角色{len(self.characters) + 1}")
        self.characters.append(char)
        return char
    
    def remove_character(self, index: int):
        """删除角色"""
        if 0 <= index < len(self.characters):
            del self.characters[index]
    
    def calculate_all(self):
        """计算整个队伍"""
        for char in self.characters:
            char.calculate_all()
    
    def get_team_damage(self) -> float:
        """获取队伍总伤害"""
        return sum(c.get_total_damage() for c in self.characters)
    
    def get_team_dps(self) -> float:
        """获取队伍DPS"""
        return self.get_team_damage() / self.time_seconds if self.time_seconds > 0 else 0
