#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校友入校登记系统 - 快速测试设置
一键启动系统并运行测试
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def check_system_status():
    """检查系统状态"""
    print("🔍 检查系统状态...")

    try:
        response = subprocess.run(
            ['curl', '-s', 'http://localhost:5000/health'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if response.returncode == 0:
            print("✅ 系统正在运行")
            return True
        else:
            print("❌ 系统未响应")
            return False
    except:
        print("❌ 无法连接到系统")
        return False

def start_system():
    """启动系统"""
    print("🚀 启动校友入校登记系统...")

    try:
        # 检查是否有快速重启脚本
        quick_restart = Path("quick_restart.bat")
        if quick_restart.exists():
            print("🔄 使用快速重启脚本启动系统...")
            result = subprocess.run(['quick_restart.bat'], shell=True)
            return result.returncode == 0
        else:
            # 使用server_manager启动
            print("🔄 使用服务器管理器启动系统...")
            result = subprocess.run([
                sys.executable, 'server_manager.py',
                'restart', '--debug', '--app-dir', 'backend'
            ])
            return result.returncode == 0
    except Exception as e:
        print(f"❌ 启动系统失败: {e}")
        return False

def create_test_accounts():
    """创建测试账户"""
    print("👥 创建测试账户...")

    try:
        result = subprocess.run([
            sys.executable, 'create_test_accounts.py', 'create-all'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ 测试账户创建成功")
            return True
        else:
            print(f"❌ 测试账户创建失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 创建测试账户失败: {e}")
        return False

def run_api_tests():
    """运行API测试"""
    print("🧪 运行API测试...")

    try:
        result = subprocess.run([
            sys.executable, 'comprehensive_api_test.py'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ API测试完成")
            return True
        else:
            print(f"❌ API测试失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 运行API测试失败: {e}")
        return False

def display_test_info():
    """显示测试信息"""
    print("\n" + "="*60)
    print("📋 测试信息")
    print("="*60)

    print("\n🌐 访问地址:")
    print("  移动端/访客界面: http://localhost:5000")
    print("  管理后台登录页: http://localhost:5000/admin-login")
    print("  管理后台主页: http://localhost:5000/admin (登录后)")
    print("  保安管理端: http://localhost:5000/security-portal")

    print("\n👤 预设测试账户:")
    print("  管理员: admin / admin123")
    print("  教师: teacher001 / teacher123")
    print("  保安: security001 / security123")

    print("\n🧪 测试命令:")
    print("  创建测试账户: python create_test_accounts.py create-all")
    print("  运行API测试: python comprehensive_api_test.py")
    print("  查看用户列表: python create_test_accounts.py list")
    print("  清理测试数据: python create_test_accounts.py clean")

def main():
    """主函数"""
    print("🎯 校友入校登记系统 - 快速测试设置")
    print("="*60)

    # 1. 检查系统状态
    if not check_system_status():
        # 2. 启动系统
        if not start_system():
            print("❌ 无法启动系统，请手动启动后重试")
            sys.exit(1)

        print("⏳ 等待系统启动...")
        time.sleep(10)

        # 再次检查状态
        if not check_system_status():
            print("❌ 系统启动失败")
            sys.exit(1)

    # 3. 创建测试账户
    create_test_accounts()

    # 4. 运行API测试
    run_api_tests()

    # 5. 显示测试信息
    display_test_info()

    print("\n🎉 快速测试设置完成！")
    print("现在可以使用上述地址和账户信息进行测试。")

if __name__ == '__main__':
    main()