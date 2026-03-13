"""
Star/点赞模型
"""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin


class Star(Base, TimestampMixin):
    """Star/点赞表"""
    __tablename__ = "stars"
    __table_args__ = (
        UniqueConstraint("user_id", "spreadsheet_id", name="uq_user_spreadsheet"),
    )
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    spreadsheet_id = Column(String(36), ForeignKey("spreadsheets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    user = relationship("User", backref="stars")
    spreadsheet = relationship("Spreadsheet", backref="stars")
