"""
Star评分相关API路由
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
    StarUpdate,
    StarResponse
)
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/stars", tags=["Star评分"])


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
    """创建Star评分"""
    # 检查表格是否存在
    spreadsheet = db.query(Spreadsheet).filter(Spreadsheet.id == star_data.spreadsheet_id).first()
    if not spreadsheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表格不存在"
        )
    
    # 检查是否已经star过
    existing_star = db.query(Star).filter(
        Star.user_id == current_user.id,
        Star.spreadsheet_id == star_data.spreadsheet_id
    ).first()
    if existing_star:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="你已经给这个表格评分了"
        )
    
    # 创建star
    star = Star(
        user_id=current_user.id,
        spreadsheet_id=star_data.spreadsheet_id,
        rating=star_data.rating,
        comment=star_data.comment
    )
    
    db.add(star)
    db.commit()
    db.refresh(star)
    
    # 更新star计数
    update_spreadsheet_star_count(db, str(star_data.spreadsheet_id))
    
    return star


@router.get("/spreadsheet/{spreadsheet_id}", response_model=List[StarResponse])
def get_spreadsheet_stars(
    spreadsheet_id: str,
    db: Session = Depends(get_db)
):
    """获取表格的所有Star评分"""
    stars = db.query(Star).filter(Star.spreadsheet_id == spreadsheet_id).all()
    return stars


@router.get("/spreadsheet/{spreadsheet_id}/me", response_model=StarResponse)
def get_my_star(
    spreadsheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取我对某个表格的Star评分"""
    star = db.query(Star).filter(
        Star.user_id == current_user.id,
        Star.spreadsheet_id == spreadsheet_id
    ).first()
    
    if not star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="你还没有给这个表格评分"
        )
    
    return star


@router.put("/spreadsheet/{spreadsheet_id}", response_model=StarResponse)
def update_star(
    spreadsheet_id: str,
    star_data: StarUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新Star评分"""
    star = db.query(Star).filter(
        Star.user_id == current_user.id,
        Star.spreadsheet_id == spreadsheet_id
    ).first()
    
    if not star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="你还没有给这个表格评分"
        )
    
    # 更新字段
    update_data = star_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(star, field, value)
    
    db.commit()
    db.refresh(star)
    
    return star


@router.delete("/spreadsheet/{spreadsheet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_star(
    spreadsheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除Star评分（取消点赞）"""
    star = db.query(Star).filter(
        Star.user_id == current_user.id,
        Star.spreadsheet_id == spreadsheet_id
    ).first()
    
    if not star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="你还没有给这个表格评分"
        )
    
    db.delete(star)
    db.commit()
    
    # 更新star计数
    update_spreadsheet_star_count(db, spreadsheet_id)


@router.get("/user/my", response_model=List[StarResponse])
def get_my_stars(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取我的所有Star评分"""
    stars = db.query(Star).filter(Star.user_id == current_user.id).all()
    return stars
