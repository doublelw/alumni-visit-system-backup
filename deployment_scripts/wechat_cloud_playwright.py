#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信云托管自动导航 - Playwright版本（推荐）
功能：自动化浏览器操作，导航到微信云托管
依赖：pip install playwright
使用：python deployment_scripts/wechat_cloud_playwright.py
"""

import asyncio
import sys
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    RED = '\033[0;31m'
    NC = '\033[0m'

def print_banner():
    print(f"{Colors.CYAN}")
    print("=" * 70)
    print("微信云托管自动导航助手 (Playwright版)")
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

async def check_playwright():
    """检查Playwright是否已安装"""
    try:
        import playwright
        return True
    except ImportError:
        return False

async def install_playwright():
    """安装Playwright"""
    print_warning("Playwright未安装，正在安装...")
    print_info("运行: pip install playwright")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        print_success("Playwright安装成功")
        print_info("正在安装浏览器...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print_success("浏览器安装成功")
        return True
    except Exception as e:
        print_warning(f"安装失败: {e}")
        print_info("请手动运行: pip install playwright && playwright install chromium")
        return False

async def auto_navigate():
    """自动导航到微信云托管"""
    print_banner()

    # 检查Playwright
    print_step(1, 5, "检查Playwright...")
    if not await check_playwright():
        if not await install_playwright():
            print_warning("无法自动安装，请手动安装后重试")
            return False
    print_success("Playwright已就绪")
    print()

    # 导入playwright
    from playwright.async_api import async_playwright

    print_step(2, 5, "启动浏览器...")
    print_info("浏览器将在后台运行...")

    async with async_playwright() as p:
        # 启动浏览器（非无头模式，方便扫码）
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )

        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )

        page = await context.new_page()

        print_success("浏览器已启动")
        print()

        print_step(3, 5, "打开微信公众平台登录页面...")

        try:
            await page.goto("https://mp.weixin.qq.com/", timeout=30000)
            print_success("页面已加载")
        except Exception as e:
            print_warning(f"页面加载超时: {e}")
            print_info("请检查网络连接")
            await browser.close()
            return False

        print()
        print("=" * 70)
        print("请在浏览器中扫码登录")
        print("=" * 70)
        print()
        print("操作步骤：")
        print("  1. 在已打开的浏览器窗口中找到二维码")
        print("  2. 使用微信扫描二维码")
        print("  3. 在手机上确认登录")
        print()
        input(f"{Colors.YELLOW}登录成功后，按回车键继续...{Colors.NC}")
        print()

        print_step(4, 5, "导航到云托管...")

        # 尝试多个可能的路径
        paths_to_try = [
            {
                "name": "方法一：通过云开发",
                "url": "https://cloud.weixin.qq.com/",
                "desc": "直接访问云开发控制台"
            },
            {
                "name": "方法二：通过云托管",
                "url": "https://cloud.weixin.qq.com/cloudrun",
                "desc": "直接访问云托管页面"
            },
            {
                "name": "方法三：通过开放平台",
                "url": "https://open.weixin.qq.com/",
                "desc": "访问微信开放平台"
            }
        ]

        for i, path in enumerate(paths_to_try, 1):
            print()
            print_info(f"尝试 {path['name']}...")
            print_info(f"{path['desc']}")

            try:
                await page.goto(path['url'], timeout=30000, wait_until="networkidle")
                await asyncio.sleep(2)

                # 检查是否成功加载
                title = await page.title()
                print_success(f"页面已加载: {title}")

                # 截图保存
                screenshot_path = f"wechat_cloud_screenshot_{i}.png"
                await page.screenshot(path=screenshot_path)
                print_info(f"已截图保存: {screenshot_path}")

                print()
                print(f"{Colors.CYAN}请在浏览器中查看：{Colors.NC}")
                print(f"  - 如果看到云托管入口，点击进入")
                print(f"  - 如果提示开通，按照提示操作")
                print()

                if i < len(paths_to_try):
                    input(f"{Colors.YELLOW}如果此页面不正确，按回车尝试下一个方法...{Colors.NC}")
                else:
                    input(f"{Colors.YELLOW}按回车键结束...{Colors.NC}")

            except Exception as e:
                print_warning(f"访问失败: {e}")
                continue

        print_step(5, 5, "导航完成")
        print()

        print("=" * 70)
        print_success("导航完成！")
        print("=" * 70)
        print()
        print("提示：")
        print("  1. 浏览器窗口将保持打开，你可以继续操作")
        print("  2. 截图已保存在项目目录中")
        print("  3. 关闭浏览器窗口将结束程序")
        print()

        # 保持浏览器打开
        print_info("浏览器将保持打开30秒，你可以继续操作...")
        await asyncio.sleep(30)

        await browser.close()

    return True

async def main():
    try:
        success = await auto_navigate()
        if success:
            print()
            print_success("✅ 操作完成！")
        else:
            print()
            print_warning("⚠ 操作未完成")
    except KeyboardInterrupt:
        print()
        print_warning("操作已取消")
    except Exception as e:
        print()
        print_warning(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print_warning("操作已取消")
