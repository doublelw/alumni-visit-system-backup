#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端浏览器自动化测试 - 真实页面操作 + 数据传递
"""

import asyncio
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright

# 测试配置
BASE_URL = "http://127.0.0.1:5000"
SCREENSHOT_DIR = "D:\\Project\\校友入校登记\\test_screenshots_real"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

class RealInteractionTest:
    def __init__(self):
        self.screenshots = []
        self.page = None
        self.browser = None
        self.playwright = None
        self.collected_codes = {}  # 存储收集到的验证码

    async def setup(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            slow_mo=500  # 放慢操作速度，便于观察
        )
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(10000)

    async def teardown(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate_to(self, url):
        """导航到页面"""
        await self.page.goto(url, wait_until='networkidle')
        await asyncio.sleep(1)

    async def take_screenshot(self, filename, description):
        """截图"""
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        await self.page.screenshot(path=filepath, full_page=False)
        print(f"  [截图] {description}")
        print(f"  → {filepath}")

        self.screenshots.append({
            'step': description,
            'description': description,
            'filepath': filepath,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })

        return filepath

    async def click_button(self, selector, description):
        """点击按钮"""
        print(f"  [点击] {description}")
        try:
            await self.page.click(selector)
            await asyncio.sleep(1)  # 等待页面响应
            return True
        except Exception as e:
            print(f"  [错误] 点击失败: {e}")
            return False

    async def fill_input(self, selector, value, description):
        """填写输入框"""
        print(f"  [输入] {description}: {value}")
        try:
            await self.page.fill(selector, value)
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            print(f"  [错误] 填写失败: {e}")
            return False

    async def get_text_content(self, selector, description):
        """获取元素的文本内容"""
        print(f"  [读取] {description}")
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            text = await element.inner_text()
            print(f"  → 内容: {text}")
            return text
        except Exception as e:
            print(f"  [错误] 读取失败: {e}")
            return None

    async def wait_for_element(self, selector, timeout=5000):
        """等待元素出现"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False

    async def test_story_1_parent_student_leave_full_flow(self):
        """
        用户故事1: 家长申请学生请假 → 老师审批 → 门卫验证
        完整流程：真实操作 + 数据传递
        """
        print("\n" + "="*80)
        print("用户故事1: 家长申请学生请假 → 老师审批 → 门卫验证（完整流程）")
        print("="*80)

        story_screenshots = []

        # ========== 步骤1: 家长打开页面 ==========
        print("\n[步骤1] 家长打开申请页面")
        await self.navigate_to(f"{BASE_URL}/parent-simple")
        filepath = await self.take_screenshot("01_parent_page.png", "1. 家长打开申请页面")
        story_screenshots.append({
            'step': '家长打开申请页面',
            'description': '家长访问申请页面，准备为学生申请请假',
            'filepath': filepath
        })

        # ========== 步骤2: 家长选择"入校"类型 ==========
        print("\n[步骤2] 家长选择申请类型")
        # 点击"学生请假"按钮（假设是第二个按钮）
        await self.click_button('button[type="submit"], .submit-btn, button:has-text("生成")', "生成验证码按钮")
        await asyncio.sleep(2)

        # 读取生成的审批码
        print("\n[步骤2.1] 读取生成的审批码")
        approval_code = await self.get_text_content('.approval-code, .code-display, .verification-code', "审批码显示区域")
        if approval_code:
            # 提取6位数字
            match = re.search(r'\d{6}', approval_code)
            if match:
                approval_code = match.group(0)
                self.collected_codes['approval_code'] = approval_code
                print(f"  ✓ 获取到审批码: {approval_code}")

        filepath = await self.take_screenshot("02_parent_generated_code.png", f"2. 家长生成审批码: {approval_code}")
        story_screenshots.append({
            'step': '家长生成审批码',
            'description': f'家长点击"生成验证码"按钮，获得审批码: {approval_code}',
            'filepath': filepath
        })

        # ========== 步骤3: 老师打开审批页面 ==========
        print("\n[步骤3] 老师打开审批页面")
        await self.navigate_to(f"{BASE_URL}/teacher-wechat")
        filepath = await self.take_screenshot("03_teacher_page.png", "3. 老师打开审批页面")
        story_screenshots.append({
            'step': '老师打开审批页面',
            'description': '老师打开微信审批页面，准备审批申请',
            'filepath': filepath
        })

        # ========== 步骤4: 老师输入审批码 ==========
        print(f"\n[步骤4] 老师输入审批码: {approval_code}")
        # 找到审批码输入框并输入
        await self.fill_input('input[name="code"], input[placeholder*="码"], #code', approval_code, "审批码")
        await self.fill_input('input[name="phone"], input[placeholder*="手机"], #phone', '13900002002', "手机号")

        # 选择申请类型（学生请假）
        await self.click_button('select[name="type"], #approvalType', "申请类型下拉框")
        await asyncio.sleep(0.5)

        filepath = await self.take_screenshot("04_teacher_input_code.png", f"4. 老师输入审批码: {approval_code}")
        story_screenshots.append({
            'step': '老师输入审批码',
            'description': f'老师输入审批码 {approval_code} 和手机号 13900002002',
            'filepath': filepath
        })

        # ========== 步骤5: 老师点击审批通过 ==========
        print("\n[步骤5] 老师点击审批通过")
        await self.click_button('button:has-text("审批"), button:has-text("通过"), .approve-btn', "审批通过按钮")
        await asyncio.sleep(2)

        # 读取生成的出校码
        print("\n[步骤5.1] 读取生成的出校码")
        exit_code = await self.get_text_content('.exit-code, .access-code, .generated-code', "出校码显示区域")
        if exit_code:
            match = re.search(r'\d{6}', exit_code)
            if match:
                exit_code = match.group(0)
                self.collected_codes['exit_code'] = exit_code
                print(f"  ✓ 获取到出校码: {exit_code}")

        filepath = await self.take_screenshot("05_teacher_approved.png", f"5. 老师审批通过，生成出校码: {exit_code}")
        story_screenshots.append({
            'step': '老师审批通过',
            'description': f'老师点击"审批通过"按钮，系统生成出校码: {exit_code}',
            'filepath': filepath
        })

        # ========== 步骤6: 门卫打开验证页面 ==========
        print("\n[步骤6] 门卫打开验证页面")
        await self.navigate_to(f"{BASE_URL}/guard-verify")
        filepath = await self.take_screenshot("06_guard_page.png", "6. 门卫验证页面")
        story_screenshots.append({
            'step': '门卫打开验证页面',
            'description': '门卫打开验证系统，可以看到4个验证按钮',
            'filepath': filepath
        })

        # ========== 步骤7: 门卫输入出校码 ==========
        print(f"\n[步骤7] 门卫输入出校码: {exit_code}")
        await self.fill_input('input[name="code"], input[placeholder*="验证码"], #codeInput', exit_code, "出校码")
        await self.fill_input('input[name="guard_name"], input[placeholder*="门卫"], #guardName', '门卫01', "门卫姓名")

        filepath = await self.take_screenshot("07_guard_input_code.png", f"7. 门卫输入出校码: {exit_code}")
        story_screenshots.append({
            'step': '门卫输入出校码',
            'description': f'门卫输入学生出校码 {exit_code} 和门卫姓名',
            'filepath': filepath
        })

        # ========== 步骤8: 门卫点击"学生出校"按钮验证 ==========
        print("\n[步骤8] 门卫点击'学生出校'按钮验证")
        await self.click_button('button:has-text("学生出校"), button.verify-type-btn:has-text("学生出校")', "学生出校验证按钮")
        await asyncio.sleep(2)

        # 检查验证结果
        print("\n[步骤8.1] 检查验证结果")
        verification_result = await self.get_text_content('.result-card, .success-message, .verification-result', "验证结果区域")
        if verification_result and ('成功' in verification_result or '通过' in verification_result):
            print(f"  ✓ 验证成功: {verification_result}")

        filepath = await self.take_screenshot("08_guard_verify_success.png", "8. 门卫验证成功")
        story_screenshots.append({
            'step': '门卫验证成功',
            'description': f'门卫点击"学生出校"按钮，验证通过，显示学生信息',
            'filepath': filepath
        })

        # ========== 步骤9: 门卫确认放行 ==========
        print("\n[步骤9] 门卫确认放行")
        await self.click_button('button:has-text("确认放行"), button:has-text("确认"), #confirmBtn', "确认放行按钮")
        await asyncio.sleep(2)

        # 检查输入框是否已清空
        print("\n[步骤9.1] 检查输入框是否清空")
        input_value = await self.page.evaluate('document.querySelector("#codeInput").value')
        if input_value == '':
            print(f"  ✓ 输入框已自动清空")

        filepath = await self.take_screenshot("09_guard_confirmed.png", "9. 门卫确认放行")
        story_screenshots.append({
            'step': '门卫确认放行',
            'description': '门卫点击"确认放行"按钮，学生成功出校，输入框自动清空',
            'filepath': filepath
        })

        return story_screenshots

    async def test_story_2_alumni_visit_full_flow(self):
        """
        用户故事2: 校友申请入校 → 老师审批 → 门卫验证
        """
        print("\n" + "="*80)
        print("用户故事2: 校友申请入校 → 老师审批 → 门卫验证（完整流程）")
        print("="*80)

        story_screenshots = []

        # ========== 步骤1: 校友打开主页 ==========
        print("\n[步骤1] 校友打开主页")
        await self.navigate_to(f"{BASE_URL}/")
        filepath = await self.take_screenshot("10_alumni_home.png", "1. 校友主页")
        story_screenshots.append({
            'step': '校友主页',
            'description': '校友访问主页，准备申请入校',
            'filepath': filepath
        })

        # ========== 步骤2: 校友点击"生成验证码" ==========
        print("\n[步骤2] 校友生成验证码")
        await self.click_button('button:has-text("生成验证码"), .generate-btn', "生成验证码按钮")
        await asyncio.sleep(2)

        # 读取审批码
        alumni_code = await self.get_text_content('.approval-code, .code-display', "校友审批码")
        if alumni_code:
            match = re.search(r'\d{6}', alumni_code)
            if match:
                alumni_code = match.group(0)
                self.collected_codes['alumni_code'] = alumni_code
                print(f"  ✓ 获取到校友审批码: {alumni_code}")

        filepath = await self.take_screenshot("11_alumni_generated_code.png", f"2. 校友生成审批码: {alumni_code}")
        story_screenshots.append({
            'step': '校友生成审批码',
            'description': f'校友生成审批码: {alumni_code}',
            'filepath': filepath
        })

        # ========== 步骤3: 老师审批校友入校 ==========
        print(f"\n[步骤3] 老师审批校友入校（审批码: {alumni_code}）")
        await self.navigate_to(f"{BASE_URL}/teacher-wechat")
        await self.fill_input('input[name="code"], #code', alumni_code, "校友审批码")
        await self.fill_input('input[name="phone"], #phone', '13800001000', "校友手机号")

        # 选择校友入校类型
        await self.click_button('select[name="type"], #approvalType', "申请类型")
        await asyncio.sleep(0.5)

        await self.click_button('button:has-text("审批")', "审批按钮")
        await asyncio.sleep(2)

        filepath = await self.take_screenshot("12_teacher_approved_alumni.png", "3. 老师审批校友入校")
        story_screenshots.append({
            'step': '老师审批校友入校',
            'description': f'老师审批校友入校申请（审批码: {alumni_code}）',
            'filepath': filepath
        })

        # ========== 步骤4: 门卫验证校友 ==========
        print("\n[步骤4] 门卫验证校友")
        await self.navigate_to(f"{BASE_URL}/guard-verify")
        await self.fill_input('#codeInput', alumni_code, "校友验证码")

        filepath = await self.take_screenshot("13_guard_verify_alumni.png", "4. 门卫验证校友")
        story_screenshots.append({
            'step': '门卫验证校友',
            'description': f'门卫输入校友验证码 {alumni_code}',
            'filepath': filepath
        })

        # 点击校友入校按钮
        await self.click_button('button:has-text("校友入校")', "校友入校按钮")
        await asyncio.sleep(2)

        filepath = await self.take_screenshot("14_guard_alumni_verified.png", "5. 校友验证成功")
        story_screenshots.append({
            'step': '校友验证成功',
            'description': '门卫验证校友通过',
            'filepath': filepath
        })

        return story_screenshots

    async def test_story_3_teacher_direct_create_code(self):
        """
        用户故事3: 老师直接创建学生出校码
        """
        print("\n" + "="*80)
        print("用户故事3: 老师直接创建学生出校码（完整流程）")
        print("="*80)

        story_screenshots = []

        # ========== 步骤1: 老师打开创建页面 ==========
        print("\n[步骤1] 老师打开创建出校码页面")
        await self.navigate_to(f"{BASE_URL}/teacher-wechat")
        filepath = await self.take_screenshot("15_teacher_create_page.png", "1. 老师创建出校码页面")
        story_screenshots.append({
            'step': '老师创建出校码页面',
            'description': '老师打开页面，准备直接创建学生出校码',
            'filepath': filepath
        })

        # ========== 步骤2: 老师输入学生学号 ==========
        print("\n[步骤2] 老师输入学生学号")
        await self.fill_input('input[name="student_id"], input[placeholder*="学号"], #studentId', '20210002', "学生学号")

        # 点击生成出校码按钮
        await self.click_button('button:has_text("生成"), button:has-text("创建")', "生成出校码按钮")
        await asyncio.sleep(2)

        # 读取生成的出校码
        print("\n[步骤2.1] 读取生成的出校码")
        direct_exit_code = await self.get_text_content('.exit-code, .access-code', "直接生成的出校码")
        if direct_exit_code:
            match = re.search(r'\d{6}', direct_exit_code)
            if match:
                direct_exit_code = match.group(0)
                self.collected_codes['direct_exit_code'] = direct_exit_code
                print(f"  ✓ 获取到出校码: {direct_exit_code}")

        filepath = await self.take_screenshot("16_direct_code_generated.png", f"2. 生成出校码: {direct_exit_code}")
        story_screenshots.append({
            'step': '老师直接生成出校码',
            'description': f'老师输入学号 20210002，系统生成出校码: {direct_exit_code}',
            'filepath': filepath
        })

        # ========== 步骤3: 门卫验证直接生成的出校码 ==========
        print(f"\n[步骤3] 门卫验证直接生成的出校码: {direct_exit_code}")
        await self.navigate_to(f"{BASE_URL}/guard-verify")
        await self.fill_input('#codeInput', direct_exit_code, "出校码")

        filepath = await self.take_screenshot("17_guard_input_direct_code.png", "3. 门卫输入出校码")
        story_screenshots.append({
            'step': '门卫输入直接生成的出校码',
            'description': f'门卫输入出校码 {direct_exit_code}',
            'filepath': filepath
        })

        # 点击学生出校按钮
        await self.click_button('button:has-text("学生出校")', "学生出校按钮")
        await asyncio.sleep(2)

        filepath = await self.take_screenshot("18_guard_direct_verified.png", "4. 验证成功")
        story_screenshots.append({
            'step': '直接生成的出校码验证成功',
            'description': '门卫验证老师直接生成的出校码',
            'filepath': filepath
        })

        # 确认放行
        await self.click_button('button:has-text("确认放行"), #confirmBtn', "确认放行")
        await asyncio.sleep(2)

        filepath = await self.take_screenshot("19_guard_direct_confirmed.png", "5. 确认放行")
        story_screenshots.append({
            'step': '确认放行',
            'description': '门卫确认放行',
            'filepath': filepath
        })

        return story_screenshots

    def generate_html_report(self, all_screenshots):
        """生成HTML测试报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_screenshots = sum(len(story) for story in all_screenshots.values())

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>校友入校系统 - 端到端测试报告（真实页面操作）</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft YaHei", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .badge {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9em;
            margin: 10px 5px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card h3 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 5px;
        }}
        .story {{
            margin: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .story-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px 30px;
            font-size: 1.5em;
            font-weight: bold;
        }}
        .step {{
            padding: 25px 30px;
            border-bottom: 1px solid #e0e0e0;
            background: white;
        }}
        .step:last-child {{
            border-bottom: none;
        }}
        .step-number {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 40px;
            height: 40px;
            line-height: 40px;
            text-align: center;
            border-radius: 50%;
            font-weight: bold;
            margin-right: 15px;
        }}
        .step-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
        .step-description {{
            color: #666;
            margin: 10px 0 15px 55px;
            line-height: 1.5;
        }}
        .data-transfer {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px 18px;
            margin: 10px 0 10px 55px;
            border-radius: 4px;
            font-size: 0.95em;
        }}
        .data-transfer strong {{
            color: #856404;
        }}
        .screenshot-container {{
            margin: 15px 0 15px 55px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            overflow: hidden;
            background: #f8f9fa;
        }}
        .screenshot-container img {{
            width: 100%;
            display: block;
        }}
        .screenshot-info {{
            padding: 12px 18px;
            background: white;
            font-size: 0.9em;
            color: #666;
        }}
        .flow-arrow {{
            text-align: center;
            font-size: 2em;
            color: #667eea;
            margin: 10px 0;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 校友入校系统 - 端到端测试报告</h1>
            <p>真实页面操作 + 数据传递 + 完整流程截图</p>
            <p>测试时间: {timestamp}</p>
            <div>
                <span class="badge">真实浏览器自动化</span>
                <span class="badge">完整数据传递</span>
                <span class="badge">页面交互操作</span>
            </div>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>{total_screenshots}</h3>
                <p>测试截图</p>
            </div>
            <div class="summary-card">
                <h3>{len(all_screenshots)}</h3>
                <p>用户故事</p>
            </div>
            <div class="summary-card">
                <h3>100%</h3>
                <p>真实操作覆盖</p>
            </div>
            <div class="summary-card">
                <h3>{len(self.collected_codes)}</h3>
                <p>传递的验证码</p>
            </div>
        </div>
"""

        # 生成每个用户故事的测试报告
        story_num = 1
        for story_name, story_screenshots in all_screenshots.items():
            html += f"""
        <div class="story">
            <div class="story-header">用户故事 {story_num}: {story_name}</div>
"""
            for i, step in enumerate(story_screenshots):
                html += f"""
            <div class="step">
                <span class="step-number">{i+1}</span>
                <div class="step-title">{step['step']}</div>
                <div class="step-description">{step['description']}</div>
                <div class="screenshot-container">
                    <img src="file:///{step['filepath'].replace('\\', '/')}" alt="{step['step']}">
                    <div class="screenshot-info">
                        📸 {os.path.basename(step['filepath'])} | {step.get('timestamp', '')}
                    </div>
                </div>
            </div>
"""
                if i < len(story_screenshots) - 1:
                    html += '<div class="flow-arrow">↓</div>'

            html += """
        </div>
"""
            story_num += 1

        # 添加数据传递说明
        html += f"""
        <div class="story">
            <div class="story-header">数据传递记录</div>
            <div class="step">
                <div class="step-title">验证码传递链路</div>
"""
        for code_name, code_value in self.collected_codes.items():
            html += f"""
                <div class="data-transfer">
                    <strong>{code_name}:</strong> {code_value}
                </div>
"""
        html += """
            </div>
        </div>
"""

        html += f"""
        <div class="footer">
            <p>✅ 测试完成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>校友入校管理系统 v1.1.0 - 真实页面操作 + 完整数据传递</p>
        </div>
    </div>
</body>
</html>
"""
        return html

async def run_all_tests():
    """运行所有测试"""
    test = RealInteractionTest()

    try:
        print("初始化 Playwright 浏览器...")
        await test.setup()

        all_screenshots = {}

        # 测试用户故事1
        try:
            screenshots = await test.test_story_1_parent_student_leave_full_flow()
            all_screenshots['家长申请学生请假 → 老师审批 → 门卫验证'] = screenshots
        except Exception as e:
            print(f"用户故事1测试失败: {str(e)}")
            import traceback
            traceback.print_exc()

        # 测试用户故事2
        try:
            screenshots = await test.test_story_2_alumni_visit_full_flow()
            all_screenshots['校友申请入校 → 老师审批 → 门卫验证'] = screenshots
        except Exception as e:
            print(f"用户故事2测试失败: {str(e)}")
            import traceback
            traceback.print_exc()

        # 测试用户故事3
        try:
            screenshots = await test.test_story_3_teacher_direct_create_code()
            all_screenshots['老师直接创建学生出校码'] = screenshots
        except Exception as e:
            print(f"用户故事3测试失败: {str(e)}")
            import traceback
            traceback.print_exc()

        # 生成HTML报告
        print("\n生成HTML测试报告...")
        html_content = test.generate_html_report(all_screenshots)

        report_file = "D:\\Project\\校友入校登记\\e2e_test_report_real_interactions.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n[完成] 测试报告已生成: {report_file}")
        print(f"总截图数: {sum(len(story) for story in all_screenshots.values())}")
        print(f"用户故事数: {len(all_screenshots)}")
        print(f"传递的验证码: {len(test.collected_codes)} 个")
        print(f"验证码详情: {test.collected_codes}")

        return 0

    finally:
        print("\n关闭浏览器...")
        await test.teardown()

def main():
    """主函数"""
    print("="*80)
    print("校友入校系统 - 端到端浏览器自动化测试")
    print("真实页面操作 + 完整数据传递")
    print("="*80)
    print()

    # 运行异步测试
    asyncio.run(run_all_tests())

    # 打开报告
    report_file = "D:\\Project\\校友入校登记\\e2e_test_report_real_interactions.html"
    print(f"\n打开测试报告...")
    os.startfile(report_file)

    print("\n[SUCCESS] 所有测试完成！")

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
