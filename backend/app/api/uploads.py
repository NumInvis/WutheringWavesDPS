"""
文件上传相关API路由
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.file_storage import file_storage
from app.core.config import get_settings
from app.models.user import User
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/uploads", tags=["文件上传"])
settings = get_settings()


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传文件"""
    # 验证文件类型
    allowed_extensions = [".xlsx", ".xls", ".csv"]
    filename = file.filename or ""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    
    if f".{ext}" not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型，仅支持: {', '.join(allowed_extensions)}"
        )
    
    # 保存文件
    max_size = settings.max_upload_size or 10 * 1024 * 1024
    file_url, file_size = await file_storage.save_file(file, max_size)
    
    return {
        "file_url": file_url,
        "file_size": file_size,
        "filename": filename,
        "message": "文件上传成功"
    }
