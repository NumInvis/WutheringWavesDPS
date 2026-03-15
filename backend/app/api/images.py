"""
图片上传API
用于上传角色头像等图片
"""
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.core.rate_limit import rate_limiter
from app.models.user import User
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/images", tags=["图片上传"])
settings = get_settings()

# 允许的图片扩展名
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# 允许的图片 MIME 类型
ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp"
}


def _get_image_upload_dir() -> str:
    upload_dir = settings.upload_dir
    if not os.path.isabs(upload_dir):
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        upload_dir = os.path.join(backend_dir, upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _generate_file_id() -> str:
    return str(uuid.uuid4())


def _validate_image_extension(filename: str) -> bool:
    """验证图片文件扩展名"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def _validate_image_mime_type(content_type: Optional[str]) -> bool:
    """验证图片 MIME 类型"""
    if not content_type:
        return False
    return content_type in ALLOWED_IMAGE_MIME_TYPES


@router.post("")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    上传图片文件
    - 支持 jpg, jpeg, png, gif, webp
    - 最大 5MB
    """
    # 速率限制检查
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip, max_requests=20, window=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="上传过于频繁，请稍后再试"
        )
    
    filename = file.filename or "unknown.png"
    
    # 1. 验证文件扩展名
    if not _validate_image_extension(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"仅支持图片文件: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )
    
    # 2. 验证 MIME 类型
    if not _validate_image_mime_type(file.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件类型不合法"
        )
    
    # 读取文件内容
    content = await file.read()
    file_size = len(content)
    
    # 检查文件大小限制（5MB）
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="文件大小超过限制（最大 5MB）"
        )
    
    file_id = _generate_file_id()
    ext = os.path.splitext(filename)[1].lower()
    
    upload_dir = _get_image_upload_dir()
    
    # 保存文件
    file_path = os.path.join(upload_dir, f"{file_id}{ext}")
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "file_id": file_id,
        "file_url": f"/WutheringWavesDPS/uploads/{file_id}{ext}",
        "file_size": file_size,
        "filename": filename,
        "message": "图片上传成功"
    }
