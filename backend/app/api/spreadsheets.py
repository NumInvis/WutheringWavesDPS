"""
表格相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models.user import User
from app.models.spreadsheet import Spreadsheet
from app.schemas.spreadsheet import (
    SpreadsheetCreate,
    SpreadsheetUpdate,
    SpreadsheetAdminUpdate,
    SpreadsheetResponse,
    SpreadsheetListResponse
)
from app.api.auth import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/api/spreadsheets", tags=["表格"])


@router.get("", response_model=SpreadsheetListResponse)
def list_spreadsheets(
    category: Optional[str] = None,
    area: Optional[str] = None,
    character_tag: Optional[str] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None,
    owner_id: Optional[int] = None,
    sort_by: str = Query("created_at", regex="^(created_at|star_count|view_count|download_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取表格列表"""
    # 基础查询：默认只显示公开的、非下架的、非草稿的
    query = db.query(Spreadsheet).filter(
        Spreadsheet.is_public == True,
        Spreadsheet.is_draft == False,
        Spreadsheet.is_banned == False
    )
    
    # 如果指定了owner_id，显示该用户的所有表格（包括草稿）
    if owner_id:
        query = db.query(Spreadsheet).filter(Spreadsheet.user_id == owner_id)
    
    # 分类筛选
    if category:
        query = query.filter(Spreadsheet.category == category)
    
    # 区域筛选
    if area:
        query = query.filter(Spreadsheet.area == area)
    
    # 角色标签筛选
    if character_tag:
        query = query.filter(Spreadsheet.character_tags.contains([character_tag]))
    
    # 精华筛选
    if featured:
        query = query.filter(Spreadsheet.is_featured == True)
    
    # 搜索
    if search:
        query = query.filter(
            Spreadsheet.title.contains(search) | 
            Spreadsheet.description.contains(search)
        )
    
    # 排序：精华优先
    if featured is None:
        query = query.order_by(Spreadsheet.is_featured.desc())
    
    # 排序
    sort_column = getattr(Spreadsheet, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # 分页
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 添加拥有者信息
    for item in items:
        if item.user:
            item.owner_username = item.user.username
            item.owner_display_name = item.user.display_name or item.user.username
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{spreadsheet_id}", response_model=SpreadsheetResponse)
def get_spreadsheet(
    spreadsheet_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """获取单个表格详情"""
    spreadsheet = db.query(Spreadsheet).filter(Spreadsheet.id == spreadsheet_id).first()
    
    if not spreadsheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表格不存在"
        )
    
    # 检查权限（如果是草稿或下架，只有拥有者或管理员可以访问）
    if (spreadsheet.is_draft or spreadsheet.is_banned) and (not current_user or (current_user.id != spreadsheet.user_id and not current_user.is_admin)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此表格"
        )
    
    # 如果不是草稿且不是下架，且不是拥有者，增加浏览次数
    if not spreadsheet.is_draft and not spreadsheet.is_banned and (not current_user or current_user.id != spreadsheet.user_id):
        spreadsheet.view_count += 1
        db.commit()
    
    return spreadsheet


@router.post("", response_model=SpreadsheetResponse, status_code=status.HTTP_201_CREATED)
def create_spreadsheet(
    spreadsheet_data: SpreadsheetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新表格"""
    spreadsheet = Spreadsheet(
        user_id=current_user.id,
        title=spreadsheet_data.title,
        description=spreadsheet_data.description,
        category=spreadsheet_data.category,
        tags=spreadsheet_data.tags,
        character_tags=spreadsheet_data.character_tags,
        area=spreadsheet_data.area,
        is_public=spreadsheet_data.is_public,
        is_draft=spreadsheet_data.is_draft,
        file_url=spreadsheet_data.file_url,
        file_size=spreadsheet_data.file_size,
        thumbnail_url=spreadsheet_data.thumbnail_url,
        metadata=spreadsheet_data.metadata
    )
    
    db.add(spreadsheet)
    db.commit()
    db.refresh(spreadsheet)
    
    return spreadsheet


@router.put("/{spreadsheet_id}", response_model=SpreadsheetResponse)
def update_spreadsheet(
    spreadsheet_id: str,
    spreadsheet_data: SpreadsheetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新表格（只有拥有者可以）"""
    spreadsheet = db.query(Spreadsheet).filter(Spreadsheet.id == spreadsheet_id).first()
    
    if not spreadsheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表格不存在"
        )
    
    if spreadsheet.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此表格"
        )
    
    # 更新字段
    update_data = spreadsheet_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(spreadsheet, field, value)
    
    db.commit()
    db.refresh(spreadsheet)
    
    return spreadsheet


@router.put("/{spreadsheet_id}/admin", response_model=SpreadsheetResponse)
def admin_update_spreadsheet(
    spreadsheet_id: str,
    spreadsheet_data: SpreadsheetAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """管理员更新表格（下架/精华）"""
    spreadsheet = db.query(Spreadsheet).filter(Spreadsheet.id == spreadsheet_id).first()
    
    if not spreadsheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表格不存在"
        )
    
    # 更新字段
    update_data = spreadsheet_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(spreadsheet, field, value)
    
    db.commit()
    db.refresh(spreadsheet)
    
    return spreadsheet


@router.delete("/{spreadsheet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spreadsheet(
    spreadsheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除表格（拥有者或管理员）"""
    spreadsheet = db.query(Spreadsheet).filter(Spreadsheet.id == spreadsheet_id).first()
    
    if not spreadsheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表格不存在"
        )
    
    if spreadsheet.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此表格"
        )
    
    db.delete(spreadsheet)
    db.commit()


@router.get("/user/my", response_model=SpreadsheetListResponse)
def get_my_spreadsheets(
    include_drafts: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的表格"""
    query = db.query(Spreadsheet).filter(Spreadsheet.user_id == current_user.id)
    
    if not include_drafts:
        query = query.filter(Spreadsheet.is_draft == False)
    
    query = query.order_by(Spreadsheet.updated_at.desc())
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }
