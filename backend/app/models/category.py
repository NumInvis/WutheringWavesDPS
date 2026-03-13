"""
分类模型
"""
from sqlalchemy import Column, String, Text, Integer, Boolean
from sqlalchemy import Sequence
from .base import Base


class Category(Base):
    """分类表"""
    __tablename__ = "categories"
    
    id = Column(Integer, Sequence("category_id_seq"), primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String(100))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
