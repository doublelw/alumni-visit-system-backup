# 微信云托管快速部署指南

## 🚀 5分钟快速部署

### 前置准备

1. **微信公众平台账号**
   - 访问 https://mp.weixin.qq.com/ 注册/登录

2. **云数据库（二选一）**
   - ✅ 微信云数据库（推荐）
   - ✅ 腾讯云MySQL

### 步骤1：准备部署包

```bash
# 运行部署准备脚本
bash deployment_scripts/deploy_to_welife.sh
```

脚本会自动生成：
- `welife_deploy_package_YYYYMMDD_HHMMSS.zip` - 部署包
- `welife_deploy_README_YYYYMMDD_HHMMSS.md` - 详细说明

### 步骤2：创建云数据库

#### 方式A：微信云数据库（推荐）

1. 微信公众平台 → 开发 → 云托管
2. 点击"云数据库"
3. 创建MySQL实例
4. 记录连接信息：
   ```
   主机: xxx.mysql.rds.aliyuncs.com
   端口: 3306
   数据库: lsalumni
   用户: lsalumni
   密码: your_password
   ```

#### 方式B：腾讯云MySQL

1. 腾讯云控制台 → 云数据库 MySQL
2. 创建实例
3. 配置白名单：添加微信云托管IP段
4. 记录连接信息

### 步骤3：部署到云托管

1. **创建服务**
   - 进入：开发 → 云托管 → 新建服务
   - 服务名称：`lsalumni-api`
   - 框架：Flask（或选择"其他"）

2. **上传代码**
   - 方式1：上传部署包zip文件
   - 方式2：连接Git仓库（推荐，支持自动部署）

3. **配置环境变量**（必须）

   在"环境变量"页签添加：

   ```bash
   # ============ 必须配置 ============
   FLASK_APP=app.py
   FLASK_ENV=production

   # 数据库连接（替换为实际值）
   DATABASE_URL=mysql+pymysql://lsalumni:your_password@host:3306/lsalumni

   # 密钥（生成随机字符串）
   SECRET_KEY=use-openssl-rand-base64-32
   JWT_SECRET_KEY=use-openssl-rand-base64-32
   ELECTRONIC_CARD_SECRET_KEY=use-openssl-rand-base64-32
   HMAC_SECRET_KEY=use-openssl-rand-base64-32

   # 微信云托管标识
   WECHAT_CLOUD=true
   ```

   **生成密钥的命令**：
   ```bash
   openssl rand -base64 32
   ```

4. **启动部署**
   - 点击"部署"按钮
   - 等待2-5分钟

### 步骤4：验证部署

部署完成后，测试访问：

```
健康检查: https://your-service.welife.icu/api/health
主页: https://your-service.welife.icu/
```

期望返回：
```json
{"status": "healthy", "database": "connected"}
```

## 📝 环境变量完整清单

### 基础配置
| 变量 | 值 | 说明 |
|------|-----|------|
| FLASK_APP | app.py | 应用入口 |
| FLASK_ENV | production | 生产环境 |
| WECHAT_CLOUD | true | 云托管标识 |

### 数据库
| 变量 | 格式 | 必需 |
|------|------|------|
| DATABASE_URL | mysql+pymysql://user:pass@host:port/db | ✅ |

### 安全密钥
| 变量 | 说明 | 生成方式 |
|------|------|----------|
| SECRET_KEY | Flask密钥 | `openssl rand -base64 32` |
| JWT_SECRET_KEY | JWT令牌密钥 | `openssl rand -base64 32` |
| ELECTRONIC_CARD_SECRET_KEY | 电子校友卡密钥 | `openssl rand -base64 32` |
| HMAC_SECRET_KEY | 动态码HMAC密钥 | `openssl rand -base64 32` |

### 可选配置
| 变量 | 默认值 | 说明 |
|------|--------|------|
| CACHE_ENABLED | true | 启用Redis缓存 |
| REDIS_HOST | localhost | Redis主机 |
| REDIS_PORT | 6379 | Redis端口 |
| UPLOAD_FOLDER | /app/uploads | 上传目录 |

## 🔍 常见问题排查

### 问题1：部署失败 - 数据库连接错误

**错误信息**: `Can't connect to MySQL server`

**解决方案**:
1. 检查DATABASE_URL格式
2. 确认数据库白名单已配置
3. 测试数据库连接：
   ```bash
   mysql -h host -P 3306 -u user -p
   ```

### 问题2：服务启动超时

**错误信息**: `Health check failed`

**解决方案**:
1. 检查日志确认具体错误
2. 确认所有必需环境变量已设置
3. 检查数据库是否可访问

### 问题3：访问500错误

**错误信息**: `Internal Server Error`

**解决方案**:
1. 查看云托管日志
2. 检查环境变量SECRET_KEY是否设置
3. 验证数据库连接

## 📊 监控和维护

### 查看日志
```
云托管控制台 → 服务 → 日志
```

### 监控指标
- CPU使用率
- 内存使用率
- 请求QPS
- 响应时间
- 错误率

### 更新部署

**Git方式**（推荐）:
```bash
git add .
git commit -m "更新功能"
git push
# 自动部署
```

**手动上传**:
```bash
# 重新构建部署包
bash deployment_scripts/deploy_to_welife.sh

# 上传新zip文件到云托管控制台
```

## 🔗 相关链接

- [微信公众平台](https://mp.weixin.qq.com/)
- [微信云托管文档](https://developers.weixin.qq.com/miniprogram/dev/cloud托管/)
- [腾讯云MySQL](https://cloud.tencent.com/product/cdb)

## 💡 最佳实践

1. **使用Git仓库部署** - 支持版本管理和自动部署
2. **配置健康检查** - 自动重启失败服务
3. **设置告警** - 监控CPU、内存、错误率
4. **定期备份** - 备份数据库和上传文件
5. **使用独立环境** - 测试环境 + 生产环境

---

**需要帮助？** 查看 `welife_deploy_README_*.md` 获取详细说明
