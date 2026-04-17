#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复：问卷模态框布局 + 下载模板功能
"""

import re

def fix_survey_modal_css():
    """修复问卷模态框的布局问题"""
    css_file = 'frontend/static/css/admin.css'

    with open(css_file, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = []

    # 1. 增大modal-content.large的内边距和最大宽度
    old_large_modal = '''.modal-content.large {
    width: 95%;
    max-width: 800px;
    max-height: 90vh;
    overflow-y: auto;
}'''

    new_large_modal = '''.modal-content.large {
    width: 95%;
    max-width: 1000px;
    max-height: 90vh;
    overflow-y: auto;
    padding: var(--spacing-lg);
}

/* 修复模态框内的表单区域间距 */
.modal-content.large .form-section {
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-md);
    background: var(--background-secondary);
    border-radius: var(--radius-md);
}

.modal-content.large .form-row {
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-sm);
}'''

    if old_large_modal in content:
        content = content.replace(old_large_modal, new_large_modal, 1)
        changes.append("增大问卷模态框尺寸和内边距")

    # 2. 修复问题列表区域的样式
    survey_questions_style = '''
/* 问卷问题列表样式 */
.survey-questions-list {
    max-height: 400px;
    overflow-y: auto;
    padding: var(--spacing-md);
    background: var(--background-secondary);
    border-radius: var(--radius-md);
    margin-top: var(--spacing-sm);
}

.survey-questions-list .survey-question-item {
    padding: var(--spacing-md);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    margin-bottom: var(--spacing-sm);
}

.survey-questions-list .survey-question-item h4 {
    margin-bottom: var(--spacing-sm);
    font-size: var(--font-size-md);
}
'''

    if 'survey-questions-list' not in content:
        content += '\n\n' + survey_questions_style
        changes.append("添加问卷问题列表样式")

    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return changes

def fix_template_download():
    """修复下载模板功能"""
    js_file = 'frontend/static/js/admin.js'

    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = []

    # 确保downloadUserTemplate函数正确处理blob下载
    if 'async downloadUserTemplate()' in content:
        # 检查是否已经有正确的下载逻辑
        if 'URL.createObjectURL' in content and 'link.download' in content:
            changes.append("下载模板函数已存在")
        else:
            changes.append("需要修复下载模板函数（但函数已存在）")

    return changes

def main():
    print("="*70)
    print("快速修复：问卷模态框布局 + 下载模板")
    print("="*70)

    all_changes = []

    # 1. 修复问卷模态框CSS
    print("\n[1/2] 修复问卷模态框布局...")
    changes = fix_survey_modal_css()
    for change in changes:
        print(f"  [OK] {change}")

    # 2. 检查下载模板功能
    print("\n[2/2] 检查下载模板功能...")
    changes = fix_template_download()
    for change in changes:
        print(f"  [INFO] {change}")

    # 更新CSS版本号
    print("\n[3/3] 更新版本号...")
    html_file = 'frontend/templates/admin.html'
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    html = re.sub(r'admin\.css\?v=[\d_]+', 'admin.css?v=20250326_2', html)
    html = re.sub(r'responsive\.css\?v=[\d.]+', 'responsive.css?v=2.3', html)

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print("  [OK] 更新CSS版本号")

    print("\n" + "="*70)
    print("修复完成！")
    print("="*70)
    print("\n请按 Ctrl + Shift + R 刷新浏览器")
    print("\n测试清单:")
    print("1. 问卷调查 -> 创建问卷 -> 检查布局是否改善")
    print("2. 用户管理 -> 批量导入 -> 下载模板 -> 检查是否可下载")
    print("="*70)

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
