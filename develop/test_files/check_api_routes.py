#!/usr/bin/env python3
"""
检查API路由注册情况
"""
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app

def check_routes():
    app = create_app('development')

    with app.app_context():
        print("=== API路由检查 ===")

        # 获取所有路由
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'rule': rule.rule,
                'methods': list(rule.methods),
                'endpoint': rule.endpoint
            })

        # 按路径排序
        routes.sort(key=lambda x: x['rule'])

        # 查找学生出校相关的路由
        print("\n=== 学生出校相关API路由 ===")
        student_exit_routes = [r for r in routes if '/api/student-exit' in r['rule'] or 'student_exit' in r['endpoint']]

        if student_exit_routes:
            for route in student_exit_routes:
                print(f"  - {route['rule']} [{', '.join(route['methods'])}] -> {route['endpoint']}")
        else:
            print("  ❌ 没有找到学生出校相关的API路由")

        # 查找所有API路由
        print("\n=== 所有API路由 ===")
        api_routes = [r for r in routes if r['rule'].startswith('/api/')]

        for route in api_routes:
            methods = [m for m in route['methods'] if m not in ['HEAD', 'OPTIONS']]
            if methods:
                print(f"  - {route['rule']} [{', '.join(methods)}] -> {route['endpoint']}")

        # 检查蓝图注册
        print("\n=== 蓝图注册情况 ===")
        if hasattr(app, 'blueprints'):
            for name, blueprint in app.blueprints.items():
                print(f"  - {name}: {blueprint}")

        # 检查student_exit.py是否被正确导入
        print("\n=== 模块导入检查 ===")
        try:
            from backend.app.routes import student_exit
            print("  ✅ student_exit 模块导入成功")

            # 检查模块中定义的路由
            if hasattr(student_exit, 'student_exit_bp'):
                print("  ✅ student_exit_bp 蓝图存在")
                for rule in student_exit.student_exit_bp.url_map.iter_rules():
                    print(f"    - {rule.rule} [{', '.join(rule.methods)}] -> {rule.endpoint}")
            else:
                print("  ❌ student_exit_bp 蓝图不存在")

        except ImportError as e:
            print(f"  ❌ student_exit 模块导入失败: {e}")

if __name__ == "__main__":
    check_routes()