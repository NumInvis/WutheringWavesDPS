"""
FastAPI主应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import get_settings
from app.models.base import Base
from app.core.database import engine, SessionLocal
import os

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="鸣潮排轴DPS计算器 - 面向多用户的开源协作平台",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保上传目录存在
os.makedirs(settings.upload_dir, exist_ok=True)

# 挂载静态文件服务（用于访问上传的文件
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 注册API路由
from app.api import auth, spreadsheets, stars, categories, uploads

app.include_router(auth.router)
app.include_router(spreadsheets.router)
app.include_router(stars.router)
app.include_router(categories.router)
app.include_router(uploads.router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    db = SessionLocal()
    try:
        from app.api.categories import init_categories
        from app.api.auth import init_admin_user
        init_categories(db)
        init_admin_user(db)
    finally:
        db.close()


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用鸣潮排轴DPS计算器 API",
        "version": "3.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
