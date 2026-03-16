"""
贴吧观察者数据模型
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON
from datetime import datetime
from .base import Base, TimestampMixin
import uuid


class TiebaDailyStats(Base, TimestampMixin):
    """贴吧每日统计"""
    __tablename__ = "tieba_daily_stats"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tieba_name = Column(String(100), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    post_count = Column(Integer, default=0, nullable=False)


class TiebaHotPost(Base, TimestampMixin):
    """热帖记录"""
    __tablename__ = "tieba_hot_posts"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tieba_name = Column(String(100), nullable=False, index=True)
    post_id = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    reply_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    post_url = Column(String(500))
    post_time = Column(DateTime, nullable=False)
    hot_date = Column(String(10), nullable=False, index=True)
    hot_type = Column(String(20), default='daily')


class DownloadRecord(Base, TimestampMixin):
    """下载记录"""
    __tablename__ = "download_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    download_type = Column(String(50), nullable=False)
    download_date = Column(String(10), nullable=False, index=True)
