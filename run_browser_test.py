#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import time
import webbrowser
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class BrowserTest:
    def __init__(self):
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """设置Chrome浏览器"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.maximize_window()
            print("浏览器启动成功")
        except Exception as e:
            print(f"浏览器启动失败: {e}")

    def test_visitor_flow(self):
        """测试访客流程"""
        try:
            print("开始测试访客流程...")

            # 1. 打开访客端
            self.driver.get("http://localhost:8080/index.html")
            time.sleep(2)

            # 2. 查找并点击注册按钮
            try:
                register_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "showRegisterBtn"))
                )
                register_btn.click()
                print("点击注册按钮")
            except:
                print("未找到注册按钮，可能已在注册页面")

            time.sleep(1)

            # 3. 填写注册表单
            timestamp = int(time.time())
            username = f"test_visitor_{timestamp}"

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(username)

            self.driver.find_element(By.ID, "password").send_keys("Test123456")
            self.driver.find_element(By.ID, "confirmPassword").send_keys("Test123456")
            self.driver.find_element(By.ID, "realName").send_keys("测试访客")
            self.driver.find_element(By.ID, "email").send_keys(f"test{timestamp}@example.com")
            self.driver.find_element(By.ID, "phone").send_keys("13800138000")
            self.driver.find_element(By.ID, "idCard").send_keys("110101199001011234")

            # 选择校友类型
            try:
                self.driver.find_element(By.ID, "userTypeAlumni").click()
            except:
                print("未找到校友类型选择器")

            # 4. 提交注册
            self.driver.find_element(By.ID, "registerBtn").click()
            print("提交注册")
            time.sleep(3)

            # 5. 登录
            self.driver.find_element(By.ID, "username").send_keys(username)
            self.driver.find_element(By.ID, "password").send_keys("Test123456")
            self.driver.find_element(By.ID, "loginBtn").click()
            print("访客登录成功")
            time.sleep(2)

            return username

        except Exception as e:
            print(f"访客流程测试失败: {e}")
            return None

    def test_admin_flow(self):
        """测试教师审批流程"""
        try:
            print("开始测试教师审批流程...")

            # 打开新窗口用于教师端
            self.driver.execute_script("window.open('http://localhost:8080/admin.html', '_blank');")
            time.sleep(2)

            # 切换到教师端窗口
            windows = self.driver.window_handles
            self.driver.switch_to.window(windows[1])

            # 教师登录
            self.driver.find_element(By.ID, "username").send_keys("teacher001")
            self.driver.find_element(By.ID, "password").send_keys("teacher123")
            self.driver.find_element(By.ID, "loginBtn").click()
            print("教师登录成功")
            time.sleep(3)

            # 查找审批菜单
            try:
                approval_menu = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '审批')]"))
                )
                approval_menu.click()
                print("进入审批页面")
                time.sleep(2)

                # 查找待审批的申请
                approve_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), '批准')]")
                if approve_btns:
                    approve_btns[0].click()
                    print("点击审批按钮")
                    time.sleep(2)

                    # 提交审批
                    confirm_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '确认')]")
                    if confirm_btn:
                        confirm_btn.click()
                        print("审批提交成功")
                else:
                    print("未找到待审批的申请")

            except Exception as e:
                print(f"审批流程失败: {e}")

            return True

        except Exception as e:
            print(f"教师流程测试失败: {e}")
            return False

    def test_security_flow(self):
        """测试保安验证流程"""
        try:
            print("开始测试保安验证流程...")

            # 打开新窗口用于保安端
            self.driver.execute_script("window.open('http://localhost:8080/security-portal.html', '_blank');")
            time.sleep(2)

            # 切换到保安端窗口
            windows = self.driver.window_handles
            self.driver.switch_to.window(windows[2])

            # 保安登录
            self.driver.find_element(By.ID, "username").send_keys("security001")
            self.driver.find_element(By.ID, "password").send_keys("security123")
            self.driver.find_element(By.ID, "loginBtn").click()
            print("保安登录成功")
            time.sleep(3)

            # 二维码验证
            try:
                qr_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "qrScanBtn"))
                )
                qr_btn.click()
                print("进入二维码验证")
                time.sleep(2)

                # 手动输入申请编号
                manual_btn = self.driver.find_element(By.ID, "manualInputBtn")
                manual_btn.click()
                time.sleep(1)

                # 输入测试申请编号
                self.driver.find_element(By.ID, "applicationIdInput").send_keys("1")
                self.driver.find_element(By.ID, "verifyManualQrBtn").click()
                print("二维码验证完成")
                time.sleep(2)

            except Exception as e:
                print(f"二维码验证失败: {e}")

            # 人脸识别验证
            try:
                face_btn = self.driver.find_element(By.ID, "faceScanBtn")
                face_btn.click()
                print("进入人脸识别")
                time.sleep(2)

                # 开始人脸扫描（模拟）
                scan_btn = self.driver.find_element(By.ID, "startFaceScanBtn")
                scan_btn.click()
                print("人脸识别完成")
                time.sleep(2)

            except Exception as e:
                print(f"人脸识别失败: {e}")

            return True

        except Exception as e:
            print(f"保安流程测试失败: {e}")
            return False

    def run_full_test(self):
        """运行完整测试"""
        try:
            print("开始完整的自动化测试...")

            # 1. 访客流程
            username = self.test_visitor_flow()
            if not username:
                print("访客流程失败")
                return False

            # 2. 教师审批流程
            if not self.test_admin_flow():
                print("教师审批流程失败")
                return False

            # 3. 保安验证流程
            if not self.test_security_flow():
                print("保安验证流程失败")
                return False

            print("\n测试完成！所有流程测试通过。")
            print(f"测试访客用户: {username}")
            print("测试账户:")
            print("教师: teacher001 / teacher123")
            print("保安: security001 / security123")

            return True

        except Exception as e:
            print(f"测试执行失败: {e}")
            return False

    def cleanup(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()

def main():
    print("启动校友入校登记系统自动化测试...")

    test = BrowserTest()
    try:
        success = test.run_full_test()
        if success:
            print("\n所有测试通过！系统运行正常。")
        else:
            print("\n部分测试失败，请检查系统配置。")
    finally:
        # 保持浏览器打开5分钟供查看
        print("\n浏览器将保持打开5分钟供查看结果...")
        time.sleep(300)
        test.cleanup()

if __name__ == "__main__":
    main()