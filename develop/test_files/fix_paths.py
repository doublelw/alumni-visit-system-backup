#!/usr/bin/env python3
with open('e2e_test_report_correct.html', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('e2e_screenshots_correct\\', 'e2e_screenshots_correct/')
with open('e2e_test_report_correct.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('路径已修复')
