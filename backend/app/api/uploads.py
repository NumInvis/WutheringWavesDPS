"""
Excel文件上传/下载API
核心原则：Excel原表格的公式、格式全部不变
"""
import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.models.user import User
from app.api.auth import get_current_active_user, get_current_user_optional

router = APIRouter(prefix="/api/uploads", tags=["Excel文件"])
settings = get_settings()


def _get_upload_dir() -> str:
    upload_dir = settings.upload_dir
    if not os.path.isabs(upload_dir):
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        upload_dir = os.path.join(backend_dir, upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _generate_file_id() -> str:
    return str(uuid.uuid4())


def _get_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@router.post("")
async def upload_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    上传Excel文件
    - 原始文件二进制保存，不做任何转换
    - 公式、格式、数据完全保留
    - 使用流式读取防止内存溢出
    """
    filename = file.filename or "unknown.xlsx"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in [".xlsx", ".xlsm", ".xls"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"仅支持Excel文件: .xlsx, .xlsm, .xls"
        )
    
    # 流式读取文件内容，防止内存溢出
    content = b""
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        
        # 检查文件大小限制（在读取过程中检查，防止大文件攻击）
        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制（最大 {settings.max_upload_size / 1024 / 1024:.1f}MB）"
            )
        
        content += chunk
    
    file_id = _generate_file_id()
    file_hash = _get_file_hash(content)
    
    upload_dir = _get_upload_dir()
    
    original_path = os.path.join(upload_dir, f"{file_id}_original{ext}")
    with open(original_path, "wb") as f:
        f.write(content)
    
    access_path = os.path.join(upload_dir, f"{file_id}{ext}")
    with open(access_path, "wb") as f:
        f.write(content)
    
    return {
        "file_id": file_id,
        "file_url": f"/uploads/{file_id}{ext}",
        "original_url": f"/api/uploads/{file_id}/download",
        "file_size": file_size,
        "file_hash": file_hash,
        "filename": filename,
        "message": "Excel文件已完整保存（公式、格式、数据不变）"
    }


@router.get("/{file_id}/download")
async def download_excel(
    file_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    下载原始Excel文件
    - 返回原始二进制文件
    - 公式、格式、数据完全不变
    """
    upload_dir = _get_upload_dir()
    
    for ext in [".xlsx", ".xlsm", ".xls"]:
        file_path = os.path.join(upload_dir, f"{file_id}_original{ext}")
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                content = f.read()
            
            filename = f"{file_id}{ext}"
            
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Cache-Control": "no-cache"
                }
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="文件不存在"
    )


@router.get("/{file_id}/info")
async def get_file_info(
    file_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取文件信息"""
    upload_dir = _get_upload_dir()
    
    for ext in [".xlsx", ".xlsm", ".xls"]:
        file_path = os.path.join(upload_dir, f"{file_id}_original{ext}")
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            return {
                "file_id": file_id,
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "download_url": f"/api/uploads/{file_id}/download"
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="文件不存在"
    )


@router.delete("/{file_id}")
async def delete_excel(
    file_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """删除Excel文件"""
    upload_dir = _get_upload_dir()
    deleted = False
    
    for ext in [".xlsx", ".xlsm", ".xls"]:
        for suffix in ["_original", ""]:
            file_path = os.path.join(upload_dir, f"{file_id}{suffix}{ext}")
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted = True
    
    if deleted:
        return {"message": "文件已删除"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="文件不存在"
    )
