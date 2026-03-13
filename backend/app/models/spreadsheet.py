"""
表格模型
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin


class Spreadsheet(Base, TimestampMixin):
    """表格表"""
    __tablename__ = "spreadsheets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), index=True)
    tags = Column(ARRAY(Text))
    character_tags = Column(ARRAY(Text))
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
    metadata = Column(JSONB)
    
    user = relationship("User", backref="spreadsheets")
