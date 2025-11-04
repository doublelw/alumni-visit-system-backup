#!/usr/bin/env python3
"""
测试数据库连接脚本
"""
import os
import sys
import sqlite3

# 设置路径
os.chdir("/var/www/lsalumni")
sys.path.insert(0, "/var/www/lsalumni")
sys.path.insert(0, "/var/www/lsalumni/backend")

print(f"当前工作目录: {os.getcwd()}")
print(f"数据库文件路径: /var/www/lsalumni/lsalumni.db")

# 直接使用sqlite3测试
conn = sqlite3.connect("/var/www/lsalumni/lsalumni.db")
cursor = conn.cursor()

# 检查表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"数据库中的表: {[table[0] for table in tables]}")

# 检查用户
if 'users' in [table[0] for table in tables]:
    cursor.execute("SELECT username, real_name FROM users WHERE username='admin';")
    admin = cursor.fetchone()
    if admin:
        print(f"找到管理员用户: {admin[0]}, {admin[1]}")
    else:
        print("未找到管理员用户")
else:
    print("users表不存在")

conn.close()

# 测试Flask应用连接
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////var/www/lsalumni/lsalumni.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

with app.app_context():
    try:
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result]
        print(f"Flask应用看到的数据库表: {tables}")

        if 'users' in tables:
            result = db.session.execute(text("SELECT username, real_name FROM users WHERE username='admin';"))
            admin = result.fetchone()
            if admin:
                print(f"Flask应用找到管理员用户: {admin[0]}, {admin[1]}")
            else:
                print("Flask应用未找到管理员用户")
        else:
            print("Flask应用看不到users表")

    except Exception as e:
        print(f"Flask应用数据库测试失败: {e}")
        import traceback
        traceback.print_exc()