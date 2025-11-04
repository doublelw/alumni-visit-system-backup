#!/usr/bin/env python
"""
创建生产环境部署包
"""

import os
import sys
import json
import zipfile
from datetime import datetime

def create_deployment_package():
    """创建部署包"""

    print("正在创建部署包...")

    # 部署包名称
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    package_name = f"lsalumni_deploy_package_{timestamp}.zip"

    # 需要包含的文件和目录
    include_files = [
        'requirements.txt',
        'requirements_prod.txt',
        'production_config.json',
        '.env.template',
        'run.py',
        'gunicorn_config.py',
        'nginx_config.conf',
        'systemd_service.service',
        'server_setup.sh',
        'deploy.sh'
    ]

    include_dirs = [
        'backend',
        'frontend',
        'deployment_scripts',
        'config'
    ]

    # 需要排除的文件和目录
    exclude_patterns = [
        '__pycache__',
        '.git',
        'node_modules',
        'venv',
        'env',
        '.vscode',
        'logs',
        'uploads',
        '*.pyc',
        '.log',
        '.db',
        '.sqlite3'
    ]

    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加文件
        for file_name in include_files:
            if os.path.exists(file_name):
                zipf.write(file_name)
                print(f"  + {file_name}")

        # 添加目录
        for dir_name in include_dirs:
            if os.path.exists(dir_name):
                for root, dirs, files in os.walk(dir_name):
                    # 过滤排除的目录
                    dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]

                    for file in files:
                        # 过滤排除的文件
                        if not any(pattern in file for pattern in exclude_patterns):
                            file_path = os.path.join(root, file)
                            zipf.write(file_path)
                            print(f"  + {file_path}")

    print(f"\n部署包已创建: {package_name}")
    return package_name

def create_production_env():
    """创建生产环境.env模板"""

    env_content = """# 校友入校登记系统 - 生产环境配置
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
MAX_CONTENT_LENGTH=10485760
"""

    with open('.env.template', 'w', encoding='utf-8') as f:
        f.write(env_content)

    print("生产环境配置模板已创建: .env.template")

def create_deployment_instructions():
    """创建部署说明"""

    instructions = """# 校友入校登记系统 - 部署说明

## 快速部署步骤

### 1. 服务器准备
```bash
# 更新系统
apt update && apt upgrade -y

# 安装必要软件
apt install python3 python3-pip python3-venv mysql-server nginx -y

# 安装SSL证书 (Let's Encrypt)
apt install certbot python3-certbot-nginx -y
certbot --nginx -d yourdomain.com
```

### 2. 数据库配置
```bash
# 登录MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE lsalumni CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lsalumni'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON lsalumni.* TO 'lsalumni'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. 应用部署
```bash
# 上传部署包到服务器 /var/www/lsalumni/
cd /var/www/lsalumni/

# 解压部署包
unzip lsalumni_deploy_package_*.zip

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements_prod.txt

# 配置环境变量
cp .env.template .env
# 编辑 .env 文件，填入实际配置值

# 初始化数据库
cd backend
python -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all()"

# 创建管理员用户
python create_admin_user.py
```

### 4. 配置服务
```bash
# 配置Nginx
cp nginx_config.conf /etc/nginx/sites-available/lsalumni
ln -s /etc/nginx/sites-available/lsalumni /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# 配置系统服务
cp systemd_service.service /etc/systemd/system/lsalumni.service
systemctl daemon-reload
systemctl enable lsalumni
systemctl start lsalumni
```

### 5. 验证部署
```bash
# 检查服务状态
systemctl status lsalumni
systemctl status nginx

# 检查端口
netstat -tlnp | grep :80
netstat -tlnp | grep :443

# 测试API
curl -k https://yourdomain.com/api/health
```

## 访问地址配置

配置以下访问地址：
1. 主页: https://www.pofeclife.top/lsalumni/
2. 管理后台: https://www.pofeclife.top/lsalumni/admin-login
3. 保安门户: https://www.pofeclife.top/lsalumni/security-portal
4. 校友注册: https://www.pofeclife.top/lsalumni/register

## 注意事项

1. 确保防火墙开放80和443端口
2. 定期备份数据库
3. 监控日志文件
4. 及时更新系统补丁
"""

    with open('DEPLOYMENT_INSTRUCTIONS.md', 'w', encoding='utf-8') as f:
        f.write(instructions)

    print("部署说明已创建: DEPLOYMENT_INSTRUCTIONS.md")

def main():
    """主函数"""

    print("=" * 60)
    print("校友入校登记系统 - 部署包生成工具")
    print("=" * 60)

    # 1. 创建生产环境配置
    print("\n1. 创建生产环境配置...")
    create_production_env()

    # 2. 创建部署说明
    print("\n2. 创建部署说明...")
    create_deployment_instructions()

    # 3. 创建部署包
    print("\n3. 创建部署包...")
    package_name = create_deployment_package()

    print(f"\n部署包生成完成！")
    print(f"部署包文件: {package_name}")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n后续步骤:")
    print(f"1. 上传 {package_name} 到阿里云服务器")
    print(f"2. 按照 DEPLOYMENT_INSTRUCTIONS.md 进行部署")
    print(f"3. 配置域名和SSL证书")

if __name__ == '__main__':
    main()