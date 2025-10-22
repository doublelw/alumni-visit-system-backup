#!/bin/bash

# 校友入校登记系统服务器安装脚本
# 运行命令: bash server_setup.sh

echo "============================================"
echo "校友入校登记系统 - 服务器环境配置"
echo "============================================"

# 更新系统
echo "正在更新系统包..."
apt update && apt upgrade -y

# 安装基础软件包
echo "正在安装基础软件包..."
apt install -y curl wget git unzip software-properties-common

# 安装Nginx
echo "正在安装Nginx..."
apt install -y nginx

# 安装Python 3.11和相关工具
echo "正在安装Python 3.11..."
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 安装MySQL
echo "正在安装MySQL..."
apt install -y mysql-server
systemctl start mysql
systemctl enable mysql

# 安装Redis
echo "正在安装Redis..."
apt install -y redis-server
systemctl start redis-server
systemctl enable redis-server

# 创建应用目录
echo "正在创建应用目录..."
mkdir -p /var/www/lsalumni
mkdir -p /var/log/lsalumni
mkdir -p /etc/ssl/certs
mkdir -p /etc/ssl/private

# 创建虚拟环境
echo "正在创建Python虚拟环境..."
python3.11 -m venv /var/www/lsalumni/venv
source /var/www/lsalumni/venv/bin/activate
pip install --upgrade pip

# 设置目录权限
echo "正在设置目录权限..."
chown -R www-data:www-data /var/www/lsalumni
chown -R www-data:www-data /var/log/lsalumni

# 配置MySQL安全设置
echo "请运行 mysql_secure_installation 进行MySQL安全配置"
echo "然后创建数据库: CREATE DATABASE lsalumni CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 配置防火墙
echo "正在配置防火墙..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "============================================"
echo "基础环境安装完成!"
echo "============================================"
echo "下一步："
echo "1. 配置MySQL数据库"
echo "2. 上传应用文件到 /var/www/lsalumni"
echo "3. 安装Python依赖: pip install -r requirements_prod.txt"
echo "4. 配置Nginx"
echo "5. 配置SSL证书"
echo "6. 启动应用服务"
echo "============================================"