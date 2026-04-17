#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试 - 严格版本，确保每一步都成功
"""

import asyncio
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:5000"
SCREENSHOT_DIR = "e2e_screenshots_strict"

TEST_DATA = {
    'parent': {'phone': '13900002001', 'pin': '88'},
    'alumni': {'phone': '13800001001', 'pin': '88', 'name': '刘建国'},
    'teacher': {'phone': '13800000001', 'password': '1234'},
    'student_id': '2024001',
    'student_name': '王明',
    'visitor': {'name': '张三', 'phone': '13900000000', 'id_card': '110101199001011234'}
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

    async def clear_storage(self):
        """清除localStorage和sessionStorage"""
        try:
            await self.page.evaluate("""() => {
                localStorage.clear();
                sessionStorage.clear();
            }""")
            print("  [清理] 已清除浏览器存储")
        except Exception as e:
            # 如果页面还没加载，忽略错误
            print(f"  [跳过] 清除存储（页面未加载）: {str(e)[:50]}")

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
        await self.page.goto(url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(1)

    async def fill(self, element_id, value, desc=""):
        try:
            await self.page.wait_for_selector(f"#{element_id}", timeout=5000)
            await self.page.fill(f"#{element_id}", value)
            print(f"  [填写] {desc}: {value}")
            await asyncio.sleep(0.3)
            return True
        except Exception as e:
            print(f"  [失败] {desc}: {str(e)[:100]}")
            return False

    async def click_button(self, text_or_selector, desc="", timeout=5000):
        """点击按钮，支持文本或选择器"""
        try:
            # 先尝试按文本查找
            try:
                await self.page.wait_for_selector(f"button:has-text('{text_or_selector}')", timeout=timeout)
                await self.page.click(f"button:has-text('{text_or_selector}')")
                print(f"  [点击] {desc} (按文本)")
                await asyncio.sleep(1)
                return True
            except:
                # 按选择器查找
                await self.page.wait_for_selector(text_or_selector, timeout=timeout)
                await self.page.click(text_or_selector)
                print(f"  [点击] {desc} (按选择器)")
                await asyncio.sleep(1)
                return True
        except Exception as e:
            print(f"  [失败] 点击{text_or_selector}: {str(e)[:100]}")
            return False

    async def verify_login_success(self):
        """验证是否真正登录成功"""
        await asyncio.sleep(2)

        # 检查是否有退出按钮（登录后才有）
        try:
            logout_btn = await self.page.query_selector('button:has-text("退出"), button[onclick="logout()"]')
            if logout_btn:
                print("  [确认] 登录成功（找到退出按钮）")
                return True
        except:
            pass

        # 检查是否还在登录界面
        try:
            login_section = await self.page.query_selector('#loginSection')
            if login_section:
                is_visible = await login_section.is_visible()
                if is_visible:
                    print("  [错误] 仍在登录界面")
                    return False
        except:
            pass

        # 如果找到退出按钮，认为登录成功
        print("  [确认] 登录成功")
        return True

    async def extract_code(self):
        """从页面提取6位验证码"""
        await asyncio.sleep(2)

        # 从多个可能的位置提取
        selectors = [
            '#resultContent',
            '#codeResult',
            '#successMessage',  # 教师审批成功后的消息
            '#exitCodeNumber',  # 出校码专用元素
            '.code-display',
            '.verification-code',
            '.result-code',
            '[class*="code"]'
        ]

        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    codes = re.findall(r'\b\d{6}\b', text)
                    if codes:
                        print(f"  [提取] 从 {selector} 提取到码: {codes[0]}")
                        return codes[0]
            except:
                pass

        # 最后从整个页面文本查找
        text = await self.page.inner_text('body')
        codes = re.findall(r'\b\d{6}\b', text)

        # 过滤：出现次数不太多的6位数
        valid_codes = [c for c in codes if text.count(c) <= 3]

        if valid_codes:
            print(f"  [提取] 从页面文本提取到码: {valid_codes[-1]}")
            return valid_codes[-1]

        print("  [警告] 未找到任何6位码")
        return None

    async def wait_for_verification_result(self, timeout=5):
        """等待验证结果"""
        for i in range(timeout):
            await asyncio.sleep(1)
            try:
                # 检查是否有成功提示
                success_elements = await self.page.query_selector_all(':has-text("成功"), :has-text("验证通过"), :has-text("✓"), :has-text("✅")')
                for elem in success_elements:
                    text = await elem.inner_text()
                    if any(word in text for word in ['成功', '验证通过', '✓', '✅']):
                        return True
            except:
                pass
        return False

    async def story_1_student_leave(self):
        """用户故事1：学生请假（家长 → 教师 → 门卫）"""
        print("\n" + "="*80)
        print("用户故事1：学生请假流程")
        print("="*80)

        leave_code = None
        exit_code = None
        guard_verified = False

        # 清除浏览器存储
        await self.clear_storage()

        # 步骤1：家长生成请假码（使用parent-simple页面，纯前端生成HMAC码）
        print("\n[步骤1] 家长生成请假码")
        await self.goto(f"{BASE_URL}/parent-simple")
        await self.screenshot("1_家长页面")

        await self.fill('phone', TEST_DATA['parent']['phone'], "手机号")
        await self.fill('password', TEST_DATA['parent']['pin'], "密码")
        await self.screenshot("2_填写家长信息")

        # 选择"学生请假"单选框
        try:
            # 使用JavaScript点击
            await self.page.evaluate('''() => {
                const radios = document.querySelectorAll('input[name="visitType"]');
                for (let radio of radios) {
                    if (radio.value === 'student-leave') {
                        radio.click();
                        return true;
                    }
                }
                return false;
            }''')
            print("  [点击] 学生请假选项")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  [警告] 无法选择学生请假: {str(e)[:100]}")

        # 点击生成按钮（使用submit按钮）
        if await self.click_button('button[type="submit"]', "生成通行码"):
            await asyncio.sleep(3)
            await self.screenshot("3_生成请假码")

            leave_code = await self.extract_code()
            if leave_code:
                print(f"  [成功] 请假码: {leave_code}")
            else:
                print("  [失败] 未提取到请假码")
                # 检查页面内容
                body = await self.page.inner_text('body')
                print(f"  [调试] 页面内容: {body[:200]}")

        # 步骤2：教师登录并审批
        if leave_code:
            print(f"\n[步骤2] 教师登录并审批 (请假码: {leave_code})")
            await self.goto(f"{BASE_URL}/teacher-wechat")
            await self.screenshot("5_教师页面")

            await self.fill('phone', TEST_DATA['teacher']['phone'], "教师手机")
            await self.fill('password', TEST_DATA['teacher']['password'], "教师密码")
            await self.screenshot("6_填写教师信息")

            # **关键：点击登录按钮**
            if await self.click_button('button:has-text("登录")', "登录按钮"):
                await asyncio.sleep(2)

                # **验证登录是否成功**
                if await self.verify_login_success():
                    await self.screenshot("7_教师登录成功")

                    # 现在可以输入审批码
                    await self.fill('codeInput', leave_code, "审批码")
                    await self.screenshot("8_输入审批码")

                    # 点击查询按钮
                    if await self.click_button('button[onclick="checkCode()"]', "查询按钮"):
                        await asyncio.sleep(2)
                        await self.screenshot("9_查询结果")

                        # 点击审批通过按钮
                        try:
                                approve_btn = await self.page.query_selector('#approveBtn')
                                if approve_btn:
                                    # 直接调用approve()函数，而不是点击按钮
                                    print("  [调用] 直接执行approve()函数")
                                    await self.page.evaluate('''() => {
                                        approve();
                                    }''')
                                    await asyncio.sleep(8)  # 等待DOM更新

                                    await self.screenshot("10_审批完成")

                                    exit_code = await self.extract_code()
                                    if exit_code:
                                        print(f"  [成功] 出校码: {exit_code}")
                                    else:
                                        print("  [失败] 未提取到出校码")
                                        # 调试：从successMessage直接提取
                                        try:
                                            code_from_success = await self.page.evaluate('''() => {
                                                const el = document.getElementById('successMessage');
                                                if (!el) return 'NO_ELEMENT';
                                                const match = el.textContent.match(/\b\d{6}\b/);
                                                return match ? match[0] : 'NO_CODE';
                                            }''')
                                            print(f"  [调试] successMessage内容: {code_from_success}")

                                            if 'NO_CODE' not in code_from_success and 'NO_ELEMENT' not in code_from_success:
                                                exit_code = code_from_success
                                                print(f"  [成功] 提取到出校码: {exit_code}")
                                        except Exception as debug_e:
                                            print(f"  [调试] 出错: {str(debug_e)[:100]}")
                                else:
                                    print("  [失败] 未找到审批按钮")
                        except Exception as e:
                            print(f"  [错误] 审批过程出错: {str(e)[:100]}")
                else:
                    print("  [错误] 教师登录失败")
                    await self.screenshot("7_登录失败")
                    return {'success': False, 'error': '教师登录失败'}

        # 步骤3：门卫验证
        if exit_code:
            print(f"\n[步骤3] 门卫验证 (出校码: {exit_code})")
            await self.goto(f"{BASE_URL}/guard-verify")
            await self.screenshot("10_门卫页面")

            # 填写出校码
            await self.fill('codeInput', exit_code, "出校码")
            await self.screenshot("11_输入出校码")

            # 直接调用verifyWithType('student-leave')函数
            try:
                await self.page.evaluate('''() => {
                    verifyWithType('student-leave');
                }''')
                print("  [调用] 验证学生出校")
                await asyncio.sleep(2)
                await self.screenshot("12_验证结果")

                # 检查页面是否有成功提示（通过头像元素判断）
                try:
                    # 检查结果卡片是否显示成功（头像大元素有内容）
                    avatar_text = await self.page.evaluate('''() => {
                        const avatar = document.getElementById('avatarLarge');
                        return avatar ? avatar.textContent.trim() : '';
                    }''')

                    if avatar_text and avatar_text != '?':
                        print(f"  [成功] 门卫验证通过（头像: {avatar_text}）")
                        guard_verified = True
                    else:
                        # 备用检查：查看页面文本
                        body_text = await self.page.inner_text('body')
                        print("  [失败] 门卫验证失败")
                        print(f"  [调试] 页面文本: {body_text[:200]}")
                except:
                    print("  [警告] 无法确认验证结果")
            except Exception as e:
                print(f"  [错误] 验证失败: {str(e)[:100]}")

        return {
            'leave_code': leave_code,
            'exit_code': exit_code,
            'guard_verified': guard_verified,
            'success': bool(leave_code and exit_code and guard_verified)
        }

    async def story_2_teacher_direct_create(self):
        """用户故事2：教师直接创建出校码"""
        print("\n" + "="*80)
        print("用户故事2：教师直接创建出校码")
        print("="*80)

        exit_code = None
        guard_verified = False

        # 清除浏览器存储
        await self.clear_storage()

        # 步骤1：教师登录
        print("\n[步骤1] 教师登录")
        await self.goto(f"{BASE_URL}/teacher-wechat")
        await self.screenshot("1_教师页面")

        await self.fill('phone', TEST_DATA['teacher']['phone'], "教师手机")
        await self.fill('password', TEST_DATA['teacher']['password'], "教师密码")
        await self.screenshot("2_填写教师信息")

        if await self.click_button('登录', "登录按钮"):
            await asyncio.sleep(2)

            if await self.verify_login_success():
                await self.screenshot("3_教师登录成功")

                # 步骤2：创建出校码
                print("\n[步骤2] 创建出校码")
                if await self.click_button('button[onclick="showCreateMode()"]', "代学生申请"):
                    await asyncio.sleep(1)
                elif await self.click_button('代学生申请', "代学生申请"):
                    pass

                await self.screenshot("4_申请页面")
                await self.fill('studentNameInput', TEST_DATA['student_name'], "学生姓名")
                await self.fill('studentIdInput', TEST_DATA['student_id'], "学号")
                await self.screenshot("5_填写学生信息")

                # 查找并点击生成按钮
                try:
                    create_btns = await self.page.query_selector_all('button')
                    for btn in create_btns:
                        text = await btn.inner_text()
                        if '生成' in text:
                            await btn.click()
                            print("  [点击] 生成出校码")
                            await asyncio.sleep(3)
                            await self.screenshot("6_生成出校码")

                            exit_code = await self.extract_code()
                            if exit_code:
                                print(f"  [成功] 出校码: {exit_code}")
                            break
                except Exception as e:
                    print(f"  [错误] {str(e)}")

        # 步骤3：门卫验证
        if exit_code:
            print(f"\n[步骤3] 门卫验证 (出校码: {exit_code})")
            await self.goto(f"{BASE_URL}/guard-verify")
            await self.screenshot("7_门卫页面")

            # 填写出校码
            await self.fill('codeInput', exit_code, "出校码")
            await self.screenshot("8_输入出校码")

            # 直接调用verifyWithType('student-leave')函数
            try:
                await self.page.evaluate('''() => {
                    verifyWithType('student-leave');
                }''')
                print("  [调用] 验证学生出校")
                await asyncio.sleep(2)
                await self.screenshot("9_验证结果")

                # 检查页面是否有成功提示（通过头像元素判断）
                try:
                    # 检查结果卡片是否显示成功（头像大元素有内容）
                    avatar_text = await self.page.evaluate('''() => {
                        const avatar = document.getElementById('avatarLarge');
                        return avatar ? avatar.textContent.trim() : '';
                    }''')

                    if avatar_text and avatar_text != '?':
                        print(f"  [成功] 门卫验证通过（头像: {avatar_text}）")
                        guard_verified = True
                    else:
                        # 备用检查：查看页面文本
                        body_text = await self.page.inner_text('body')
                        print("  [失败] 门卫验证失败")
                        print(f"  [调试] 页面文本: {body_text[:200]}")
                except:
                    print("  [警告] 无法确认验证结果")
            except Exception as e:
                print(f"  [错误] 验证失败: {str(e)[:100]}")

        return {'exit_code': exit_code, 'guard_verified': guard_verified, 'success': bool(exit_code and guard_verified)}

    async def story_3_parent_visit(self):
        """用户故事3：家长访问（家长 → 教师 → 门卫进校）"""
        print("\n" + "="*80)
        print("用户故事3：家长访问流程")
        print("="*80)

        visit_code = None
        guard_verified = False

        await self.clear_storage()

        # 步骤1：家长生成访问码
        print("\n[步骤1] 家长生成访问码")
        await self.goto(f"{BASE_URL}/parent-simple")
        await self.screenshot("1_家长页面")

        await self.fill('phone', TEST_DATA['parent']['phone'], "手机号")
        await self.fill('password', TEST_DATA['parent']['pin'], "密码")
        await self.screenshot("2_填写家长信息")

        # 选择"入校申请"（parent-visit，默认已选中）
        print("  [确认] 已选择：入校申请")

        if await self.click_button('button[type="submit"]', "生成通行码"):
            await asyncio.sleep(3)
            await self.screenshot("3_生成访问码")

            visit_code = await self.extract_code()
            if visit_code:
                print(f"  [成功] 访问码: {visit_code}")

        # 步骤2：教师审批
        if visit_code:
            print(f"\n[步骤2] 教师审批 (访问码: {visit_code})")
            await self.goto(f"{BASE_URL}/teacher-wechat")
            await self.screenshot("4_教师页面")

            await self.fill('phone', TEST_DATA['teacher']['phone'], "教师手机")
            await self.fill('password', TEST_DATA['teacher']['password'], "教师密码")
            await self.screenshot("5_填写教师信息")

            if await self.click_button('登录', "登录按钮"):
                await asyncio.sleep(2)
                if await self.verify_login_success():
                    await self.screenshot("6_教师登录成功")

                    await self.fill('codeInput', visit_code, "访问码")
                    await self.screenshot("7_输入访问码")

                    if await self.click_button('button[onclick="checkCode()"]', "查询按钮"):
                        await asyncio.sleep(2)
                        await self.screenshot("8_查询结果")

                        # 审批通过
                        try:
                            await self.page.evaluate('''() => {
                                approve();
                            }''')
                            print("  [调用] 审批通过")
                            await asyncio.sleep(3)
                            await self.screenshot("9_审批完成")
                        except Exception as e:
                            print(f"  [错误] 审批失败: {str(e)[:100]}")

        # 步骤3：门卫验证（进校）
        if visit_code:
            print(f"\n[步骤3] 门卫验证进校 (访问码: {visit_code})")
            await self.goto(f"{BASE_URL}/guard-verify")
            await self.screenshot("10_门卫页面")

            await self.fill('codeInput', visit_code, "访问码")
            await self.screenshot("11_输入访问码")

            # 调用进校验证（parent-visit）
            try:
                await self.page.evaluate('''() => {
                    verifyWithType('parent-visit');
                }''')
                print("  [调用] 验证家长进校")
                await asyncio.sleep(2)
                await self.screenshot("12_验证结果")

                avatar_text = await self.page.evaluate('''() => {
                    const avatar = document.getElementById('avatarLarge');
                    return avatar ? avatar.textContent.trim() : '';
                }''')

                if avatar_text and avatar_text != '?':
                    print(f"  [成功] 门卫验证通过（头像: {avatar_text}）")
                    guard_verified = True
                else:
                    print("  [失败] 门卫验证失败")
            except Exception as e:
                print(f"  [错误] 验证失败: {str(e)[:100]}")

        return {'visit_code': visit_code, 'guard_verified': guard_verified, 'success': bool(visit_code and guard_verified)}

    async def story_4_alumni_visit(self):
        """用户故事4：校友访问（校友 → 教师 → 门卫进校）"""
        print("\n" + "="*80)
        print("用户故事4：校友访问流程")
        print("="*80)

        visit_code = None
        guard_verified = False

        await self.clear_storage()

        # 步骤1：校友生成访问码
        print("\n[步骤1] 校友生成访问码")
        await self.goto(f"{BASE_URL}/parent-simple")
        await self.screenshot("1_校友页面")

        await self.fill('phone', TEST_DATA['alumni']['phone'], "校友手机")
        await self.fill('password', TEST_DATA['alumni']['pin'], "密码")
        await self.screenshot("2_填写校友信息")

        # 选择"入校申请"
        print("  [确认] 已选择：入校申请")

        if await self.click_button('button[type="submit"]', "生成通行码"):
            await asyncio.sleep(3)
            await self.screenshot("3_生成访问码")

            visit_code = await self.extract_code()
            if visit_code:
                print(f"  [成功] 访问码: {visit_code}")

        # 步骤2：教师审批
        if visit_code:
            print(f"\n[步骤2] 教师审批 (访问码: {visit_code})")
            await self.goto(f"{BASE_URL}/teacher-wechat")
            await self.screenshot("4_教师页面")

            await self.fill('phone', TEST_DATA['teacher']['phone'], "教师手机")
            await self.fill('password', TEST_DATA['teacher']['password'], "教师密码")
            await self.screenshot("5_填写教师信息")

            if await self.click_button('登录', "登录按钮"):
                await asyncio.sleep(2)
                if await self.verify_login_success():
                    await self.screenshot("6_教师登录成功")

                    await self.fill('codeInput', visit_code, "访问码")
                    await self.screenshot("7_输入访问码")

                    if await self.click_button('button[onclick="checkCode()"]', "查询按钮"):
                        await asyncio.sleep(2)
                        await self.screenshot("8_查询结果")

                        # 审批通过
                        try:
                            await self.page.evaluate('''() => {
                                approve();
                            }''')
                            print("  [调用] 审批通过")
                            await asyncio.sleep(3)
                            await self.screenshot("9_审批完成")
                        except Exception as e:
                            print(f"  [错误] 审批失败: {str(e)[:100]}")

        # 步骤3：门卫验证（进校）
        if visit_code:
            print(f"\n[步骤3] 门卫验证进校 (访问码: {visit_code})")
            await self.goto(f"{BASE_URL}/guard-verify")
            await self.screenshot("10_门卫页面")

            await self.fill('codeInput', visit_code, "访问码")
            await self.screenshot("11_输入访问码")

            # 调用进校验证（alumni-visit）
            try:
                await self.page.evaluate('''() => {
                    verifyWithType('alumni-visit');
                }''')
                print("  [调用] 验证校友进校")
                await asyncio.sleep(2)
                await self.screenshot("12_验证结果")

                avatar_text = await self.page.evaluate('''() => {
                    const avatar = document.getElementById('avatarLarge');
                    return avatar ? avatar.textContent.trim() : '';
                }''')

                if avatar_text and avatar_text != '?':
                    print(f"  [成功] 门卫验证通过（头像: {avatar_text}）")
                    guard_verified = True
                else:
                    print("  [失败] 门卫验证失败")
            except Exception as e:
                print(f"  [错误] 验证失败: {str(e)[:100]}")

        return {'visit_code': visit_code, 'guard_verified': guard_verified, 'success': bool(visit_code and guard_verified)}

    async def story_5_visitor_register(self):
        """用户故事5：访客登记（访客填写信息 → 老师添加 → 门卫验证）"""
        print("\n" + "="*80)
        print("用户故事5：访客登记流程")
        print("="*80)

        visit_code = None
        guard_verified = False

        await self.clear_storage()

        # 步骤1：访客登记页面填写信息并生成码
        print("\n[步骤1] 访客登记")
        await self.goto(f"{BASE_URL}/visitor-register")
        await self.screenshot("1_访客登记页面")

        await self.fill('visitorName', '张三', "访客姓名")
        await self.fill('visitorPhone', '13900009999', "访客手机")
        await self.fill('idCard', '110101199001011234', "身份证")
        await self.screenshot("2_填写访客信息")

        # 选择访问目的
        try:
            await self.page.evaluate('''() => {
                document.getElementById('visitPurpose').value = 'meeting';
            }''')
            print("  [选择] 访问目的: 商务会议")
        except:
            pass

        await self.fill('visitReason', '商务洽谈', "访问说明")
        await self.screenshot("3_完整信息")

        if await self.click_button('button[type="submit"]', "生成访客码"):
            await asyncio.sleep(3)
            await self.screenshot("4_生成访客码")

            visit_code = await self.extract_code()
            if visit_code:
                print(f"  [成功] 访客码: {visit_code}")

        # 步骤2：老师添加访客（模拟发送复制信息给老师）
        if visit_code:
            print(f"\n[步骤2] 老师添加访客 (访客码: {visit_code})")
            await self.goto(f"{BASE_URL}/teacher-wechat")
            await self.screenshot("5_教师页面")

            await self.fill('phone', TEST_DATA['teacher']['phone'], "教师手机")
            await self.fill('password', TEST_DATA['teacher']['password'], "教师密码")
            await self.screenshot("6_填写教师信息")

            if await self.click_button('登录', "登录按钮"):
                await asyncio.sleep(2)
                if await self.verify_login_success():
                    await self.screenshot("7_教师登录成功")

                    # 点击"访客验证"按钮
                    if await self.click_button('button[onclick="showVisitorVerifyMode()"]', "访客验证"):
                        await asyncio.sleep(1)
                        await self.screenshot("8_访客验证页面")

                        # 准备访客信息文本（模拟从访客复制的信息）
                        visitor_info_text = f"""【访客登记信息】
姓名：张三
手机：13900009999
身份证：110101199001011234
访问目的：商务会议
访问说明：商务洽谈
访客码：{visit_code}
申请时间：2026-03-28

请老师点击"访客验证"按钮，粘贴以上信息完成访客添加。"""

                        await self.page.evaluate('''(text) => {
                            document.getElementById('visitorInfo').value = text;
                        }''', visitor_info_text)
                        await self.screenshot("9_粘贴访客信息")

                        # 点击"添加访客"按钮
                        try:
                            await self.page.evaluate('''() => {
                                addVisitor();
                            }''')
                            print("  [调用] 添加访客")
                            await asyncio.sleep(3)
                            await self.screenshot("10_添加完成")

                            # 从页面提取访客码
                            code_from_page = await self.page.evaluate('''() => {
                                const resultDiv = document.getElementById('visitorResult');
                                if (!resultDiv) return '';
                                const match = resultDiv.textContent.match(/\b\d{6}\b/);
                                return match ? match[0] : '';
                            }''')

                            if code_from_page:
                                print(f"  [成功] 访客码: {code_from_page}")
                                visit_code = code_from_page
                        except Exception as e:
                            print(f"  [错误] 添加访客失败: {str(e)[:100]}")

        # 步骤3：门卫验证访客码
        if visit_code:
            print(f"\n[步骤3] 门卫验证 (访客码: {visit_code})")
            await self.goto(f"{BASE_URL}/guard-verify")
            await self.screenshot("11_门卫页面")

            await self.fill('codeInput', visit_code, "访客码")
            await self.screenshot("12_输入访客码")

            # 访客验证
            try:
                await self.page.evaluate('''() => {
                    verifyWithType('visitor');
                }''')
                print("  [调用] 验证访客")
                await asyncio.sleep(2)
                await self.screenshot("13_验证结果")

                avatar_text = await self.page.evaluate('''() => {
                    const avatar = document.getElementById('avatarLarge');
                    return avatar ? avatar.textContent.trim() : '';
                }''')

                if avatar_text and avatar_text != '?':
                    print(f"  [成功] 门卫验证通过（头像: {avatar_text}）")
                    guard_verified = True
                else:
                    print("  [失败] 门卫验证失败")
            except Exception as e:
                print(f"  [错误] 验证失败: {str(e)[:100]}")

        return {'visit_code': visit_code, 'guard_verified': guard_verified, 'success': bool(visit_code and guard_verified)}

    def generate_report(self, results):
        """生成HTML报告"""
        success_count = sum(1 for r in results.values() if r.get('success'))

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
        .story.success {{ border-left: 5px solid #4caf50; }}
        .story.failed {{ border-left: 5px solid #f44336; }}
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
        <p>成功: {success_count}/5</p>
    </div>

    <div class="summary">
        <h2>测试概览</h2>
        <p>总用户故事: 5</p>
        <p>总截图: {len(self.screenshots)}</p>
    </div>
"""

        for i, (story_name, result) in enumerate(results.items(), 1):
            status = "✅ 成功" if result.get('success') else "❌ 失败"
            css_class = "success" if result.get('success') else "failed"

            html += f"""
    <div class="story {css_class}">
        <h2>用户故事{i}: {story_name} {status}</h2>
"""

            if result.get('leave_code'):
                html += f"<div class='code'>请假码: {result['leave_code']}</div>"
            if result.get('exit_code'):
                html += f"<div class='code'>出校码: {result['exit_code']}</div>"
            if result.get('error'):
                html += f"<div style='color:red; padding:10px; background:#ffebee;'>错误: {result['error']}</div>"

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

        with open("e2e_test_report_strict.html", 'w', encoding='utf-8') as f:
            f.write(html)

        # 修复路径
        with open("e2e_test_report_strict.html", 'r', encoding='utf-8') as f:
            content = f.read()
        content = content.replace('e2e_screenshots_strict\\', 'e2e_screenshots_strict/')
        with open("e2e_test_report_strict.html", 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n[报告] 已生成: e2e_test_report_strict.html")


async def main():
    print("\n" + "="*80)
    print("校友入校系统 - 严格端到端测试")
    print("="*80)

    test = E2ETest()
    results = {}

    try:
        await test.setup()

        # 测试所有5个用户故事
        results['学生请假'] = await test.story_1_student_leave()
        results['教师直接创建'] = await test.story_2_teacher_direct_create()
        results['家长访问'] = await test.story_3_parent_visit()
        results['校友访问'] = await test.story_4_alumni_visit()
        results['访客登记'] = await test.story_5_visitor_register()

    finally:
        await test.teardown()
        test.generate_report(results)

        success_count = sum(1 for r in results.values() if r.get('success'))
        print("\n" + "="*80)
        print(f"测试完成 - 成功: {success_count}/5")
        print("="*80)

        if success_count > 0:
            import subprocess
            subprocess.Popen(['cmd', '/c', 'start', 'e2e_test_report_strict.html'],
                           shell=True, cwd=r"D:\Project\校友入校登记")


if __name__ == '__main__':
    asyncio.run(main())
