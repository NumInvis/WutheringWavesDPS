# -*- coding: utf-8 -*-
"""
事件系统 - 实现实时计算更新
"""

from enum import Enum, auto
from typing import Callable, Dict, List, Any


class EventType(Enum):
    """事件类型"""
    SKILL_CHANGED = auto()      # 动作数据改变
    SKILL_ADDED = auto()        # 添加动作
    SKILL_REMOVED = auto()      # 删除动作
    LAYER_CHANGED = auto()      # 叠层改变
    ENV_CHANGED = auto()        # 环境改变
    CHAR_CHANGED = auto()       # 角色切换
    CALCULATION_NEEDED = auto() # 需要重新计算


class EventBus:
    """
    事件总线
    
    实现观察者模式，支持实时更新
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers: Dict[EventType, List[Callable]] = {}
            cls._instance._enabled = True
        return cls._instance
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """取消订阅"""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def emit(self, event_type: EventType, data: Any = None):
        """触发事件"""
        if not self._enabled:
            return
        
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"事件处理错误: {e}")
    
    def enable(self):
        """启用事件"""
        self._enabled = True
    
    def disable(self):
        """禁用事件"""
        self._enabled = False
    
    def clear(self):
        """清空所有订阅"""
        self._subscribers.clear()


# 全局事件总线
event_bus = EventBus()
