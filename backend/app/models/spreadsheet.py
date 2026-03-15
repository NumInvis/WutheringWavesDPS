"""
表格模型
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .base import Base, TimestampMixin


class Spreadsheet(Base, TimestampMixin):
    """表格表"""
    __tablename__ = "spreadsheets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sheet_number = Column(Integer, unique=True, nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(50), index=True)
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
    
    # 软删除字段
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    user = relationship("User", backref="spreadsheets")
    tags = relationship("SpreadsheetTag", back_populates="spreadsheet", cascade="all, delete-orphan")
    character_tags = relationship("SpreadsheetCharacterTag", back_populates="spreadsheet", cascade="all, delete-orphan")
    
    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """恢复软删除"""
        self.is_deleted = False
        self.deleted_at = None


class SpreadsheetTag(Base):
    """表格标签关联表"""
    __tablename__ = "spreadsheet_tags"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    spreadsheet_id = Column(String(36), ForeignKey("spreadsheets.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_name = Column(String(50), nullable=False, index=True)
    
    spreadsheet = relationship("Spreadsheet", back_populates="tags")


class SpreadsheetCharacterTag(Base):
    """表格角色标签关联表"""
    __tablename__ = "spreadsheet_character_tags"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    spreadsheet_id = Column(String(36), ForeignKey("spreadsheets.id", ondelete="CASCADE"), nullable=False, index=True)
    character_name = Column(String(50), nullable=False, index=True)
    
    spreadsheet = relationship("Spreadsheet", back_populates="character_tags")
