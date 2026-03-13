"""
核心DPS计算引擎 - 整合V1-V4版本的最优计算逻辑
提供完整的八大乘区计算、Excel解析、伤害计算功能
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import json


class Environment(Enum):
    """战斗环境枚举"""
    TOWER = "深塔"
    FIELD = "海墟"
    BOSS = "首领"


class DamageType(Enum):
    """伤害类型"""
    NORMAL = "a"
    RESONANCE = "r"
    ECHO = "e"
    LIBERATION = "q"
    FUSION = "z"


@dataclass
class Skill:
    """技能数据"""
    name: str
    multiplier: float
    skill_type: DamageType = DamageType.NORMAL
    count: int = 1
    panel_atk: Optional[float] = None
    atk_zone: Optional[float] = None
    bonus_zone: Optional[float] = None
    crit_zone: Optional[float] = None
    amplify_zone: Optional[float] = None
    defense_zone: Optional[float] = None
    resistance_zone: Optional[float] = None
    multiplier_boost: Optional[float] = None
    vulnerable_zone: Optional[float] = None
    independent_zone: Optional[float] = None
    final_damage: Optional[float] = None
    counter1: Optional[int] = None
    counter2: Optional[int] = None
    skill_def_ignore: Optional[float] = None
    skill_def_shred: Optional[float] = None
    skill_defense_zone: Optional[float] = None
    skill_enemy_level: Optional[int] = None


@dataclass
class Stats:
    """角色属性（整合V3-V4的完整属性系统）"""
    
    # 攻击区
    base_atk: float = 0.0
    inherent_weapon_atk: float = 0.0
    echo_main_sub_atk: float = 0.0
    fixed_atk: float = 0.0
    extra_fixed_atk: float = 0.0
    self_atk_buff: float = 0.0
    received_atk_buff: float = 0.0
    
    # 加成区
    echo_3c_count: int = 0
    echo_set_first: float = 0.0
    self_element_buff: float = 0.0
    received_element_buff: float = 0.0
    other_element_buff: float = 0.0
    main_type_bonus: float = 0.0
    
    # 暴击区
    base_crit_rate: float = 0.0
    base_crit_damage: float = 0.0
    weapon_crit_rate: float = 0.0
    weapon_crit_damage: float = 0.0
    set_crit_rate: float = 0.0
    set_crit_damage: float = 0.0
    echo_crit_rate: float = 0.0
    echo_crit_damage: float = 0.0
    chain_crit_rate: float = 0.0
    chain_crit_damage: float = 0.0
    teammate_crit_rate: float = 0.0
    teammate_crit_damage: float = 0.0
    panel_crit_rate: float = 0.0
    overflow_crit_rate: float = 0.0
    panel_crit_damage: float = 0.0
    
    # 加深区
    universal_amplify: float = 0.0
    main_type_amplify: float = 0.0
    
    # 副词条
    sub_atk_percent: float = 0.0
    sub_skill_bonus: float = 0.0
    sub_crit_rate: float = 0.0
    sub_crit_damage: float = 0.0
    
    # 环境
    environment: Environment = Environment.TOWER
    character_level: int = 90
    enemy_level: int = 100
    def_ignore: float = 0.0
    def_shred: float = 0.0
    res_shred: float = 0.0
    
    def calculate_panel_atk(self) -> float:
        """计算面板攻击"""
        return (self.base_atk + self.inherent_weapon_atk + 
                self.echo_main_sub_atk + self.fixed_atk + 
                self.extra_fixed_atk)
    
    def calculate_atk_zone(self) -> float:
        """计算攻击区"""
        panel = self.calculate_panel_atk()
        return panel * (1 + self.self_atk_buff + self.received_atk_buff)
    
    def calculate_crit_rate(self) -> float:
        """计算暴击率"""
        total = (self.base_crit_rate + self.weapon_crit_rate + 
                 self.set_crit_rate + self.echo_crit_rate + 
                 self.chain_crit_rate + self.teammate_crit_rate + 
                 self.panel_crit_rate)
        return min(max(total, 0.0), 1.0)
    
    def calculate_crit_damage(self) -> float:
        """计算暴击伤害"""
        return (self.base_crit_damage + self.weapon_crit_damage + 
                self.set_crit_damage + self.echo_crit_damage + 
                self.chain_crit_damage + self.teammate_crit_damage + 
                self.panel_crit_damage)
    
    def calculate_crit_zone(self) -> float:
        """计算双爆区"""
        crit_rate = self.calculate_crit_rate()
        crit_dmg = self.calculate_crit_damage()
        return 1 + crit_rate * crit_dmg
    
    def calculate_bonus_zone(self) -> float:
        """计算加成区"""
        return (1 + self.echo_set_first + self.self_element_buff + 
                self.received_element_buff + self.other_element_buff + 
                self.main_type_bonus)
    
    def calculate_amplify_zone(self) -> float:
        """计算加深区"""
        return 1 + self.universal_amplify + self.main_type_amplify


@dataclass
class Character:
    """角色类 - 整合所有版本的最优特性"""
    name: str
    position: int = 1
    stats: Stats = field(default_factory=Stats)
    skills: List[Skill] = field(default_factory=list)
    environment: Environment = Environment.TOWER
    rotation_time: float = 25.0
    
    def calculate_defense_zone(self, char_level: int = None, 
                               enemy_level: int = None,
                               def_ignore: float = None,
                               def_shred: float = None) -> float:
        """
        计算防御区 - V2版本的精确公式
        
        Args:
            char_level: 角色等级（默认使用stats中的值）
            enemy_level: 敌人等级（默认使用stats中的值）
            def_ignore: 无视防御（默认使用stats中的值）
            def_shred: 减防（默认使用stats中的值）
        
        Returns:
            防御区乘数值
        """
        cl = char_level or self.stats.character_level
        el = enemy_level or self.stats.enemy_level
        di = def_ignore or self.stats.def_ignore
        ds = def_shred or self.stats.def_shred
        
        enemy_def = 800 + 10 * el
        effective_def = enemy_def * (1 - di) * (1 - ds)
        def_factor = (cl + 100) / (cl + 100 + effective_def)
        
        return max(def_factor, 0.1)
    
    def calculate_resistance_zone(self, base_res: float = 0.2,
                                   res_shred: float = None,
                                   env: Environment = None) -> float:
        """
        计算抗性区 - V2版本的精确公式
        
        Args:
            base_res: 基础抗性（默认0.2）
            res_shred: 减抗（默认使用stats中的值）
            env: 环境（默认使用当前环境）
        
        Returns:
            抗性区乘数值
        """
        rs = res_shred or self.stats.res_shred
        current_env = env or self.environment
        
        effective_res = base_res - rs
        
        if current_env == Environment.TOWER:
            effective_res -= 0.1
        
        if effective_res < 0:
            return 1 - effective_res / 2
        elif effective_res < 0.75:
            return 1 - effective_res
        else:
            return 1 / (1 + 4 * effective_res)
    
    def calculate_skill_damage(self, skill: Skill) -> float:
        """
        计算单个技能伤害 - 完整八大乘区
        
        Args:
            skill: 技能对象
        
        Returns:
            技能总伤害
        """
        atk_zone = self.stats.calculate_atk_zone()
        bonus_zone = self.stats.calculate_bonus_zone()
        crit_zone = self.stats.calculate_crit_zone()
        amplify_zone = self.stats.calculate_amplify_zone()
        defense_zone = self.calculate_defense_zone()
        resistance_zone = self.calculate_resistance_zone()
        
        base_damage = atk_zone * skill.multiplier
        total_damage = (base_damage * bonus_zone * crit_zone * 
                       amplify_zone * defense_zone * resistance_zone)
        
        if skill.multiplier_boost:
            total_damage *= (1 + skill.multiplier_boost)
        if skill.vulnerable_zone:
            total_damage *= skill.vulnerable_zone
        if skill.independent_zone:
            total_damage += skill.independent_zone
        
        return total_damage * skill.count
    
    def calculate_all_skills(self):
        """计算所有技能的伤害"""
        for skill in self.skills:
            skill.panel_atk = self.stats.calculate_panel_atk()
            skill.atk_zone = self.stats.calculate_atk_zone()
            skill.bonus_zone = self.stats.calculate_bonus_zone()
            skill.crit_zone = self.stats.calculate_crit_zone()
            skill.amplify_zone = self.stats.calculate_amplify_zone()
            skill.defense_zone = self.calculate_defense_zone()
            skill.resistance_zone = self.calculate_resistance_zone()
            skill.final_damage = self.calculate_skill_damage(skill)
    
    def get_total_damage(self) -> float:
        """获取总伤害"""
        return sum(skill.final_damage or 0 for skill in self.skills)
    
    def get_dps(self) -> float:
        """获取DPS"""
        total_damage = self.get_total_damage()
        return total_damage / self.rotation_time if self.rotation_time > 0 else 0
    
    def get_optimization_suggestions(self) -> List[Dict]:
        """
        获取优化建议 - 来自V1版本的智能建议
        
        Returns:
            优化建议列表
        """
        suggestions = []
        
        crit_rate = self.stats.calculate_crit_rate()
        panel_atk = self.stats.calculate_panel_atk()
        
        if crit_rate < 0.7:
            suggestions.append({
                "type": "crit_rate",
                "message": f"暴击率偏低 ({crit_rate:.1%})，建议提升至70%+",
                "priority": "high"
            })
        
        if panel_atk < 2000:
            suggestions.append({
                "type": "atk",
                "message": f"面板攻击偏低 ({panel_atk:.0f})",
                "priority": "medium"
            })
        
        return suggestions
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "name": self.name,
            "position": self.position,
            "environment": self.environment.value,
            "rotation_time": self.rotation_time,
            "stats": {
                "panel_atk": self.stats.calculate_panel_atk(),
                "atk_zone": self.stats.calculate_atk_zone(),
                "crit_rate": self.stats.calculate_crit_rate(),
                "crit_damage": self.stats.calculate_crit_damage(),
                "crit_zone": self.stats.calculate_crit_zone(),
                "bonus_zone": self.stats.calculate_bonus_zone(),
                "amplify_zone": self.stats.calculate_amplify_zone(),
            },
            "skills": [
                {
                    "name": s.name,
                    "type": s.skill_type.value,
                    "multiplier": s.multiplier,
                    "count": s.count,
                    "final_damage": s.final_damage
                }
                for s in self.skills
            ],
            "total_damage": self.get_total_damage(),
            "dps": self.get_dps(),
            "suggestions": self.get_optimization_suggestions()
        }


@dataclass
class Team:
    """队伍类"""
    name: str
    characters: List[Character] = field(default_factory=list)
    rotation_time: float = 25.0
    
    def add_character(self, character: Character):
        """添加角色到队伍"""
        character.rotation_time = self.rotation_time
        self.characters.append(character)
    
    def get_team_dps(self) -> float:
        """获取队伍总DPS"""
        return sum(char.get_dps() for char in self.characters)
    
    def get_total_damage(self) -> float:
        """获取队伍总伤害"""
        return sum(char.get_total_damage() for char in self.characters)
    
    def compare_with(self, other_team: 'Team') -> Dict:
        """与另一支队伍对比"""
        dps1 = self.get_team_dps()
        dps2 = other_team.get_team_dps()
        
        return {
            "self_name": self.name,
            "other_name": other_team.name,
            "self_dps": dps1,
            "other_dps": dps2,
            "difference": dps1 - dps2,
            "percent_diff": ((dps1 - dps2) / dps2 * 100) if dps2 > 0 else 0,
            "winner": self.name if dps1 > dps2 else other_team.name
        }
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "name": self.name,
            "characters": [c.to_dict() for c in self.characters],
            "rotation_time": self.rotation_time,
            "total_damage": self.get_total_damage(),
            "team_dps": self.get_team_dps()
        }


class DPSCalculator:
    """
    DPS计算器主引擎 - 整合所有版本的最优功能
    
    功能特性：
    - V1: 基础DPS计算、队伍对比、排名
    - V2: 完整乘区计算、环境参数
    - V3/V4: 拉表模板解析、技能级精度
    """
    
    def __init__(self):
        self.characters: Dict[str, Character] = {}
        self.teams: Dict[str, Team] = {}
    
    def add_character(self, character: Character, key: str = None) -> str:
        """添加角色"""
        char_key = key or f"{character.name}_{len(self.characters)}"
        self.characters[char_key] = character
        return char_key
    
    def create_team(self, name: str, char_keys: List[str], 
                   rotation_time: float = 25.0) -> Team:
        """创建队伍"""
        team = Team(name=name, rotation_time=rotation_time)
        
        for key in char_keys:
            if key in self.characters:
                team.add_character(self.characters[key])
            else:
                matches = [k for k in self.characters.keys() if key in k]
                if matches:
                    team.add_character(self.characters[matches[0]])
        
        self.teams[name] = team
        return team
    
    def get_character_ranking(self) -> List[Tuple[str, float]]:
        """获取角色DPS排名"""
        rankings = [(k, v.get_dps()) for k, v in self.characters.items()]
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings
    
    def get_team_ranking(self) -> List[Tuple[str, float]]:
        """获取队伍DPS排名"""
        rankings = [(k, v.get_team_dps()) for k, v in self.teams.items()]
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings
    
    def compare_teams(self, team1_name: str, team2_name: str) -> Optional[Dict]:
        """对比两支队伍"""
        if team1_name in self.teams and team2_name in self.teams:
            return self.teams[team1_name].compare_with(self.teams[team2_name])
        return None
    
    def generate_report(self) -> str:
        """生成完整报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("鸣潮DPS计算报告 - 整合优化版")
        lines.append("=" * 80)
        
        lines.append(f"\n【角色统计】共 {len(self.characters)} 个角色")
        lines.append("-" * 80)
        
        char_ranking = self.get_character_ranking()[:10]
        for i, (key, dps) in enumerate(char_ranking, 1):
            lines.append(f"{i:2d}. {key:40s} {dps:>12,.2f} DPS")
        
        if self.teams:
            lines.append(f"\n【队伍统计】共 {len(self.teams)} 支队伍")
            lines.append("-" * 80)
            
            team_ranking = self.get_team_ranking()
            for i, (name, dps) in enumerate(team_ranking, 1):
                team = self.teams[name]
                char_names = ", ".join([c.name for c in team.characters])
                lines.append(f"{i:2d}. {name:20s} ({char_names:30s}) {dps:>12,.2f} DPS")
        
        return "\n".join(lines)
    
    def export_to_json(self) -> Dict:
        """导出所有数据到JSON"""
        return {
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "teams": {k: v.to_dict() for k, v in self.teams.items()},
            "character_ranking": self.get_character_ranking(),
            "team_ranking": self.get_team_ranking()
        }
