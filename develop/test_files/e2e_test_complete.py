#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试 - 完整版本
"""
import asyncio
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:5000"
SCREENSHOT_DIR = "e2e_screenshots_final"

TEST_DATA = {
    'parent': {'phone': '13900002001', 'pin': '88'},
    'teacher': {'phone': '13800000001', 'password': '1234'},
    'student_id': '2024001'
}

print("创建测试文件...")
