@echo off
chcp 65001 >nul
title 校友入校登记系统 - 服务器管理

echo.
echo ========================================
echo   校友入校登记系统 - 服务器管理工具
echo ========================================
echo.

:menu
echo 请选择操作:
echo 1. 启动服务器 (开发模式)
echo 2. 启动服务器 (生产模式)
echo 3. 重启服务器
echo 4. 停止服务器
echo 5. 查看服务器状态
echo 6. 安装项目依赖
echo 7. 强制停止所有服务器
echo 0. 退出
echo.
set /p choice=请输入选项 (0-7):

if "%choice%"=="1" goto start_dev
if "%choice%"=="2" goto start_prod
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto stop
if "%choice%"=="5" goto status
if "%choice%"=="6" goto install
if "%choice%"=="7" goto force_stop
if "%choice%"=="0" goto exit
echo 无效选项，请重新选择！
goto menu

:start_dev
echo.
echo 正在启动服务器 (开发模式)...
python server_manager.py start --debug --env development
goto menu

:start_prod
echo.
echo 正在启动服务器 (生产模式)...
python server_manager.py start --env production
goto menu

:restart
echo.
echo 正在重启服务器...
python server_manager.py restart --debug
goto menu

:stop
echo.
echo 正在停止服务器...
python server_manager.py stop
pause
goto menu

:status
echo.
echo 正在检查服务器状态...
python server_manager.py status
pause
goto menu

:install
echo.
echo 正在安装项目依赖...
python server_manager.py install
pause
goto menu

:force_stop
echo.
echo 正在强制停止所有服务器...
python server_manager.py stop --force
pause
goto menu

:exit
echo.
echo 感谢使用！
pause
exit