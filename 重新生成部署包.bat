@echo off
chcp 65001 >nul
cls
echo ==========================================
echo   重新生成部署包（修复镜像源问题）
echo ==========================================
echo.

echo [修复] Dockerfile镜像源问题...
echo [说明] 清华镜像源403错误，已更换为官方源+阿里云源
echo.

echo [1/2] 重新生成部署包...
cd /d "D:\Project\校友入校登记"
python deployment_scripts\deploy_to_welife.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] 部署包生成失败
    pause
    exit /b 1
)

echo.
echo [2/2] 部署包生成完成！
echo.
echo ==========================================
echo   下一步操作
echo ==========================================
echo.
echo 1. 在微信云托管控制台:
echo    - 删除当前的失败部署
echo    - 重新上传新的部署包
echo.
echo 2. 新部署包名称中会包含当前时间戳
echo.
echo 3. 如果仍然失败，请查看日志并联系我
echo.
pause
