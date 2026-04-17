#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理后台UI问题全面修复
修复用户报告的所有UI问题
"""

import os
import re

def fix_admin_css():
    """修复admin.css中的UI问题"""
    css_file = 'frontend/static/css/admin.css'

    with open(css_file, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = []

    # 1. 修复操作按钮大小（增大padding和字体）
    old_action_btn = '''.action-buttons .btn {
    min-width: auto;
    padding: var(--spacing-xs) var(--spacing-sm);
}'''

    new_action_btn = '''.action-buttons .btn {
    min-width: 32px;
    min-height: 32px;
    padding: 6px 10px;
    font-size: var(--font-size-sm);
}

.action-buttons .btn i {
    font-size: 16px;
}'''

    if old_action_btn.split('\n')[0] in content:
        content = content.replace(old_action_btn, new_action_btn)
        changes.append("[OK] 增大操作按钮尺寸")

    # 2. 增大btn-sm按钮的大小
    old_btn_sm = '''.btn-sm {
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: var(--font-size-xs);
}'''

    new_btn_sm = '''.btn-sm {
    padding: 6px 12px;
    font-size: var(--font-size-sm);
    min-width: 32px;
    min-height: 32px;
}'''

    if old_btn_sm in content:
        content = content.replace(old_btn_sm, new_btn_sm)
        changes.append("[OK] 增大小按钮(btn-sm)尺寸")

    # 3. 确保表格操作列有足够宽度
    # 在.data-table样式中添加操作列的min-width
    table_col_style = '''
/* 表格操作列最小宽度 */
.data-table th:last-child,
.data-table td:last-child {
    min-width: 150px;
    width: 150px;
}

.data-table th:nth-last-child(2),
.data-table td:nth-last-child(2) {
    min-width: 120px;
    width: 120px;
}
'''

    if '表格操作列最小宽度' not in content:
        # 找到.data-table定义后的位置插入
        data_table_pos = content.find('/* 数据表格样式 */')
        if data_table_pos > 0:
            insert_pos = content.find('\n}', content.find('.data-table {', data_table_pos))
            if insert_pos > 0:
                content = content[:insert_pos+2] + table_col_style + content[insert_pos+2:]
                changes.append("[OK] 增加表格操作列宽度")

    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return changes

def fix_responsive_css():
    """修复responsive.css中的布局问题"""
    css_file = 'frontend/static/css/responsive.css'

    with open(css_file, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = []

    # 1. 移除可能导致侧边栏问题的样式
    if '.sidebar {\n        display: block;\n        width: 250px;\n        position: fixed;\n        left: 0;\n        top: 0;\n        bottom: 0;\n        background: white;' in content:
            old_sidebar = '''.sidebar {
        display: block;
        width: 250px;
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        background: white;
        box-shadow: 2px 0 8px rgba(0,0,0,0.1);
        z-index: 1000;
    }'''

            new_sidebar = '''.sidebar {
        display: block;
        width: 250px;
        /* 使用flex布局，不使用fixed定位以避免遮挡 */
        box-shadow: 2px 0 8px rgba(0,0,0,0.1);
        z-index: 1000;
    }'''

            content = content.replace(old_sidebar, new_sidebar)
            changes.append("[OK] 修复侧边栏布局")

    # 2. 确保主内容区域不会被侧边栏遮挡
    main_content_fix = '''
/* 确保大屏幕下主内容区域不被侧边栏遮挡 */
@media screen and (min-width: 1024px) {
    body.has-sidebar .main-content {
        margin-left: var(--sidebar-width);
    }

    body.has-sidebar.sidebar-collapsed .main-content {
        margin-left: var(--sidebar-collapsed-width);
    }
}
'''

    if '确保大屏幕下主内容区域不被侧边栏遮挡' not in content:
        content += '\n\n' + main_content_fix
        changes.append("[OK] 添加主内容区域边距")

    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return changes

def update_html_version():
    """更新HTML中的CSS版本号以强制刷新"""
    html_file = 'frontend/templates/admin.html'

    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = []

    # 更新CSS版本号
    content = re.sub(
        r'admin\.css\?v=[\d_]+',
        'admin.css?v=20250326_1',
        content
    )
    changes.append("[OK] 更新admin.css版本号")

    content = re.sub(
        r'responsive\.css\?v=[\d.]+',
        'responsive.css?v=2.2',
        content
    )
    changes.append("[OK] 更新responsive.css版本号")

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return changes

def main():
    print("="*70)
    print("管理后台UI问题全面修复")
    print("="*70)

    all_changes = []

    # 1. 修复admin.css
    print("\n[1/3] 修复 admin.css...")
    changes = fix_admin_css()
    all_changes.extend(changes)
    for change in changes:
        print(f"  {change}")

    # 2. 修复responsive.css
    print("\n[2/3] 修复 responsive.css...")
    changes = fix_responsive_css()
    all_changes.extend(changes)
    for change in changes:
        print(f"  {change}")

    # 3. 更新版本号
    print("\n[3/3] 更新CSS版本号...")
    changes = update_html_version()
    all_changes.extend(changes)
    for change in changes:
        print(f"  {change}")

    # 总结
    print("\n" + "="*70)
    print("修复完成")
    print("="*70)
    print(f"总共进行了 {len(all_changes)} 项修复")
    print("\n请按 Ctrl + Shift + R 强制刷新浏览器以应用更改")
    print("="*70)

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
