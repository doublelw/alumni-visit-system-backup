@echo off
REM Auto Navigate to WeChat Cloud Hosting
REM Usage: Double click to run

echo ============================================================
echo WeChat Cloud Hosting - Auto Navigation
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/2] Checking Python...
python --version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python first: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python is available
echo.

echo [2/2] Starting navigation assistant...
python deployment_scripts/auto_navigate_wechat_cloud.py

echo.
pause
