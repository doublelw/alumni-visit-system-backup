#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复HTML报告中的图片路径"""

with open('e2e_test_report_v2.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复路径：把反斜杠替换为正斜杠
content = content.replace('e2e_screenshots_v2\\', 'e2e_screenshots_v2/')

with open('e2e_test_report_v2.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('路径已修复，请重新打开 e2e_test_report_v2.html')
