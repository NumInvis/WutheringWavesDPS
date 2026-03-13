# -*- coding: utf-8 -*-
"""
叠层系统 - 处理特殊叠层效果
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class LayerEffect:
    """叠层效果定义"""
    target: str  # 目标属性: 'atk_zone', 'bonus_zone', 'crit_zone', 'amplify_zone', 'multiplier', 'panel_atk'
    type: str    # 效果类型: 'add', 'multiply'
    value: float # 每层数值


@dataclass
class LayerTemplate:
    """叠层模板"""
    name: str
    description: str
    max_layers: int
    effects: List[LayerEffect] = field(default_factory=list)
    
    def create_layer(self, character_name: str = "") -> 'SpecialLayer':
        """创建叠层实例"""
        return SpecialLayer(
            name=f"{character_name} - {self.name}" if character_name else self.name,
            template=self,
            max_layers=self.max_layers
        )


@dataclass
class SpecialLayer:
    """特殊叠层实例"""
    name: str
    template: Optional[LayerTemplate] = None
    current: int = 0
    max_layers: int = 10
    
    # 回调
    on_changed: Optional[Callable] = None
    
    def set_layers(self, value: int):
        """设置层数"""
        old_value = self.current
        self.current = max(0, min(value, self.max_layers))
        if old_value != self.current and self.on_changed:
            self.on_changed()
    
    def add_layers(self, delta: int = 1):
        """增加层数"""
        self.set_layers(self.current + delta)
    
    def remove_layers(self, delta: int = 1):
        """减少层数"""
        self.set_layers(self.current - delta)
    
    def get_effects(self) -> Dict[str, float]:
        """获取当前层数的效果"""
        effects = {}
        
        if self.template:
            for effect in self.template.effects:
                key = f"{effect.target}_{effect.type}"
                effects[key] = effects.get(key, 0) + effect.value * self.current
        
        return effects
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'current': self.current,
            'max_layers': self.max_layers
        }


class LayerSystem:
    """
    叠层系统管理器
    
    管理所有叠层模板和实例
    """
    
    # 预定义叠层模板
    TEMPLATES = {
        'augusta': LayerTemplate(
            name="奥古斯塔叠层",
            description="每层增加加成区",
            max_layers=10,
            effects=[
                LayerEffect('bonus_zone', 'multiply', 0.05)  # 每层+5%加成区
            ]
        ),
        'flolo': LayerTemplate(
            name="弗洛洛叠层",
            description="每层增加爆伤和特定技能倍率",
            max_layers=5,
            effects=[
                LayerEffect('crit_zone', 'multiply', 0.02),  # 每层+2%双爆区
                LayerEffect('multiplier', 'add', 50)  # 每层+50%倍率
            ]
        ),
        'sigilica': LayerTemplate(
            name="西格莉卡叠层",
            description="每层增加加深区",
            max_layers=10,
            effects=[
                LayerEffect('amplify_zone', 'add', 0.05)  # 每层+5%加深
            ]
        ),
        'custom': LayerTemplate(
            name="自定义叠层",
            description="可自由配置的叠层",
            max_layers=10,
            effects=[]
        )
    }
    
    @classmethod
    def get_template(cls, name: str) -> Optional[LayerTemplate]:
        """获取叠层模板"""
        return cls.TEMPLATES.get(name)
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, LayerTemplate]:
        """获取所有模板"""
        return cls.TEMPLATES.copy()
    
    @classmethod
    def create_layer(cls, template_name: str, character_name: str = "") -> Optional[SpecialLayer]:
        """创建叠层实例"""
        template = cls.get_template(template_name)
        if template:
            return template.create_layer(character_name)
        return None
