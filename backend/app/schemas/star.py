"""
Star评分相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class StarBase(BaseModel):
    """Star基础模式"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class StarCreate(StarBase):
    """Star创建模式"""
    spreadsheet_id: UUID


class StarUpdate(BaseModel):
    """Star更新模式"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class StarResponse(StarBase):
    """Star响应模式"""
    id: UUID
    user_id: UUID
    spreadsheet_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
