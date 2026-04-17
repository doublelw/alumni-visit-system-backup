#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信云托管部署准备脚本
使用方法: python deployment_scripts/deploy_to_welife.py
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
os.chdir(project_root)

class Colors:
    """终端颜色"""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def log_info(msg):
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {msg}")

def log_warn(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def log_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

def log_step(msg):
    print(f"{Colors.BLUE}[STEP]{Colors.NC} {msg}")

def log_success(msg):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")

def show_banner():
    print(f"{Colors.CYAN}")
    print("=" * 60)
    print("校友入校登记系统 - 微信云托管部署准备")
    print("=" * 60)
    print(f"{Colors.NC}")
    print()

def check_required_files():
    """检查必要文件"""
    log_step("检查必要文件...")

    required_files = [
        "main.py",
        "wsgi.py",
        "Dockerfile",
        "requirements.txt",
        "backend/app/__init__.py",
        "backend/app/config.py",
        "frontend/templates",
        "frontend/static"
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        log_error("缺少必要的文件:")
        for file in missing_files:
            print(f"  - {file}")
        sys.exit(1)

    log_success("所有必要文件检查通过")

def clean_build_dir():
    """清理构建目录"""
    log_step("清理构建目录...")

    build_dir = Path("build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    build_dir.mkdir()
    log_success("构建目录已清理")

def copy_project_files():
    """复制项目文件"""
    log_step("复制项目文件...")

    build_dir = Path("build")

    # 核心文件
    files_to_copy = [
        "main.py",
        "wsgi.py",
        "requirements.txt",
        "Dockerfile",
        ".dockerignore"
    ]

    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy2(file, build_dir / file)

    # 复制backend目录
    if Path("backend").exists():
        shutil.copytree("backend", build_dir / "backend",
                       ignore=shutil.ignore_patterns(
                           "*__pycache__*",
                           "*.pyc",
                           "*.pyo",
                           "*.pyd",
                           ".pytest_cache",
                           "test_*.py",
                           "*_test.py"
                       ))

    # 复制frontend目录
    if Path("frontend").exists():
        shutil.copytree("frontend", build_dir / "frontend",
                       ignore=shutil.ignore_patterns(
                           "node_modules",
                           ".DS_Store"
                       ))

    # 复制环境变量文件
    if Path(".env.welife").exists():
        shutil.copy2(".env.welife", build_dir / ".env")
        log_info("已复制环境变量配置")
    else:
        log_warn("未找到.env.welife文件")

    # 创建必要目录
    (build_dir / "uploads").mkdir(exist_ok=True)
    (build_dir / "logs").mkdir(exist_ok=True)
    (build_dir / "instance").mkdir(exist_ok=True)

    log_success("项目文件复制完成")

def cleanup_unnecessary_files():
    """清理不需要的文件"""
    log_step("清理不需要的文件...")

    build_dir = Path("build")

    # 删除测试文件
    for pattern in ["*_test.py", "test_*.py", "*.pyc", "*.pyo", "*.pyd"]:
        for file in build_dir.rglob(pattern):
            file.unlink(missing_ok=True)

    # 删除缓存目录
    for dir_name in ["__pycache__", ".pytest_cache", ".pytest_cache"]:
        for dir_path in build_dir.rglob(dir_name):
            if dir_path.is_dir():
                shutil.rmtree(dir_path, ignore_errors=True)

    # 删除数据库文件
    for ext in ["*.db", "*.db-journal", "*.sqlite", "*.sqlite3"]:
        for file in build_dir.rglob(ext):
            file.unlink(missing_ok=True)

    # 删除其他不需要的文件
    for file in build_dir.rglob(".DS_Store"):
        file.unlink(missing_ok=True)

    log_success("清理完成")

def create_package():
    """创建部署包"""
    log_step("创建部署包...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"welife_deploy_package_{timestamp}.zip"

    build_dir = Path("build")

    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            # 过滤掉不需要的目录
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]

            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(build_dir)
                zipf.write(file_path, arcname)

    # 获取文件大小
    size = package_name
    log_success(f"部署包创建完成: {package_name}")

    return package_name

def show_deployment_guide(package_name):
    """显示部署指引"""
    print()
    print("=" * 60)
    print("部署准备完成")
    print("=" * 60)
    print()
    print(f"📦 部署包: {package_name}")
    print()
    print("下一步操作:")
    print("  1. 登录微信公众平台: https://mp.weixin.qq.com/")
    print("  2. 进入 '开发' → '云托管' → '新建服务'")
    print(f"  3. 上传部署包: {package_name}")
    print("  4. 配置环境变量（参考 QUICK_START_WELIFE.md）")
    print("  5. 启动服务")
    print()
    print("详细说明请查看: WELIFE_DEPLOYMENT_SUMMARY.md")
    print()

def main():
    """主函数"""
    try:
        # 显示横幅
        show_banner()

        # 执行部署步骤
        log_step("开始准备微信云托管部署包...")
        print()

        check_required_files()
        clean_build_dir()
        copy_project_files()
        cleanup_unnecessary_files()
        package_name = create_package()

        # 显示部署指引
        show_deployment_guide(package_name)

        log_success("✅ 部署包准备完成！")

    except KeyboardInterrupt:
        print()
        log_warn("部署已取消")
        sys.exit(1)
    except Exception as e:
        print()
        log_error(f"部署失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
