#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信云托管位置识别助手
功能：帮助用户在已登录的页面中找到云托管入口
"""

import os
import webbrowser
from pathlib import Path

class Colors:
    """终端颜色"""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    RED = '\033[0;31m'
    BOLD = '\033[1m'
    NC = '\033[0m'

def print_header(text):
    """打印标题"""
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.NC}")
    print(f"{Colors.BOLD}{text.center(70)}{Colors.NC}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.NC}\n")

def print_step(num, total, text):
    """打印步骤"""
    print(f"{Colors.BLUE}[步骤 {num}/{total}]{Colors.NC} {text}")

def print_success(text):
    """打印成功"""
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")

def print_warning(text):
    """打印警告"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.NC}")

def print_info(text):
    """打印信息"""
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {text}")

def print_menu_diagram():
    """打印菜单示意图"""
    print(f"""
{Colors.CYAN}在页面左侧查找这样的菜单：{Colors.NC}

┌─────────────────┐
│                 │
│  🏠 首页         │
│                 │
│  📰 内容管理     │
│                 │
│  💻 开发  ←─────│─ 1️⃣ 点击这个
│                 │
│  ⚙️ 设置         │
│                 │
└─────────────────┘

{Colors.YELLOW}点击"开发"后会展开子菜单：{Colors.NC}

┌─────────────────┐
│                 │
│  💻 开发         │
│    ├─ 开发管理   │
│    │            │
│    ├─ 云开发  ←─│─ 2️⃣ 点击这个
│    │            │
│    └─ 接口权限   │
│                 │
└─────────────────┘

{Colors.YELLOW}进入云开发后，查找：{Colors.NC}

┌──────────────────────────────────────┐
│  云开发控制台                         │
├──────────────────────────────────────┤
│                                      │
│  [概览] [数据库] [存储] [云托管]   │
│                    ↑─ 3️⃣ 点击这个  │
│                                      │
└──────────────────────────────────────┘
""")

def print_alternative_paths():
    """打印备用路径"""
    print(f"\n{Colors.YELLOW}如果找不到，尝试这些方法：{Colors.NC}\n")

    methods = [
        {
            "name": "方法1：直接访问云开发",
            "url": "https://cloud.weixin.qq.com/",
            "instruction": "在浏览器地址栏粘贴这个地址，按回车"
        },
        {
            "name": "方法2：直接访问云托管",
            "url": "https://cloud.weixin.qq.com/cloudrun",
            "instruction": "在浏览器地址栏粘贴这个地址，按回车"
        },
        {
            "name": "方法3：使用搜索",
            "url": None,
            "instruction": "在当前页面按 Ctrl+F，输入'云托管'搜索"
        }
    ]

    for i, method in enumerate(methods, 1):
        print(f"{Colors.BLUE}{i}. {method['name']}{Colors.NC}")
        if method['url']:
            print(f"   URL: {Colors.GREEN}{method['url']}{Colors.NC}")
            print(f"   {method['instruction']}")
            # 自动打开URL
            if input(f"\n   是否自动打开？(y/n): ").lower() == 'y':
                webbrowser.open(method['url'])
                print(f"   {Colors.GREEN}✓ 已在浏览器打开{Colors.NC}")
        else:
            print(f"   {method['instruction']}")
        print()

def check_account_type():
    """检查账号类型"""
    print(f"\n{Colors.CYAN}请确认你的账号类型：{Colors.NC}\n")

    account_types = [
        ("1", "个人订阅号", False, "❌ 不支持云托管"),
        ("2", "已认证的服务号", True, "✅ 支持云托管"),
        ("3", "企业微信", True, "✅ 支持云托管"),
        ("4", "小程序", True, "✅ 支持云托管"),
        ("5", "不确定/其他", None, "⚠️ 需要检查")
    ]

    for code, name, supports, note in account_types:
        status = note
        print(f"  [{code}] {name:<20} {status}")

    print()
    choice = input(f"{Colors.YELLOW}请选择你的账号类型 (1-5): {Colors.NC}")

    return choice

def main():
    """主函数"""
    print_header("微信云托管位置识别助手")

    print(f"{Colors.GREEN}你已经登录了微信公众平台，很好！{Colors.NC}")
    print(f"{Colors.GREEN}现在让我帮你找到云托管入口。{Colors.NC}\n")

    # 检查账号类型
    choice = check_account_type()

    if choice == "1":
        print_warning("\n个人订阅号不支持微信云托管功能")
        print_info("\n建议使用替代方案：")
        print("  1. 腾讯云轻量服务器（50-100元/月）")
        print("  2. 阿里云云托管")
        print("  3. 使用项目中的 deploy.sh 脚本部署\n")
        return

    # 显示菜单示意图
    print_menu_diagram()

    # 显示步骤
    print_step(1, 3, "在左侧菜单中找到并点击 '开发'")
    input(f"\n{Colors.YELLOW}按回车继续...{Colors.NC}\n")

    print_step(2, 3, "在展开的子菜单中找到并点击 '云开发'")
    input(f"\n{Colors.YELLOW}按回车继续...{Colors.NC}\n")

    print_step(3, 3, "在云开发控制台中找到 '云托管' 或 '云函数'")
    print_info("\n如果看到'立即开通'，点击开通即可\n")

    # 提供备用方案
    if input(f"{Colors.YELLOW}是否找到云托管入口？(y/n): {Colors.NC}").lower() == 'n':
        print_alternative_paths()

    # 询问是否需要进一步帮助
    print_header("需要进一步帮助吗？")

    print(f"\n如果你仍然找不到，可以：\n")
    print(f"  {Colors.CYAN}1.{Colors.NC} 截图当前页面发给我看")
    print(f"     Windows: Win + Shift + S")
    print(f"     Mac: Command + Shift + 4")
    print()
    print(f"  {Colors.CYAN}2.{Colors.NC} 告诉我你看到了什么菜单")
    print()
    print(f"  {Colors.CYAN}3.{Colors.NC} 使用替代部署方案")
    print(f"     - 腾讯云服务器部署")
    print(f"     - 阿里云云托管")
    print(f"     - 本地服务器")
    print()

    # 自动打开云开发页面
    if input(f"\n{Colors.YELLOW}是否自动打开云开发页面？(y/n): {Colors.NC}").lower() == 'y':
        print_info("正在打开云开发控制台...")
        webbrowser.open("https://cloud.weixin.qq.com/")
        webbrowser.open("https://cloud.weixin.qq.com/cloudrun")
        print_success("已在浏览器打开云开发页面")
        print_info("请查看浏览器，应该能看到云托管入口了")

    print()
    print_success("✓ 助手运行完成！")
    print_info("如果仍有问题，请查看: 微信云托管操作指南（已登录版）.md\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}操作已取消{Colors.NC}\n")
    except Exception as e:
        print(f"\n{Colors.RED}发生错误: {e}{Colors.NC}\n")
