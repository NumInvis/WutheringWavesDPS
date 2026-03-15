"""
公告相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.announcement import Announcement
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementResponse
)
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/announcements", tags=["公告"])


@router.get("", response_model=List[AnnouncementResponse])
def list_announcements(
    db: Session = Depends(get_db)
):
    """获取所有公告（管理员使用）"""
    return db.query(Announcement).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()


@router.get("/active", response_model=List[AnnouncementResponse])
def list_active_announcements(
    db: Session = Depends(get_db)
):
    """获取激活的公告（公开访问）"""
    return db.query(Announcement).filter(Announcement.is_active == True).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(
    announcement_id: str,
    db: Session = Depends(get_db)
):
    """获取单个公告"""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )
    return announcement


@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement_data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """创建公告（管理员功能）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建公告"
        )
    
    announcement = Announcement(**announcement_data.model_dump())
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    
    return announcement


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: str,
    announcement_data: AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """更新公告（管理员功能）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新公告"
        )
    
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )
    
    update_data = announcement_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(announcement, field, value)
    
    db.commit()
    db.refresh(announcement)
    
    return announcement


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """删除公告（管理员功能）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除公告"
        )
    
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )
    
    db.delete(announcement)
    db.commit()
