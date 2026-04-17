@echo off
REM Find WeChat Cloud Entry Point
REM Usage: Double click to run

echo ============================================================
echo WeChat Cloud - Find Entry Point Assistant
echo ============================================================
echo.

cd /d "%~dp0"

python deployment_scripts/wechat_cloud_locator.py

echo.
pause
