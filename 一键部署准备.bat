@echo off
chcp 65001 >nul
echo ==========================================
echo   校友入校登记系统 - 微信云托管部署助手
echo ==========================================
echo.

echo [1/5] 检查部署包...
if exist "welife_deploy_package_20260406_191348.zip" (
    echo ✅ 部署包已存在: welife_deploy_package_20260406_191348.zip
    for %%A in ("welife_deploy_package_20260406_191348.zip") do echo    文件大小: %%~zA 字节
) else (
    echo ❌ 部署包不存在，正在重新生成...
    python deployment_scripts\deploy_to_welife.py
)
echo.

echo [2/5] 检查配置文件...
if exist "部署配置-微信云托管.txt" (
    echo ✅ 配置文件已生成
) else (
    echo ❌ 配置文件缺失
)
echo.

echo [3/5] 打开部署配置文件...
start notepad "部署配置-微信云托管.txt"
echo ✅ 已打开配置文件
echo.

echo [4/5] 准备部署环境...
echo 📦 部署包位置: %CD%\welife_deploy_package_20260406_191348.zip
echo 📋 配置文件位置: %CD%\部署配置-微信云托管.txt
echo.

echo [5/5] 打开微信云托管控制台...
echo ⏳ 正在打开浏览器...
timeout /t 2 >nul
start https://cloud.weixin.qq.com/cloudrun/service
echo ✅ 已打开微信云托管控制台
echo.

echo ==========================================
echo   准备工作完成！
echo ==========================================
echo.
echo 📋 下一步操作:
echo.
echo 1. 在已打开的配置文件中复制环境变量
echo 2. 在微信云托管控制台中:
echo    - 点击 "新建服务"
echo    - 上传部署包: welife_deploy_package_20260406_191348.zip
echo    - 粘贴环境变量配置
echo    - 开始部署
echo.
echo 💡 详细步骤请查看已打开的配置文件
echo.
pause
