"""
FastAPI application entry.
WutheringWavesDPS - Beta1.0
Port: 14876
"""
import os
import uvicorn

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.models.base import Base
from app.core.database import engine, SessionLocal

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有 HTTP 请求"""
    from app.api.admin import add_log
    
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # 只记录重要请求
    if not request.url.path.startswith("/uploads/") and duration > 0.1:
        add_log(
            "INFO",
            f"{request.method} {request.url.path}",
            {"duration": f"{duration:.2f}s", "status": response.status_code}
        )
    
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Import models to register
from app.models import user, spreadsheet, star, category  # noqa: F401

# Create tables (SQLite/dev)
Base.metadata.create_all(bind=engine)

# Routers
from app.api import auth, spreadsheets, stars, categories, uploads, admin  # noqa: E402

app.include_router(auth.router)
app.include_router(spreadsheets.router)
app.include_router(stars.router)
app.include_router(categories.router)
app.include_router(uploads.router)
app.include_router(admin.router)


@app.on_event("startup")
async def startup_event():
    """Startup hook."""
    from app.api.admin import add_log
    
    add_log("INFO", "系统启动", {"version": "Beta1.0", "port": settings.app_port})
    
    db = SessionLocal()
    try:
        from app.api.categories import init_categories
        from app.api.auth import init_admin_user
        from app.api.spreadsheets import init_template_spreadsheet
        init_categories(db)
        init_admin_user(db)
        init_template_spreadsheet(db)
        add_log("INFO", "数据库初始化完成")
    except Exception as e:
        add_log("ERROR", "数据库初始化失败", {"error": str(e)})
    finally:
        db.close()


@app.get("/")
async def root():
    return {
        "message": "Welcome to WutheringWavesDPS API",
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.app_debug
    )
