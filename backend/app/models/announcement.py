"""
公告模型
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime
import uuid
from datetime import datetime
from .base import Base, TimestampMixin


class Announcement(Base, TimestampMixin):
    """公告表"""
    __tablename__ = "announcements"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)
