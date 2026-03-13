"""
Star/点赞模型
"""
from sqlalchemy import Column, Text, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin


class Star(Base, TimestampMixin):
    """Star/点赞表"""
    __tablename__ = "stars"
    __table_args__ = (
        UniqueConstraint("user_id", "spreadsheet_id", name="uq_user_spreadsheet"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_rating_range"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    spreadsheet_id = Column(UUID(as_uuid=True), ForeignKey("spreadsheets.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer)
    comment = Column(Text)
    
    user = relationship("User", backref="stars")
    spreadsheet = relationship("Spreadsheet", backref="stars")
