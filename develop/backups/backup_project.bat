@echo off
REM 校园访问管理系统 - 备份脚本
REM 使用方法：双击运行此脚本

setlocal

echo ========================================
echo 校园访问管理系统 - 项目备份
echo ========================================
echo.

REM 设置项目路径
set PROJECT_DIR=D:\Project\校友入校登记
set BACKUP_DIR=%PROJECT_DIR%\backups
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

REM 创建备份目录
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
)

echo 正在备份项目...
echo 备份路径: %BACKUP_DIR%
echo 时间戳: %TIMESTAMP%
echo.

REM 切换到项目目录
cd /d "%PROJECT_DIR%"

REM 创建备份文件
echo 正在创建备份文件...
tar -czf "%BACKUP_DIR%\backup_%TIMESTAMP%.tar.gz" ^
    --exclude='__pycache__' ^
    --exclude='*.pyc' ^
    --exclude='.git' ^
    --exclude='node_modules' ^
    --exclude='backups' ^
    --exclude='*.db' ^
    --exclude='instance' ^
    --exclude='backup_*.tar.gz' ^
    . 2>nul

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 备份成功！
    echo ========================================
    echo.
    echo 备份文件: %BACKUP_DIR%\backup_%TIMESTAMP%.tar.gz
    echo.

    REM 显示备份文件大小
    for %%A in ("%BACKUP_DIR%\backup_%TIMESTAMP%.tar.gz") do (
        echo 文件大小: %%~zA 字节
    )

    echo.
    echo 恢复方法：
    echo   tar -xzf backup_%TIMESTAMP%.tar.gz
    echo.

) else (
    echo.
    echo ========================================
    echo 备份失败！
    echo ========================================
    echo.
    echo 请检查：
    echo   1. 是否安装了tar工具（Git Bash或WSL）
    echo   2. 项目路径是否正确
    echo   3. 磁盘空间是否充足
    echo.
)

pause
