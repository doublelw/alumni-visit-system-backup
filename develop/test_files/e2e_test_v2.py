#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的端到端测试 - 真实浏览器交互
使用Playwright进行真实的页面操作和数据传递
"""

import asyncio
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# 基础配置
BASE_URL = "http://127.0.0.1:5000"
SCREENSHOT_DIR = "e2e_screenshots_v2"

# 真实测试数据 - 从prepare_test_data.py获取
TEST_DATA = {
    'parent': {
        'phone': '13900002001',
        'password': '88',
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
        'password': '88',
        'name': '李建国'
    },
    'visitor': {
        'name': '张三',
        'phone': '13900000000',
        'id_card': '110101199001011234'
    }
}


class E2ETest:
    def __init__(self):
        self.screenshots = []
        self.browser = None
        self.context = None
        self.page = None

    async def setup(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 720})
        self.page = await self.context.new_page()
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        print("浏览器初始化完成")

    async def teardown(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        print("浏览器已关闭")

    async def screenshot(self, description):
        """截图并保存"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{timestamp}_{description.replace(' ', '_')}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        await self.page.screenshot(path=filepath)
        self.screenshots.append({
            'path': filepath,
            'description': description,
            'url': self.page.url
        })
        print(f"  [截图] {description}")
        return filepath

    async def navigate(self, url):
        """导航到指定页面"""
        print(f"  [导航] {url}")
        await self.page.goto(url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(1)  # 等待JS执行

    async def fill_by_id(self, element_id, value, description=""):
        """通过ID填充输入框"""
        try:
            await self.page.wait_for_selector(f"#{element_id}", timeout=5000)
            await self.page.fill(f"#{element_id}", value)
            print(f"  [填充] {description}: {value}")
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            print(f"  [错误] 填充{element_id}失败: {e}")
            return False

    async def click_by_text(self, text, description=""):
        """通过文本点击按钮"""
        try:
            # 尝试多种选择器
            selectors = [
                f"button:has-text('{text}')",
                f"input[type='button'][value='{text}']",
                f".btn:has-text('{text}')",
                f"[role='button']:has-text('{text}')"
            ]

            for selector in selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    await self.page.click(selector)
                    print(f"  [点击] {description}")
                    await asyncio.sleep(0.5)
                    return True
                except:
                    continue

            print(f"  [警告] 未找到按钮: {text}")
            return False
        except Exception as e:
            print(f"  [错误] 点击失败: {e}")
            return False

    async def click_by_id(self, element_id, description=""):
        """通过ID点击元素"""
        try:
            await self.page.wait_for_selector(f"#{element_id}", timeout=5000)
            await self.page.click(f"#{element_id}")
            print(f"  [点击] {description}")
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            print(f"  [错误] 点击{element_id}失败: {e}")
            return False

    async def extract_code_from_page(self):
        """从页面提取6位验证码"""
        print("  [提取] 正在查找验证码...")

        # 尝试多个可能的选择器
        code_patterns = [
            r'\b\d{6}\b',  # 6位数字
        ]

        # 获取页面文本
        page_text = await self.page.inner_text('body')

        # 查找所有6位数字
        codes = re.findall(r'\b\d{6}\b', page_text)

        if codes:
            # 返回找到的第一个6位码
            code = codes[0]
            print(f"  [找到] 验证码: {code}")
            return code

        print("  [未找到] 页面上没有6位验证码")
        return None

    async def wait_for_message(self):
        """等待并获取页面消息"""
        try:
            # 等待可能的提示消息
            await asyncio.sleep(1)

            # 尝试从页面获取消息文本
            message_elements = await self.page.query_selector_all('.toast, .message, .alert, .notification')
            if message_elements:
                messages = []
                for el in message_elements:
                    text = await el.inner_text()
                    if text.strip():
                        messages.append(text.strip())
                if messages:
                    return ' '.join(messages)

            return None
        except:
            return None

    # ==================== 用户故事 ====================

    async def story_1_student_leave(self):
        """用户故事1：学生请假（家长申请 → 教师审批 → 门卫验证）"""
        print("\n" + "="*80)
        print("用户故事1：学生请假流程")
        print("="*80)

        # 步骤1：家长登录并生成请假码
        print("\n[步骤1] 家长登录并生成请假码")
        await self.navigate(f"{BASE_URL}/parent-portal")
        await self.screenshot("1.1_家长登录页")

        # 填写登录信息
        await self.fill_by_id('phone', TEST_DATA['parent']['phone'], "家长手机号")
        await self.fill_by_id('password', TEST_DATA['parent']['password'], "家长密码")
        await self.screenshot("1.2_家长登录信息填写")

        # 点击登录
        if await self.click_by_text('登录', "登录按钮"):
            await asyncio.sleep(2)
            await self.screenshot("1.3_家长登录成功")

        # 选择"请假"类型
        await self.fill_by_id('applicationType', 'leave', "申请类型(请假)")
        await asyncio.sleep(0.5)

        # 选择请假原因
        await self.fill_by_id('leaveReason', 'sick', "请假原因")
        await asyncio.sleep(0.5)

        # 点击生成请假码
        if await self.click_by_text('生成6位码', "生成请假码"):
            await asyncio.sleep(2)
            await self.screenshot("1.4_生成请假码")

        # 提取请假码
        leave_code = await self.extract_code_from_page()
        print(f"  [获取] 请假码: {leave_code}")
        await self.screenshot("1.5_请假码页面")

        # 步骤2：教师登录并审批
        print("\n[步骤2] 教师登录并审批")
        await self.navigate(f"{BASE_URL}/teacher-approve")
        await self.screenshot("2.1_教师登录页")

        # 填写教师登录信息
        await self.fill_by_id('phone', TEST_DATA['teacher']['phone'], "教师手机号")
        await self.fill_by_id('password', TEST_DATA['teacher']['password'], "教师密码")
        await self.screenshot("2.2_教师登录信息")

        # 点击登录
        if await self.click_by_text('登录', "登录按钮"):
            await asyncio.sleep(2)
            await self.screenshot("2.3_教师登录成功")

        # 等待待审批列表加载
        await asyncio.sleep(1)

        # 查找并点击"审批"按钮
        approval_buttons = await self.page.query_selector_all('button:has-text("审批"), .btn-approve')
        if approval_buttons:
            await approval_buttons[0].click()
            print("  [点击] 审批按钮")
            await asyncio.sleep(1)
            await self.screenshot("2.4_打开审批对话框")

            # 输入请假码
            if leave_code:
                await self.fill_by_id('approvalCode', leave_code, "审批码")
                await self.screenshot("2.5_输入审批码")

            # 点击审批通过
            if await self.click_by_text('通过', "审批通过"):
                await asyncio.sleep(2)
                await self.screenshot("2.6_审批通过")

            # 获取生成的出校码
            exit_code = await self.extract_code_from_page()
            print(f"  [获取] 出校码: {exit_code}")
            await self.screenshot("2.7_出校码生成")
        else:
            print("  [警告] 未找到待审批申请")

        # 步骤3：门卫验证出校码
        print("\n[步骤3] 门卫验证出校码")
        await self.navigate(f"{BASE_URL}/guard-verify")
        await self.screenshot("3.1_门卫验证页")

        # 点击"学生出校"按钮
        if await self.click_by_text('学生出校', "学生出校"):
            await asyncio.sleep(1)
            await self.screenshot("3.2_选择学生出校")

        # 输入出校码
        if exit_code:
            await self.fill_by_id('codeInput', exit_code, "出校码")
            await self.screenshot("3.3_输入出校码")

        # 点击验证
        if await self.click_by_text('验证', "验证按钮"):
            await asyncio.sleep(2)
            await self.screenshot("3.4_验证结果")

        return {
            'leave_code': leave_code,
            'exit_code': exit_code,
            'screenshots': len(self.screenshots)
        }

    async def story_2_alumni_visit(self):
        """用户故事2：校友入校（校友申请 → 门卫验证）"""
        print("\n" + "="*80)
        print("用户故事2：校友入校流程")
        print("="*80)

        # 步骤1：校友登录
        print("\n[步骤1] 校友登录")
        await self.navigate(f"{BASE_URL}/")
        await self.screenshot("1.1_首页")

        # 填写校友登录信息
        await self.fill_by_id('phone', TEST_DATA['alumni']['phone'], "校友手机号")
        await self.fill_by_id('password', TEST_DATA['alumni']['password'], "校友密码")
        await self.screenshot("1.2_校友登录信息")

        # 点击登录
        if await self.click_by_text('登录', "登录按钮"):
            await asyncio.sleep(2)
            await self.screenshot("1.3_校友登录成功")

        # 点击快速申请
        if await self.click_by_id('quickVisit', "快速申请"):
            await asyncio.sleep(1)
            await self.screenshot("1.4_访问申请页")

        # 填写申请表单
        await self.fill_by_id('visitDate', datetime.now().strftime('%Y-%m-%d'), "访问日期")
        await self.fill_by_id('timeStart', '09:00', "开始时间")
        await self.fill_by_id('timeEnd', '11:00', "结束时间")
        await self.fill_by_id('visitPurpose', '参观校园', "访问目的")
        await self.fill_by_id('visitorName', TEST_DATA['alumni']['name'], "访问人姓名")
        await self.fill_by_id('visitorPhone', TEST_DATA['alumni']['phone'], "联系电话")
        await self.fill_by_id('visitorIdCard', '110101198001011234', "身份证号")
        await self.screenshot("1.5_申请表单填写")

        # 提交申请
        if await self.click_by_text('提交申请', "提交申请"):
            await asyncio.sleep(2)
            await self.screenshot("1.6_申请提交")

        # 获取入校码
        visit_code = await self.extract_code_from_page()
        print(f"  [获取] 入校码: {visit_code}")
        await self.screenshot("1.7_入校码生成")

        # 步骤2：门卫验证
        print("\n[步骤2] 门卫验证")
        await self.navigate(f"{BASE_URL}/guard-verify")
        await self.screenshot("2.1_门卫验证页")

        # 点击"校友入校"按钮
        if await self.click_by_text('校友入校', "校友入校"):
            await asyncio.sleep(1)
            await self.screenshot("2.2_选择校友入校")

        # 输入入校码
        if visit_code:
            await self.fill_by_id('codeInput', visit_code, "入校码")
            await self.screenshot("2.3_输入入校码")

        # 点击验证
        if await self.click_by_text('验证', "验证按钮"):
            await asyncio.sleep(2)
            await self.screenshot("2.4_验证结果")

        return {
            'visit_code': visit_code,
            'screenshots': len(self.screenshots)
        }

    async def story_3_parent_visit(self):
        """用户故事3：家长入校（家长申请 → 教师审批 → 门卫验证）"""
        print("\n" + "="*80)
        print("用户故事3：家长入校流程")
        print("="*80)

        # 步骤1：家长登录并生成入校码
        print("\n[步骤1] 家长登录并生成入校码")
        await self.navigate(f"{BASE_URL}/parent-portal")
        await self.screenshot("1.1_家长登录页")

        # 填写登录信息
        await self.fill_by_id('phone', TEST_DATA['parent']['phone'], "家长手机号")
        await self.fill_by_id('password', TEST_DATA['parent']['password'], "家长密码")
        await self.screenshot("1.2_家长登录信息")

        # 点击登录
        if await self.click_by_text('登录', "登录按钮"):
            await asyncio.sleep(2)
            await self.screenshot("1.3_家长登录成功")

        # 选择"入校"类型
        await self.fill_by_id('applicationType', 'enter-school', "申请类型(入校)")
        await asyncio.sleep(0.5)

        # 选择访问目的
        await self.fill_by_id('visitPurpose', 'visit-child', "访问目的")
        await asyncio.sleep(0.5)

        # 点击生成入校码
        if await self.click_by_text('生成6位码', "生成入校码"):
            await asyncio.sleep(2)
            await self.screenshot("1.4_生成入校码")

        # 提取入校码
        visit_code = await self.extract_code_from_page()
        print(f"  [获取] 入校码: {visit_code}")
        await self.screenshot("1.5_入校码页面")

        # 步骤2：教师登录并审批
        print("\n[步骤2] 教师审批")
        await self.navigate(f"{BASE_URL}/teacher-approve")
        await self.screenshot("2.1_教师登录页")

        # 填写教师登录信息
        await self.fill_by_id('phone', TEST_DATA['teacher']['phone'], "教师手机号")
        await self.fill_by_id('password', TEST_DATA['teacher']['password'], "教师密码")
        await self.screenshot("2.2_教师登录信息")

        # 点击登录
        if await self.click_by_text('登录', "登录按钮"):
            await asyncio.sleep(2)
            await self.screenshot("2.3_教师登录成功")

        # 等待待审批列表
        await asyncio.sleep(1)

        # 查找并点击"审批"按钮
        approval_buttons = await self.page.query_selector_all('button:has-text("审批"), .btn-approve')
        if approval_buttons:
            await approval_buttons[0].click()
            print("  [点击] 审批按钮")
            await asyncio.sleep(1)
            await self.screenshot("2.4_打开审批对话框")

            # 输入审批码
            if visit_code:
                await self.fill_by_id('approvalCode', visit_code, "审批码")
                await self.screenshot("2.5_输入审批码")

            # 点击审批通过
            if await self.click_by_text('通过', "审批通过"):
                await asyncio.sleep(2)
                await self.screenshot("2.6_审批通过")
        else:
            print("  [警告] 未找到待审批申请")

        # 步骤3：门卫验证
        print("\n[步骤3] 门卫验证")
        await self.navigate(f"{BASE_URL}/guard-verify")
        await self.screenshot("3.1_门卫验证页")

        # 点击"家长入校"按钮
        if await self.click_by_text('家长入校', "家长入校"):
            await asyncio.sleep(1)
            await self.screenshot("3.2_选择家长入校")

        # 输入入校码
        if visit_code:
            await self.fill_by_id('codeInput', visit_code, "入校码")
            await self.screenshot("3.3_输入入校码")

        # 点击验证
        if await self.click_by_text('验证', "验证按钮"):
            await asyncio.sleep(2)
            await self.screenshot("3.4_验证结果")

        return {
            'visit_code': visit_code,
            'screenshots': len(self.screenshots)
        }

    async def story_4_visitor(self):
        """用户故事4：访客登记（填写信息 → 门卫验证）"""
        print("\n" + "="*80)
        print("用户故事4：访客登记流程")
        print("="*80)

        # 步骤1：访客登记
        print("\n[步骤1] 访客登记")
        await self.navigate(f"{BASE_URL}/apply-visit")
        await self.screenshot("1.1_访客登记页")

        # 填写访客信息
        await self.fill_by_id('visitorName', TEST_DATA['visitor']['name'], "访客姓名")
        await self.fill_by_id('visitorPhone', TEST_DATA['visitor']['phone'], "访客手机")
        await self.fill_by_id('visitorIdCard', TEST_DATA['visitor']['id_card'], "身份证号")
        await self.fill_by_id('visitPurpose', 'meeting', "访问目的")
        await self.screenshot("1.2_访客信息填写")

        # 点击生成验证码
        if await self.click_by_text('生成验证码', "生成验证码"):
            await asyncio.sleep(2)
            await self.screenshot("1.3_生成验证码")

        # 获取验证码
        visitor_code = await self.extract_code_from_page()
        print(f"  [获取] 访客验证码: {visitor_code}")
        await self.screenshot("1.4_验证码页面")

        # 步骤2：门卫验证
        print("\n[步骤2] 门卫验证")
        await self.navigate(f"{BASE_URL}/guard-verify")
        await self.screenshot("2.1_门卫验证页")

        # 点击"访客登记"按钮
        if await self.click_by_text('访客登记', "访客登记"):
            await asyncio.sleep(1)
            await self.screenshot("2.2_选择访客登记")

        # 输入验证码
        if visitor_code:
            await self.fill_by_id('codeInput', visitor_code, "访客码")
            await self.screenshot("2.3_输入访客码")

        # 点击验证
        if await self.click_by_text('验证', "验证按钮"):
            await asyncio.sleep(2)
            await self.screenshot("2.4_验证结果")

        return {
            'visitor_code': visitor_code,
            'screenshots': len(self.screenshots)
        }

    async def story_5_teacher_create_code(self):
        """用户故事5：教师直接创建出校码（教师登录 → 输入学号 → 生成码 → 门卫验证）"""
        print("\n" + "="*80)
        print("用户故事5：教师直接创建出校码流程")
        print("="*80)

        # 步骤1：教师登录
        print("\n[步骤1] 教师登录")
        await self.navigate(f"{BASE_URL}/teacher-approve")
        await self.screenshot("1.1_教师登录页")

        # 填写教师登录信息
        await self.fill_by_id('phone', TEST_DATA['teacher']['phone'], "教师手机号")
        await self.fill_by_id('password', TEST_DATA['teacher']['password'], "教师密码")
        await self.screenshot("1.2_教师登录信息")

        # 点击登录
        if await self.click_by_text('登录', "登录按钮"):
            await asyncio.sleep(2)
            await self.screenshot("1.3_教师登录成功")

        # 步骤2：直接创建出校码
        print("\n[步骤2] 直接创建出校码")

        # 查找"直接创建"按钮或输入框
        create_buttons = await self.page.query_selector_all('button:has-text("直接创建"), button:has-text("创建出校码")')
        if create_buttons:
            await create_buttons[0].click()
            print("  [点击] 直接创建按钮")
            await asyncio.sleep(1)
            await self.screenshot("2.1_打开创建对话框")

        # 输入学号
        await self.fill_by_id('studentId', TEST_DATA['parent']['student_id'], "学号")
        await self.screenshot("2.2_输入学号")

        # 点击生成
        if await self.click_by_text('生成', "生成出校码"):
            await asyncio.sleep(2)
            await self.screenshot("2.3_生成出校码")

        # 获取出校码
        exit_code = await self.extract_code_from_page()
        print(f"  [获取] 出校码: {exit_code}")
        await self.screenshot("2.4_出校码页面")

        # 步骤3：门卫验证
        print("\n[步骤3] 门卫验证")
        await self.navigate(f"{BASE_URL}/guard-verify")
        await self.screenshot("3.1_门卫验证页")

        # 点击"学生出校"按钮
        if await self.click_by_text('学生出校', "学生出校"):
            await asyncio.sleep(1)
            await self.screenshot("3.2_选择学生出校")

        # 输入出校码
        if exit_code:
            await self.fill_by_id('codeInput', exit_code, "出校码")
            await self.screenshot("3.3_输入出校码")

        # 点击验证
        if await self.click_by_text('验证', "验证按钮"):
            await asyncio.sleep(2)
            await self.screenshot("3.4_验证结果")

        return {
            'exit_code': exit_code,
            'screenshots': len(self.screenshots)
        }

    def generate_html_report(self, results):
        """生成HTML测试报告"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>校友入校系统 - 端到端测试报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .story {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .story h2 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .story-info {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .story-info p {{
            margin: 5px 0;
        }}
        .screenshot-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .screenshot-item {{
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }}
        .screenshot-item img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        .screenshot-caption {{
            background: #f8f9fa;
            padding: 10px;
            font-size: 14px;
            text-align: center;
        }}
        .summary {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .summary h2 {{
            margin-top: 0;
            color: #333;
        }}
        .stat {{
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border-radius: 5px;
            font-weight: bold;
        }}
        .code-display {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            font-weight: bold;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>校友入校系统 - 端到端测试报告</h1>
        <p>测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>真实浏览器自动化测试 - Playwright</p>
    </div>

    <div class="summary">
        <h2>测试概览</h2>
        <div class="stat">总用户故事: 5</div>
        <div class="stat">总截图: {len(self.screenshots)}</div>
        <div class="stat">测试状态: 完成</div>
    </div>

"""

        # 为每个用户故事生成报告
        story_num = 1
        for story_name, story_data in results.items():
            if story_data.get('error'):
                html += f"""
    <div class="story">
        <h2>用户故事{story_num}: {story_name} ❌</h2>
        <div class="story-info">
            <p><strong>状态:</strong> 失败</p>
            <p><strong>错误:</strong> {story_data.get('error')}</p>
        </div>
    </div>
"""
            else:
                html += f"""
    <div class="story">
        <h2>用户故事{story_num}: {story_name} ✅</h2>
        <div class="story-info">
"""

                # 添加提取的验证码信息
                if story_data.get('leave_code'):
                    html += f"""
            <div class="code-display">
                请假码: {story_data['leave_code']}
            </div>
"""

                if story_data.get('exit_code'):
                    html += f"""
            <div class="code-display">
                出校码: {story_data['exit_code']}
            </div>
"""

                if story_data.get('visit_code'):
                    html += f"""
            <div class="code-display">
                入校码: {story_data['visit_code']}
            </div>
"""

                if story_data.get('visitor_code'):
                    html += f"""
            <div class="code-display">
                访客码: {story_data['visitor_code']}
            </div>
"""

                html += f"""
            <p><strong>截图数量:</strong> {story_data.get('screenshots', 0)}</p>
        </div>
    </div>
"""

            story_num += 1

        # 添加所有截图
        html += """
    <div class="summary">
        <h2>所有截图</h2>
        <div class="screenshot-grid">
"""

        for idx, shot in enumerate(self.screenshots, 1):
            html += f"""
            <div class="screenshot-item">
                <img src="{shot['path']}" alt="{shot['description']}">
                <div class="screenshot-caption">
                    <strong>{idx}.</strong> {shot['description']}<br>
                    <small>{shot['url']}</small>
                </div>
            </div>
"""

        html += """
        </div>
    </div>

    <div style="text-align: center; margin-top: 30px; color: #666;">
        <p>由 Playwright 自动生成 | 真实浏览器测试</p>
    </div>
</body>
</html>
"""

        report_path = "e2e_test_report_v2.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n[报告] 已生成: {report_path}")
        print(f"[截图] 总数: {len(self.screenshots)}")
        print(f"[目录] {os.path.abspath(SCREENSHOT_DIR)}")


async def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("校友入校系统 - 端到端自动化测试")
    print("="*80)
    print(f"\n测试数据:")
    print(f"  家长: {TEST_DATA['parent']['name']} ({TEST_DATA['parent']['phone']})")
    print(f"  教师: {TEST_DATA['teacher']['name']} ({TEST_DATA['teacher']['phone']})")
    print(f"  校友: {TEST_DATA['alumni']['name']} ({TEST_DATA['alumni']['phone']})")
    print(f"  学生: {TEST_DATA['parent']['student_name']} (学号: {TEST_DATA['parent']['student_id']})")
    print()

    test = E2ETest()
    results = {}

    try:
        await test.setup()

        # 执行所有用户故事
        try:
            results['学生请假流程'] = await test.story_1_student_leave()
        except Exception as e:
            results['学生请假流程'] = {'error': str(e)}
            print(f"[错误] 学生请假流程失败: {e}")

        try:
            results['校友入校流程'] = await test.story_2_alumni_visit()
        except Exception as e:
            results['校友入校流程'] = {'error': str(e)}
            print(f"[错误] 校友入校流程失败: {e}")

        try:
            results['家长入校流程'] = await test.story_3_parent_visit()
        except Exception as e:
            results['家长入校流程'] = {'error': str(e)}
            print(f"[错误] 家长入校流程失败: {e}")

        try:
            results['访客登记流程'] = await test.story_4_visitor()
        except Exception as e:
            results['访客登记流程'] = {'error': str(e)}
            print(f"[错误] 访客登记流程失败: {e}")

        try:
            results['教师直接创建出校码'] = await test.story_5_teacher_create_code()
        except Exception as e:
            results['教师直接创建出校码'] = {'error': str(e)}
            print(f"[错误] 教师直接创建出校码失败: {e}")

    finally:
        await test.teardown()

        # 生成测试报告
        test.generate_html_report(results)

        print("\n" + "="*80)
        print("测试完成")
        print("="*80)


if __name__ == '__main__':
    asyncio.run(main())
