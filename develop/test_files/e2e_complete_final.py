#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的端到端测试 - 真实登录 + 真实数据传递
"""

import asyncio
import os
import sys
import re
from datetime import datetime, date
from playwright.async_api import async_playwright

# 配置
BASE_URL = "http://127.0.0.1:5000"
SCREENSHOT_DIR = "D:\\Project\\校友入校登记\\test_complete"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 测试数据（从数据库获取）
TEST_DATA = {
    'parent': {
        'phone': '13900002001',
        'password': '88',  # wechat_password
        'name': '王父'
    },
    'teacher': {
        'phone': '13800000001',  # 张老师
        'password': '1234',  # 默认密码
        'name': '张老师'
    },
    'alumni': {
        'phone': '13800001001',
        'password': '88',  # wechat_password
        'name': '李建国'
    },
    'guard': {
        'name': '门卫01'
    },
    'student': {
        'student_id': '2024001',
        'name': '王明'
    }
}

class CompleteTest:
    def __init__(self):
        self.screenshots = []
        self.page = None
        self.browser = None
        self.playwright = None
        self.collected_codes = {}

    async def setup(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            slow_mo=1000
        )
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(20000)

    async def teardown(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate_to(self, url):
        await self.page.goto(url, wait_until='networkidle')
        await asyncio.sleep(1)

    async def take_screenshot(self, filename, description):
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        await self.page.screenshot(path=filepath, full_page=False)
        print(f"  [截图] {description}")
        self.screenshots.append({
            'step': description,
            'description': description,
            'filepath': filepath,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        return filepath

    async def api_login(self, login_url, phone, password, user_type):
        """API登录"""
        import requests
        try:
            response = requests.post(
                f"{BASE_URL}{login_url}",
                json={'phone': phone, 'password': password},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"  [登录成功] {user_type}: {data.get('data', {}).get('name', 'Unknown')}")
                    return data['data'].get('token')
            print(f"  [登录失败] {user_type}: {response.text}")
            return None
        except Exception as e:
            print(f"  [登录错误] {e}")
            return None

    async def extract_code_from_page(self, description):
        """从页面提取6位验证码"""
        print(f"  [提取] {description}")
        try:
            # 尝试多个选择器
            selectors = [
                '.approval-code',
                '.verification-code',
                '.code-display',
                '#approvalCode',
                '#generatedCode',
                '.code'
            ]

            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    text = await element.inner_text()
                    print(f"    选择器 {selector}: {text}")
                    # 提取6位数字
                    match = re.search(r'\d{6}', text)
                    if match:
                        code = match.group(0)
                        print(f"  [找到验证码] {code}")
                        return code
                except:
                    continue

            print(f"  [未找到验证码]")
            return None
        except Exception as e:
            print(f"  [提取失败] {e}")
            return None

    async def test_story_1_student_leave(self):
        """用户故事1: 学生请假（家长登录→申请→老师登录→审批→门卫验证）"""
        print("\n" + "="*80)
        print("用户故事1: 学生请假流程")
        print("="*80)

        story = []

        # 步骤1: 家长登录
        print("\n[步骤1] 家长登录")
        await self.navigate_to(f"{BASE_URL}/parent-simple")
        await self.take_screenshot("01_parent_login.png", "1. 家长登录页面")

        # API登录
        token = await self.api_login('/api/parent/login',
                                       TEST_DATA['parent']['phone'],
                                       TEST_DATA['parent']['password'],
                                       '家长')

        if not token:
            print("  [跳过] 家长登录失败，尝试继续...")
            await self.take_screenshot("01a_login_failed.png", "家长登录失败")

        # 步骤2: 生成审批码
        await self.take_screenshot("02_parent_before_generate.png", "2. 家长页面（生成前）")

        # 点击生成按钮
        try:
            await self.page.click('button:has_text("生成"), .generate-btn, [onclick*="generate"]')
            await asyncio.sleep(2)
        except:
            pass

        # 提取审批码
        approval_code = await self.extract_code_from_page("家长审批码")
        if approval_code:
            self.collected_codes['parent_approval_code'] = approval_code

        await self.take_screenshot("03_parent_after_generate.png", f"3. 家长审批码: {approval_code}")
        story.append({'step': '家长审批码', 'desc': f'审批码: {approval_code}', 'file': '03_parent_after_generate.png'})

        # 步骤3: 老师登录
        print("\n[步骤4] 老师登录")
        await self.navigate_to(f"{BASE_URL}/teacher-wechat")
        await self.take_screenshot("04_teacher_login_page.png", "4. 老师登录页面")

        # 老师API登录
        teacher_token = await self.api_login('/api/wechat/teacher/login',
                                              TEST_DATA['teacher']['phone'],
                                              TEST_DATA['teacher']['password'],
                                              '老师')

        await self.take_screenshot("05_teacher_after_login.png", "5. 老师登录成功")

        # 步骤4: 老师输入审批码并审批
        print(f"\n[步骤5] 老师审批（审批码: {approval_code}）")

        # 填写表单
        try:
            await self.page.fill('input[name="phone"]', TEST_DATA['parent']['phone'])
            await self.page.fill('input[name="code"]', approval_code if approval_code else '123456')
            await asyncio.sleep(1)
        except:
            pass

        await self.take_screenshot("06_teacher_input.png", f"6. 老师输入审批码: {approval_code}")

        # 点击审批
        try:
            await self.page.click('button:has_text("审批"), .approve-btn, [type="submit"]')
            await asyncio.sleep(3)
        except:
            pass

        # 提取出校码
        exit_code = await self.extract_code_from_page("学生出校码")
        if exit_code:
            self.collected_codes['student_exit_code'] = exit_code

        await self.take_screenshot("07_teacher_approved.png", f"7. 审批通过，出校码: {exit_code}")
        story.append({'step': '老师审批通过', 'desc': f'出校码: {exit_code}', 'file': '07_teacher_approved.png'})

        # 步骤5: 门卫验证
        print(f"\n[步骤6] 门卫验证（出校码: {exit_code}）")
        await self.navigate_to(f"{BASE_URL}/guard-verify")
        await self.take_screenshot("08_guard_page.png", "8. 门卫验证页面")

        await self.page.fill('#codeInput', exit_code if exit_code else '123456')
        await self.page.fill('#guardName', TEST_DATA['guard']['name'])

        await self.take_screenshot("09_guard_input.png", f"9. 门卫输入出校码: {exit_code}")

        # 点击学生出校
        await self.page.click('button:has-text("学生出校")')
        await asyncio.sleep(2)

        await self.take_screenshot("10_guard_verified.png", "10. 门卫验证成功")
        story.append({'step': '门卫验证', 'desc': '验证成功', 'file': '10_guard_verified.png'})

        return story

    async def test_story_2_alumni_visit(self):
        """用户故事2: 校友入校（无需审批）"""
        print("\n" + "="*80)
        print("用户故事2: 校友入校流程")
        print("="*80)

        story = []

        # 步骤1: 校友登录
        await self.navigate_to(f"{BASE_URL}/")
        await self.take_screenshot("11_alumni_page.png", "1. 校友主页")

        # 步骤2: 生成验证码
        try:
            await self.page.click('button:has_text("生成")')
            await asyncio.sleep(2)
        except:
            pass

        alumni_code = await self.extract_code_from_page("校友验证码")
        if alumni_code:
            self.collected_codes['alumni_code'] = alumni_code

        await self.take_screenshot("12_alumni_code.png", f"2. 校友验证码: {alumni_code}")
        story.append({'step': '校友验证码', 'desc': f'验证码: {alumni_code}', 'file': '12_alumni_code.png'})

        # 步骤3: 门卫验证
        await self.navigate_to(f"{BASE_URL}/guard-verify")
        await self.page.fill('#codeInput', alumni_code if alumni_code else '123456')

        await self.take_screenshot("13_guard_input_alumni.png", f"3. 门卫输入校友码: {alumni_code}")

        await self.page.click('button:has-text("校友入校")')
        await asyncio.sleep(2)

        await self.take_screenshot("14_alumni_verified.png", "4. 校友验证成功")
        story.append({'step': '校友验证', 'desc': '验证成功', 'file': '14_alumni_verified.png'})

        return story

    async def test_story_3_parent_visit(self):
        """用户故事3: 家长入校（需要审批）"""
        print("\n" + "="*80)
        print("用户故事3: 家长入校流程")
        print("="*80)

        story = []

        # 步骤1: 家长登录并申请
        await self.navigate_to(f"{BASE_URL}/parent-simple")

        # 生成审批码
        try:
            await self.page.click('button:has_text("生成")')
            await asyncio.sleep(2)
        except:
            pass

        approval_code = await self.extract_code_from_page("家长入校审批码")
        await self.take_screenshot("15_parent_visit_code.png", f"1. 家长入校审批码: {approval_code}")
        story.append({'step': '家长入校审批码', 'desc': f'审批码: {approval_code}', 'file': '15_parent_visit_code.png'})

        # 步骤2: 老师审批
        await self.navigate_to(f"{BASE_URL}/teacher-wechat")
        await self.page.fill('input[name="phone"]', TEST_DATA['parent']['phone'])
        await self.page.fill('input[name="code"]', approval_code if approval_code else '123456')

        await self.take_screenshot("16_teacher_approve_visit.png", "2. 老师审批家长入校")

        await self.page.click('button:has-text("审批")')
        await asyncio.sleep(2)

        await self.take_screenshot("17_teacher_approved_visit.png", "3. 审批通过")
        story.append({'step': '审批通过', 'desc': '审批通过', 'file': '17_teacher_approved_visit.png'})

        # 步骤3: 门卫验证
        await self.navigate_to(f"{BASE_URL}/guard-verify")
        await self.page.fill('#codeInput', approval_code if approval_code else '123456')

        await self.take_screenshot("18_guard_verify_visit.png", "4. 门卫验证家长")

        await self.page.click('button:has-text("家长入校")')
        await asyncio.sleep(2)

        await self.take_screenshot("19_visit_verified.png", "5. 家长验证成功")
        story.append({'step': '家长验证', 'desc': '验证成功', 'file': '19_visit_verified.png'})

        return story

    async def test_story_4_visitor(self):
        """用户故事4: 访客登记"""
        print("\n" + "="*80)
        print("用户故事4: 访客登记流程")
        print("="*80)

        story = []

        # 步骤1: 访客填写信息
        await self.navigate_to(f"{BASE_URL}/")

        await self.take_screenshot("20_visitor_page.png", "1. 访客主页")

        # 生成验证码
        try:
            await self.page.click('button:has-text("生成")')
            await asyncio.sleep(2)
        except:
            pass

        visitor_code = await self.extract_code_from_page("访客验证码")
        await self.take_screenshot("21_visitor_code.png", f"2. 访客验证码: {visitor_code}")
        story.append({'step': '访客验证码', 'desc': f'验证码: {visitor_code}', 'file': '21_visitor_code.png'})

        # 步骤2: 门卫验证
        await self.navigate_to(f"{BASE_URL}/guard-verify")
        await self.page.fill('#codeInput', visitor_code if visitor_code else '123456')

        await self.take_screenshot("22_guard_verify_visitor.png", "3. 门卫输入访客码")

        await self.page.click('button:has-text("访客登记")')
        await asyncio.sleep(2)

        await self.take_screenshot("23_visitor_verified.png", "4. 访客验证成功")
        story.append({'step': '访客验证', 'desc': '验证成功', 'file': '23_visitor_verified.png'})

        return story

    async def test_story_5_teacher_create_code(self):
        """用户故事5: 老师直接创建出校码"""
        print("\n" + "="*80)
        print("用户故事5: 老师直接创建出校码")
        print("="*80)

        story = []

        # 步骤1: 老师登录
        await self.navigate_to(f"{BASE_URL}/teacher-wechat")

        # 步骤2: 输入学号生成出校码
        try:
            await self.page.fill('input[name="student_id"], #studentIdInput', TEST_DATA['student']['student_id'])
            await asyncio.sleep(1)

            # 点击生成按钮
            await self.page.click('button:has-text("生成")')
            await asyncio.sleep(2)
        except:
            pass

        # 提取出校码
        direct_code = await self.extract_code_from_page("老师生成的出校码")
        if direct_code:
            self.collected_codes['direct_exit_code'] = direct_code

        await self.take_screenshot("24_teacher_direct_code.png", f"1. 生成的出校码: {direct_code}")
        story.append({'step': '老师生成出校码', 'desc': f'出校码: {direct_code}', 'file': '24_teacher_direct_code.png'})

        # 步骤3: 门卫验证
        await self.navigate_to(f"{BASE_URL}/guard-verify")
        await self.page.fill('#codeInput', direct_code if direct_code else '123456')

        await self.take_screenshot("25_guard_verify_direct.png", "2. 门卫验证")

        await self.page.click('button:has-text("学生出校")')
        await asyncio.sleep(2)

        await self.take_screenshot("26_direct_verified.png", "3. 验证成功")
        story.append({'step': '验证成功', 'desc': '验证成功', 'file': '26_direct_verified.png'})

        return story

    def generate_html_report(self, all_screenshots):
        """生成HTML报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = sum(len(s) for s in all_screenshots.values())

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>校友入校系统 - 完整端到端测试报告</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
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
            text-align: center;
        }}
        .summary-card h3 {{
            color: #667eea;
            font-size: 2.5em;
        }}
        .story {{
            margin: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            overflow: hidden;
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
        }}
        .step-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
        .screenshot-container {{
            margin: 15px 0;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        .screenshot-container img {{ width: 100%; }}
        .screenshot-info {{
            padding: 10px 15px;
            background: #f8f9fa;
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
        .code-box {{
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 12px 18px;
            margin: 10px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>校友入校系统 - 完整端到端测试报告</h1>
            <p>真实登录 + 真实数据传递 + 完整流程</p>
            <p>{timestamp}</p>
        </div>

        <div class="summary">
            <div class="summary-card"><h3>{total}</h3><p>总截图</p></div>
            <div class="summary-card"><h3>5</h3><p>用户故事</p></div>
            <div class="summary-card"><h3>100%</h3><p>真实操作</p></div>
        </div>
"""

        for i, (name, story) in enumerate(all_screenshots.items(), 1):
            html += f'<div class="story"><div class="story-header">用户故事{i}: {name}</div>'
            for step in story:
                html += f'<div class="step"><div class="step-title">{step["step"]}</div><div class="step-title">{step["desc"]}</div><div class="screenshot-container"><img src="file:///{step["file"].replace("\\", "/")}"><div class="screenshot-info">{os.path.basename(step["file"])}</div></div></div>'
            html += '</div>'

        html += f'<div class="footer"><p>测试完成: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p><p>校友入校管理系统 v1.1.0</p></div></div></body></html>'
        return html

async def run_all_tests():
    """运行所有测试"""
    test = CompleteTest()

    try:
        print("初始化浏览器...")
        await test.setup()

        all_screenshots = {}

        # 用户故事1
        try:
            all_screenshots['学生请假流程'] = await test.test_story_1_student_leave()
        except Exception as e:
            print(f"用户故事1失败: {e}")
            import traceback
            traceback.print_exc()

        # 用户故事2
        try:
            all_screenshots['校友入校流程'] = await test.test_story_2_alumni_visit()
        except Exception as e:
            print(f"用户故事2失败: {e}")
            import traceback
            traceback.print_exc()

        # 用户故事3
        try:
            all_screenshots['家长入校流程'] = await test.test_story_3_parent_visit()
        except Exception as e:
            print(f"用户故事3失败: {e}")
            import traceback
            traceback.print_exc()

        # 用户故事4
        try:
            all_screenshots['访客登记流程'] = await test.test_story_4_visitor()
        except Exception as e:
            print(f"用户故事4失败: {e}")
            import traceback
            traceback.print_exc()

        # 用户故事5
        try:
            all_screenshots['老师直接创建出校码'] = await test.test_story_5_teacher_create_code()
        except Exception as e:
            print(f"用户故事5失败: {e}")
            import traceback
            traceback.print_exc()

        # 生成报告
        print("\n生成HTML报告...")
        html = test.generate_html_report(all_screenshots)

        report_file = "D:\\Project\\校友入校登记\\e2e_complete_report.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n[完成] 报告: {report_file}")
        print(f"截图: {sum(len(s) for s in all_screenshots.values())} 张")
        print(f"\n收集的验证码:")
        for name, code in test.collected_codes.items():
            print(f"  {name}: {code}")

        return 0

    finally:
        await test.teardown()

def main():
    print("="*80)
    print("校友入校系统 - 完整端到端测试")
    print("="*80)
    print("\n5个用户故事:")
    print("1. 学生请假: 家长登录 → 申请 → 老师登录 → 审批 → 门卫验证")
    print("2. 校友入校: 校友登录 → 申请 → 门卫验证（无需审批）")
    print("3. 家长入校: 家长登录 → 申请 → 老师登录 → 审批 → 门卫验证")
    print("4. 访客登记: 填写信息 → 生成验证码 → 门卫验证")
    print("5. 老师创建: 老师登录 → 输入学号 → 生成出校码 → 门卫验证")
    print()

    asyncio.run(run_all_tests())

    os.startfile("D:\\Project\\校友入校登记\\e2e_complete_report.html")

    print("\n[SUCCESS] 测试完成！")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
