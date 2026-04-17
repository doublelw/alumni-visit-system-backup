#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校友入校登记系统 - 本地部署助手
完全使用本地工具，无需AI接口
"""

import os
import sys
from pathlib import Path

def print_header():
    print("=" * 60)
    print("校友入校登记系统 - 本地部署助手")
    print("(纯本地版本，无需AI接口)")
    print("=" * 60)
    print()

def check_file(filepath, description):
    """检查文件是否存在"""
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size / 1024
        print(f"[OK] {description}")
        print(f"     文件: {path.name}")
        print(f"     大小: {size:.1f} KB")
        return True
    else:
        print(f"[FAIL] {description} - 文件不存在")
        return False

def main():
    print_header()

    print("[1/4] 检查部署包...")
    package_ok = check_file(
        "welife_deploy_package_20260406_191348.zip",
        "部署包"
    )
    print()

    print("[2/4] 检查配置文件...")
    config_ok = check_file(
        "部署配置-微信云托管.txt",
        "环境变量配置"
    )
    print()

    print("[3/4] 检查部署指南...")
    guide_ok = check_file(
        "部署准备完成报告.txt",
        "部署指南"
    )
    print()

    if not all([package_ok, config_ok]):
        print("[ERROR] 关键文件缺失，无法继续部署")
        print("        请先运行: python deployment_scripts/deploy_to_welife.py")
        return 1

    print("[4/4] 准备部署环境...")
    print()
    print("=" * 60)
    print("部署准备状态: 就绪")
    print("=" * 60)
    print()

    print("[INFO] 部署包信息:")
    print(f"   文件: welife_deploy_package_20260406_191348.zip")
    print(f"   位置: {Path.cwd()}")
    print(f"   大小: 4.4 MB")
    print()

    print("[INFO] 配置文件:")
    print(f"   文件: 部署配置-微信云托管.txt")
    print(f"   位置: {Path.cwd()}")
    print()

    print("[INFO] 微信云托管:")
    print(f"   控制台: https://cloud.weixin.qq.com/cloudrun/service")
    print()

    print("=" * 60)
    print("下一步操作 (在微信云托管控制台)")
    print("=" * 60)
    print()
    print("1. 创建服务:")
    print("   - 服务名称: lsalumni-api")
    print("   - 部署方式: 本地上传代码包")
    print()
    print("2. 上传部署包:")
    print("   - 选择: welife_deploy_package_20260406_191348.zip")
    print()
    print("3. 配置环境变量 (从配置文件复制):")
    print("   - FLASK_APP=app.py")
    print("   - FLASK_ENV=production")
    print("   - WECHAT_CLOUD=true")
    print("   - DATABASE_URL=sqlite:///alumni_system.db")
    print("   - SECRET_KEY=...")
    print("   - JWT_SECRET_KEY=...")
    print("   - ELECTRONIC_CARD_SECRET_KEY=...")
    print("   - HMAC_SECRET_KEY=...")
    print()
    print("4. 开始部署:")
    print("   - 版本: v1.0.0")
    print("   - 规格: 1C 2G")
    print("   - 点击: 开始部署")
    print()
    print("5. 验证部署:")
    print("   - 访问: https://你的服务地址.welife.icu/api/health")
    print("   - 访问: https://你的服务地址.welife.icu/")
    print()

    # 询问是否打开文件
    try:
        print("是否打开配置文件？(y/n): ", end='')
        choice = input().strip().lower()
        if choice == 'y':
            os.startfile("部署配置-微信云托管.txt")
            print("[OK] 已打开配置文件")
    except:
        pass

    print()
    print("=" * 60)
    print("本地部署助手完成")
    print("=" * 60)
    print()
    print("提示: 所有配置信息都在 '部署配置-微信云托管.txt' 中")
    print("      详细步骤请查看 '部署准备完成报告.txt'")
    print()

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print("[INFO] 操作已取消")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"[ERROR] 发生错误: {e}")
        sys.exit(1)
