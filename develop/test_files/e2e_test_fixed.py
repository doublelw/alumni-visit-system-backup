#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整端到端测试 - 修正版
使用正确的元素ID和选择器
"""

import asyncio
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:5000"
SCREENSHOT_DIR = "e2e_screenshots_fixed"

TEST_DATA = {
    'parent': {
        'phone': '13900002001',
        'pin': '88',  # 2位PIN码
        'name': '王父',
        'student_name': '王明',
        'student_id': '2024001'
    },
    'teacher': {
        'phone': '13800000001',
        'password': '1234',
        'name': '张老师'
    },
    'alumni': {
        'phone': '13800001001',
        'pin': '88',
        'name': '李建国'
    }
}


class E2ETest:
    def __init__(self):
        self.screenshots = []
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def setup(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 720})
        self.page = await self.context.new_page()
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        print("浏览器初始化完成")

    async def teardown(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("浏览器已关闭")

    async def screenshot(self, description):
        """截图"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{timestamp}_{description.replace(' ', '_')}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        await self.page.screenshot(path=filepath, full_page=False)
        self.screenshots.append({
            'path': filepath,
            'description': description,
            'url': self.page.url
        })
        print(f"  [截图] {description}")
        return filepath

    async def navigate(self, url):
        """导航"""
        print(f"  [导航] {url}")
        await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(1)

    async def fill_by_id(self, element_id, value, desc=""):
        """填充输入框"""
        try:
            await self.page.wait_for_selector(f"#{element_id}", timeout=5000)
            await self.page.fill(f"#{element_id}", value)
            print(f"  [填充] {desc}: {value}")
            await asyncio.sleep(0.3)
            return True
        except Exception as e:
            print(f"  [失败] 填充{element_id}: {e}")
            return False

    async def click_button(self, selector, desc=""):
        """点击按钮"""
        try:
            await self.page.wait_for_selector(selector, timeout=5000)
            await self.page.click(selector)
            print(f"  [点击] {desc}")
            await asyncio.sleep(1)
            return True
        except Exception as e:
            print(f"  [失败] 点击{selector}: {e}")
            return False

    async def extract_code(self):
        """从页面提取6位码"""
        try:
            # 等待内容加载
            await asyncio.sleep(1)

            # 获取页面文本
            text = await self.page.inner_text('body')

            # 查找6位数字
            matches = re.findall(r'\b\d{6}\b', text)

            if matches:
                code = matches[0]
                print(f"  [提取] 验证码: {code}")
                return code

            print("  [未找到] 6位验证码")
            return None
        except Exception as e:
            print(f"  [错误] 提取验证码: {e}")
            return None

    async def story_1_student_leave(self):
        """用户故事1：学生请假"""
        print("\n" + "="*80)
        print("用户故事1：学生请假（家长申请 → 教师审批 → 门卫验证）")
        print("="*80)

        leave_code = None
        exit_code = None

        # 步骤1：家长生成请假码
        print("\n[步骤1] 家长生成请假码")
        await self.navigate(f"{BASE_URL}/parent-portal")
        await self.screenshot("1.1_家长页面")

        # 填写信息
        await self.fill_by_id('parentPhone', TEST_DATA['parent']['phone'], "手机号")
        await self.fill_by_id('parentPin', TEST_DATA['parent']['pin'], "PIN码")
        await self.screenshot("1.2_填写家长信息")

        # 点击"孩子请假"按钮
        if await self.click_button('button[onclick="generateLeaveCode()"]', "孩子请假"):
            await asyncio.sleep(2)
            await self.screenshot("1.3_选择学生")

            # 点击第一个学生
            student_buttons = await self.page.query_selector_all('.child-item')
            if student_buttons:
                await student_buttons[0].click()
                print("  [点击] 选择学生")
                await asyncio.sleep(2)
                await self.screenshot("1.4_生成请假码")

                # 提取请假码
                leave_code = await self.extract_code()

        # 步骤2：教师审批
        if leave_code:
            print("\n[步骤2] 教师审批")
            await self.navigate(f"{BASE_URL}/teacher-wechat")
            await self.screenshot("2.1_教师页面")

            # 教师登录
            await self.fill_by_id('phone', TEST_DATA['teacher']['phone'], "教师手机号")
            await self.fill_by_id('password', TEST_DATA['teacher']['password'], "教师密码")
            await self.screenshot("2.2_填写教师信息")

            if await self.click_button('button[onclick="login()"]', "登录"):
                await asyncio.sleep(2)
                await self.screenshot("2.3_教师登录成功")

            # 输入审批码
            await self.fill_by_id('codeInput', leave_code, "审批码")
            await self.screenshot("2.4_输入审批码")

            if await self.click_button('button[onclick="checkCode()"]', "确认通过"):
                await asyncio.sleep(2)
                await self.screenshot("2.5_审批通过")

                # 提取出校码
                exit_code = await self.extract_code()

        # 步骤3：门卫验证
        if exit_code:
            print("\n[步骤3] 门卫验证")
            await self.navigate(f"{BASE_URL}/guard-verify")
            await self.screenshot("3.1_门卫页面")

            # 点击"学生出校"
            if await self.click_button('button:has-text("学生出校")', "学生出校"):
                await asyncio.sleep(1)

            await self.fill_by_id('codeInput', exit_code, "出校码")
            await self.screenshot("3.2_输入出校码")

            if await self.click_button('button:has-text("验证")', "验证"):
                await asyncio.sleep(2)
                await self.screenshot("3.3_验证结果")

        return {
            'leave_code': leave_code,
            'exit_code': exit_code,
            'success': bool(leave_code and exit_code)
        }

    async def story_2_alumni_visit(self):
        """用户故事2：校友入校"""
        print("\n" + "="*80)
        print("用户故事2：校友入校（无需审批）")
        print("="*80)

        visit_code = None

        # 步骤1：校友登录并申请
        print("\n[步骤1] 校友申请入校")
        await self.navigate(f"{BASE_URL}/")
        await self.screenshot("1.1_首页")

        # 校友登录
        await self.fill_by_id('phone', TEST_DATA['alumni']['phone'], "校友手机号")
        await self.fill_by_id('password', TEST_DATA['alumni']['pin'], "校友密码")
        await self.screenshot("1.2_填写校友信息")

        if await self.click_button('button:has-text("登录")', "登录"):
            await asyncio.sleep(2)
            await self.screenshot("1.3_登录成功")

        # 点击快速申请
        if await self.click_button('#quickVisit', "快速申请"):
            await asyncio.sleep(1)
            await self.screenshot("1.4_申请页面")

            # 填写表单
            await self.fill_by_id('visitDate', datetime.now().strftime('%Y-%m-%d'), "日期")
            await self.fill_by_id('timeStart', '09:00', "开始时间")
            await self.fill_by_id('timeEnd', '11:00', "结束时间")
            await self.fill_by_id('visitPurpose', '参观校园', "访问目的")
            await self.fill_by_id('visitorName', TEST_DATA['alumni']['name'], "姓名")
            await self.fill_by_id('visitorPhone', TEST_DATA['alumni']['phone'], "电话")
            await self.fill_by_id('visitorIdCard', '110101198001011234', "身份证")
            await self.screenshot("1.5_填写申请表")

            # 提交
            if await self.click_button('button[type="submit"]', "提交申请"):
                await asyncio.sleep(2)
                await self.screenshot("1.6_申请提交")

                # 提取入校码
                visit_code = await self.extract_code()

        # 步骤2：门卫验证
        if visit_code:
            print("\n[步骤2] 门卫验证")
            await self.navigate(f"{BASE_URL}/guard-verify")
            await self.screenshot("2.1_门卫页面")

            # 点击"校友入校"
            if await self.click_button('button:has-text("校友入校")', "校友入校"):
                await asyncio.sleep(1)

            await self.fill_by_id('codeInput', visit_code, "入校码")
            await self.screenshot("2.2_输入入校码")

            if await self.click_button('button:has-text("验证")', "验证"):
                await asyncio.sleep(2)
                await self.screenshot("2.3_验证结果")

        return {
            'visit_code': visit_code,
            'success': bool(visit_code)
        }

    async def story_3_parent_visit(self):
        """用户故事3：家长入校"""
        print("\n" + "="*80)
        print("用户故事3：家长入校（需要审批）")
        print("="*80)

        visit_code = None

        # 步骤1：家长生成入校码
        print("\n[步骤1] 家长生成入校码")
        await self.navigate(f"{BASE_URL}/parent-portal")
        await self.screenshot("1.1_家长页面")

        await self.fill_by_id('parentPhone', TEST_DATA['parent']['phone'], "手机号")
        await self.fill_by_id('parentPin', TEST_DATA['parent']['pin'], "PIN码")
        await self.screenshot("1.2_填写家长信息")

        # 点击"我要进校"
        if await self.click_button('button[onclick="generateVisitCode()"]', "我要进校"):
            await asyncio.sleep(2)
            await self.screenshot("1.3_生成入校码")

            # 提取入校码
            visit_code = await self.extract_code()

        # 步骤2：教师审批
        if visit_code:
            print("\n[步骤2] 教师审批")
            await self.navigate(f"{BASE_URL}/teacher-wechat")
            await self.screenshot("2.1_教师页面")

            await self.fill_by_id('phone', TEST_DATA['teacher']['phone'], "教师手机号")
            await self.fill_by_id('password', TEST_DATA['teacher']['password'], "教师密码")
            await self.screenshot("2.2_填写教师信息")

            if await self.click_button('button[onclick="login()"]', "登录"):
                await asyncio.sleep(2)
                await self.screenshot("2.3_登录成功")

            await self.fill_by_id('codeInput', visit_code, "审批码")
            await self.screenshot("2.4_输入审批码")

            if await self.click_button('button[onclick="checkCode()"]', "确认通过"):
                await asyncio.sleep(2)
                await self.screenshot("2.5_审批完成")

        # 步骤3：门卫验证
        if visit_code:
            print("\n[步骤3] 门卫验证")
            await self.navigate(f"{BASE_URL}/guard-verify")
            await self.screenshot("3.1_门卫页面")

            # 点击"家长入校"
            if await self.click_button('button:has-text("家长入校")', "家长入校"):
                await asyncio.sleep(1)

            await self.fill_by_id('codeInput', visit_code, "入校码")
            await self.screenshot("3.2_输入入校码")

            if await self.click_button('button:has-text("验证")', "验证"):
                await asyncio.sleep(2)
                await self.screenshot("3.3_验证结果")

        return {
            'visit_code': visit_code,
            'success': bool(visit_code)
        }

    async def story_4_visitor(self):
        """用户故事4：访客登记"""
        print("\n" + "="*80)
        print("用户故事4：访客登记")
        print("="*80)

        visitor_code = None

        # 步骤1：访客登记
        print("\n[步骤1] 访客登记")
        await self.navigate(f"{BASE_URL}/apply-visit")
        await self.screenshot("1.1_访客页面")

        # 填写信息
        await self.fill_by_id('visitorName', '张三', "访客姓名")
        await self.fill_by_id('visitorPhone', '13900000000', "访客手机")
        await self.fill_by_id('visitorIdCard', '110101199001011234', "身份证")
        await self.screenshot("1.2_填写访客信息")

        # 点击生成
        if await self.click_button('button:has-text("生成验证码")', "生成验证码"):
            await asyncio.sleep(2)
            await self.screenshot("1.3_生成验证码")

            # 提取访客码
            visitor_code = await self.extract_code()

        # 步骤2：门卫验证
        if visitor_code:
            print("\n[步骤2] 门卫验证")
            await self.navigate(f"{BASE_URL}/guard-verify")
            await self.screenshot("2.1_门卫页面")

            # 点击"访客登记"
            if await self.click_button('button:has-text("访客登记")', "访客登记"):
                await asyncio.sleep(1)

            await self.fill_by_id('codeInput', visitor_code, "访客码")
            await self.screenshot("2.2_输入访客码")

            if await self.click_button('button:has-text("验证")', "验证"):
                await asyncio.sleep(2)
                await self.screenshot("2.3_验证结果")

        return {
            'visitor_code': visitor_code,
            'success': bool(visitor_code)
        }

    async def story_5_teacher_create_code(self):
        """用户故事5：教师直接创建出校码"""
        print("\n" + "="*80)
        print("用户故事5：教师直接创建出校码")
        print("="*80)

        exit_code = None

        # 步骤1：教师登录
        print("\n[步骤1] 教师登录")
        await self.navigate(f"{BASE_URL}/teacher-wechat")
        await self.screenshot("1.1_教师页面")

        await self.fill_by_id('phone', TEST_DATA['teacher']['phone'], "教师手机号")
        await self.fill_by_id('password', TEST_DATA['teacher']['password'], "教师密码")
        await self.screenshot("1.2_填写教师信息")

        if await self.click_button('button[onclick="login()"]', "登录"):
            await asyncio.sleep(2)
            await self.screenshot("1.3_登录成功")

        # 步骤2：直接创建出校码
        print("\n[步骤2] 创建出校码")

        # 切换到"代学生申请"标签
        create_tabs = await self.page.query_selector_all('.nav-item, .tab')
        if create_tabs:
            for tab in create_tabs:
                text = await tab.inner_text()
                if '创建' in text or '申请' in text:
                    await tab.click()
                    print("  [点击] 切换到创建标签")
                    await asyncio.sleep(1)
                    break

        await self.screenshot("2.1_创建页面")

        # 输入学号
        student_id_inputs = await self.page.query_selector_all('input[placeholder*="学号"]')
        if student_id_inputs:
            await student_id_inputs[0].fill(TEST_DATA['parent']['student_id'])
            print(f"  [填充] 学号: {TEST_DATA['parent']['student_id']}")
            await self.screenshot("2.2_输入学号")

            # 点击生成
            create_buttons = await self.page.query_selector_all('button:has-text("生成")')
            if create_buttons:
                await create_buttons[0].click()
                print("  [点击] 生成出校码")
                await asyncio.sleep(2)
                await self.screenshot("2.3_生成出校码")

                # 提取出校码
                exit_code = await self.extract_code()

        # 步骤3：门卫验证
        if exit_code:
            print("\n[步骤3] 门卫验证")
            await self.navigate(f"{BASE_URL}/guard-verify")
            await self.screenshot("3.1_门卫页面")

            # 点击"学生出校"
            if await self.click_button('button:has-text("学生出校")', "学生出校"):
                await asyncio.sleep(1)

            await self.fill_by_id('codeInput', exit_code, "出校码")
            await self.screenshot("3.2_输入出校码")

            if await self.click_button('button:has-text("验证")', "验证"):
                await asyncio.sleep(2)
                await self.screenshot("3.3_验证结果")

        return {
            'exit_code': exit_code,
            'success': bool(exit_code)
        }

    def generate_report(self, results):
        """生成HTML报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>校友入校系统 - 端到端测试报告</title>
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
    </div>

    <div class="summary">
        <h2>测试概览</h2>
        <p>总用户故事: 5</p>
        <p>总截图: {len(self.screenshots)}</p>
    </div>
"""

        for i, (story_name, result) in enumerate(results.items(), 1):
            status = "✅ 成功" if result.get('success') else "❌ 失败"
            html += f"""
    <div class="story">
        <h2>用户故事{i}: {story_name} {status}</h2>
"""

            if result.get('leave_code'):
                html += f"<div class='code'>请假码: {result['leave_code']}</div>"
            if result.get('exit_code'):
                html += f"<div class='code'>出校码: {result['exit_code']}</div>"
            if result.get('visit_code'):
                html += f"<div class='code'>入校码: {result['visit_code']}</div>"
            if result.get('visitor_code'):
                html += f"<div class='code'>访客码: {result['visitor_code']}</div>"

            html += "    </div>\n"

        # 添加所有截图
        html += "    <div class='summary'><h2>所有截图</h2><div class='screenshot-grid'>\n"
        for idx, shot in enumerate(self.screenshots, 1):
            html += f"""
        <div class='screenshot-item'>
            <img src='{shot['path']}'>
            <div class='screenshot-caption'>{idx}. {shot['description']}</div>
        </div>
"""
        html += "    </div></div>\n</body>\n</html>"

        report_path = "e2e_test_report_fixed.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n[报告] 已生成: {report_path}")


async def main():
    """主函数"""
    print("\n" + "="*80)
    print("校友入校系统 - 端到端自动化测试（修正版）")
    print("="*80)
    print(f"\n测试数据:")
    print(f"  家长: {TEST_DATA['parent']['name']} ({TEST_DATA['parent']['phone']})")
    print(f"  教师: {TEST_DATA['teacher']['name']} ({TEST_DATA['teacher']['phone']})")
    print(f"  校友: {TEST_DATA['alumni']['name']} ({TEST_DATA['alumni']['phone']})")
    print()

    test = E2ETest()
    results = {}

    try:
        await test.setup()

        # 执行所有用户故事
        results['学生请假'] = await test.story_1_student_leave()
        results['校友入校'] = await test.story_2_alumni_visit()
        results['家长入校'] = await test.story_3_parent_visit()
        results['访客登记'] = await test.story_4_visitor()
        results['教师直接创建'] = await test.story_5_teacher_create_code()

    finally:
        await test.teardown()
        test.generate_report(results)

        print("\n" + "="*80)
        print("测试完成")
        print("="*80)


if __name__ == '__main__':
    asyncio.run(main())
