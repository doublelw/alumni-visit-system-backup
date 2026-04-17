@echo off
REM 校友入校登记系统 - 启动服务器
REM 使用方法: 双击运行此脚本

echo ============================================================
echo 校友入校登记系统 - 启动服务器
echo ============================================================
echo.

cd /d "%~dp0backend"

echo 正在启动服务器...
echo 访问地址: http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务器
echo.

python scripts/run.py

pause
