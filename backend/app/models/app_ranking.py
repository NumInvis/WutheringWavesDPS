"""
iOS应用排名数据模型
监控目标游戏在各地区的iOS畅销榜排名
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey

from app.models.base import Base


class AppInfo(Base):
    """游戏应用信息"""
    __tablename__ = "app_info"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    itunes_id = Column(String(50), unique=True, index=True)
    name_cn = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    app_id_cn = Column(String(50))
    app_id_jp = Column(String(50))
    app_id_us = Column(String(50))
    app_id_kr = Column(String(50))
    icon_url = Column(String(500))
    developer = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RankingRecord(Base):
    """排名记录"""
    __tablename__ = "ranking_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    app_id = Column(String(36), ForeignKey("app_info.id"), nullable=False, index=True)
    country = Column(String(10), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TopAppsCache(Base):
    """各地区TOP应用缓存"""
    __tablename__ = "top_apps_cache"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    country = Column(String(10), nullable=False, index=True)
    rank_data = Column(Text, nullable=False)
    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
