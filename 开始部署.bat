@echo off
chcp 65001 >nul
cls
echo ==========================================
echo   校友入校登记系统 - 开始部署
echo   (纯本地版本，无需AI接口)
echo ==========================================
echo.

echo [检查] 部署包...
if exist "welife_deploy_package_20260406_191348.zip" (
    echo [OK] 部署包已准备
) else (
    echo [ERROR] 部署包不存在
    echo        请运行: python deployment_scripts/deploy_to_welife.py
    pause
    exit /b 1
)
echo.

echo [检查] 配置文件...
if exist "部署配置-微信云托管.txt" (
    echo [OK] 配置文件已准备
) else (
    echo [ERROR] 配置文件不存在
    pause
    exit /b 1
)
echo.

echo [检查] 部署指南...
if exist "纯本地部署-最终状态报告.txt" (
    echo [OK] 部署指南已准备
) else (
    echo [WARN] 部署指南缺失
)
echo.

echo ==========================================
echo   状态: 所有文件已就绪，可以开始部署
echo ==========================================
echo.
echo 正在打开必要文件...
echo.

if exist "部署配置-微信云托管.txt" (
    start notepad "部署配置-微信云托管.txt"
    echo [OK] 已打开配置文件
)

timeout /t 2 >nul

echo.
echo [INFO] 正在打开微信云托管控制台...
timeout /t 2 >nul
start https://cloud.weixin.qq.com/cloudrun/service
echo [OK] 已打开微信云托管控制台
echo.

echo ==========================================
echo   下一步操作:
echo ==========================================
echo.
echo 1. 在已打开的配置文件中复制环境变量
echo.
echo 2. 在微信云托管控制台:
echo    - 点击 "新建服务"
echo    - 上传部署包: welife_deploy_package_20260406_191348.zip
echo    - 粘贴环境变量配置
echo    - 开始部署
echo.
echo 3. 详细步骤请查看配置文件
echo.
echo ==========================================
echo   提示: 如需查看完整部署指南
echo         请查看: 纯本地部署-最终状态报告.txt
echo ==========================================
echo.
pause
