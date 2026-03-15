"""
角色素材图片API
提供角色头像图片访问
"""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, Response

router = APIRouter(prefix="/api/sucai", tags=["角色素材"])

BASE_DIR = Path(__file__).resolve().parents[3]
SUCAI_DIR = BASE_DIR / "sucai"

# 支持的图片扩展名
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.gif']


@router.get("/{filename}")
async def get_sucai_image(filename: str):
    """
    获取角色素材图片
    """
    # 安全检查：防止目录遍历 - 使用Path验证文件名
    try:
        # 验证文件名不包含路径分隔符
        if Path(filename).name != filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
    
    # 尝试不同的扩展名
    for ext in IMAGE_EXTENSIONS:
        file_path = SUCAI_DIR / f"{filename}{ext}"
        if file_path.exists() and file_path.is_file():
            return FileResponse(
                str(file_path),
                media_type=f"image/{ext.lstrip('.').replace('jpg', 'jpeg')}"
            )
    
    # 如果直接匹配不到，尝试完整文件名
    file_path = SUCAI_DIR / filename
    if file_path.exists() and file_path.is_file():
        ext = file_path.suffix.lower()
        media_type = "image/png"
        if ext in ['.jpg', '.jpeg']:
            media_type = "image/jpeg"
        elif ext == '.webp':
            media_type = "image/webp"
        elif ext == '.gif':
            media_type = "image/gif"
        return FileResponse(str(file_path), media_type=media_type)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Image not found"
    )


@router.get("/list")
async def list_sucai_images():
    """
    列出所有可用的角色素材图片
    """
    if not SUCAI_DIR.exists():
        return {"images": []}
    
    images = []
    for file in SUCAI_DIR.iterdir():
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS:
            images.append({
                "name": file.stem,
                "filename": file.name,
                "size": file.stat().st_size
            })
    
    return {"images": images, "count": len(images)}
