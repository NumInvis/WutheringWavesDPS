"""
访问统计模型
"""
from sqlalchemy import Column, String, Integer, DateTime
import uuid
from datetime import datetime
from .base import Base, TimestampMixin


class VisitStat(Base, TimestampMixin):
    """访问统计表"""
    __tablename__ = "visit_stats"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(String(10), nullable=False, index=True)
    hour = Column(Integer, nullable=False, index=True)
    path = Column(String(500), nullable=False, default='/')
    visit_count = Column(Integer, default=1, nullable=False)
