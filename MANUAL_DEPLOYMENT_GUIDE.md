# 校友入校登记系统 - 手动部署指南

## 服务器信息
- **IP地址**: 8.152.209.82
- **SSH用户**: root
- **SSH密码**: Sy6787687.
- **域名**: www.pofeclife.top
- **部署路径**: /var/www/lsalumni

## 部署包内容
✅ 部署包已创建完成：
- **目录位置**: `D:\Project\校友入校登记\upload_package`
- **压缩包**: `D:\Project\校友入校登记\lsalumni_deploy_package.zip`
- **大小**: 9.73 MB

包含文件：
- `backend/` - Flask后端应用
- `frontend/` - 前端HTML文件
- `run.py` - 应用启动文件
- `requirements_prod.txt` - Python依赖
- `nginx_config.conf` - Nginx配置
- `systemd_service.service` - 系统服务配置
- `server_setup.sh` - 服务器环境安装脚本
- `deploy.sh` - 应用部署脚本

---

## 第一步：连接服务器并上传文件

### 1.1 使用SSH连接服务器
```bash
ssh root@8.152.209.82
# 密码: Sy6787687.
```

### 1.2 上传部署文件
**方法A：使用SCP上传**
```bash
# 在本地Windows命令行中运行
scp -r "D:\Project\校友入校登记\upload_package" root@8.152.209.82:/var/www/lsalumni
```

**方法B：使用FTP/SFTP工具**
- 连接地址: 8.152.209.82
- 用户名: root
- 密码: Sy6787687.
- 端口: 22 (SFTP) 或 21 (FTP)
- 上传 `upload_package` 目录到 `/var/www/`
- 重命名为 `lsalumni`

---

## 第二步：服务器环境配置

### 2.1 运行环境安装脚本
```bash
cd /var/www/lsalumni
bash server_setup.sh
```

如果脚本无法运行，请手动执行以下命令：

#### 2.1.1 更新系统
```bash
apt update && apt upgrade -y
```

#### 2.1.2 安装基础软件
```bash
apt install -y curl wget git unzip software-properties-common python3-pip python3-venv build-essential
```

#### 2.1.3 安装Nginx
```bash
apt install -y nginx
systemctl start nginx
systemctl enable nginx
```

#### 2.1.4 安装Node.js (可选)
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs
```

#### 2.1.5 安装MySQL/MariaDB
```bash
apt install -y mysql-server
# 或者
apt install -y mariadb-server

systemctl start mysql
systemctl enable mysql
```

#### 2.1.6 安装Redis
```bash
apt install -y redis-server
systemctl start redis-server
systemctl enable redis-server
```

### 2.2 配置MySQL数据库
```bash
# 安全配置
mysql_secure_installation

# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE lsalumni CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lsalumni'@'localhost' IDENTIFIED BY 'Sy6787687.';
GRANT ALL PRIVILEGES ON lsalumni.* TO 'lsalumni'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 第三步：部署应用

### 3.1 设置文件权限
```bash
cd /var/www
chown -R www-data:www-data lsalumni
chmod -R 755 lsalumni
```

### 3.2 创建Python虚拟环境
```bash
cd /var/www/lsalumni
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 3.3 安装Python依赖
```bash
source venv/bin/activate
pip install -r requirements_prod.txt
```

### 3.4 配置环境变量
```bash
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=mysql+pymysql://root:Sy6787687.@localhost/lsalumni
UPLOAD_FOLDER=/var/www/lsalumni/uploads
LOG_LEVEL=INFO
EOF
```

### 3.5 创建必要目录
```bash
mkdir -p /var/www/lsalumni/uploads
mkdir -p /var/www/lsalumni/logs
mkdir -p /var/log/lsalumni
```

### 3.6 初始化数据库
```bash
source venv/bin/activate
python -c "
from backend.app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('数据库表创建成功')
"
```

### 3.7 创建管理员账户
```bash
source venv/bin/activate
python -c "
import sys
sys.path.append('/var/www/lsalumni/backend')
from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            real_name='系统管理员',
            email='admin@pofeclife.top',
            phone='13800138001',
            user_type='admin',
            status='active'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('管理员账户创建成功 - 用户名: admin, 密码: admin123')
    else:
        print('管理员账户已存在')
"
```

---

## 第四步：配置Nginx

### 4.1 复制Nginx配置
```bash
cp nginx_config.conf /etc/nginx/sites-available/lsalumni
ln -sf /etc/nginx/sites-available/lsalumni /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
```

### 4.2 测试并重载Nginx
```bash
nginx -t
systemctl reload nginx
```

---

## 第五步：配置系统服务

### 5.1 创建systemd服务
```bash
cp systemd_service.service /etc/systemd/system/lsalumni.service
systemctl daemon-reload
systemctl enable lsalumni
```

### 5.2 修改服务配置（如果需要）
编辑 `/etc/systemd/system/lsalumni.service`：
```ini
[Unit]
Description=LS Alumni System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/lsalumni
Environment=PATH=/var/www/lsalumni/venv/bin
ExecStart=/var/www/lsalumni/venv/bin/gunicorn --config gunicorn_config.py run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5.3 启动服务
```bash
systemctl start lsalumni
systemctl status lsalumni
```

---

## 第六步：配置SSL证书

### 6.1 方法A：使用Let's Encrypt（推荐）
```bash
# 安装Certbot
apt install -y certbot python3-certbot-nginx

# 获取SSL证书
certbot --nginx -d www.pofeclife.top -d pofeclife.top

# 设置自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### 6.2 方法B：自签名证书（临时测试）
```bash
# 创建证书目录
mkdir -p /etc/ssl/certs /etc/ssl/private

# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/lsalumni.key \
    -out /etc/ssl/certs/lsalumni.crt \
    -subj "/C=CN/ST=State/L=City/O=Organization/CN=www.pofeclife.top"
```

---

## 第七步：测试访问

### 7.1 检查服务状态
```bash
# 检查应用服务
systemctl status lsalumni

# 检查Nginx服务
systemctl status nginx

# 检查端口监听
netstat -tlnp | grep -E ':(80|443|5000)'
```

### 7.2 访问测试
- **主页面**: https://www.pofeclife.top/lsalumni
- **管理后台**: https://www.pofeclife.top/lsalumni/admin.html
- **保安门户**: https://www.pofeclife.top/lsalumni/security-portal.html

### 7.3 默认账户
- **管理员**: admin / admin123

---

## 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 查看服务日志
journalctl -u lsalumni -f

# 查看应用日志
tail -f /var/log/lsalumni/*.log

# 检查配置文件
cd /var/www/lsalumni
source venv/bin/activate
python -c "from backend.app import create_app; print('应用配置正常')"
```

#### 2. 数据库连接失败
```bash
# 检查MySQL服务
systemctl status mysql

# 测试数据库连接
mysql -u root -p -e "SHOW DATABASES;"

# 检查数据库权限
mysql -u root -p -e "SHOW GRANTS FOR 'root'@'localhost';"
```

#### 3. Nginx配置错误
```bash
# 测试Nginx配置
nginx -t

# 查看Nginx日志
tail -f /var/log/nginx/error.log

# 重新加载配置
systemctl reload nginx
```

#### 4. 权限问题
```bash
# 重新设置权限
chown -R www-data:www-data /var/www/lsalumni
chmod -R 755 /var/www/lsalumni
chmod -R 777 /var/www/lsalumni/uploads
```

### 日志位置
- **应用日志**: `/var/log/lsalumni/`
- **Nginx访问日志**: `/var/log/nginx/lsalumni_access.log`
- **Nginx错误日志**: `/var/log/nginx/lsalumni_error.log`
- **系统服务日志**: `journalctl -u lsalumni`

---

## 维护命令

### 服务管理
```bash
# 重启应用
systemctl restart lsalumni

# 重启Nginx
systemctl restart nginx

# 查看服务状态
systemctl status lsalumni nginx
```

### 数据库备份
```bash
# 备份数据库
mysqldump -u root -p lsalumni > lsalumni_backup_$(date +%Y%m%d).sql

# 恢复数据库
mysql -u root -p lsalumni < lsalumni_backup_20251020.sql
```

### 应用更新
```bash
cd /var/www/lsalumni
git pull  # 如果使用git
# 或上传新文件覆盖

# 重启服务
systemctl restart lsalumni
```

---

## 安全建议

1. **定期更新系统和依赖包**
2. **修改默认密码**
3. **配置防火墙规则**
4. **启用fail2ban防暴力破解**
5. **定期备份数据**
6. **监控日志文件**

---

## 联系支持

如果遇到部署问题，请提供以下信息：
- 服务器操作系统版本
- 错误日志内容
- 执行的具体命令
- 错误发生的步骤

部署完成后，系统将可以通过 https://www.pofeclife.top/lsalumni 访问。