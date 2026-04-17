#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校友入校登记系统 - 微信云托管一键部署准备
"""

import os
import sys
import webbrowser
from pathlib import Path
import subprocess

def main():
    print("=" * 70)
    print("校友入校登记系统 - 微信云托管部署助手")
    print("=" * 70)
    print()

    # [1/5] 检查部署包
    print("[1/5] 检查部署包...")
    deploy_package = Path("welife_deploy_package_20260406_191348.zip")
    if deploy_package.exists():
        print(f"[SUCCESS] 部署包已存在: {deploy_package.name}")
        size = deploy_package.stat().st_size / (1024 * 1024)
        print(f"         文件大小: {size:.2f} MB")
    else:
        print("[ERROR] 部署包不存在，正在重新生成...")
        result = subprocess.run(["python", "deployment_scripts/deploy_to_welife.py"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ERROR] 部署包生成失败: {result.stderr}")
            return
    print()

    # [2/5] 检查配置文件
    print("[2/5] 检查配置文件...")
    config_file = Path("部署配置-微信云托管.txt")
    if config_file.exists():
        print("[SUCCESS] 配置文件已生成")
    else:
        print("[ERROR] 配置文件缺失")
        return
    print()

    # [3/5] 打开配置文件
    print("[3/5] 打开部署配置文件...")
    try:
        os.startfile(config_file.absolute())
        print("[SUCCESS] 已打开配置文件")
    except:
        print(f"[INFO] 请手动打开配置文件: {config_file.absolute()}")
    print()

    # [4/5] 准备部署环境
    print("[4/5] 准备部署环境...")
    print(f"[INFO] 部署包位置: {Path.cwd()}\\{deploy_package.name}")
    print(f"[INFO] 配置文件位置: {Path.cwd()}\\{config_file.name}")
    print()

    # [5/5] 打开微信云托管控制台
    print("[5/5] 打开微信云托管控制台...")
    print("[INFO] 正在打开浏览器...")
    try:
        webbrowser.open("https://cloud.weixin.qq.com/cloudrun/service")
        print("[SUCCESS] 已打开微信云托管控制台")
    except:
        print("[ERROR] 无法打开浏览器，请手动访问:")
        print("       https://cloud.weixin.qq.com/cloudrun/service")
    print()

    print("=" * 70)
    print("准备工作完成！")
    print("=" * 70)
    print()
    print("[INFO] 下一步操作:")
    print()
    print("1. 在已打开的配置文件中复制环境变量")
    print("2. 在微信云托管控制台中:")
    print("   - 点击 '新建服务'")
    print("   - 上传部署包: welife_deploy_package_20260406_191348.zip")
    print("   - 粘贴环境变量配置")
    print("   - 开始部署")
    print()
    print("[INFO] 详细步骤请查看已打开的配置文件")
    print()

if __name__ == "__main__":
    try:
        main()
        input("按回车键退出...")
    except KeyboardInterrupt:
        print()
        print("[INFO] 操作已取消")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")
        sys.exit(1)
