# 校友入校登记系统 v1.1.0 部署说明

## 📋 部署前准备

### 系统要求
- Python 3.8+
- SQLite 3.x
- Nginx (可选，用于生产环境)
- 足够的磁盘空间用于日志和数据

### 备份重要数据
```bash
# 备份数据库
cp /var/www/lsalumni/backend/instance/alumni_system_prod.db /var/www/lsalumni/backup/alumni_system_prod_backup_$(date +%Y%m%d_%H%M%S).db

# 备份配置文件
cp -r /var/www/lsalumni/backend/app/config.py /var/www/lsalumni/backup/
```

## 🚀 部署步骤

### 1. 停止当前服务
```bash
# 查找并停止Flask进程
ps aux | grep "python.*run.py"
pkill -f "python.*run.py"

# 或使用systemctl（如果配置了服务）
sudo systemctl stop lsalumni
```

### 2. 部署新代码
```bash
# 进入项目目录
cd /var/www/lsalumni

# 备份当前代码
tar -czf backup_code_$(date +%Y%m%d_%H%M%S).tar.gz backend/ frontend/

# 上传并解压新版本（或直接复制）
# 上传 lsalumni_v1.1.0_release.zip 并解压
unzip lsalumni_v1.1.0_release.zip
cp -r lsalumni_v1.1.0_release/* ./
rm -rf lsalumni_v1.1.0_release/

# 确保权限正确
chown -R www-data:www-data /var/www/lsalumni
chmod -R 755 /var/www/lsalumni
```

### 3. 更新依赖（如有需要）
```bash
cd /var/www/lsalumni/backend
source ../venv/bin/activate
pip install -r requirements.txt
```

### 4. 数据库更新
如果需要执行数据库更新（本次v1.1.0需要）：
```sql
-- 添加 verification_code 字段到 event_registrations 表
ALTER TABLE event_registrations ADD COLUMN verification_code VARCHAR(6);

-- 验证字段添加成功
.schema event_registrations
```

### 5. 重启服务
```bash
cd /var/www/lsalumni
source venv/bin/activate
nohup python backend/run.py > app.log 2>&1 &

# 验证服务启动
ps aux | grep "python.*run.py"
curl http://127.0.0.1:5000/health
```

### 6. 验证功能
```bash
# 检查健康状态
curl http://127.0.0.1:5000/health

# 应该返回：
# {"status": "healthy", "message": "系统运行正常", "version": "1.1.0"}

# 测试用户注册
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test123456","confirmPassword":"Test123456","realName":"测试用户","phone":"13800138000","graduationYear":"2020","classNumber":"1班","division":"高三","major":"理科","classTeacher":"张老师","currentCity":"北京","workUnit":"测试公司","agreeTerms":true}'

# 测试活动报名
curl -X POST http://127.0.0.1:5000/api/event/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","contactPhone":"13800138000","willDine":false}'
```

## 🔧 配置说明

### 环境变量
确保以下环境变量正确设置：
```bash
export FLASK_ENV=production
export FLASK_DEBUG=False
```

### Nginx配置（如果使用）
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🚨 回滚方案

如果部署出现问题，快速回滚：

### 1. 停止服务
```bash
pkill -f "python.*run.py"
```

### 2. 恢复代码
```bash
# 恢复备份的代码
tar -xzf backup_code_YYYYMMDD_HHMMSS.tar.gz

# 或者从Git恢复
git checkout HEAD~1
```

### 3. 恢复数据库（如需要）
```bash
cp /var/www/lsalumni/backup/alumni_system_prod_backup_YYYYMMDD_HHMMSS.db /var/www/lsalumni/backend/instance/alumni_system_prod.db
```

### 4. 重启服务
```bash
cd /var/www/lsalumni
source venv/bin/activate
nohup python backend/run.py > app.log 2>&1 &
```

## 📊 监控检查

### 日志监控
```bash
# 查看应用日志
tail -f /var/www/lsalumni/app.log

# 查看Nginx日志（如果使用）
tail -f /var/log/nginx/lsalumni_access.log
tail -f /var/log/nginx/lsalumni_error.log
```

### 性能监控
```bash
# 检查内存使用
top -p $(pgrep -f "python.*run.py")

# 检查数据库大小
du -sh /var/www/lsalumni/backend/instance/

# 检查日志文件大小
du -sh /var/www/lsalumni/app.log
```

## ✅ 部署验证清单

- [ ] 服务正常启动
- [ ] 健康检查返回v1.1.0
- [ ] 用户注册功能正常
- [ ] 活动报名功能正常
- [ ] 验证码正确生成
- [ ] 时间显示正确
- [ ] 数据库连接正常
- [ ] 日志记录正常
- [ ] 前端页面加载正常
- [ ] 文件上传功能正常

## 🆘 故障排除

### 常见问题

1. **服务启动失败**
   - 检查Python环境：`python --version`
   - 检查依赖：`pip list`
   - 查看错误日志：`tail -n 50 app.log`

2. **数据库错误**
   - 检查数据库文件权限：`ls -la backend/instance/`
   - 验证数据库完整性：`sqlite3 backend/instance/alumni_system_prod.db ".schema"`

3. **时间显示不正确**
   - 确认服务器时区：`timedatectl status`
   - 检查Python时间：`python -c "from datetime import datetime; print(datetime.now())"`

4. **权限问题**
   - 检查文件所有者：`ls -la`
   - 修复权限：`chown -R www-data:www-data /var/www/lsalumni`

## 📞 技术支持

如部署过程中遇到问题，请：
1. 查看详细错误日志
2. 检查系统资源使用情况
3. 参考CHANGELOG_v1.1.0.md了解本次更新内容
4. 联系技术支持团队

---

**部署完成后，请记得清理临时文件和备份文件，保持系统整洁。**