#!/usr/bin/env python
"""
部署准备脚本
清理硬编码地址，生成生产配置，准备部署
"""

import os
import sys
import json
import re
from datetime import datetime

def find_hardcoded_addresses(directory):
    """查找系统中的硬编码地址"""

    # 需要搜索的文件类型
    extensions = ['.py', '.js', '.html', '.json', '.md', '.txt', '.conf', '.sh']

    # 需要查找的模式
    patterns = [
        r'localhost:\d+',
        r'127\.0\.0\.1:\d+',
        r'192\.168\.\d+\.\d+:\d+',
        r'172\.20\.\d+\.\d+:\d+',
        r'https?://[^/]*(localhost|127\.0\.0\.1|192\.168\.|172\.20\.)[^/\s]*',
    ]

    found_addresses = []

    for root, dirs, files in os.walk(directory):
        # 跳过一些不需要的目录
        skip_dirs = {'__pycache__', '.git', 'node_modules', 'venv', 'env', '.vscode', 'logs'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                        for pattern in patterns:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                found_addresses.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'match': match.group(),
                                    'pattern': pattern
                                })
                except Exception as e:
                    print(f"无法读取文件 {file_path}: {e}")

    return found_addresses

def generate_production_config():
    """生成生产环境配置"""

    config = {
        "production": {
            "FLASK_ENV": "production",
            "HOST": "0.0.0.0",
            "PORT": 5000,
            "SSL_ENABLED": "true",

            # 数据库配置 - 需要用户手动设置
            "DATABASE_URL": "mysql+pymysql://lsalumni:YOUR_PASSWORD@localhost/lsalumni",

            # JWT密钥 - 需要用户手动设置
            "JWT_SECRET_KEY": "GENERATE_NEW_SECRET_KEY",

            # SSL证书路径 - 需要用户手动设置
            "SSL_CERT": "/etc/ssl/certs/alumni_system.crt",
            "SSL_KEY": "/etc/ssl/private/alumni_system.key",

            # 邮件配置 - 需要用户手动设置
            "MAIL_SERVER": "smtp.gmail.com",
            "MAIL_PORT": 587,
            "MAIL_USE_TLS": "true",
            "MAIL_USERNAME": "your_email@gmail.com",
            "MAIL_PASSWORD": "your_app_password",

            # 应用配置
            "SITE_NAME": "校友入校登记系统",
            "ADMIN_EMAIL": "admin@yourdomain.com",
            "UPLOAD_FOLDER": "/var/www/alumni_system/uploads",
            "MAX_CONTENT_LENGTH": "10485760"  # 10MB
        }
    }

    return config

def create_env_file():
    """创建.env文件模板"""

    env_template = """# 校友入校登记系统 - 生产环境配置
# 复制此文件为 .env 并填入实际值

# 基本配置
FLASK_ENV=production
HOST=0.0.0.0
PORT=5000

# 数据库配置
DATABASE_URL=mysql+pymysql://lsalumni:YOUR_DB_PASSWORD@localhost/lsalumni

# 安全配置
JWT_SECRET_KEY=GENERATE_STRONG_SECRET_KEY_HERE
SSL_ENABLED=true

# SSL证书配置
SSL_CERT=/etc/ssl/certs/alumni_system.crt
SSL_KEY=/etc/ssl/private/alumni_system.key

# 邮件配置
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

# 应用配置
SITE_NAME=校友入校登记系统
ADMIN_EMAIL=admin@yourdomain.com
UPLOAD_FOLDER=/var/www/alumni_system/uploads
"""

    return env_template

def create_deployment_checklist():
    """创建部署检查清单"""

    checklist = """# 部署检查清单

## 数据库配置
- [ ] 创建MySQL数据库 `lsalumni`
- [ ] 创建数据库用户 `lsalumni`
- [ ] 授予用户权限
- [ ] 测试数据库连接

## SSL证书配置
- [ ] 获取SSL证书文件
- [ ] 配置证书路径
- [ ] 测试HTTPS访问

## 安全配置
- [ ] 生成强随机JWT密钥
- [ ] 更改默认管理员密码
- [ ] 配置防火墙规则
- [ ] 设置定期备份

## 邮件配置
- [ ] 配置SMTP服务器
- [ ] 测试邮件发送功能
- [ ] 设置邮件模板

## 文件权限
- [ ] 设置上传目录权限
- [ ] 配置日志目录权限
- [ ] 检查配置文件权限

## 性能优化
- [ ] 配置数据库连接池
- [ ] 设置静态文件缓存
- [ ] 配置反向代理（Nginx）
- [ ] 设置进程管理器（Gunicorn）

## 监控配置
- [ ] 配置日志轮转
- [ ] 设置系统监控
- [ ] 配置错误报告
- [ ] 设置健康检查

## 测试验证
- [ ] 测试用户注册登录
- [ ] 测试访问申请流程
- [ ] 测试管理后台功能
- [ ] 测试移动端访问
"""

    return checklist

def main():
    """主函数"""

    print("=" * 60)
    print("校友入校登记系统 - 部署准备工具")
    print("=" * 60)

    # 1. 查找硬编码地址
    print("\n1. 扫描硬编码地址...")
    try:
        addresses = find_hardcoded_addresses('.')

        if addresses:
            print(f"发现 {len(addresses)} 个硬编码地址:")
            for addr in addresses[:10]:  # 只显示前10个
                rel_path = os.path.relpath(addr['file'], '.')
                print(f"  {rel_path}:{addr['line']} - {addr['match']}")

            if len(addresses) > 10:
                print(f"  ... 还有 {len(addresses) - 10} 个")
        else:
            print("  ✅ 未发现硬编码地址")

    except Exception as e:
        print(f"  ❌ 扫描失败: {e}")

    # 2. 生成配置文件
    print("\n2. 生成配置文件...")

    try:
        # 生成生产配置
        prod_config = generate_production_config()
        with open('production_config.json', 'w', encoding='utf-8') as f:
            json.dump(prod_config, f, indent=2, ensure_ascii=False)
        print("  ✅ 生成 production_config.json")

        # 生成.env模板
        env_template = create_env_file()
        with open('.env.template', 'w', encoding='utf-8') as f:
            f.write(env_template)
        print("  ✅ 生成 .env.template")

        # 生成部署检查清单
        checklist = create_deployment_checklist()
        with open('DEPLOYMENT_CHECKLIST.md', 'w', encoding='utf-8') as f:
            f.write(checklist)
        print("  ✅ 生成 DEPLOYMENT_CHECKLIST.md")

    except Exception as e:
        print(f"  ❌ 生成配置文件失败: {e}")

    # 3. 部署建议
    print("\n3. 部署建议:")
    print("  🔧 使用 nginx 作为反向代理")
    print("  🔧 使用 gunicorn 作为 WSGI 服务器")
    print("  🔧 配置 SSL 证书启用 HTTPS")
    print("  🔧 设置数据库连接池")
    print("  🔧 配置日志轮转和监控")

    print("\n4. 下一步操作:")
    print("  1. 复制 .env.template 为 .env 并填入实际配置")
    print("  2. 按照 DEPLOYMENT_CHECKLIST.md 完成部署准备")
    print("  3. 使用 production_config.json 中的配置")
    print("  4. 运行部署脚本")

    print(f"\n✅ 部署准备完成！时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()