#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连接测试脚本
用于测试服务器连接和诊断SSL问题
"""

import requests
import sys
from urllib.parse import urlparse

def test_connection(url):
    """测试连接"""
    print(f"正在测试连接: {url}")

    try:
        # 发送GET请求
        response = requests.get(url, timeout=10)

        print(f"✓ 连接成功!")
        print(f"  状态码: {response.status_code}")
        print(f"  响应时间: {response.elapsed.total_seconds():.2f}秒")
        print(f"  服务器: {response.headers.get('Server', 'Unknown')}")
        print(f"  内容类型: {response.headers.get('Content-Type', 'Unknown')}")

        # 显示部分响应内容
        if response.status_code == 200:
            content = response.text[:200]
            print(f"  响应内容预览: {content}...")

        return True

    except requests.exceptions.SSLError as e:
        print(f"✗ SSL错误: {e}")
        print("  建议使用 HTTP 而不是 HTTPS")
        return False

    except requests.exceptions.ConnectionError as e:
        print(f"✗ 连接错误: {e}")
        print("  请检查服务器是否正在运行")
        return False

    except requests.exceptions.Timeout as e:
        print(f"✗ 超时错误: {e}")
        print("  服务器响应时间过长")
        return False

    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("       校友入校登记系统 - 连接测试")
    print("=" * 50)

    # 测试不同的URL
    test_urls = [
        "http://127.0.0.1:5000",
        "https://127.0.0.1:5000",  # 这个应该失败
        "http://localhost:5000",
        "https://localhost:5000",   # 这个也应该失败
    ]

    results = {}

    for url in test_urls:
        print(f"\n测试 {url}:")
        results[url] = test_connection(url)
        print("-" * 30)

    # 显示总结
    print("\n" + "=" * 50)
    print("测试总结:")
    print("=" * 50)

    for url, success in results.items():
        status = "✓ 成功" if success else "✗ 失败"
        print(f"{url}: {status}")

    # 推荐解决方案
    successful_urls = [url for url, success in results.items() if success]

    if successful_urls:
        print(f"\n✓ 推荐使用以下地址访问:")
        for url in successful_urls:
            print(f"  • {url}")
    else:
        print("\n✗ 所有连接测试都失败了")
        print("  请确保服务器正在运行:")
        print("  python server_manager.py start --debug --app-dir backend")

if __name__ == '__main__':
    main()