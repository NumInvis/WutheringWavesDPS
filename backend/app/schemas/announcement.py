"""
公告相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AnnouncementBase(BaseModel):
    title: str = Field(..., description="公告标题", max_length=200)
    content: str = Field(..., description="公告内容")
    is_active: bool = Field(default=True, description="是否激活")
    is_pinned: bool = Field(default=False, description="是否置顶")


class AnnouncementCreate(AnnouncementBase):
    pass


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(None, description="公告标题", max_length=200)
    content: Optional[str] = Field(None, description="公告内容")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_pinned: Optional[bool] = Field(None, description="是否置顶")


class AnnouncementResponse(AnnouncementBase):
    id: str
    published_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
