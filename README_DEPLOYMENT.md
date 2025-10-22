# 校友入校登记系统 - 服务器部署指南

## 服务器信息
- **IP地址**: 8.152.209.82
- **SSH用户**: root
- **SSH密码**: Sy6787687.
- **域名**: www.pofeclife.top
- **部署路径**: /var/www/lsalumni
- **访问地址**: https://www.pofeclife.top/lsalumni

## 部署步骤

### 1. 连接服务器
```bash
ssh root@8.152.209.82
# 输入密码: Sy6787687.
```

### 2. 上传文件到服务器
将以下文件上传到服务器的 `/var/www/lsalumni/` 目录：

#### 必需的应用文件：
- `backend/` - 后端应用目录
- `frontend/` - 前端静态文件
- `run.py` - 应用启动文件
- `gunicorn_config.py` - Gunicorn配置
- `requirements_prod.txt` - Python依赖
- `nginx_config.conf` - Nginx配置
- `systemd_service.service` - 系统服务配置
- `server_setup.sh` - 服务器环境安装脚本
- `deploy.sh` - 部署脚本

### 3. 运行环境安装脚本
```bash
cd /var/www/lsalumni
chmod +x server_setup.sh
bash server_setup.sh
```

### 4. 配置MySQL数据库
```bash
# 安全配置MySQL
mysql_secure_installation

# 登录MySQL创建数据库
mysql -u root -p
CREATE DATABASE lsalumni CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 5. 安装SSL证书（使用Let's Encrypt）
```bash
# 安装Certbot
apt install -y certbot python3-certbot-nginx

# 获取SSL证书
certbot --nginx -d www.pofeclife.top -d pofeclife.top

# 自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### 6. 运行部署脚本
```bash
cd /var/www/lsalumni
chmod +x deploy.sh
bash deploy.sh
```

## 目录结构
```
/var/www/lsalumni/
├── backend/                    # 后端应用
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/
│   │   ├── routes/
│   │   └── config.py
│   └── run.py
├── frontend/                   # 前端文件
│   ├── static/
│   │   ├── js/
│   │   ├── css/
│   │   └── images/
│   └── templates/
├── uploads/                   # 上传文件目录
├── venv/                      # Python虚拟环境
├── gunicorn_config.py        # Gunicorn配置
├── nginx_config.conf         # Nginx配置
├── systemd_service.service   # 系统服务配置
├── requirements_prod.txt     # Python依赖
├── .env                      # 环境变量
└── deploy.sh                 # 部署脚本
```

## 配置文件说明

### 1. Nginx配置 (`nginx_config.conf`)
- 监听80和443端口
- 自动HTTP重定向到HTTPS
- API代理到后端Flask应用
- 静态文件缓存和压缩

### 2. Gunicorn配置 (`gunicorn_config.py`)
- 绑定127.0.0.1:5000
- 多进程worker配置
- 日志配置

### 3. 系统服务配置 (`systemd_service.service`)
- systemd服务配置
- 自动启动和重启
- 用户权限设置

## 常用管理命令

### 服务管理
```bash
# 查看服务状态
systemctl status lsalumni

# 启动服务
systemctl start lsalumni

# 停止服务
systemctl stop lsalumni

# 重启服务
systemctl restart lsalumni

# 查看服务日志
journalctl -u lsalumni -f
```

### Nginx管理
```bash
# 测试Nginx配置
nginx -t

# 重新加载Nginx配置
systemctl reload nginx

# 查看Nginx日志
tail -f /var/log/nginx/lsalumni_*.log
```

### 数据库管理
```bash
# 登录MySQL
mysql -u root -p

# 备份数据库
mysqldump -u root -p lsalumni > backup.sql

# 恢复数据库
mysql -u root -p lsalumni < backup.sql
```

## 安全配置

### 1. 防火墙设置
```bash
# 查看防火墙状态
ufw status

# 允许特定端口
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS
```

### 2. SSL证书自动续期
```bash
# 查看证书到期时间
certbot certificates

# 手动续期测试
certbot renew --dry-run
```

## 默认账户信息

### 管理员账户
- **用户名**: admin
- **密码**: admin123
- **邮箱**: admin@pofeclife.top

### 访问地址
- **主应用**: https://www.pofeclife.top/lsalumni
- **管理后台**: https://www.pofeclife.top/lsalumni/admin
- **保安门户**: https://www.pofeclife.top/lsalumni/security-portal

## 监控和日志

### 应用日志
```bash
# 应用日志
tail -f /var/log/lsalumni/access.log
tail -f /var/log/lsalumni/error.log

# 系统日志
tail -f /var/log/syslog
```

### 性能监控
```bash
# 查看系统资源
htop
df -h
free -h

# 查看网络连接
netstat -tulpn | grep :5000
```

## 故障排除

### 1. 服务无法启动
```bash
# 检查服务状态
systemctl status lsalumni

# 查看详细错误日志
journalctl -u lsalumni --no-pager -l

# 检查端口占用
netstat -tulpn | grep :5000
```

### 2. Nginx配置错误
```bash
# 测试Nginx配置
nginx -t

# 查看Nginx错误日志
tail -f /var/log/nginx/error.log
```

### 3. 数据库连接错误
```bash
# 检查MySQL服务状态
systemctl status mysql

# 测试数据库连接
mysql -u root -p lsalumni
```

## 更新部署

### 更新应用代码
```bash
cd /var/www/lsalumni

# 停止服务
systemctl stop lsalumni

# 更新代码文件
# (上传新文件)

# 重启服务
systemctl start lsalumni

# 检查服务状态
systemctl status lsalumni
```

### 更新依赖
```bash
cd /var/www/lsalumni
source venv/bin/activate
pip install -r requirements_prod.txt --upgrade
systemctl restart lsalumni
```

## 备份策略

### 数据库备份
```bash
# 创建备份脚本
cat > /var/www/lsalumni/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u root -p'Sy6787687.' lsalumni > /var/backups/lsalumni_$DATE.sql
find /var/backups/ -name "lsalumni_*.sql" -mtime +7 -delete
EOF

chmod +x /var/www/lsalumni/backup.sh

# 设置定时备份
echo "0 2 * * * /var/www/lsalumni/backup.sh" | crontab -
```

### 文件备份
```bash
# 备份上传文件
tar -czf /var/backups/uploads_$(date +%Y%m%d).tar.gz /var/www/lsalumni/uploads/

# 备份配置文件
tar -czf /var/backups/config_$(date +%Y%m%d).tar.gz \
    /var/www/lsalumni/.env \
    /etc/nginx/sites-available/lsalumni \
    /etc/systemd/system/lsalumni.service
```

---

## 联系支持

如有问题，请检查：
1. 服务状态和日志
2. Nginx配置和日志
3. 数据库连接
4. SSL证书状态

部署完成后，访问 https://www.pofeclife.top/lsalumni 测试系统功能。