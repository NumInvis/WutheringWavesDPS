"""
FastAPI application entry.
WutheringWavesDPS - Beta1.0
Port: 14876
"""
import os
import uvicorn
from pathlib import Path

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.models.base import Base
from app.core.database import engine, SessionLocal

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # CSRF 检查：对非 GET 请求验证 Origin 和 Referer
        if request.method not in ["GET", "HEAD", "OPTIONS"]:
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            
            allowed_hosts = [
                "http://www.arcanamorning.tech",
                "https://www.arcanamorning.tech",
                "http://localhost",
                "http://127.0.0.1"
            ]
            
            valid = False
            if origin:
                for host in allowed_hosts:
                    if origin.startswith(host):
                        valid = True
                        break
            elif referer:
                for host in allowed_hosts:
                    if referer.startswith(host):
                        valid = True
                        break
            
            # 如果是本地开发环境或没有 Origin/Referer，也放行（避免影响开发）
            if not valid:
                host = request.headers.get("host", "")
                if "localhost" in host or "127.0.0.1" in host:
                    valid = True
            
            if not valid and origin and referer:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF 验证失败"}
                )
        
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 只在 HTTPS 环境下启用 HSTS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https: data:; "
            "connect-src 'self' ws: wss:; "
            "worker-src 'self' blob: data:; "
            "frame-ancestors 'self';"
        )
        return response

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/WutheringWavesDPS/docs",
    redoc_url="/WutheringWavesDPS/redoc"
)

app.add_middleware(SecurityHeadersMiddleware)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有 HTTP 请求（安全版本，不记录敏感信息）并统计访问量"""
    from app.api.admin import add_log
    from app.api.visit_stats import record_visit
    
    start_time = time.time()
    
    # 过滤敏感路径和无信息量的路径
    excluded_paths = ["/login", "/register", "/change-password", "/admin/logs", "/health"]
    is_excluded = any(path in request.url.path for path in excluded_paths)
    
    # 记录访问统计
    if not is_excluded and not request.url.path.startswith("/uploads/") and not request.url.path.startswith("/assets/") and not request.url.path.startswith("/sucai/"):
        try:
            record_visit(request.url.path)
        except Exception:
            pass
    
    response = await call_next(request)
    duration = time.time() - start_time
    
    # 只记录有价值的请求，排除无信息量的请求
    if not is_excluded and not request.url.path.startswith("/uploads/") and not request.url.path.startswith("/assets/") and not request.url.path.startswith("/sucai/"):
        add_log(
            "INFO",
            f"{request.method} {request.url.path}",
            {"duration": f"{duration:.2f}s", "status": response.status_code}
        )
    
    return response


# CORS 配置优化 - 只允许必要的来源和方法
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 限制方法
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],  # 限制头部
    max_age=600,  # 预检请求缓存 10 分钟
)

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)

# Import models to register
from app.models import user, spreadsheet, star, category, character, announcement, visit_stat  # noqa: F401

# Create tables (SQLite/dev)
Base.metadata.create_all(bind=engine)

# Static files for uploads with cache
class CachedStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if isinstance(response, Response):
            if path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.webp')):
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            elif path.endswith('.html'):
                response.headers['Cache-Control'] = 'public, max-age=3600'
            else:
                response.headers['Cache-Control'] = 'public, max-age=86400'
        return response

# Note: sucai images are now served via API route /api/sucai/{filename}
# Static file mount removed to avoid conflicts with API routes

# Static files for uploads
app.mount("/WutheringWavesDPS/uploads", CachedStaticFiles(directory=settings.upload_dir), name="uploads")

# Static files for frontend assets with cache
if FRONTEND_DIST.exists():
    app.mount("/WutheringWavesDPS/assets", CachedStaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

# Routers - mount with prefix
from app.api import auth, spreadsheets, stars, categories, uploads, admin, health, characters, images, announcements, visit_stats, sucai  # noqa: E402

app.include_router(auth.router, prefix="/WutheringWavesDPS")
app.include_router(spreadsheets.router, prefix="/WutheringWavesDPS")
app.include_router(stars.router, prefix="/WutheringWavesDPS")
app.include_router(categories.router, prefix="/WutheringWavesDPS")
app.include_router(uploads.router, prefix="/WutheringWavesDPS")
app.include_router(images.router, prefix="/WutheringWavesDPS")
app.include_router(admin.router, prefix="/WutheringWavesDPS")
app.include_router(health.router, prefix="/WutheringWavesDPS")
app.include_router(characters.router, prefix="/WutheringWavesDPS")
app.include_router(announcements.router, prefix="/WutheringWavesDPS")
app.include_router(visit_stats.router, prefix="/WutheringWavesDPS")
app.include_router(sucai.router, prefix="/WutheringWavesDPS")

# Health check endpoint
@app.get("/WutheringWavesDPS/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}

# Frontend SPA catch-all route - MUST be last
@app.get("/WutheringWavesDPS/{path:path}")
async def serve_frontend(path: str):
    """Serve frontend SPA and handle client-side routing"""
    if path.startswith("api/"):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content={"detail": "API endpoint not found"}
        )
    
    if FRONTEND_DIST.exists():
        # 首先检查是否是具体的静态文件
        file_path = FRONTEND_DIST / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        # 如果不是静态文件，返回 index.html 给 SPA 处理路由
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    
    return {
        "message": "Welcome to WutheringWavesDPS API",
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/WutheringWavesDPS/docs"
    }

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


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=settings.app_port,
        reload=settings.app_debug
    )
