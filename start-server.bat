@echo off
cd /d "%~dp0backend"

echo Starting server...
echo URL: http://localhost:5000
echo Press Ctrl+C to stop
echo.

python scripts/run.py

pause
