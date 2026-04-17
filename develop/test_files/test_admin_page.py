#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理后台页面完整性测试
检查所有功能、样式、脚本是否正常
"""

import requests
import re
import json
from urllib.parse import urljoin

BASE_URL = 'http://localhost:5000'

def test_page_structure():
    """测试页面HTML结构"""
    print("=" * 70)
    print("1. 测试页面HTML结构")
    print("=" * 70)

    url = f"{BASE_URL}/admin-login"
    response = requests.get(url)

    print(f"[OK] 登录页面状态码: {response.status_code}")

    html = response.text

    # 检查关键标签
    checks = {
        '<html': html.count('<html'),
        '</html>': html.count('</html'),
        '<head>': html.count('<head>'),
        '</head>': html.count('</head>'),
        '<body>': html.count('<body>'),
        '</body>': html.count('</body>'),
    }

    all_ok = True
    for tag, count in checks.items():
        status = "[OK]" if count == 1 else "[FAIL]"
        try:
            print(f"  {status} {tag}: {count} 个")
        except:
            print(f"  {status} tag: {count} 个")
        if count != 1:
            all_ok = False

    return all_ok

def test_css_resources():
    """测试CSS资源加载"""
    print("\n" + "=" * 70)
    print("2. 测试CSS资源加载")
    print("=" * 70)

    css_files = [
        '/static/vendor/remixicon.css',
        '/static/css/admin.css?v=20251111_4',
        '/static/css/responsive.css?v=2.0'
    ]

    all_ok = True
    for css_file in css_files:
        url = f"{BASE_URL}{css_file}"
        try:
            response = requests.head(url)
            status = "[OK]" if response.status_code == 200 else "[FAIL]"
            try:
                print(f"  {status} {css_file}: {response.status_code}")
            except:
                print(f"  {status} CSS file: {response.status_code}")
            if response.status_code != 200:
                all_ok = False
        except Exception as e:
            try:
                print(f"  [FAIL] {css_file}: {str(e)}")
            except:
                print(f"  [FAIL] CSS file error")
            all_ok = False

    return all_ok

def test_js_resources():
    """测试JavaScript资源加载"""
    print("\n" + "=" * 70)
    print("3. 测试JavaScript资源加载")
    print("=" * 70)

    js_files = [
        '/static/vendor/chart.js',
        '/static/js/config.js?v=2.3',
        '/static/js/relationship-management.js?v=1.0',
        '/static/js/admin.js?v=20251113_5'
    ]

    all_ok = True
    for js_file in js_files:
        url = f"{BASE_URL}{js_file}"
        try:
            response = requests.head(url)
            status = "[OK]" if response.status_code == 200 else "[FAIL]"
            print(f"  {status} {js_file}: {response.status_code}")
            if response.status_code != 200:
                all_ok = False
        except Exception as e:
            print(f"  [FAIL] {js_file}: {str(e)}")
            all_ok = False

    return all_ok

def test_login_functionality():
    """测试登录功能"""
    print("\n" + "=" * 70)
    print("4. 测试登录功能")
    print("=" * 70)

    # 首先获取登录页面
    login_url = f"{BASE_URL}/admin-login"
    session = requests.Session()

    try:
        # 获取登录页面
        response = session.get(login_url)
        print(f"[OK] 获取登录页面: {response.status_code}")

        # 尝试登录
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'captcha': '1234'  # 可能需要验证码
        }

        login_api_url = f"{BASE_URL}/api/auth/admin-login"
        response = session.post(login_api_url, json=login_data)

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("[OK] 登录成功")
                return session
            else:
                print(f"[INFO] 登录失败: {result.get('message', 'Unknown error')}")
        else:
            print(f"[INFO] 登录请求失败: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] 登录测试出错: {str(e)}")

    return None

def test_admin_dashboard(session):
    """测试管理后台主页"""
    print("\n" + "=" * 70)
    print("5. 测试管理后台主页")
    print("=" * 70)

    if not session:
        print("[SKIP] 需要先登录")
        return False

    dashboard_url = f"{BASE_URL}/alumni-management-2025"
    response = session.get(dashboard_url)

    print(f"  状态码: {response.status_code}")

    if response.status_code == 200:
        html = response.text

        # 检查关键元素
        elements = {
            'sidebar': '侧边栏' in html or 'sidebar' in html,
            'navigation': '导航' in html or 'nav' in html,
            'user_management': '用户管理' in html,
            'dashboard': '仪表板' in html or 'dashboard' in html.lower()
        }

        for elem, found in elements.items():
            status = "[OK]" if found else "[WARN]"
            try:
                print(f"  {status} {elem}: {'存在' if found else '未找到'}")
            except:
                print(f"  {status} {elem}: {'Found' if found else 'Not found'}")

        return True
    else:
        try:
            print(f"[FAIL] 无法访问管理后台")
        except:
            print(f"[FAIL] Cannot access admin dashboard")
        return False

def test_buttons_and_links():
    """测试页面中的按钮和链接"""
    print("\n" + "=" * 70)
    print("6. 测试页面按钮和链接")
    print("=" * 70)

    url = f"{BASE_URL}/admin-login"
    response = requests.get(url)
    html = response.text

    # 检查按钮
    buttons = re.findall(r'<button[^>]*>([^<]*)</button>', html)
    try:
        print(f"  找到 {len(buttons)} 个按钮:")
    except:
        print(f"  Found {len(buttons)} buttons")
    for i, btn in enumerate(buttons[:10], 1):  # 只显示前10个
        try:
            print(f"    {i}. {btn.strip()}")
        except:
            print(f"    {i}. [Button]")

    # 检查链接
    links = re.findall(r'<a[^>]*href=\"([^\"]+)\"[^>]*>([^<]*)</a>', html)
    try:
        print(f"\n  找到 {len(links)} 个链接:")
    except:
        print(f"\n  Found {len(links)} links")
    for i, (href, text) in enumerate(links[:10], 1):
        try:
            print(f"    {i}. {text.strip()} -> {href}")
        except:
            print(f"    {i}. [Link] -> {href}")

    return len(buttons) > 0 or len(links) > 0

def test_console_errors():
    """检查可能的JavaScript错误"""
    print("\n" + "=" * 70)
    print("7. 检查JavaScript文件语法")
    print("=" * 70)

    js_file = 'D:/Project/校友入校登记/frontend/static/js/admin.js'

    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 简单的括号匹配检查
        checks = {
            '大括号': (content.count('{'), content.count('}')),
            '圆括号': (content.count('('), content.count(')')),
            '方括号': (content.count('['), content.count(']'))
        }

        all_ok = True
        for name, (open_count, close_count) in checks.items():
            status = "[OK]" if open_count == close_count else "[FAIL]"
            try:
                print(f"  {status} {name}: 开={open_count}, 闭={close_count}")
            except:
                print(f"  {status} {name}: open={open_count}, close={close_count}")
            if open_count != close_count:
                all_ok = False

        return all_ok

    except Exception as e:
        print(f"  [ERROR] 无法读取JavaScript文件: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("管理后台页面完整性测试")
    print("=" * 70)

    results = {}

    # 运行所有测试
    results['页面结构'] = test_page_structure()
    results['CSS资源'] = test_css_resources()
    results['JS资源'] = test_js_resources()
    results['按钮链接'] = test_buttons_and_links()
    results['JS语法'] = test_console_errors()

    # 测试登录和后台（需要交互）
    session = test_login_functionality()
    if session:
        results['后台主页'] = test_admin_dashboard(session)

    # 输出总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        try:
            print(f"  {status} {test_name}")
        except:
            print(f"  {status} Test")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    try:
        print(f"\n总计: {passed}/{total} 测试通过")
    except:
        print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        try:
            print("\n[OK] 所有测试通过！页面应该可以正常使用。")
        except:
            print("\n[OK] All tests passed! Page should work normally.")
        return 0
    else:
        try:
            print(f"\n[WARN] 有 {total - passed} 个测试失败，需要修复。")
        except:
            print(f"\n[WARN] {total - passed} tests failed, need fixing.")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
