@echo off
cd /d "%~dp0backend"

echo ============================================================
echo School Visit Management System - Quick Start
echo ============================================================
echo.

echo [1/3] Database Migration...
echo ------------------------------------------------------------
python scripts/migrate_database.py
if %errorlevel% neq 0 (
    echo [ERROR] Database migration failed!
    pause
    exit /b 1
)
echo.

echo [2/3] Create Teacher Accounts...
echo ------------------------------------------------------------
python scripts/create_teacher_accounts.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create teacher accounts!
    pause
    exit /b 1
)
echo.

echo [3/3] Starting Server...
echo ------------------------------------------------------------
echo Starting server at http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python scripts/run.py

pause
