@echo off
echo ========================================
echo WutheringWavesDPS - Beta1.0
echo Starting server on port 14876
echo ========================================

cd /d "%~dp0backend"

echo Creating necessary directories...
if not exist "uploads" mkdir uploads
if not exist "excel_storage" mkdir excel_storage

echo Starting backend server...
start "WutheringWavesDPS Backend" cmd /k python -m uvicorn app.main:app --host 0.0.0.0 --port 14876 --reload

echo Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo Starting frontend development server...
cd /d "%~dp0frontend"
start "WutheringWavesDPS Frontend" cmd /k npm run dev

echo ========================================
echo Servers starting!
echo Backend API: http://localhost:14876
echo Frontend: http://localhost:14876
echo API Docs: http://localhost:14876/docs
echo ========================================

echo Press any key to open the website...
pause > nul
start http://localhost:14876
