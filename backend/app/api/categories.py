"""
分类相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse
)
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/categories", tags=["分类"])


@router.get("", response_model=List[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db)
):
    """获取所有分类"""
    categories = db.query(Category).filter(
        Category.is_active == True
    ).order_by(Category.sort_order.asc()).all()
    return categories


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """获取单个分类"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在"
        )
    return category


@router.get("/slug/{slug}", response_model=CategoryResponse)
def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """通过slug获取分类"""
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在"
        )
    return category


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """创建分类（管理员功能）"""
    # 检查slug是否已存在
    existing_slug = db.query(Category).filter(Category.slug == category_data.slug).first()
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分类slug已存在"
        )
    
    # 检查名称是否已存在
    existing_name = db.query(Category).filter(Category.name == category_data.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分类名称已存在"
        )
    
    category = Category(**category_data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """更新分类"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在"
        )
    
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """删除分类"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在"
        )
    
    db.delete(category)
    db.commit()


def init_categories(db: Session):
    """初始化默认分类"""
    default_categories = [
        {"name": "角色计算", "slug": "character", "description": "单个角色伤害计算模板", "icon": "👤", "sort_order": 1},
        {"name": "队伍排轴", "slug": "team", "description": "完整队伍DPS排轴", "icon": "👥", "sort_order": 2},
        {"name": "声骸搭配", "slug": "echo", "description": "声骸选择与搭配方案", "icon": "🎭", "sort_order": 3},
        {"name": "机制研究", "slug": "mechanics", "description": "游戏机制深度研究", "icon": "🔬", "sort_order": 4},
        {"name": "教程模板", "slug": "tutorial", "description": "新手教程与示例", "icon": "📚", "sort_order": 5},
    ]
    
    for cat_data in default_categories:
        existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
        if not existing:
            category = Category(**cat_data)
            db.add(category)
    
    db.commit()
