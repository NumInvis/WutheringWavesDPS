"""
Star相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.spreadsheet import Spreadsheet
from app.models.star import Star
from app.schemas.star import (
    StarCreate,
    StarResponse
)
from app.api.auth import get_current_active_user, get_current_user_optional

router = APIRouter(prefix="/api/stars", tags=["Star"])


def update_spreadsheet_star_count(db: Session, spreadsheet_id: str):
    """更新表格的star计数"""
    spreadsheet = db.query(Spreadsheet).filter(Spreadsheet.id == spreadsheet_id).first()
    if spreadsheet:
        star_count = db.query(func.count(Star.id)).filter(Star.spreadsheet_id == spreadsheet_id).scalar()
        spreadsheet.star_count = star_count or 0
        db.commit()


@router.post("", response_model=StarResponse, status_code=status.HTTP_201_CREATED)
def create_star(
    star_data: StarCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建Star"""
    spreadsheet = db.query(Spreadsheet).filter(Spreadsheet.id == star_data.spreadsheet_id).first()
    if not spreadsheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表格不存在"
        )
    
    existing_star = db.query(Star).filter(
        Star.user_id == current_user.id,
        Star.spreadsheet_id == star_data.spreadsheet_id
    ).first()
    if existing_star:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="你已经给这个表格点过star了"
        )
    
    star = Star(
        user_id=current_user.id,
        spreadsheet_id=star_data.spreadsheet_id
    )
    
    db.add(star)
    db.commit()
    db.refresh(star)
    
    update_spreadsheet_star_count(db, str(star_data.spreadsheet_id))
    
    return star


@router.delete("/spreadsheet/{spreadsheet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_star(
    spreadsheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除Star（取消点赞）"""
    star = db.query(Star).filter(
        Star.user_id == current_user.id,
        Star.spreadsheet_id == spreadsheet_id
    ).first()
    
    if not star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="你还没有给这个表格点过star"
        )
    
    db.delete(star)
    db.commit()
    
    update_spreadsheet_star_count(db, spreadsheet_id)
