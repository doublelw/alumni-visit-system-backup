#!/bin/bash

# 校友入校登记系统 - 快速初始化脚本
# 使用方法: chmod +x 快速初始化.sh && ./快速初始化.sh

echo "============================================================"
echo "校友入校登记系统 - 快速初始化"
echo "============================================================"
echo ""

cd "$(dirname "$0")/backend"

echo "[1/3] 数据库迁移..."
echo "------------------------------------------------------------"
python3 scripts/migrate_database.py
if [ $? -ne 0 ]; then
    echo "[错误] 数据库迁移失败！"
    exit 1
fi
echo ""

echo "[2/3] 创建教师账户..."
echo "------------------------------------------------------------"
python3 scripts/create_teacher_accounts.py
if [ $? -ne 0 ]; then
    echo "[错误] 创建教师账户失败！"
    exit 1
fi
echo ""

echo "[3/3] 启动系统..."
echo "------------------------------------------------------------"
echo "正在启动服务器..."
echo "访问地址: http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

python3 scripts/run.py
