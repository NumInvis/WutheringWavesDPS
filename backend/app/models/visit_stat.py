"""
访问统计模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Text
import uuid
from datetime import datetime
from .base import Base, TimestampMixin


class VisitStat(Base, TimestampMixin):
    """访问统计表 - 按日期和小时统计PV"""
    __tablename__ = "visit_stats"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(String(10), nullable=False, index=True)
    hour = Column(Integer, nullable=False, index=True)
    path = Column(String(500), nullable=False, default='/')
    visit_count = Column(Integer, default=1, nullable=False)


class DailyVisitStat(Base, TimestampMixin):
    """每日访问统计表 - 统计PV和UV"""
    __tablename__ = "daily_visit_stats"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(String(10), nullable=False, unique=True, index=True)
    pv = Column(Integer, default=0, nullable=False)
    uv = Column(Integer, default=0, nullable=False)


class VisitorRecord(Base, TimestampMixin):
    """访客记录表 - 用于UV统计"""
    __tablename__ = "visitor_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(String(10), nullable=False, index=True)
    visitor_hash = Column(String(64), nullable=False, index=True)
