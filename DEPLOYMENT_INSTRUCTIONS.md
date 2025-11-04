# 校友入校登记系统 - 部署说明

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
