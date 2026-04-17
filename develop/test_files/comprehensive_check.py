#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理后台所有页面和功能的全面检查
主动发现问题并记录
"""

import requests
import re

BASE_URL = 'http://localhost:5000'

# 所有需要检查的菜单页面
PAGES = [
    {'name': '仪表板', 'url': '/alumni-management-2025', 'id': 'dashboardPage'},
    {'name': '用户管理', 'url': '/alumni-management-2025', 'id': 'usersPage'},
    {'name': '拜访对象管理', 'url': '/alumni-management-2025', 'id': 'targetPersonsPage'},
    {'name': '校友审核', 'url': '/alumni-management-2025', 'id': 'alumniApprovePage'},
    {'name': '访问申请', 'url': '/alumni-management-2025', 'id': 'visitApplicationsPage'},
    {'name': '访问记录', 'url': '/alumni-management-2025', 'id': 'visitRecordsPage'},
    {'name': '车辆管理', 'url': '/alumni-management-2025', 'id': 'vehiclesPage'},
    {'name': '数据统计', 'url': '/alumni-management-2025', 'id': 'statisticsPage'},
    {'name': '批量审核', 'url': '/alumni-management-2025', 'id': 'batchApprovePage'},
    {'name': '校历管理', 'url': '/alumni-management-2025', 'id': 'calendarPage'},
    {'name': '问卷调查', 'url': '/alumni-management-2025', 'id': 'surveyPage'},
    {'name': '活动统计', 'url': '/alumni-management-2025', 'id': 'event-statisticsPage'},
]

def check_page_structure(page):
    """检查页面HTML结构"""
    try:
        response = requests.get(f"{BASE_URL}{page['url']}", timeout=5)
        if response.status_code != 200:
            return False, f"页面访问失败: {response.status_code}"

        html = response.text
        page_id = page.get('id')

        if page_id and page_id in html:
            return True, "页面ID存在"
        elif page_id:
            return False, f"页面ID '{page_id}' 未找到"
        else:
            return True, "页面加载成功"

    except Exception as e:
        return False, f"检查失败: {str(e)}"

def check_css_files():
    """检查所有CSS文件"""
    css_files = [
        '/static/css/admin.css',
        '/static/css/responsive.css',
        '/static/vendor/remixicon.css'
    ]

    results = []
    for css_file in css_files:
        try:
            response = requests.head(f"{BASE_URL}{css_file}", timeout=3)
            status = "[OK]" if response.status_code == 200 else "[FAIL]"
            results.append(f"{status} {css_file}: {response.status_code}")
        except Exception as e:
            results.append(f"[FAIL] {css_file}: {str(e)}")

    return results

def check_js_files():
    """检查所有JavaScript文件"""
    js_files = [
        '/static/js/admin.js',
        '/static/js/config.js',
        '/static/vendor/chart.js'
    ]

    results = []
    for js_file in js_files:
        try:
            response = requests.head(f"{BASE_URL}{js_file}", timeout=3)
            status = "[OK]" if response.status_code == 200 else "[FAIL]"
            results.append(f"{status} {js_file}: {response.status_code}")
        except Exception as e:
            results.append(f"[FAIL] {js_file}: {str(e)}")

    return results

def check_common_ui_issues():
    """检查常见的UI问题"""
    issues = []

    try:
        response = requests.get(f"{BASE_URL}/alumni-management-2025", timeout=5)
        html = response.text

        # 检查1: 是否有侧边栏
        if 'class="sidebar"' not in html:
            issues.append("[FAIL] Sidebar not found")
        else:
            issues.append("[OK] Sidebar exists")

        # 检查2: 是否有主内容区
        if 'class="main-content"' not in html:
            issues.append("[FAIL] Main content not found")
        else:
            issues.append("[OK] Main content exists")

        # 检查3: 是否有按钮
        button_count = html.count('class="btn')
        if button_count > 0:
            issues.append(f"[OK] Found {button_count} buttons")
        else:
            issues.append("[FAIL] No buttons found")

        # 检查4: 是否有表格
        table_count = html.count('<table')
        if table_count > 0:
            issues.append(f"[OK] Found {table_count} tables")
        else:
            issues.append("[FAIL] No tables found")

    except Exception as e:
        issues.append(f"[FAIL] UI check error: {str(e)}")

    return issues

def main():
    print("="*70)
    print("管理后台全面检查")
    print("="*70)

    all_ok = True

    # 1. 检查CSS文件
    print("\n[1/4] CSS文件检查:")
    css_results = check_css_files()
    for result in css_results:
        print(f"  {result}")

    # 2. 检查JavaScript文件
    print("\n[2/4] JavaScript文件检查:")
    js_results = check_js_files()
    for result in js_results:
        print(f"  {result}")

    # 3. 检查UI问题
    print("\n[3/4] UI元素检查:")
    ui_issues = check_common_ui_issues()
    for issue in ui_issues:
        print(f"  {issue}")
        if "✗" in issue:
            all_ok = False

    # 4. 检查页面结构
    print("\n[4/4] 页面结构检查:")
    page_ok = 0
    for page in PAGES:
        ok, msg = check_page_structure(page)
        status = "[OK]" if ok else "[FAIL]"
        try:
            print(f"  {status} {page['name']}: {msg}")
        except:
            print(f"  {status} {page['name']}: Check done")
        if ok:
            page_ok += 1
        else:
            all_ok = False

    # 总结
    print("\n" + "="*70)
    print("检查总结")
    print("="*70)
    print(f"CSS文件: {len([r for r in css_results if '✓' in r])}/{len(css_results)} 正常")
    print(f"JS文件: {len([r for r in js_results if '✓' in r])}/{len(js_results)} 正常")
    print(f"页面结构: {page_ok}/{len(PAGES)} 正常")

    if all_ok:
        try:
            print("\n[OK] All checks passed!")
        except:
            print("\n[OK] All checks passed!")
        return 0
    else:
        try:
            print("\n[FAIL] Issues found, need fixing")
        except:
            print("\n[FAIL] Issues found")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
