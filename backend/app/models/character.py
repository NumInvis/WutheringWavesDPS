"""
角色模型
"""
from sqlalchemy import Column, String
import uuid
from .base import Base, TimestampMixin


class Character(Base, TimestampMixin):
    """角色表"""
    __tablename__ = "characters"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    image = Column(String(500))
