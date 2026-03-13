#!/usr/bin/env python3
"""
WutheringWavesDPS - Beta1.0
启动脚本
"""
import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

def create_directories():
    """创建必要的目录"""
    dirs = [
        BACKEND_DIR / "uploads",
        BACKEND_DIR / "excel_storage",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {d}")

def check_dependencies():
    """检查依赖"""
    print("\n检查依赖...")
    
    try:
        import fastapi
        print("  [OK] FastAPI")
    except ImportError:
        print("  [!] FastAPI 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
    
    try:
        import openpyxl
        print("  [OK] openpyxl")
    except ImportError:
        print("  [!] openpyxl 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "openpyxl"])
    
    try:
        import sqlalchemy
        print("  [OK] SQLAlchemy")
    except ImportError:
        print("  [!] SQLAlchemy 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "sqlalchemy"])

def start_backend():
    """启动后端服务器"""
    print("\n启动后端服务器...")
    os.chdir(BACKEND_DIR)
    
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "14876",
        "--reload"
    ]
    
    return subprocess.Popen(cmd, shell=True)

def start_frontend():
    """启动前端开发服务器"""
    print("\n启动前端开发服务器...")
    os.chdir(FRONTEND_DIR)
    
    if sys.platform == "win32":
        npm_cmd = "npm"
    else:
        npm_cmd = "npm"
    
    cmd = [npm_cmd, "run", "dev"]
    return subprocess.Popen(cmd, shell=True)

def main():
    print("=" * 50)
    print("  WutheringWavesDPS - Beta1.0")
    print("  鸣潮拉表社区平台")
    print("  Port: 14876")
    print("=" * 50)
    
    print("\n创建必要的目录...")
    create_directories()
    
    check_dependencies()
    
    backend_process = start_backend()
    
    print("\n等待后端服务器启动...")
    time.sleep(3)
    
    frontend_process = start_frontend()
    
    print("\n" + "=" * 50)
    print("  服务器启动成功!")
    print("  后端 API: http://localhost:14876")
    print("  前端页面: http://localhost:14876")
    print("  API 文档: http://localhost:14876/docs")
    print("=" * 50)
    
    print("\n按 Enter 打开网站...")
    input()
    webbrowser.open("http://localhost:14876")
    
    print("\n按 Ctrl+C 停止服务器...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        backend_process.terminate()
        frontend_process.terminate()
        print("服务器已停止")

if __name__ == "__main__":
    main()
