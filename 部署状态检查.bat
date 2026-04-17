@echo off
chcp 65001 >nul
cls
echo ==========================================
echo   校友入校登记系统 - 部署状态检查
echo   (纯本地版本，无需AI接口)
echo ==========================================
echo.

echo [检查] 部署包...
if exist "welife_deploy_package_20260406_191348.zip" (
    echo [OK] 部署包已准备
    echo      文件: welife_deploy_package_20260406_191348.zip
    echo      大小: 约4.4 MB
) else (
    echo [FAIL] 部署包不存在
    goto :error
)
echo.

echo [检查] 配置文件...
if exist "部署配置-微信云托管.txt" (
    echo [OK] 配置文件已生成
) else (
    echo [FAIL] 配置文件缺失
    goto :error
)
echo.

echo [检查] 部署指南...
if exist "部署准备完成报告.txt" (
    echo [OK] 部署指南已准备
) else (
    echo [WARN] 部署指南缺失
)
echo.

echo ==========================================
echo   状态: 所有准备文件已就绪
echo ==========================================
echo.
echo 下一步操作:
echo.
echo 1. 双击运行: 打开配置文件.bat
echo 2. 在微信云托管控制台执行部署
echo.
echo 按任意键打开配置文件...
pause >nul

if exist "部署配置-微信云托管.txt" (
    start notepad "部署配置-微信云托管.txt"
    echo.
    echo [OK] 已打开配置文件
)

echo.
echo 按任意键打开微信云托管控制台...
pause >nul

start https://cloud.weixin.qq.com/cloudrun/service
echo.
echo [OK] 已打开微信云托管控制台
echo.
goto :end

:error
echo.
echo [ERROR] 检查失败，请重新运行部署准备脚本
echo.
pause
exit /b 1

:end
echo 所有准备工作已完成，请查看已打开的文件和页面。
echo.
pause
