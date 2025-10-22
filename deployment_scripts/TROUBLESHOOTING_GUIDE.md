# 校友入校登记系统 - 故障排除指南

## 📋 目录
- [快速诊断](#快速诊断)
- [常见问题](#常见问题)
- [服务故障](#服务故障)
- [网络问题](#网络问题)
- [数据库问题](#数据库问题)
- [SSL证书问题](#ssl证书问题)
- [性能问题](#性能问题)
- [安全事件](#安全事件)
- [紧急恢复](#紧急恢复)

---

## 🔍 快速诊断

### 一键健康检查
```bash
# 使用管理脚本进行健康检查
sudo bash /var/www/lsalumni/deployment_scripts/manage_system.sh health

# 或手动检查
curl -s http://127.0.0.1:5000/health && echo "应用正常"
```

### 检查系统状态
```bash
# 检查所有服务状态
sudo systemctl status lsalumni nginx mysql

# 检查端口监听
sudo netstat -tlnp | grep -E ':(80|443|5000|3306)'

# 检查磁盘空间
df -h

# 检查内存使用
free -h

# 检查系统负载
uptime
```

### 查看关键日志
```bash
# 应用日志
sudo journalctl -u lsalumni -f

# Nginx访问日志
sudo tail -f /var/log/nginx/lsalumni_access.log

# Nginx错误日志
sudo tail -f /var/log/nginx/lsalumni_error.log

# MySQL错误日志
sudo tail -f /var/log/mysql/error.log
```

---

## ❓ 常见问题

### 1. 网站无法访问

**症状**: 浏览器显示"无法访问此网站"

**排查步骤**:
```bash
# 1. 检查Nginx服务状态
sudo systemctl status nginx

# 2. 检查端口监听
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# 3. 检查防火墙
sudo ufw status
sudo ufw allow 80,443/tcp

# 4. 检查域名解析
nslookup your-domain.com
ping your-domain.com

# 5. 检查Nginx配置
sudo nginx -t

# 6. 重启Nginx
sudo systemctl restart nginx
```

**可能原因及解决方案**:

| 原因 | 解决方案 |
|------|----------|
| Nginx服务未启动 | `sudo systemctl start nginx` |
| 防火墙阻止端口 | `sudo ufw allow 80,443/tcp` |
| 域名未解析 | 检查DNS设置，确保域名指向服务器IP |
| Nginx配置错误 | `sudo nginx -t` 检查配置，修复错误后重启 |

### 2. 500内部服务器错误

**症状**: 网站显示"500 Internal Server Error"

**排查步骤**:
```bash
# 1. 查看Nginx错误日志
sudo tail -f /var/log/nginx/lsalumni_error.log

# 2. 查看应用日志
sudo journalctl -u lsalumni -f

# 3. 检查Flask应用服务
sudo systemctl status lsalumni

# 4. 测试应用直接访问
curl -I http://127.0.0.1:5000/

# 5. 检查环境变量
sudo cat /var/www/lsalumni/.env
```

**可能原因及解决方案**:

| 原因 | 解决方案 |
|------|----------|
| Flask应用未运行 | `sudo systemctl start lsalumni` |
| 数据库连接失败 | 检查数据库配置和连接 |
| Python依赖缺失 | 重新安装依赖: `pip install -r requirements_prod.txt` |
| 权限问题 | `sudo chown -R lsalumni:lsalumni /var/www/lsalumni` |
| 环境变量配置错误 | 检查`.env`文件配置 |

### 3. 数据库连接失败

**症状**: 应用日志显示数据库连接错误

**排查步骤**:
```bash
# 1. 检查MySQL服务状态
sudo systemctl status mysql

# 2. 检查MySQL端口
sudo netstat -tlnp | grep :3306

# 3. 测试数据库连接
mysql -u lsalumni -p lsalumni

# 4. 检查数据库配置
sudo cat /var/www/lsalumni/config/database.conf

# 5. 检查MySQL用户权限
mysql -u root -p -e "SELECT User, Host FROM mysql.user WHERE User='lsalumni';"
```

**解决方案**:
```bash
# 重置MySQL用户密码
mysql -u root -p << EOF
ALTER USER 'lsalumni'@'localhost' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
EOF

# 重新创建数据库用户
mysql -u root -p << EOF
DROP USER IF EXISTS 'lsalumni'@'localhost';
CREATE USER 'lsalumni'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON lsalumni.* TO 'lsalumni'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### 4. 静态文件404错误

**症状**: CSS、JS、图片文件无法加载

**排查步骤**:
```bash
# 1. 检查文件是否存在
ls -la /var/www/lsalumni/frontend/static/

# 2. 检查文件权限
sudo ls -la /var/www/lsalumni/frontend/static/

# 3. 检查Nginx配置中的root路径
grep -n "root" /etc/nginx/sites-available/lsalumni

# 4. 测试静态文件访问
curl -I http://your-domain.com/static/css/style.css
```

**解决方案**:
```bash
# 修复文件权限
sudo chown -R www-data:www-data /var/www/lsalumni/frontend/
sudo chmod -R 755 /var/www/lsalumni/frontend/

# 修复Nginx配置中的路径
sudo vim /etc/nginx/sites-available/lsalumni
# 确保 root /var/www/lsalumni/frontend; 正确

# 重启Nginx
sudo systemctl restart nginx
```

---

## 🔧 服务故障

### Flask应用服务故障

**症状**: lsalumni服务无法启动或频繁重启

**诊断命令**:
```bash
# 查看服务状态和日志
sudo systemctl status lsalumni
sudo journalctl -u lsalumni -n 50

# 检查配置文件
sudo cat /etc/systemd/system/lsalumni.service

# 手动启动应用进行调试
cd /var/www/lsalumni
source venv/bin/activate
python app.py
```

**常见问题**:

1. **虚拟环境问题**
```bash
# 重新创建虚拟环境
cd /var/www/lsalumni
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements_prod.txt
```

2. **端口占用**
```bash
# 查找占用5000端口的进程
sudo lsof -i :5000
sudo kill -9 <PID>
```

3. **权限问题**
```bash
# 修复权限
sudo chown -R lsalumni:lsalumni /var/www/lsalumni
sudo chmod +x /var/www/lsalumni/venv/bin/gunicorn
```

### Nginx服务故障

**症状**: Nginx无法启动或配置测试失败

**诊断命令**:
```bash
# 测试Nginx配置
sudo nginx -t

# 查看详细错误信息
sudo journalctl -u nginx -n 50

# 检查配置文件语法
sudo nginx -t -c /etc/nginx/nginx.conf
```

**常见配置错误修复**:

1. **配置文件语法错误**
```bash
# 备份当前配置
sudo cp /etc/nginx/sites-available/lsalumni /etc/nginx/sites-available/lsalumni.backup

# 重新生成配置
sudo bash /var/www/lsalumni/deployment_scripts/configure_nginx.sh --domain your-domain.com
```

2. **SSL证书问题**
```bash
# 检查证书文件
sudo ls -la /etc/ssl/certs/lsalumni.crt
sudo ls -la /etc/ssl/private/lsalumni.key

# 重新申请证书
sudo certbot --nginx -d your-domain.com --force-renewal
```

### MySQL服务故障

**症状**: 数据库服务无法启动

**诊断命令**:
```bash
# 查看MySQL状态
sudo systemctl status mysql

# 查看错误日志
sudo tail -f /var/log/mysql/error.log

# 检查磁盘空间
df -h /var/lib/mysql
```

**解决方案**:

1. **磁盘空间不足**
```bash
# 清理日志文件
sudo find /var/log -name "*.log" -mtime +30 -delete
# 清理MySQL二进制日志
mysql -u root -p -e "PURGE BINARY LOGS BEFORE DATE(NOW() - INTERVAL 7 DAY);"
```

2. **权限问题**
```bash
# 修复MySQL数据目录权限
sudo chown -R mysql:mysql /var/lib/mysql
sudo chmod 755 /var/lib/mysql
```

---

## 🌐 网络问题

### SSL证书问题

**症状**: 浏览器显示SSL证书警告

**诊断步骤**:
```bash
# 检查证书状态
sudo certbot certificates

# 检查证书有效期
sudo openssl x509 -in /etc/ssl/certs/lsalumni.crt -text -noout | grep "Not After"

# 测试证书配置
sudo openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

**解决方案**:

1. **证书过期**
```bash
# 手动续期
sudo certbot renew

# 强制续期
sudo certbot renew --force-renewal
```

2. **证书配置错误**
```bash
# 重新配置SSL
sudo bash /var/www/lsalumni/deployment_scripts/configure_nginx.sh --domain your-domain.com
```

### 跨域问题

**症状**: 前端无法调用API，出现CORS错误

**解决方案**:
```bash
# 检查Nginx配置中的CORS设置
grep -A 5 "Access-Control" /etc/nginx/sites-available/lsalumni

# 检查Flask应用的CORS配置
cd /var/www/lsalumni
grep -r "CORS" backend/
```

---

## 💾 数据库问题

### 数据库损坏

**症状**: 应用无法访问数据库，表损坏

**诊断命令**:
```bash
# 检查表状态
mysql -u root -p lsalumni -e "SHOW TABLE STATUS;"

# 检查表错误
mysql -u root -p lsalumni -e "CHECK TABLE user;"
```

**解决方案**:
```bash
# 修复表
mysql -u root -p lsalumni -e "REPAIR TABLE user;"

# 优化表
mysql -u root -p lsalumni -e "OPTIMIZE TABLE user;"

# 完整数据库修复
mysqlcheck -u root -p --repair lsalumni
```

### 数据丢失

**紧急恢复步骤**:
```bash
# 1. 停止应用服务
sudo systemctl stop lsalumni

# 2. 从最新备份恢复
cd /var/www/lsalumni/backups
LATEST_BACKUP=$(ls -t *.sql.gz | head -1)
gunzip -c "$LATEST_BACKUP" | mysql -u root -p lsalumni

# 3. 重新初始化应用数据
cd /var/www/lsalumni
source venv/bin/activate
python scripts/init_database.py

# 4. 重启服务
sudo systemctl start lsalumni
```

---

## ⚡ 性能问题

### 响应缓慢

**诊断工具**:
```bash
# 检查系统资源使用
htop
iotop
free -h

# 检查数据库性能
mysql -u root -p -e "SHOW PROCESSLIST;"
mysql -u root -p -e "SHOW FULL PROCESSLIST;"

# 检查应用性能
curl -w "@curl-format.txt" -o /dev/null -s http://your-domain.com/
```

**创建curl格式文件**:
```bash
cat > curl-format.txt << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF
```

### 内存不足

**解决方案**:
```bash
# 1. 检查内存使用
free -h
ps aux --sort=-%mem | head -10

# 2. 优化应用配置
# 减少Gunicorn工作进程数量
sudo vim /etc/systemd/system/lsalumni.service
# 修改 --workers 4 为 --workers 2

# 3. 启用交换文件
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 高并发问题

**优化配置**:
```bash
# 1. 优化Nginx配置
sudo vim /etc/nginx/nginx.conf
# 增加 worker_connections
worker_connections 2048;

# 2. 优化数据库配置
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf
# 增加连接数
max_connections = 200

# 3. 启用缓存
# 在Flask应用中配置Redis缓存
```

---

## 🚨 安全事件

### 疑似入侵

**应急响应**:
```bash
# 1. 检查登录日志
sudo last -n 50
sudo journalctl -u sshd -n 100

# 2. 检查可疑进程
ps auxf
sudo netstat -tlnp

# 3. 检查文件完整性
find /var/www/lsalumni -type f -mtime -1 -ls

# 4. 查看Web访问日志
sudo tail -1000 /var/log/nginx/lsalumni_access.log | grep -v "200\|301\|304"

# 5. 立即更改所有密码
sudo passwd root
sudo passwd lsalumni
mysql -u root -p -e "ALTER USER 'lsalumni'@'localhost' IDENTIFIED BY 'new_strong_password';"
```

### DDoS攻击

**缓解措施**:
```bash
# 1. 限制连接数
sudo vim /etc/nginx/nginx.conf
# 添加限制配置
limit_conn_zone $binary_remote_addr zone=addr:10m;
limit_conn addr 10;

# 2. 限制请求频率
sudo vim /etc/nginx/sites-available/lsalumni
# 添加到location块
limit_req zone=api burst=20 nodelay;

# 3. 使用fail2ban封禁IP
sudo fail2ban-client status nginx-req-limit
sudo fail2ban-client set nginx-req-limit bantime 3600
```

---

## 🆘 紧急恢复

### 完整系统恢复

**步骤1: 停止所有服务**
```bash
sudo systemctl stop lsalumni nginx mysql
```

**步骤2: 恢复数据库**
```bash
cd /var/www/lsalumni/backups
BACKUP_FILE="lsalumni_backup_$(date +%Y%m%d).sql.gz"
if [[ -f "$BACKUP_FILE" ]]; then
    gunzip -c "$BACKUP_FILE" | mysql -u root -p lsalumni
    echo "数据库恢复完成"
else
    echo "备份文件不存在: $BACKUP_FILE"
    exit 1
fi
```

**步骤3: 恢复配置文件**
```bash
# 从备份恢复Nginx配置
sudo cp /etc/nginx/backup/*/lsalumni /etc/nginx/sites-available/

# 恢复应用配置
sudo cp /var/www/lsalumni/backup/.env /var/www/lsalumni/
```

**步骤4: 检查文件系统**
```bash
# 检查并修复权限
sudo chown -R lsalumni:lsalumni /var/www/lsalumni
sudo chmod 755 /var/www/lsalumni
sudo chmod -R 644 /var/www/lsalumni/frontend/static/
sudo chmod +x /var/www/lsalumni/venv/bin/*
```

**步骤5: 重启服务**
```bash
sudo systemctl start mysql
sleep 5
sudo systemctl start lsalumni
sleep 5
sudo systemctl start nginx
```

**步骤6: 验证恢复**
```bash
# 运行健康检查
sudo bash /var/www/lsalumni/deployment_scripts/manage_system.sh health

# 测试网站访问
curl -I http://127.0.0.1/
```

### 快速故障转移

**临时解决方案**:
```bash
# 1. 启用维护模式
sudo bash -c 'echo "maintenance_mode = true" >> /var/www/lsalumni/config/database.conf'

# 2. 显示维护页面
sudo cp /var/www/lsalumni/maintenance.html /var/www/lsalumni/frontend/index.html

# 3. 重启Nginx
sudo systemctl restart nginx
```

---

## 📞 联系支持

### 收集诊断信息
```bash
# 生成诊断报告
sudo bash -c '
cat > /tmp/system_diagnostic.txt << EOF
=== 系统诊断报告 ===
生成时间: $(date)
系统信息: $(uname -a)
磁盘使用: $(df -h)
内存使用: $(free -h)
服务状态:
$(systemctl status lsalumni nginx mysql --no-pager)
网络连接: $(netstat -tlnp | grep -E ":(80|443|5000|3306)")
最近错误:
$(journalctl -u lsalumni --since "1 hour ago" --no-pager | tail -20)
EOF
echo "诊断报告已生成: /tmp/system_diagnostic.txt"
'
```

### 紧急联系方式

| 问题类型 | 联系方式 | 响应时间 |
|----------|----------|----------|
| 系统完全宕机 | 电话/短信 | 30分钟内 |
| 安全事件 | 电话/邮件 | 15分钟内 |
| 性能问题 | 邮件/工单 | 2小时内 |
| 一般问题 | 邮件/工单 | 24小时内 |

---

## 🔍 监控和预防

### 设置监控脚本
```bash
# 创建系统监控脚本
cat > /var/www/lsalumni/scripts/monitor.sh << 'EOF'
#!/bin/bash

# 检查服务状态
services=("lsalumni" "nginx" "mysql")
for service in "${services[@]}"; do
    if ! systemctl is-active --quiet "$service"; then
        echo "[$service] 服务异常，尝试重启..."
        systemctl restart "$service"
        echo "[$service] 服务已重启"
    fi
done

# 检查磁盘空间
disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
if [ "$disk_usage" -gt 90 ]; then
    echo "磁盘空间不足: ${disk_usage}%"
    # 清理日志文件
    find /var/log -name "*.log.*" -mtime +7 -delete
fi

# 检查内存使用
mem_usage=$(free | grep Mem | awk '{printf("%.0f"), $3/$2 * 100.0}')
if [ "$mem_usage" -gt 90 ]; then
    echo "内存使用过高: ${mem_usage}%"
fi
EOF

chmod +x /var/www/lsalumni/scripts/monitor.sh

# 添加到定时任务（每5分钟检查一次）
echo "*/5 * * * * /var/www/lsalumni/scripts/monitor.sh" | sudo crontab -
```

---

*最后更新: 2025-10-20*
*版本: v1.0.0*
*维护者: 系统管理员*