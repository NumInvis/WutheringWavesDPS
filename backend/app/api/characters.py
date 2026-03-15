"""
角色相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.character import Character
from app.schemas.character import (
    CharacterCreate,
    CharacterUpdate,
    CharacterResponse
)
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/characters", tags=["角色"])


@router.get("", response_model=List[CharacterResponse])
def list_characters(
    db: Session = Depends(get_db)
):
    """获取所有角色"""
    characters = db.query(Character).order_by(Character.created_at.desc()).all()
    return characters


@router.get("/{character_id}", response_model=CharacterResponse)
def get_character(
    character_id: str,
    db: Session = Depends(get_db)
):
    """获取单个角色"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    return character


@router.post("/admin/characters", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
def create_character(
    character_data: CharacterCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """创建角色（管理员功能）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建角色"
        )
    
    character = Character(**character_data.model_dump())
    db.add(character)
    db.commit()
    db.refresh(character)
    
    return character


@router.put("/admin/characters/{character_id}", response_model=CharacterResponse)
def update_character(
    character_id: str,
    character_data: CharacterUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """更新角色（管理员功能）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新角色"
        )
    
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    update_data = character_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(character, field, value)
    
    db.commit()
    db.refresh(character)
    
    return character


@router.delete("/admin/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(
    character_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """删除角色（管理员功能）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除角色"
        )
    
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    db.delete(character)
    db.commit()
