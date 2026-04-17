#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试 - 使用正确的页面和元素ID
三个主要页面：parent-portal, teacher-wechat, guard-verify
"""

import asyncio
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:5000"
SCREENSHOT_DIR = "e2e_screenshots_correct"

TEST_DATA = {
    'parent': {
        'phone': '13900002001',
        'pin': '88',
        'name': '王父'
    },
    'teacher': {
        'phone': '13800000001',
        'password': '1234',
        'name': '张老师'
    },
    'student_id': '2024001'
}


class E2ETest:
    def __init__(self):
        self.screenshots = []
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def setup(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 720})
        self.page = await self.context.new_page()
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    async def teardown(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def screenshot(self, desc):
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{timestamp}_{desc.replace(' ', '_')}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        await self.page.screenshot(path=filepath)
        self.screenshots.append({'path': filepath, 'desc': desc})
        print(f"  [截图] {desc}")
        return filepath

    async def goto(self, url):
        print(f"  [导航] {url}")
        await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(1)

    async def fill(self, element_id, value, desc=""):
        try:
            await self.page.wait_for_selector(f"#{element_id}", timeout=5000)
            await self.page.fill(f"#{element_id}", value)
            print(f"  [填写] {desc}: {value}")
            await asyncio.sleep(0.3)
            return True
        except Exception as e:
            print(f"  [失败] 填写{element_id}: {str(e)[:100]}")
            return False

    async def click_button(self, text, desc=""):
        try:
            # 按文本查找按钮
            await self.page.wait_for_selector(f"button:has-text('{text}')", timeout=5000)
            await self.page.click(f"button:has-text('{text}')")
            print(f"  [点击] {desc}")
            await asyncio.sleep(1)
            return True
        except Exception as e:
            print(f"  [失败] 点击'{text}': {str(e)[:100]}")
            return False

    async def extract_code(self):
        """从页面提取6位验证码"""
        await asyncio.sleep(1)
        text = await self.page.inner_text('body')
        codes = re.findall(r'\b\d{6}\b', text)
        if codes:
            code = codes[0]
            print(f"  [提取码] {code}")
            return code
        print("  [未找到] 6位码")
        return None

    async def story_1_parent_visit(self):
        """用户故事1：家长入校（家长 → 教师 → 门卫）"""
        print("\n" + "="*80)
        print("用户故事1：家长入校")
        print("="*80)

        visit_code = None
        exit_code = None

        # 步骤1：家长生成入校码
        print("\n[步骤1] 家长生成入校码")
        await self.goto(f"{BASE_URL}/parent-portal")
        await self.screenshot("1_家长页面")

        await self.fill('parentPhone', TEST_DATA['parent']['phone'], "手机号")
        await self.fill('parentPin', TEST_DATA['parent']['pin'], "PIN码")
        await self.screenshot("2_填写家长信息")

        # 点击"我要进校"按钮 - 这个按钮的onclick是generateVisitCode()
        try:
            await self.page.click('button[onclick="generateVisitCode()"]')
            print("  [点击] 我要进校")
            await asyncio.sleep(2)
            await self.screenshot("3_生成入校码")
            visit_code = await self.extract_code()
        except:
            print("  [失败] 点击'我要进校'")

        # 步骤2：教师审批
        if visit_code:
            print("\n[步骤2] 教师审批")
            await self.goto(f"{BASE_URL}/teacher-wechat")
            await self.screenshot("4_教师页面")

            await self.fill('phone', TEST_DATA['teacher']['phone'], "教师手机")
            await self.fill('password', TEST_DATA['teacher']['password'], "教师密码")
            await self.screenshot("5_填写教师信息")

            if await self.click_button('登录', "登录按钮"):
                await asyncio.sleep(2)
                await self.screenshot("6_教师登录成功")

            await self.fill('codeInput', visit_code, "审批码")
            await self.screenshot("7_输入审批码")

            if await self.click_button('确认通过', "确认通过"):
                await asyncio.sleep(2)
                await self.screenshot("8_审批完成")

        # 步骤3：门卫验证
        if visit_code:
            print("\n[步骤3] 门卫验证")
            await self.goto(f"{BASE_URL}/guard-verify")
            await self.screenshot("9_门卫页面")

            # 点击"在校验证"按钮
            try:
                await self.page.click('button[onclick="verifyWithType(\'student-parent\')"]')
                print("  [点击] 在校验证")
                await asyncio.sleep(1)
            except:
                await self.click_button('在校验证', "在校验证")

            await self.fill('codeInput', visit_code, "入校码")
            await self.screenshot("10_输入入校码")

            if await self.click_button('验证', "验证按钮"):
                await asyncio.sleep(2)
                await self.screenshot("11_验证结果")

        return {'visit_code': visit_code, 'success': bool(visit_code)}

    async def story_2_teacher_direct_create(self):
        """用户故事2：教师直接创建出校码"""
        print("\n" + "="*80)
        print("用户故事2：教师直接创建出校码")
        print("="*80)

        exit_code = None

        # 步骤1：教师登录
        print("\n[步骤1] 教师登录")
        await self.goto(f"{BASE_URL}/teacher-wechat")
        await self.screenshot("1_教师页面")

        await self.fill('phone', TEST_DATA['teacher']['phone'], "教师手机")
        await self.fill('password', TEST_DATA['teacher']['password'], "教师密码")
        await self.screenshot("2_填写教师信息")

        if await self.click_button('登录', "登录按钮"):
            await asyncio.sleep(2)
            await self.screenshot("3_教师登录成功")

        # 步骤2：切换到"代学生申请"
        print("\n[步骤2] 代学生申请")
        try:
            await self.page.click('button[onclick="showCreateMode()"]')
            print("  [点击] 代学生申请")
            await asyncio.sleep(1)
            await self.screenshot("4_申请页面")
        except:
            await self.click_button('代学生申请', "代学生申请")

        await self.fill('studentIdInput', TEST_DATA['student_id'], "学号")
        await self.screenshot("5_输入学号")

        if await self.click_button('生成', "生成出校码"):
            await asyncio.sleep(2)
            await self.screenshot("6_生成出校码")
            exit_code = await self.extract_code()

        # 步骤3：门卫验证
        if exit_code:
            print("\n[步骤3] 门卫验证")
            await self.goto(f"{BASE_URL}/guard-verify")
            await self.screenshot("7_门卫页面")

            # 点击"学生出校"按钮
            try:
                await self.page.click('button[onclick="verifyWithType(\'student-leave\')"]')
                print("  [点击] 学生出校")
                await asyncio.sleep(1)
            except:
                await self.click_button('学生出校', "学生出校")

            await self.fill('codeInput', exit_code, "出校码")
            await self.screenshot("8_输入出校码")

            if await self.click_button('验证', "验证按钮"):
                await asyncio.sleep(2)
                await self.screenshot("9_验证结果")

        return {'exit_code': exit_code, 'success': bool(exit_code)}

    async def story_3_student_leave(self):
        """用户故事3：学生请假（家长 → 教师 → 门卫）"""
        print("\n" + "="*80)
        print("用户故事3：学生请假")
        print("="*80)

        leave_code = None
        exit_code = None

        # 步骤1：家长生成请假码
        print("\n[步骤1] 家长生成请假码")
        await self.goto(f"{BASE_URL}/parent-portal")
        await self.screenshot("1_家长页面")

        await self.fill('parentPhone', TEST_DATA['parent']['phone'], "手机号")
        await self.fill('parentPin', TEST_DATA['parent']['pin'], "PIN码")
        await self.screenshot("2_填写家长信息")

        # 点击"孩子请假"
        try:
            await self.page.click('button[onclick="generateLeaveCode()"]')
            print("  [点击] 孩子请假")
            await asyncio.sleep(2)
            await self.screenshot("3_选择学生")

            # 点击第一个学生
            students = await self.page.query_selector_all('.child-item, [onclick*="selectChild"]')
            if students:
                await students[0].click()
                print("  [点击] 选择学生")
                await asyncio.sleep(2)
                await self.screenshot("4_生成请假码")
                leave_code = await self.extract_code()
        except Exception as e:
            print(f"  [失败] {str(e)[:100]}")

        # 步骤2：教师审批
        if leave_code:
            print("\n[步骤2] 教师审批")
            await self.goto(f"{BASE_URL}/teacher-wechat")
            await self.screenshot("5_教师页面")

            await self.fill('phone', TEST_DATA['teacher']['phone'], "教师手机")
            await self.fill('password', TEST_DATA['teacher']['password'], "教师密码")
            await self.screenshot("6_填写教师信息")

            if await self.click_button('登录', "登录按钮"):
                await asyncio.sleep(2)
                await self.screenshot("7_教师登录成功")

            await self.fill('codeInput', leave_code, "审批码")
            await self.screenshot("8_输入审批码")

            if await self.click_button('确认通过', "确认通过"):
                await asyncio.sleep(2)
                await self.screenshot("9_审批完成")
                exit_code = await self.extract_code()

        # 步骤3：门卫验证
        if exit_code:
            print("\n[步骤3] 门卫验证")
            await self.goto(f"{BASE_URL}/guard-verify")
            await self.screenshot("10_门卫页面")

            try:
                await self.page.click('button[onclick="verifyWithType(\'student-leave\')"]')
                print("  [点击] 学生出校")
                await asyncio.sleep(1)
            except:
                await self.click_button('学生出校', "学生出校")

            await self.fill('codeInput', exit_code, "出校码")
            await self.screenshot("11_输入出校码")

            if await self.click_button('验证', "验证按钮"):
                await asyncio.sleep(2)
                await self.screenshot("12_验证结果")

        return {'leave_code': leave_code, 'exit_code': exit_code, 'success': bool(leave_code and exit_code)}

    def generate_report(self, results):
        """生成HTML报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>端到端测试报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
        .summary {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .story {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .code {{ background: #fff3cd; padding: 15px; border-radius: 5px; text-align: center; font-family: monospace; font-size: 18px; font-weight: bold; margin: 10px 0; }}
        .screenshot-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 15px; }}
        .screenshot-item img {{ width: 100%; border-radius: 5px; }}
        .screenshot-caption {{ background: #f8f9fa; padding: 10px; text-align: center; border-radius: 0 0 5px 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>校友入校系统 - 端到端测试报告</h1>
        <p>测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>主要页面: parent-portal, teacher-wechat, guard-verify</p>
    </div>

    <div class="summary">
        <h2>测试概览</h2>
        <p>总用户故事: 3</p>
        <p>总截图: {len(self.screenshots)}</p>
    </div>
"""

        for i, (story_name, result) in enumerate(results.items(), 1):
            status = "✅ 成功" if result.get('success') else "❌ 失败"
            html += f"""
    <div class="story">
        <h2>用户故事{i}: {story_name} {status}</h2>
"""

            if result.get('visit_code'):
                html += f"<div class='code'>入校码: {result['visit_code']}</div>"
            if result.get('leave_code'):
                html += f"<div class='code'>请假码: {result['leave_code']}</div>"
            if result.get('exit_code'):
                html += f"<div class='code'>出校码: {result['exit_code']}</div>"

            html += "    </div>\n"

        html += "    <div class='summary'><h2>所有截图</h2><div class='screenshot-grid'>\n"
        for idx, shot in enumerate(self.screenshots, 1):
            html += f"""
        <div class='screenshot-item'>
            <img src='{shot['path']}'>
            <div class='screenshot-caption'>{idx}. {shot['desc']}</div>
        </div>
"""
        html += "    </div></div>\n</body>\n</html>"

        with open("e2e_test_report_correct.html", 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n[报告] 已生成: e2e_test_report_correct.html")


async def main():
    print("\n" + "="*80)
    print("校友入校系统 - 端到端测试（正确版本）")
    print("="*80)
    print(f"\n测试数据:")
    print(f"  家长: {TEST_DATA['parent']['name']} ({TEST_DATA['parent']['phone']})")
    print(f"  教师: {TEST_DATA['teacher']['name']} ({TEST_DATA['teacher']['phone']})")
    print(f"  学号: {TEST_DATA['student_id']}")

    test = E2ETest()
    results = {}

    try:
        await test.setup()

        results['家长入校'] = await test.story_1_parent_visit()
        results['教师直接创建'] = await test.story_2_teacher_direct_create()
        results['学生请假'] = await test.story_3_student_leave()

    finally:
        await test.teardown()
        test.generate_report(results)

        print("\n" + "="*80)
        print("测试完成")
        print("="*80)


if __name__ == '__main__':
    asyncio.run(main())
