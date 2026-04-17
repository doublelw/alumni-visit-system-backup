#!/usr/bin/env python3
with open('e2e_test_report_final.html', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('e2e_screenshots_final\\', 'e2e_screenshots_final/')
with open('e2e_test_report_final.html', 'w', encoding='utf-8') as f:
    f.write(content)
import subprocess
subprocess.Popen(['cmd', '/c', 'start', 'e2e_test_report_final.html'], shell=True, cwd=r'D:\Project\校友入校登记')
print('报告已打开')
