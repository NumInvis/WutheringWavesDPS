@echo off
chcp 65001 >nul
echo ==========================================
echo    鸣潮动作数据汇总 - 启动脚本
echo ==========================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
pip show flask flask-cors sqlalchemy pandas openpyxl >nul 2>&1
if errorlevel 1 (
    echo [1/3] 安装依赖...
    pip install flask flask-cors sqlalchemy pandas openpyxl -q
)

echo [2/3] 检查数据库...
if not exist "wuwa_data.db" (
    echo [2/3] 数据库不存在，正在导入数据...
    python import_excel.py
    if errorlevel 1 (
        echo [错误] 数据导入失败，请检查Excel文件路径
        pause
        exit /b 1
    )
)

echo [3/3] 启动后端服务...
start "鸣潮API服务" python api.py

echo.
echo ==========================================
echo    服务已启动！
echo    API地址: http://localhost:12056
echo    按任意键打开浏览器...
echo ==========================================
pause >nul

start http://localhost:12056

echo.
echo 提示: 前端Vue项目需要单独启动
echo 进入 frontend 目录运行: npm install ^&^& npm run serve
echo 前端地址: http://localhost:13078
echo.
pause
