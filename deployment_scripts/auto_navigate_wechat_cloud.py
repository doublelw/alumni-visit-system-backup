#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信云托管自动导航脚本
功能：自动打开浏览器、导航到登录页、扫码后自动跳转到云托管
使用：python deployment_scripts/auto_navigate_wechat_cloud.py
"""

import time
import webbrowser
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def print_banner():
    print(f"{Colors.CYAN}")
    print("=" * 70)
    print("微信云托管自动导航助手")
    print("=" * 70)
    print(f"{Colors.NC}")
    print()

def print_step(step_num, total_steps, message):
    print(f"{Colors.BLUE}[步骤 {step_num}/{total_steps}]{Colors.NC} {message}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.NC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.NC}")

def print_info(message):
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")

def main():
    print_banner()

    print_step(1, 4, "准备打开浏览器...")
    time.sleep(1)

    # 微信公众平台登录页面
    login_url = "https://mp.weixin.qq.com/"

    print_step(2, 4, f"正在打开微信公众平台登录页面...")
    print_info(f"登录地址: {login_url}")
    print()

    # 打开浏览器
    try:
        webbrowser.open(login_url)
        print_success("浏览器已打开")
    except Exception as e:
        print_warning(f"自动打开浏览器失败: {e}")
        print_info("请手动打开浏览器访问: " + login_url)
        print()

    print_step(3, 4, "等待扫码登录...")
    print()
    print("请按以下步骤操作：")
    print("-" * 70)
    print("1. 在已打开的浏览器中，您会看到微信公众平台登录页面")
    print("2. 使用微信扫描页面上的二维码")
    print("3. 在手机上确认登录")
    print("4. 登录成功后，按回车键继续...")
    print("-" * 70)
    print()

    input(f"{Colors.YELLOW}按回车键继续...{Colors.NC}")

    print_step(4, 4, "导航到云托管入口...")
    print()
    print("请在已登录的页面中按以下路径操作：")
    print()
    print(f"{Colors.CYAN}方法一：通过云开发进入{Colors.NC}")
    print("  1. 点击左侧菜单 → 开发")
    print("  2. 点击 云开发")
    print("  3. 如果未开通，点击'开通'按钮")
    print("  4. 开通后，在云开发页面中找到'云托管'选项")
    print()
    print(f"{Colors.CYAN}方法二：直接进入云托管{Colors.NC}")
    print("  1. 点击左侧菜单 → 开发")
    print("  2. 点击 开发管理 或 云托管")
    print()
    print(f"{Colors.CYAN}方法三：直接访问（如果已开通）{Colors.NC}")
    print("  在浏览器地址栏输入:")
    print(f"  {Colors.GREEN}https://cloud.weixin.qq.com/cloudrun{Colors.NC}")
    print()

    # 打开云托管页面
    cloud_run_url = "https://cloud.weixin.qq.com/cloudrun"
    print_info("尝试直接打开云托管页面...")
    time.sleep(2)
    webbrowser.open(cloud_run_url)

    print()
    print("=" * 70)
    print_success("导航完成！")
    print("=" * 70)
    print()
    print("如果云托管页面无法访问，可能原因：")
    print("  1. 账号类型不支持（需要已认证的服务号）")
    print("  2. 未开通云开发服务（需要先开通云开发）")
    print("  3. 权限不足（需要管理员或开发者权限）")
    print()
    print("详细指引请查看: 微信云托管入口指引.md")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("操作已取消")
    except Exception as e:
        print()
        print_warning(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
