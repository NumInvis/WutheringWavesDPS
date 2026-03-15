"""
Spreadsheet-related APIs.
"""
import json
import shutil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import String

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
from app.api.auth import (
    get_current_active_user,
    get_current_admin_user,
    get_current_user_optional
)

router = APIRouter(prefix="/api/spreadsheets", tags=["表格"])


def init_template_spreadsheet(db: Session):
    """初始化拉表模板（编号0000000）。"""
    import os
    from app.core.config import get_settings
    settings = get_settings()
    
    try:
        existing_template = db.query(Spreadsheet).filter(Spreadsheet.sheet_number == 0).first()
        if existing_template:
            return existing_template
    except Exception:
        pass
    
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    template_path = os.path.join(backend_dir, "拉表模板.xlsx")
    
    if not os.path.exists(template_path):
        return None
    
    upload_dir = settings.upload_dir
    if not os.path.isabs(upload_dir):
        upload_dir = os.path.join(backend_dir, upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    
    import uuid
    file_id = str(uuid.uuid4())
    ext = ".xlsx"
    dest_path = os.path.join(upload_dir, f"{file_id}{ext}")
    
    import shutil
    shutil.copyfile(template_path, dest_path)
    
    file_size = os.path.getsize(dest_path)
    file_url = f"/WutheringWavesDPS/uploads/{file_id}{ext}"
    
    admin_user = db.query(User).filter(User.is_admin == True).first()
    if not admin_user:
        return None
    
    try:
        template = Spreadsheet(
            user_id=admin_user.id,
            sheet_number=0,
            title="拉表模板",
            description="官方拉表模板，欢迎使用！",
            area="pull_table",
            is_public=True,
            is_draft=False,
            is_featured=True,
            file_url=file_url,
            file_size=file_size
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return template
    except Exception:
        db.rollback()
        return None


@router.get("/template")
def get_template_spreadsheet(
    db: Session = Depends(get_db)
):
    """Get the default template spreadsheet."""
    template = db.query(Spreadsheet).filter(
        Spreadsheet.sheet_number == 0
    ).first()
    
    if template:
        return {
            "id": template.id,
            "title": template.title,
            "file_url": template.file_url,
            "description": template.description
        }
    
    return {
        "id": None,
        "title": "拉表模板",
        "file_url": None,
        "description": "暂无模板"
    }


def _hydrate_spreadsheet(item: Spreadsheet, current_user_id: Optional[str] = None, db: Optional[Session] = None):
    result = {
        "id": item.id,
        "sheet_number": item.sheet_number,
        "user_id": item.user_id,
        "title": item.title,
        "description": item.description,
        "category": item.category,
        "area": item.area,
        "is_draft": item.is_draft,
        "is_banned": item.is_banned,
        "is_featured": item.is_featured,
        "is_public": item.is_public,
        "star_count": item.star_count,
        "view_count": item.view_count,
        "download_count": item.download_count,
        "file_url": item.file_url,
        "file_size": item.file_size,
        "thumbnail_url": item.thumbnail_url,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "tags": [],
        "character_tags": [],
        "extra_metadata": None,
        "owner_username": None,
        "owner_display_name": None,
        "has_starred": False
    }
    
    if hasattr(item, 'tags') and item.tags:
        try:
            if isinstance(item.tags, str):
                result["tags"] = json.loads(item.tags)
            else:
                result["tags"] = [tag.tag_name for tag in item.tags]
        except Exception:
            result["tags"] = []
    
    if hasattr(item, 'character_tags') and item.character_tags:
        try:
            if isinstance(item.character_tags, str):
                result["character_tags"] = json.loads(item.character_tags)
            else:
                result["character_tags"] = [tag.character_name for tag in item.character_tags]
        except Exception:
            result["character_tags"] = []
    
    if item.extra_metadata:
        try:
            if isinstance(item.extra_metadata, str):
                result["extra_metadata"] = json.loads(item.extra_metadata)
            else:
                result["extra_metadata"] = item.extra_metadata
        except Exception:
            result["extra_metadata"] = None
    
    if item.user:
        result["owner_username"] = item.user.username
        result["owner_display_name"] = item.user.display_name or item.user.username
    
    if current_user_id and db:
        from app.models.star import Star
        has_starred = db.query(Star).filter(
            Star.user_id == current_user_id,
            Star.spreadsheet_id == item.id
        ).first() is not None
        result["has_starred"] = has_starred
    
    return result


@router.get("", response_model=SpreadsheetListResponse)
def list_spreadsheets(
    category: Optional[str] = None,
    area: Optional[str] = None,
    character_tag: Optional[str] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None,
    owner_id: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|star_count|view_count|download_count)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get spreadsheet list."""
    base_query = db.query(Spreadsheet).options(joinedload(Spreadsheet.user))

    # Default: only public, non-draft, non-banned
    query = base_query.filter(
        Spreadsheet.is_public == True,
        Spreadsheet.is_draft == False,
        Spreadsheet.is_banned == False
    )

    # Owner view: show all for that user
    if owner_id:
        query = base_query.filter(Spreadsheet.user_id == owner_id)

    if category:
        query = query.filter(Spreadsheet.category == category)

    if area:
        query = query.filter(Spreadsheet.area == area)

    if character_tag:
        query = query.filter(Spreadsheet.character_tags.contains(character_tag))

    if featured is not None:
        query = query.filter(Spreadsheet.is_featured == featured)

    if search:
        query = query.filter(
            Spreadsheet.title.contains(search) |
            Spreadsheet.description.contains(search) |
            Spreadsheet.user.has(username=search) |
            (Spreadsheet.sheet_number != None) & (Spreadsheet.sheet_number.cast(String).contains(search))
        )

    if featured is None:
        query = query.order_by(Spreadsheet.is_featured.desc())

    sort_column = getattr(Spreadsheet, sort_by)
    query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    current_user_id = current_user.id if current_user else None
    hydrated_items = []
    for item in items:
        hydrated_items.append(_hydrate_spreadsheet(item, current_user_id, db))

    return {
        "items": hydrated_items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{spreadsheet_id}", response_model=SpreadsheetResponse)
def get_spreadsheet(
    spreadsheet_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get a single spreadsheet detail."""
    spreadsheet = db.query(Spreadsheet).options(joinedload(Spreadsheet.user)).filter(
        Spreadsheet.id == spreadsheet_id
    ).first()

    if not spreadsheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表格不存在"
        )

    if (spreadsheet.is_draft or spreadsheet.is_banned) and (
        not current_user or (current_user.id != spreadsheet.user_id and not current_user.is_admin)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此表格"
        )

    if not spreadsheet.is_draft and not spreadsheet.is_banned and (
        not current_user or current_user.id != spreadsheet.user_id
    ):
        spreadsheet.view_count += 1
        db.commit()

    current_user_id = current_user.id if current_user else None
    return _hydrate_spreadsheet(spreadsheet, current_user_id, db)


@router.post("/upload", response_model=SpreadsheetResponse, status_code=status.HTTP_201_CREATED)
def upload_and_create_spreadsheet(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    area: str = Form("pull_table"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload file and create spreadsheet in one step."""
    from app.core.config import get_settings
    import os
    import uuid
    
    settings = get_settings()
    
    upload_dir = settings.upload_dir
    if not os.path.isabs(upload_dir):
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        upload_dir = os.path.join(backend_dir, upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or ".xlsx")[1]
    dest_path = os.path.join(upload_dir, f"{file_id}{ext}")
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = os.path.getsize(dest_path)
    file_url = f"/WutheringWavesDPS/uploads/{file_id}{ext}"
    
    max_number = db.query(Spreadsheet.sheet_number).filter(
        Spreadsheet.sheet_number.isnot(None)
    ).order_by(Spreadsheet.sheet_number.desc()).first()
    
    next_number = 1 if max_number is None else (max_number[0] + 1)
    
    spreadsheet = Spreadsheet(
        user_id=current_user.id,
        sheet_number=next_number,
        title=title,
        description=description,
        area=area,
        is_public=True,
        is_draft=False,
        file_url=file_url,
        file_size=file_size
    )

    db.add(spreadsheet)
    db.commit()
    db.refresh(spreadsheet)

    return _hydrate_spreadsheet(spreadsheet)


@router.post("", response_model=SpreadsheetResponse, status_code=status.HTTP_201_CREATED)
def create_spreadsheet(
    spreadsheet_data: SpreadsheetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new spreadsheet."""
    max_number = db.query(Spreadsheet.sheet_number).filter(
        Spreadsheet.sheet_number.isnot(None)
    ).order_by(Spreadsheet.sheet_number.desc()).first()
    
    next_number = 1 if max_number is None else (max_number[0] + 1)
    
    spreadsheet = Spreadsheet(
        user_id=current_user.id,
        sheet_number=next_number,
        title=spreadsheet_data.title,
        description=spreadsheet_data.description,
        category=spreadsheet_data.category,
        area=spreadsheet_data.area,
        is_public=spreadsheet_data.is_public,
        is_draft=spreadsheet_data.is_draft,
        file_url=spreadsheet_data.file_url,
        file_size=spreadsheet_data.file_size,
        thumbnail_url=spreadsheet_data.thumbnail_url,
        extra_metadata=json.dumps(spreadsheet_data.extra_metadata) if spreadsheet_data.extra_metadata else None
    )

    db.add(spreadsheet)
    db.commit()
    db.refresh(spreadsheet)

    return _hydrate_spreadsheet(spreadsheet)


@router.put("/{spreadsheet_id}", response_model=SpreadsheetResponse)
def update_spreadsheet(
    spreadsheet_id: str,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update spreadsheet (owner only)."""
    from app.core.config import get_settings
    import os
    import uuid
    
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

    if title is not None:
        spreadsheet.title = title
    if description is not None:
        spreadsheet.description = description
    
    if file:
        settings = get_settings()
        upload_dir = settings.upload_dir
        if not os.path.isabs(upload_dir):
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            upload_dir = os.path.join(backend_dir, upload_dir)
        os.makedirs(upload_dir, exist_ok=True)
        
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename or ".xlsx")[1]
        dest_path = os.path.join(upload_dir, f"{file_id}{ext}")
        
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(dest_path)
        spreadsheet.file_url = f"/WutheringWavesDPS/uploads/{file_id}{ext}"
        spreadsheet.file_size = file_size

    db.commit()
    db.refresh(spreadsheet)
    return _hydrate_spreadsheet(spreadsheet)


@router.post("/{spreadsheet_id}/toggle-feature")
def toggle_feature_spreadsheet(
    spreadsheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Toggle feature status (admin only)."""
    spreadsheet = db.query(Spreadsheet).filter(Spreadsheet.id == spreadsheet_id).first()
    if not spreadsheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表格不存在"
        )

    spreadsheet.is_featured = not spreadsheet.is_featured
    db.commit()
    db.refresh(spreadsheet)
    _hydrate_spreadsheet(spreadsheet)
    return {"is_featured": spreadsheet.is_featured}


@router.put("/{spreadsheet_id}/admin", response_model=SpreadsheetResponse)
def admin_update_spreadsheet(
    spreadsheet_id: str,
    spreadsheet_data: SpreadsheetAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Admin update: ban/feature."""
    spreadsheet = db.query(Spreadsheet).filter(Spreadsheet.id == spreadsheet_id).first()
    if not spreadsheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表格不存在"
        )

    update_data = spreadsheet_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(spreadsheet, field, value)

    db.commit()
    db.refresh(spreadsheet)
    return _hydrate_spreadsheet(spreadsheet)


@router.delete("/{spreadsheet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spreadsheet(
    spreadsheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete spreadsheet (owner or admin)."""
    from app.models.star import Star
    
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

    # 先删除关联的stars
    db.query(Star).filter(Star.spreadsheet_id == spreadsheet_id).delete(synchronize_session=False)
    
    db.delete(spreadsheet)
    db.commit()


@router.get("/{spreadsheet_id}/download")
def download_spreadsheet(
    spreadsheet_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Increment download count and return file URL."""
    spreadsheet = db.query(Spreadsheet).filter(Spreadsheet.id == spreadsheet_id).first()
    if not spreadsheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表格不存在"
        )

    if (spreadsheet.is_draft or spreadsheet.is_banned) and (
        not current_user or (current_user.id != spreadsheet.user_id and not current_user.is_admin)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此表格"
        )

    spreadsheet.download_count += 1
    db.commit()

    return {"file_url": spreadsheet.file_url, "filename": spreadsheet.title + ".xlsx"}


@router.get("/user/my", response_model=SpreadsheetListResponse)
def get_my_spreadsheets(
    include_drafts: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's spreadsheets."""
    query = db.query(Spreadsheet).options(joinedload(Spreadsheet.user)).filter(
        Spreadsheet.user_id == current_user.id
    )

    if not include_drafts:
        query = query.filter(Spreadsheet.is_draft == False)

    query = query.order_by(Spreadsheet.updated_at.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    hydrated_items = []
    for item in items:
        hydrated_items.append(_hydrate_spreadsheet(item))

    return {
        "items": hydrated_items,
        "total": total,
        "page": page,
        "page_size": page_size
    }
