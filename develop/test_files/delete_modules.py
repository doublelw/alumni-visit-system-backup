# -*- coding: utf-8 -*-
import re

# 读取admin.html
with open('frontend/templates/admin.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# 删除问卷管理页面
html_content = re.sub(
    r'        <!-- 问卷管理页面 -->.*?</div>\n<arg_key>description</arg_key><arg_value>创建删除脚本
