#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
响应式优化验证测试
检查所有页面的viewport设置和CSS引用
"""

import os
import re
from pathlib import Path

def check_html_file(filepath):
    """检查HTML文件的响应式配置"""
    print(f"\n检查文件: {filepath.name}")
    print("="*70)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查viewport
    viewport_match = re.search(r'<meta\s+name=["\']viewport["\']\s+content=["\']([^"\']+)["\']', content)
    if viewport_match:
        viewport_content = viewport_match.group(1)
        print(f"[OK] Viewport设置: {viewport_content}")

        # 检查是否包含良好的viewport设置
        checks = {
            'width=device-width': 'width=device-width' in viewport_content,
            'initial-scale=1.0': 'initial-scale=1.0' in viewport_content,
            'user-scalable=yes': 'user-scalable=yes' in viewport_content,
            'maximum-scale': 'maximum-scale' in viewport_content,
            'viewport-fit=cover': 'viewport-fit=cover' in viewport_content
        }

        passed = sum(checks.values())
        total = len(checks)

        print(f"  Viewport评分: {passed}/{total}")

        for key, value in checks.items():
            status = "[OK]" if value else "[--]"
            print(f"    {status} {key}")
    else:
        print("[--] 未找到viewport设置")

    # 检查CSS引用
    css_matches = re.findall(r'<link\s+[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)["\']', content)
    if css_matches:
        print(f"\n[OK] CSS文件引用 ({len(css_matches)}个):")
        for css in css_matches:
            print(f"  - {css}")
            # 检查是否包含responsive.css
            if 'responsive.css' in css:
                print(f"    [OK] 已引入响应式CSS")
    else:
        print("\n[--] 未找到CSS文件引用")

    # 检查安全区域适配
    safe_area_inset = 'env(safe-area-inset' in content
    print(f"\n{'[OK]' if safe_area_inset else '[--]'} 安全区域适配 (iPhone X支持)")

    # 检查触摸优化
    touch_action = 'touch-action' in content or '-webkit-tap-highlight-color' in content
    print(f"{'[OK]' if touch_action else '[--]'} 触摸优化")

    return {
        'viewport': viewport_match is not None,
        'responsive_css': any('responsive.css' in css for css in css_matches),
        'safe_area': safe_area_inset,
        'touch_optimized': touch_action,
        'css_count': len(css_matches)
    }

def main():
    templates_dir = Path("D:/Project/校友入校登记/frontend/templates")

    if not templates_dir.exists():
        print(f"错误: 模板目录不存在: {templates_dir}")
        return 1

    print("="*70)
    print("响应式优化验证测试")
    print("="*70)
    print(f"扫描目录: {templates_dir}")

    # 查找所有HTML文件
    html_files = list(templates_dir.glob("*.html"))

    if not html_files:
        print("未找到HTML文件")
        return 1

    print(f"\n找到 {len(html_files)} 个HTML文件")

    results = {}
    for html_file in html_files:
        try:
            results[html_file.name] = check_html_file(html_file)
        except Exception as e:
            print(f"\n错误: 无法检查 {html_file.name}: {e}")

    # 总结报告
    print("\n" + "="*70)
    print("总结报告")
    print("="*70)

    total = len(results)
    viewport_ok = sum(1 for r in results.values() if r['viewport'])
    responsive_css_ok = sum(1 for r in results.values() if r['responsive_css'])
    safe_area_ok = sum(1 for r in results.values() if r['safe_area'])
    touch_ok = sum(1 for r in results.values() if r['touch_optimized'])

    print(f"\n总文件数: {total}")
    print(f"[OK] Viewport设置: {viewport_ok}/{total}")
    print(f"[OK] 响应式CSS: {responsive_css_ok}/{total}")
    print(f"[OK] 安全区域适配: {safe_area_ok}/{total}")
    print(f"[OK] 触摸优化: {touch_ok}/{total}")

    # 详细问题列表
    print("\n" + "-"*70)
    print("需要改进的文件:")
    print("-"*70)

    issues_found = False
    for filename, result in results.items():
        issues = []
        if not result['viewport']:
            issues.append("缺少viewport设置")
        if not result['responsive_css']:
            issues.append("未引入responsive.css")
        if not result['safe_area']:
            issues.append("缺少安全区域适配")
        if not result['touch_optimized']:
            issues.append("缺少触摸优化")

        if issues:
            issues_found = True
            print(f"\n{filename}:")
            for issue in issues:
                print(f"  [!] {issue}")

    if not issues_found:
        print("\n[SUCCESS] 所有文件配置正确！")

    # 评分
    score = (
        (viewport_ok / total * 30) +
        (responsive_css_ok / total * 30) +
        (safe_area_ok / total * 20) +
        (touch_ok / total * 20)
    )

    print(f"\n优化评分: {score:.1f}/100")

    if score >= 90:
        print("评级: 优秀 ⭐⭐⭐⭐⭐")
    elif score >= 75:
        print("评级: 良好 ⭐⭐⭐⭐")
    elif score >= 60:
        print("评级: 合格 ⭐⭐⭐")
    else:
        print("评级: 需要改进 ⭐⭐")

    print("\n" + "="*70)

    return 0 if score >= 75 else 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
