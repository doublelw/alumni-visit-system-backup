# 校友入校登记系统 - 完整部署指南

## 📋 目录
- [系统概述](#系统概述)
- [服务器要求](#服务器要求)
- [快速部署](#快速部署)
- [详细部署步骤](#详细部署步骤)
- [系统管理](#系统管理)
- [故障排除](#故障排除)

---

## 🎯 系统概述

### 系统架构
```
┌─────────────────┐    HTTPS/HTTP    ┌─────────────────┐
│   用户浏览器     │ ◄──────────────► │     Nginx       │
│  (移动端/PC端)   │                  │  (反向代理)      │
└─────────────────┘                  └─────────────────┘
                                              │
                                      ┌───────┴───────┐
                                      │               │
                              ┌───────▼───────┐ ┌─────▼─────┐
                              │  Flask应用     │ │  静态文件  │
                              │  (Gunicorn)   │ │ (Frontend) │
                              └───────┬───────┘ └───────────┘
                                      │
                              ┌───────▼───────┐
                              │   MySQL数据库 │
                              │   (用户数据)   │
                              └───────────────┘
```

### 技术栈
- **后端**: Flask + SQLAlchemy + JWT
- **前端**: HTML5 + CSS3 + JavaScript (移动端优化)
- **数据库**: MySQL 8.0
- **Web服务器**: Nginx 1.24
- **应用服务器**: Gunicorn
- **SSL证书**: Let's Encrypt
- **系统服务**: systemd

---

## 🖥️ 服务器要求

### 最低配置
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 50GB SSD
- **网络**: 公网IP，开放80/443端口

### 软件要求
- **Python**: 3.11+
- **Node.js**: 18+ (用于前端构建)
- **MySQL**: 8.0+
- **Nginx**: 1.18+

### 域名要求
- **域名**: 已解析到服务器IP
- **SSL**: 支持Let's Encrypt自动申请

---

## 🚀 快速部署

### 一键部署命令
```bash
# 下载部署脚本
curl -fsSL https://your-domain.com/deploy.sh -o deploy.sh

# 执行一键部署
chmod +x deploy.sh
sudo ./deploy.sh --domain your-domain.com --email admin@your-domain.com
```

### 预配置参数
```bash
# 默认配置
./deploy.sh \
  --domain www.pofeclife.top \
  --email admin@pofeclife.top \
  --deploy-path /var/www/lsalumni \
  --mysql-root-password your_mysql_password \
  --app-secret-key your_secret_key
```

---

## 📝 详细部署步骤

### 1. 服务器初始化

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget git unzip htop vim

# 设置时区
sudo timedatectl set-timezone Asia/Shanghai
```

### 2. 安装依赖环境

```bash
# 安装Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 安装Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 安装MySQL 8.0
sudo apt install -y mysql-server

# 安装Nginx
sudo apt install -y nginx

# 安装SSL证书工具
sudo apt install -y certbot python3-certbot-nginx
```

### 3. 数据库配置

```bash
# 安全配置MySQL
sudo mysql_secure_installation

# 创建数据库和用户
sudo mysql -u root -p << EOF
CREATE DATABASE lsalumni CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lsalumni'@'localhost' IDENTIFIED BY 'your_db_password';
GRANT ALL PRIVILEGES ON lsalumni.* TO 'lsalumni'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### 4. 部署应用代码

```bash
# 创建部署目录
sudo mkdir -p /var/www/lsalumni
sudo chown $USER:$USER /var/www/lsalumni

# 上传应用代码包
# (使用SCP/SFTP或其他方式上传)

# 解压应用代码
cd /var/www/lsalumni
unzip lsalumni-package.zip

# 创建Python虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements_prod.txt
```

### 5. 配置环境变量

```bash
# 创建环境配置文件
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=your_very_secure_secret_key_here
DATABASE_URL=mysql+pymysql://lsalumni:your_db_password@localhost/lsalumni
JWT_SECRET_KEY=your_jwt_secret_key_here
DOMAIN_NAME=www.pofeclife.top
SSL_CERT_PATH=/etc/ssl/certs/lsalumni.crt
SSL_KEY_PATH=/etc/ssl/private/lsalumni.key
EOF
```

### 6. 初始化数据库

```bash
# 运行数据库初始化脚本
source venv/bin/activate
python scripts/init_database.py

# 创建系统账户
python scripts/create_admin.py
```

### 7. 配置Nginx

```bash
# 复制Nginx配置文件
sudo cp config/nginx/lsalumni.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/lsalumni.conf /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# 测试Nginx配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### 8. 配置SSL证书

```bash
# 申请Let's Encrypt证书
sudo certbot --nginx -d www.pofeclife.top -d pofeclife.top \
  --email admin@pofeclife.top \
  --agree-tos --no-eff-email --non-interactive

# 设置自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 9. 配置系统服务

```bash
# 创建systemd服务文件
sudo cp config/systemd/lsalumni.service /etc/systemd/system/

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable lsalumni
sudo systemctl start lsalumni

# 检查服务状态
sudo systemctl status lsalumni
```

---

## 🔧 系统管理

### 服务管理命令

```bash
# 启动系统
sudo systemctl start lsalumni
sudo systemctl start nginx

# 停止系统
sudo systemctl stop lsalumni
sudo systemctl stop nginx

# 重启系统
sudo systemctl restart lsalumni
sudo systemctl restart nginx

# 查看状态
sudo systemctl status lsalumni
sudo systemctl status nginx

# 查看日志
sudo journalctl -u lsalumni -f
sudo tail -f /var/log/nginx/lsalumni_access.log
sudo tail -f /var/log/nginx/lsalumni_error.log
```

### 数据库管理

```bash
# 备份数据库
mysqldump -u root -p lsalumni > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
mysql -u root -p lsalumni < backup_file.sql

# 进入数据库
mysql -u root -p lsalumni
```

### 日志管理

```bash
# 查看应用日志
tail -f /var/log/lsalumni/app.log

# 查看Nginx访问日志
tail -f /var/log/nginx/lsalumni_access.log

# 查看Nginx错误日志
tail -f /var/log/nginx/lsalumni_error.log

# 查看系统服务日志
journalctl -u lsalumni -f
```

### 性能监控

```bash
# 查看系统资源
htop

# 查看磁盘使用
df -h

# 查看内存使用
free -h

# 查看端口占用
netstat -tlnp | grep -E ':(80|443|5000)'
```

---

## 🚨 故障排除

### 常见问题及解决方案

#### 1. 网站无法访问
```bash
# 检查Nginx状态
sudo systemctl status nginx

# 检查端口监听
sudo netstat -tlnp | grep nginx

# 检查防火墙
sudo ufw status
sudo ufw allow 80,443/tcp

# 检查DNS解析
nslookup www.pofeclife.top
```

#### 2. 500错误
```bash
# 查看应用日志
sudo journalctl -u lsalumni -f

# 检查数据库连接
source venv/bin/activate
python -c "from app import create_app; create_app()"

# 重启应用服务
sudo systemctl restart lsalumni
```

#### 3. SSL证书问题
```bash
# 检查证书状态
sudo certbot certificates

# 手动续期证书
sudo certbot renew

# 重新申请证书
sudo certbot --nginx -d www.pofeclife.top -d pofeclife.top --force-renewal
```

#### 4. 数据库连接失败
```bash
# 检查MySQL服务
sudo systemctl status mysql

# 测试数据库连接
mysql -u lsalumni -p lsalumni

# 重置MySQL密码
sudo mysql -u root -p -e "ALTER USER 'lsalumni'@'localhost' IDENTIFIED BY 'new_password';"
```

#### 5. 静态文件404
```bash
# 检查文件权限
sudo chown -R www-data:www-data /var/www/lsalumni
sudo chmod -R 755 /var/www/lsalumni

# 检查Nginx配置
sudo nginx -t

# 重新加载Nginx
sudo nginx -s reload
```

### 紧急恢复程序

```bash
# 完整系统重启
sudo systemctl restart lsalumni nginx mysql

# 从备份恢复数据库
mysql -u root -p lsalumni < latest_backup.sql

# 重新初始化应用
cd /var/www/lsalumni
source venv/bin/activate
python scripts/init_database.py
sudo systemctl restart lsalumni
```

---

## 📊 监控指标

### 关键指标
- **响应时间**: < 2秒
- **可用性**: > 99.9%
- **并发用户**: 支持100+
- **存储空间**: 监控使用率
- **带宽使用**: 监控流量

### 监控脚本
```bash
# 创建健康检查脚本
cat > /var/www/lsalumni/scripts/health_check.sh << 'EOF'
#!/bin/bash
# 检查服务状态
systemctl is-active lsalumni >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Flask应用服务异常"
    systemctl restart lsalumni
fi

systemctl is-active nginx >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Nginx服务异常"
    systemctl restart nginx
fi

# 检查网站响应
curl -s -o /dev/null -w "%{http_code}" https://www.pofeclife.top/lsalumni/ | grep -v 200
if [ $? -eq 0 ]; then
    echo "网站响应异常"
fi
EOF

chmod +x /var/www/lsalumni/scripts/health_check.sh

# 添加到定时任务
echo "*/5 * * * * /var/www/lsalumni/scripts/health_check.sh" | crontab -
```

---

## 📞 技术支持

### 联系方式
- **技术支持**: admin@pofeclife.top
- **紧急联系**: 系统管理员

### 维护时间
- **日常维护**: 每周日 02:00-04:00
- **紧急维护**: 提前24小时通知

---

*文档版本: v1.0.0*
*最后更新: 2025-10-20*
*维护者: 系统管理员*