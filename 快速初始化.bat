@echo off
REM 校友入校登记系统 - 快速初始化脚本
REM 使用方法: 双击运行此脚本

echo ============================================================
echo 校友入校登记系统 - 快速初始化
echo ============================================================
echo.

cd /d "%~dp0backend"

echo [1/3] 数据库迁移...
echo ------------------------------------------------------------
python scripts/migrate_database.py
if %errorlevel% neq 0 (
    echo [错误] 数据库迁移失败！
    pause
    exit /b 1
)
echo.

echo [2/3] 创建教师账户...
echo ------------------------------------------------------------
python scripts/create_teacher_accounts.py
if %errorlevel% neq 0 (
    echo [错误] 创建教师账户失败！
    pause
    exit /b 1
)
echo.

echo [3/3] 启动系统...
echo ------------------------------------------------------------
echo 正在启动服务器...
echo 访问地址: http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务器
echo.

python scripts/run.py

pause
