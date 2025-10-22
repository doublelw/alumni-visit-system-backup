@echo off
chcp 65001 >nul
echo ============================================
echo 校友入校登记系统 - 快速部署脚本
echo ============================================
echo.

set SERVER_IP=8.146.210.18
set SERVER_USER=root
set SERVER_PASSWORD=Sy6787687.
set DEPLOY_PATH=/var/www/lsalumni

echo 服务器信息:
echo IP: %SERVER_IP%
echo 用户: %SERVER_USER%
echo 部署路径: %DEPLOY_PATH%
echo.

echo 请确保您已安装以下工具之一:
echo 1. WinSCP (推荐)
echo 2. FileZilla
echo 3. 其他SFTP客户端
echo.

echo 手动部署步骤:
echo 1. 使用SFTP工具连接到服务器
echo    - 主机: %SERVER_IP%
echo    - 用户名: %SERVER_USER%
echo    - 密码: %SERVER_PASSWORD%
echo    - 端口: 22
echo.
echo 2. 上传文件
echo    - 将 upload_package 目录上传到 %DEPLOY_PATH%
echo.
echo 3. SSH连接并运行部署脚本
echo    ssh %SERVER_USER%@%SERVER_IP%
echo    cd %DEPLOY_PATH%
echo    bash server_setup.sh
echo    bash deploy.sh
echo.

echo 按任意键打开部署指南文档...
pause >nul

start "" "D:\Project\校友入校登记\MANUAL_DEPLOYMENT_GUIDE.md"

echo.
echo 部署指南已打开!
echo 完成文件上传后，我可以帮您继续配置服务器。
echo.
pause