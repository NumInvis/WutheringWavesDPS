"""
访问统计相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VisitStatBase(BaseModel):
    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    hour: int = Field(..., description="小时 (0-23)", ge=0, le=23)
    path: str = Field(default='/', description="访问路径")
    visit_count: int = Field(default=1, description="访问次数", ge=1)


class VisitStatCreate(VisitStatBase):
    pass


class VisitStatResponse(VisitStatBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
