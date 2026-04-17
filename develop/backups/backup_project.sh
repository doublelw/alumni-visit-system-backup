#!/bin/bash
# 校园访问管理系统 - 备份脚本（Linux/Mac版本）
# 使用方法：chmod +x backup_project.sh && ./backup_project.sh

set -e

echo "========================================"
echo "校园访问管理系统 - 项目备份"
echo "========================================"
echo ""

# 设置项目路径
PROJECT_DIR="/d/Project/校友入校登记"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
fi

echo "正在备份项目..."
echo "备份路径: $BACKUP_DIR"
echo "时间戳: $TIMESTAMP"
echo ""

# 切换到项目目录
cd "$PROJECT_DIR"

# 创建备份文件
echo "正在创建备份文件..."
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='backups' \
    --exclude='*.db' \
    --exclude='instance' \
    --exclude='backup_*.tar.gz' \
    . 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "备份成功！"
    echo "========================================"
    echo ""
    echo "备份文件: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz"
    echo ""

    # 显示备份文件大小
    if [ -f "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" ]; then
        SIZE=$(stat -f%z "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" 2>/dev/null || stat -c%s "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" 2>/dev/null)
        echo "文件大小: $SIZE 字节"
    fi

    echo ""
    echo "恢复方法："
    echo "  tar -xzf backup_$TIMESTAMP.tar.gz"
    echo ""
else
    echo ""
    echo "========================================"
    echo "备份失败！"
    echo "========================================"
    echo ""
    exit 1
fi
