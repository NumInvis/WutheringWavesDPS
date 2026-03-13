# -*- coding: utf-8 -*-
"""
计算引擎 - 实时计算伤害
"""

from typing import List, Dict, Optional
from .models import Skill, Character, Team, Environment
from .events import EventBus, EventType


class DamageCalculator:
    """
    伤害计算器
    
    提供实时计算功能，支持批量计算
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self._calculation_count = 0
        
        # 订阅计算事件
        if self.event_bus:
            self.event_bus.subscribe(EventType.CALCULATION_NEEDED, self._on_calculation_needed)
    
    def _on_calculation_needed(self, data=None):
        """收到计算请求"""
        if isinstance(data, Character):
            self.calculate_character(data)
        elif isinstance(data, Team):
            self.calculate_team(data)
    
    def calculate_skill(self, skill: Skill, environment: Environment = None) -> float:
        """
        计算单个动作伤害
        
        Args:
            skill: 动作数据
            environment: 环境设置（用于防御区计算）
        
        Returns:
            单次伤害值
        """
        # 如果环境存在，使用环境的防御区计算
        if environment:
            # 这里可以添加从环境获取防御区的逻辑
            pass
        
        return skill.calculate()
    
    def calculate_character(self, character: Character, environment: Environment = None) -> Dict:
        """
        计算角色所有动作
        
        Args:
            character: 角色数据
            environment: 环境设置
        
        Returns:
            计算结果字典
        """
        character.calculate_all()
        
        self._calculation_count += 1
        
        return {
            'character': character.name,
            'skill_count': len(character.skills),
            'total_damage': character.get_total_damage(),
            'skills': [
                {
                    'name': s.name,
                    'damage': s.damage,
                    'total_damage': s.total_damage
                }
                for s in character.skills
            ]
        }
    
    def calculate_team(self, team: Team) -> Dict:
        """
        计算整个队伍
        
        Args:
            team: 队伍数据
        
        Returns:
            计算结果字典
        """
        team.calculate_all()
        
        character_results = []
        for char in team.characters:
            result = self.calculate_character(char, team.environment)
            character_results.append(result)
        
        return {
            'team': team.name,
            'character_count': len(team.characters),
            'total_damage': team.get_team_damage(),
            'dps': team.get_team_dps(),
            'time_seconds': team.time_seconds,
            'characters': character_results
        }
    
    def get_calculation_count(self) -> int:
        """获取计算次数统计"""
        return self._calculation_count
    
    def batch_calculate(self, characters: List[Character], environment: Environment = None) -> List[Dict]:
        """批量计算多个角色"""
        return [self.calculate_character(char, environment) for char in characters]
