"""
表格模型
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin


class Spreadsheet(Base, TimestampMixin):
    """表格表"""
    __tablename__ = "spreadsheets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sheet_number = Column(Integer, unique=True, nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), index=True)
    tags = Column(Text)
    character_tags = Column(Text)
    area = Column(String(50), index=True)
    is_draft = Column(Boolean, default=False, index=True)
    is_banned = Column(Boolean, default=False, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    is_public = Column(Boolean, default=False, index=True)
    star_count = Column(Integer, default=0, index=True)
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    file_url = Column(String(500), nullable=False)
    file_size = Column(BigInteger)
    thumbnail_url = Column(String(500))
    extra_metadata = Column(Text)
    
    user = relationship("User", backref="spreadsheets")
