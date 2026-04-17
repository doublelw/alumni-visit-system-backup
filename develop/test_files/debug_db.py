#!/usr/bin/env python3
"""
调试数据库连接的简单Flask应用
"""
import os
import sys
import sqlite3

# 设置路径
os.chdir("/var/www/lsalumni")
sys.path.insert(0, "/var/www/lsalumni")
sys.path.insert(0, "/var/www/lsalumni/backend")

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////var/www/lsalumni/lsalumni.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

@app.route('/debug-db')
def debug_db():
    """调试数据库连接"""
    try:
        with app.app_context():
            # 检查表
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]

            # 检查用户
            users_info = []
            if 'users' in tables:
                result = db.session.execute(text("SELECT username, real_name, user_type, status FROM users;"))
                users_info = [dict(row) for row in result]

            return jsonify({
                'status': 'success',
                'working_directory': os.getcwd(),
                'database_uri': app.config["SQLALCHEMY_DATABASE_URI"],
                'tables': tables,
                'users': users_info
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'working_directory': os.getcwd(),
            'database_uri': app.config["SQLALCHEMY_DATABASE_URI"]
        }), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
