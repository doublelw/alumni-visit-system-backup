#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
准备上传文件脚本
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_upload_package():
    """创建上传包"""

    # 定义源目录和目标目录
    project_root = Path(__file__).parent
    upload_dir = project_root / "upload_package"

    # 清理之前的上传包
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    upload_dir.mkdir()

    print("正在创建上传包...")

    # 需要复制的文件和目录
    files_to_copy = [
        "backend",
        "frontend",
        "run.py",
        "requirements_prod.txt",
        "gunicorn_config.py",
        "nginx_config.conf",
        "systemd_service.service",
        "server_setup.sh",
        "deploy.sh",
        "README_DEPLOYMENT.md"
    ]

    # 复制文件
    for item in files_to_copy:
        src = project_root / item
        dst = upload_dir / item

        if src.exists():
            if src.is_dir():
                shutil.copytree(src, dst)
                print(f"OK 复制目录: {item}")
            else:
                shutil.copy2(src, dst)
                print(f"OK 复制文件: {item}")
        else:
            print(f"ERROR 文件不存在: {item}")

    # 创建需要排除的测试和临时文件列表
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        ".pytest_cache",
        "*.log",
        "node_modules",
        ".env",
        "uploads",
        "*.db",
        "*.sqlite",
        ".git",
        ".idea",
        "*.swp",
        "*.tmp"
    ]

    # 清理不需要的文件
    print("\n正在清理不需要的文件...")
    for root, dirs, files in os.walk(upload_dir):
        # 移除匹配的目录
        dirs[:] = [d for d in dirs if not any(d.endswith(pattern.split('*')[-1]) for pattern in exclude_patterns if pattern.startswith('*'))]

        # 移除匹配的文件
        for file in files:
            file_path = os.path.join(root, file)
            for pattern in exclude_patterns:
                if pattern.startswith('*') and file.endswith(pattern[1:]):
                    os.remove(file_path)
                    print(f"DELETE 删除文件: {file_path}")
                    break
                elif pattern in file:
                    os.remove(file_path)
                    print(f"DELETE 删除文件: {file_path}")
                    break

    # 创建上传目录
    uploads_dir = upload_dir / "uploads"
    uploads_dir.mkdir()
    print("OK 创建上传目录: uploads")

    # 创建版本信息文件
    version_info = f"""# 校友入校登记系统部署包
# 创建时间: {shutil.os.times()}
# 目标服务器: 8.152.209.82
# 部署路径: /var/www/lsalumni
# 域名: www.pofeclife.top

## 文件清单:
"""

    for item in files_to_copy:
        if (project_root / item).exists():
            version_info += f"- {item}\n"

    with open(upload_dir / "UPLOAD_INFO.txt", "w", encoding="utf-8") as f:
        f.write(version_info)

    print("OK 创建版本信息文件")

    # 创建ZIP压缩包
    zip_path = project_root / "lsalumni_deploy_package.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, upload_dir)
                zipf.write(file_path, arcname)

    print(f"\nSUCCESS 上传包创建完成!")
    print(f"解压目录: {upload_dir}")
    print(f"压缩包: {zip_path}")
    print(f"总大小: {sum(f.stat().st_size for f in upload_dir.rglob('*') if f.is_file()) / 1024 / 1024:.2f} MB")

    # 显示部署指令
    print(f"\nINFO 部署指令:")
    print(f"1. 将 upload_package 目录或 lsalumni_deploy_package.zip 上传到服务器")
    print(f"2. 在服务器上运行以下命令:")
    print(f"   cd /var/www/")
    print(f"   # 如果上传的是ZIP文件:")
    print(f"   unzip lsalumni_deploy_package.zip")
    print(f"   mv upload_package lsalumni")
    print(f"   # 如果上传的是目录:")
    print(f"   # 直接复制到 /var/www/lsalumni")
    print(f"   cd lsalumni")
    print(f"   bash server_setup.sh")
    print(f"   bash deploy.sh")

if __name__ == "__main__":
    create_upload_package()