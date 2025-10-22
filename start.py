#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校友入校登记系统启动脚本
支持开发和生产环境切换
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        sys.exit(1)
    print(f"Python版本: {sys.version}")

def install_dependencies():
    """安装依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])
        print("依赖包安装完成")
    except subprocess.CalledProcessError as e:
        print(f"依赖包安装失败: {e}")
        sys.exit(1)

def generate_self_signed_cert():
    """生成自签名证书用于开发环境HTTPS"""
    # 暂时禁用证书生成以强制使用HTTP模式
    print("开发环境跳过SSL证书生成，使用HTTP模式")
    return

def check_mysql_config():
    """检查MySQL配置"""
    mysql_uri = os.environ.get('DATABASE_URL')
    if not mysql_uri:
        print("警告: 生产环境需要配置MySQL数据库")
        print("请设置环境变量 DATABASE_URL，格式如下:")
        print("mysql://username:password@host:port/database_name")
        return False
    return True

def init_database(dev_mode=True):
    """初始化数据库"""
    print(f"正在初始化{'开发' if dev_mode else '生产'}环境数据库...")

    # 设置环境变量
    os.environ["FLASK_ENV"] = "development" if dev_mode else "production"

    # 对于生产环境，检查MySQL配置
    if not dev_mode:
        if not check_mysql_config():
            print("MySQL配置检查失败，将使用SQLite数据库")
            os.environ["DATABASE_URL"] = "sqlite:///alumni_system_prod.db"

    try:
        # 切换到backend目录
        os.chdir("backend")

        # 初始化数据库
        subprocess.check_call([sys.executable, "-c", """
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath('.'))))

from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print("数据库初始化完成")
"""])

        os.chdir("..")

    except subprocess.CalledProcessError as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)

def start_server(dev_mode=True):
    """启动服务器"""
    print(f"正在启动{'开发' if dev_mode else '生产'}环境服务器...")

    if dev_mode:
        # 开发环境
        os.environ["FLASK_ENV"] = "development"
        os.environ["FLASK_DEBUG"] = "1"

        # 启动Flask开发服务器
        os.chdir("backend")

        # 检查证书是否存在
        cert_path = "../config/certificates/localhost.crt"
        key_path = "../config/certificates/localhost.key"

        if os.path.exists(cert_path) and os.path.exists(key_path):
            # 使用HTTPS
            subprocess.call([
                sys.executable, "-m", "flask",
                "run",
                "--host=0.0.0.0",
                "--port=5000",
                "--cert=" + cert_path,
                "--key=" + key_path
            ])
        else:
            # 使用HTTP（开发环境）
            print("警告: SSL证书不存在，使用HTTP模式启动")
            print("请在浏览器中访问 http://localhost:5000")
            subprocess.call([
                sys.executable, "-m", "flask",
                "run",
                "--host=0.0.0.0",
                "--port=5000"
            ])
    else:
        # 生产环境
        os.environ["FLASK_ENV"] = "production"

        # 检查MySQL配置
        if not check_mysql_config():
            print("警告: 未配置MySQL，将使用SQLite数据库")
            os.environ["DATABASE_URL"] = "sqlite:///alumni_system_prod.db"

        # 切换到backend目录
        os.chdir("backend")

        # 检查SSL证书
        cert_path = "../config/certificates/server.crt"
        key_path = "../config/certificates/server.key"

        # 尝试使用Gunicorn启动
        try:
            print("正在尝试使用Gunicorn启动生产服务器...")
            if os.path.exists(cert_path) and os.path.exists(key_path):
                # 使用HTTPS启动
                subprocess.call([
                    "gunicorn",
                    "--bind", "0.0.0.0:5000",
                    "--workers", "4",
                    "--keyfile", key_path,
                    "--certfile", cert_path,
                    "run:app"
                ])
            else:
                # 使用HTTP启动（需要反向代理处理HTTPS）
                print("警告: 生产环境SSL证书不存在，使用HTTP模式启动")
                print("建议配置Nginx等反向代理处理HTTPS")
                subprocess.call([
                    "gunicorn",
                    "--bind", "0.0.0.0:5000",
                    "--workers", "4",
                    "run:app"
                ])
        except FileNotFoundError:
            print("Gunicorn未安装，正在使用Flask内置服务器启动...")
            print("警告: Flask内置服务器不适合生产环境，请安装Gunicorn: pip install gunicorn")
            # 回退到Flask内置服务器
            if os.path.exists(cert_path) and os.path.exists(key_path):
                subprocess.call([
                    sys.executable, "-m", "flask",
                    "run",
                    "--host=0.0.0.0",
                    "--port=5000",
                    "--cert=" + cert_path,
                    "--key=" + key_path
                ])
            else:
                print("警告: 使用HTTP模式启动生产环境")
                subprocess.call([
                    sys.executable, "-m", "flask",
                    "run",
                    "--host=0.0.0.0",
                    "--port=5000"
                ])

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python start.py dev     # 启动开发环境")
        print("  python start.py prod    # 启动生产环境")
        print("  python start.py init    # 仅初始化项目")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "init":
        check_python_version()
        install_dependencies()
        generate_self_signed_cert()
        init_database(dev_mode=True)
        print("项目初始化完成！")

    elif command == "dev":
        check_python_version()
        install_dependencies()
        generate_self_signed_cert()
        init_database(dev_mode=True)
        start_server(dev_mode=True)

    elif command == "prod":
        check_python_version()
        init_database(dev_mode=False)
        start_server(dev_mode=False)

    else:
        print(f"未知命令: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()