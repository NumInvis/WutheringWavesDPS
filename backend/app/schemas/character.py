"""
角色相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CharacterBase(BaseModel):
    """角色基础模式"""
    name: str = Field(..., min_length=1, max_length=100)
    image: Optional[str] = None


class CharacterCreate(CharacterBase):
    """角色创建模式"""
    pass


class CharacterUpdate(BaseModel):
    """角色更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    image: Optional[str] = None


class CharacterResponse(CharacterBase):
    """角色响应模式"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
