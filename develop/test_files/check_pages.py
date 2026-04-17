#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查页面实际可用的元素
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:5000"

async def check_page(url, page_name):
    """检查页面的可用元素"""
    print(f"\n{'='*80}")
    print(f"检查页面: {page_name}")
    print(f"URL: {url}")
    print('='*80)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(viewport={'width': 1280, 'height': 720})
    page = await context.new_page()

    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(2)

        # 截图
        await page.screenshot(path=f"check_{page_name}.png")
        print(f"[截图] 已保存: check_{page_name}.png")

        # 获取所有输入框
        inputs = await page.query_selector_all('input')
        print(f"\n输入框 ({len(inputs)}个):")
        for inp in inputs[:20]:  # 只显示前20个
            inp_id = await inp.get_attribute('id')
            inp_name = await inp.get_attribute('name')
            inp_type = await inp.get_attribute('type')
            inp_placeholder = await inp.get_attribute('placeholder')
            print(f"  - id={inp_id}, name={inp_name}, type={inp_type}, placeholder={inp_placeholder}")

        # 获取所有按钮
        buttons = await page.query_selector_all('button')
        print(f"\n按钮 ({len(buttons)}个):")
        for btn in buttons[:20]:  # 只显示前20个
            btn_text = await btn.inner_text()
            btn_onclick = await btn.get_attribute('onclick')
            btn_id = await btn.get_attribute('id')
            if btn_text.strip():
                print(f"  - text='{btn_text.strip()}', onclick={btn_onclick}, id={btn_id}")

        # 获取页面标题
        title = await page.title()
        print(f"\n页面标题: {title}")

        # 获取页面文本（前500个字符）
        body_text = await page.inner_text('body')
        print(f"\n页面文本预览:")
        print(body_text[:500])

    except Exception as e:
        print(f"[错误] {e}")
    finally:
        await browser.close()
        await playwright.stop()


async def main():
    """检查所有相关页面"""
    pages = [
        (f"{BASE_URL}/parent-portal", "parent-portal"),
        (f"{BASE_URL}/teacher-wechat", "teacher-wechat"),
        (f"{BASE_URL}/guard-verify", "guard-verify"),
        (f"{BASE_URL}/", "index"),
    ]

    for url, name in pages:
        await check_page(url, name)


if __name__ == '__main__':
    asyncio.run(main())
