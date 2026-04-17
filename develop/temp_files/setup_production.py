#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境配置脚本
帮助配置MySQL数据库和环境变量
"""

import os
import sys
import subprocess
from pathlib import Path

def create_env_file():
    """创建环境变量文件"""
    env_file = Path(".env")

    if env_file.exists():
        print(".env文件已存在")
        return

    print("正在创建生产环境配置文件...")

    env_content = """# 生产环境配置
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production

# MySQL数据库配置
# 请根据您的MySQL配置修改以下信息
DATABASE_URL=mysql://username:password@localhost:3306/alumni_system

# 可选: SSL证书路径
SSL_CERT=/etc/ssl/certs/alumni_system.crt
SSL_KEY=/etc/ssl/private/alumni_system.key
"""

    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)

    print(f"已创建 .env 配置文件")
    print("请编辑 .env 文件，设置您的MySQL数据库连接信息")

def install_production_dependencies():
    """安装生产环境依赖"""
    print("正在安装生产环境依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gunicorn", "pyOpenSSL"])
        print("生产环境依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e}")

def create_mysql_setup_script():
    """创建MySQL数据库设置脚本"""
    mysql_script = """-- 校友入校登记系统MySQL数据库设置脚本
-- 请在MySQL中执行此脚本来创建数据库和用户

-- 创建数据库
CREATE DATABASE IF NOT EXISTS alumni_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建专用用户（推荐）
CREATE USER IF NOT EXISTS 'alumni_user'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON alumni_system.* TO 'alumni_user'@'localhost';
FLUSH PRIVILEGES;

-- 显示创建的数据库
SHOW DATABASES LIKE 'alumni_system';

-- 显示用户权限
SHOW GRANTS FOR 'alumni_user'@'localhost';
"""

    script_path = Path("setup_mysql.sql")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(mysql_script)

    print(f"已创建 MySQL 设置脚本: {script_path}")
    print("请在MySQL中执行此脚本来创建数据库")

def main():
    """主函数"""
    print("=== 校友入校登记系统生产环境配置 ===")
    print()

    while True:
        print("请选择操作:")
        print("1. 创建 .env 配置文件")
        print("2. 安装生产环境依赖")
        print("3. 创建MySQL数据库设置脚本")
        print("4. 显示配置说明")
        print("0. 退出")
        print()

        choice = input("请输入选项 (0-4): ").strip()

        if choice == "1":
            create_env_file()
        elif choice == "2":
            install_production_dependencies()
        elif choice == "3":
            create_mysql_setup_script()
        elif choice == "4":
            show_configuration_guide()
        elif choice == "0":
            print("配置完成")
            break
        else:
            print("无效选项，请重新选择")
        print()

def show_configuration_guide():
    """显示配置说明"""
    print("""
=== 生产环境配置说明 ===

1. MySQL数据库设置:
   - 安装MySQL服务器
   - 执行 setup_mysql.sql 脚本创建数据库
   - 修改 .env 文件中的数据库连接信息

2. SSL证书配置:
   - 获取SSL证书（Let's Encrypt或自签名）
   - 将证书文件放到指定路径
   - 更新 .env 文件中的证书路径

3. 环境变量设置:
   - 复制 .env 文件并根据实际环境修改
   - 设置强密码和密钥

4. 启动生产环境:
   python start.py prod

5. 推荐部署配置:
   - 使用Nginx作为反向代理
   - 配置HTTPS和静态文件服务
   - 使用systemd管理服务进程

配置完成后，系统将自动使用MySQL数据库和HTTPS协议。
""")

if __name__ == "__main__":
    main()