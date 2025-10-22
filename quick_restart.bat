@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   校友入校登记系统 - 快速重启
echo ========================================
echo.

echo 正在重启Flask服务器...
python server_manager.py restart --debug --force --app-dir backend

echo.
echo ========================================
echo           服务器启动成功！
echo ========================================
echo.
echo 📱 访问地址（复制到浏览器）:
echo    http://127.0.0.1:5000
echo    http://localhost:5000
echo.
echo ⚠️  重要提示:
echo    • 请确保使用 http:// (不是 https://)
echo    • 如果遇到SSL错误，请查看 SSL错误解决指南.md
echo.
echo 📁 日志位置: backend\logs\
echo 📝 测试连接: python test_connection.py
echo.
echo 现在可以打开浏览器访问应用了！
echo.
pause