@echo off
echo 正在停止Flask服务器...
echo 请在运行Flask的窗口按 Ctrl+C 停止服务器
echo.
timeout /t 3
echo.
echo 正在启动新的Flask服务器...
cd /d "%~dp0backend"
python run.py
