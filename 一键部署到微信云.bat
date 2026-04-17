@echo off
REM  Prepare WeChat Cloud Deployment Package
REM  Usage: Double click to run

echo ============================================================
echo Alumni System - WeChat Cloud Deployment
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/2] Checking Python...
python --version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo [OK] Python is available
echo.

echo [2/2] Running deployment script...
python deployment_scripts/deploy_to_welife.py

echo.
echo ============================================================
echo Deployment package created successfully
echo ============================================================
echo.
pause
