"""
Star相关的Pydantic模式
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StarBase(BaseModel):
    """Star基础模式"""
    pass


class StarCreate(StarBase):
    """Star创建模式"""
    spreadsheet_id: str


class StarResponse(StarBase):
    """Star响应模式"""
    id: str
    user_id: str
    spreadsheet_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
