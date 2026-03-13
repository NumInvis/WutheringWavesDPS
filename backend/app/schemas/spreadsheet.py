"""
表格相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class SpreadsheetBase(BaseModel):
    """表格基础模式"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    character_tags: Optional[List[str]] = None
    area: Optional[str] = Field(None, pattern="^(pull_table|other)$")
    is_public: bool = False
    is_draft: bool = False
    metadata: Optional[Dict[str, Any]] = None


class SpreadsheetCreate(SpreadsheetBase):
    """表格创建模式"""
    file_url: str = Field(..., min_length=1, max_length=500)
    file_size: Optional[int] = None
    thumbnail_url: Optional[str] = None


class SpreadsheetUpdate(BaseModel):
    """表格更新模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    character_tags: Optional[List[str]] = None
    area: Optional[str] = Field(None, pattern="^(pull_table|other)$")
    is_public: Optional[bool] = None
    is_draft: Optional[bool] = None
    thumbnail_url: Optional[str] = None


class SpreadsheetAdminUpdate(BaseModel):
    """管理员表格更新模式"""
    is_banned: Optional[bool] = None
    is_featured: Optional[bool] = None


class SpreadsheetResponse(SpreadsheetBase):
    """表格响应模式"""
    id: UUID
    user_id: UUID
    owner_username: Optional[str] = None
    owner_display_name: Optional[str] = None
    is_banned: bool
    is_featured: bool
    star_count: int
    view_count: int
    download_count: int
    file_url: str
    file_size: Optional[int] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SpreadsheetListResponse(BaseModel):
    """表格列表响应模式"""
    items: List[SpreadsheetResponse]
    total: int
    page: int
    page_size: int
