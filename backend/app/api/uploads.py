"""
Excel文件上传/下载API
核心原则：Excel原表格的公式、格式全部不变
"""
import os
import uuid
import hashlib
import zipfile
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.core.rate_limit import rate_limiter
from app.models.user import User
from app.api.auth import get_current_active_user, get_current_user_optional

router = APIRouter(prefix="/api/uploads", tags=["Excel文件"])
settings = get_settings()

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {".xlsx", ".xlsm", ".xls"}

# MIME 类型白名单
ALLOWED_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel.sheet.macroenabled.12",  # .xlsm
    "application/vnd.ms-excel",  # .xls
    "application/octet-stream"  # 某些系统可能使用此类型
}

# 禁止的文件签名（可执行文件等）
FORBIDDEN_SIGNATURES = [
    b"MZ",  # Windows 可执行文件
    b"\x7fELF",  # Linux 可执行文件
    b"#!/",  # Shell 脚本
    b"<?php",  # PHP 脚本
    b"<script",  # JavaScript
]


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


def _validate_file_extension(filename: str) -> bool:
    """验证文件扩展名"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def _validate_mime_type(content: bytes) -> bool:
    """验证文件 MIME 类型"""
    # 检查 ZIP 签名（xlsx 是 ZIP 格式）
    if content.startswith(b"PK\x03\x04"):
        return True
    # 检查 OLE 签名（xls 格式）
    if content.startswith(b"\xd0\xcf\x11\xe0"):
        return True
    return False


def _validate_file_signature(content: bytes) -> bool:
    """验证文件签名，防止上传可执行文件"""
    for signature in FORBIDDEN_SIGNATURES:
        if content.startswith(signature):
            return False
    return True


def _validate_excel_structure(content: bytes) -> bool:
    """验证 Excel 文件结构"""
    try:
        # 尝试作为 ZIP 打开（xlsx 格式）
        if content.startswith(b"PK\x03\x04"):
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                # 检查必要的 Excel 文件结构
                required_files = ["[Content_Types].xml", "xl/workbook.xml"]
                for required in required_files:
                    if required not in zf.namelist():
                        return False
            return True
        return True
    except Exception:
        return False


@router.post("")
async def upload_excel(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    上传Excel文件（增强安全版本）
    - 原始文件二进制保存，不做任何转换
    - 公式、格式、数据完全保留
    - 使用流式读取防止内存溢出
    - 多重安全验证
    """
    # 速率限制检查
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip, max_requests=10, window=60):  # 每分钟最多10次上传
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="上传过于频繁，请稍后再试"
        )
    
    filename = file.filename or "unknown.xlsx"
    
    # 1. 验证文件扩展名
    if not _validate_file_extension(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"仅支持Excel文件: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 2. 验证 MIME 类型
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件类型不合法"
        )
    
    # 流式读取文件内容
    content = b""
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        
        # 检查文件大小限制
        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制（最大 {settings.max_upload_size / 1024 / 1024:.1f}MB）"
            )
        
        content += chunk
    
    # 3. 验证文件签名（防止可执行文件）
    if not _validate_file_signature(content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件内容不合法"
        )
    
    # 4. 验证文件结构
    if not _validate_mime_type(content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件格式不正确"
        )
    
    file_id = _generate_file_id()
    file_hash = _get_file_hash(content)
    
    upload_dir = _get_upload_dir()
    ext = os.path.splitext(filename)[1].lower()
    
    # 保存原始文件
    original_path = os.path.join(upload_dir, f"{file_id}_original{ext}")
    with open(original_path, "wb") as f:
        f.write(content)
    
    # 保存访问文件
    access_path = os.path.join(upload_dir, f"{file_id}{ext}")
    with open(access_path, "wb") as f:
        f.write(content)
    
    return {
        "file_id": file_id,
        "file_url": f"/WutheringWavesDPS/uploads/{file_id}{ext}",
        "original_url": f"/WutheringWavesDPS/api/uploads/{file_id}/download",
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
    
    for ext in ALLOWED_EXTENSIONS:
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
                    "Cache-Control": "no-cache",
                    "X-Content-Type-Options": "nosniff"
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
    
    for ext in ALLOWED_EXTENSIONS:
        file_path = os.path.join(upload_dir, f"{file_id}_original{ext}")
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            return {
                "file_id": file_id,
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "download_url": f"/WutheringWavesDPS/api/uploads/{file_id}/download"
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
    
    for ext in ALLOWED_EXTENSIONS:
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
