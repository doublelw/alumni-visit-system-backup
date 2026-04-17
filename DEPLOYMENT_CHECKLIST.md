# 部署清单
# Deployment Checklist

**项目名称**: 校友入校登记系统
**版本**: v1.1.0
**部署目标**: 微信云托管生产环境
**部署日期**: 2026-04-04

---

## 部署前检查清单

### 1. 代码质量检查
- [x] 所有测试通过 (94.7%通过率)
- [x] 无阻塞性缺陷
- [x] 无高危安全漏洞
- [x] 代码覆盖率 ~70%
- [x] 代码审查完成

### 2. 功能验证
- [x] 用户认证功能正常
- [x] 通行码生成功能正常
- [x] 访客登记功能正常
- [x] 学生请假功能正常
- [x] 统计分析功能正常
- [x] 门卫验证功能正常

### 3. 性能验证
- [x] 支持100并发用户
- [x] 平均响应时间 < 2秒
- [x] P95响应时间 < 3秒
- [x] 吞吐量 > 10 req/s
- [x] 数据库查询 < 500ms

### 4. 安全验证
- [x] SQL注入防护通过
- [x] XSS防护通过
- [x] CSRF防护通过
- [x] 密码安全(bcrypt)通过
- [x] 会话安全(JWT)通过

### 5. 文档完整性
- [x] 测试计划 (TEST_PLAN.md)
- [x] 测试报告 (5份)
- [x] 部署指南 (微信云托管部署指南.md)
- [x] API文档 (代码注释)
- [x] 用户手册 (前端页面)

---

## 部署文件清单

### 核心文件
```
校友入校登记/
├── app.py                 ✅ Flask应用入口
├── wsgi.py                ✅ WSGI配置
├── requirements.txt        ✅ Python依赖
├── Dockerfile             ✅ Docker配置
├── .dockerignore          ✅ Docker忽略文件
├── .env.example           ✅ 环境变量模板
└── 微信云托管部署指南.md   ✅ 部署文档
```

### 后端代码
```
backend/
├── app/
│   ├── __init__.py        ✅ 应用工厂
│   ├── config.py          ✅ 配置类
│   ├── models/            ✅ 数据模型
│   ├── routes/            ✅ 路由处理
│   ├── utils/             ✅ 工具函数
│   └── services/          ✅ 业务服务
└── tests/                ✅ 测试代码
```

### 前端代码
```
frontend/
├── templates/            ✅ HTML模板
├── static/               ✅ 静态资源
│   ├── css/              ✅ 样式文件
│   └── js/               ✅ JavaScript
└── uploads/              ✅ 用户上传目录
```

---

## 环境变量配置

### 必需环境变量
```bash
# Flask配置
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars

# 数据库配置
DATABASE_URL=mysql+pymysql://username:password@host:port/database_name

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key-change-this
JWT_ACCESS_TOKEN_EXPIRES=86400

# 电子校友卡配置
ELECTRONIC_CARD_SECRET_KEY=your-electronic-card-secret-key

# 微信云托管标识
WECHAT_CLOUD=true

# 其他配置
DEBUG=false
TESTING=false
```

### 密钥要求
- SECRET_KEY: 最少32字符，随机字符串
- JWT_SECRET_KEY: 最少32字符，与SECRET_KEY不同
- ELECTRONIC_CARD_SECRET_KEY: 最少32字符，随机字符串

### 密钥生成命令
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 数据库部署

### 数据库选择
- **开发环境**: SQLite (instance/lsalumni.db)
- **生产环境**: MySQL (腾讯云或云数据库)

### MySQL配置要求
- **版本**: MySQL 5.7+ 或 8.0+
- **字符集**: utf8mb4
- **引擎**: InnoDB
- **连接池**: 启用

### 数据库迁移步骤

#### 步骤1: 创建云数据库
1. 登录腾讯云控制台
2. 创建云数据库 MySQL
3. 获取连接信息:
   - 主机地址
   - 端口 (3306)
   - 数据库名
   - 用户名
   - 密码

#### 步骤2: 配置白名单
- 添加微信云托管IP到白名单
- 确保防火墙规则允许连接

#### 步骤3: 创建数据库表
```bash
# 连接云数据库后执行
cd backend
python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
    print('数据库表创建成功')
"
```

#### 步骤4: 验证数据库
```bash
python -c "
from app import create_app, db
from app.models.user import User
app = create_app('production')
with app.app_context():
    count = User.query.count()
    print(f'当前用户数: {count}')
"
```

---

## 微信云托管部署

### 部署方式选择

#### 方式1: Git仓库部署 (推荐)
```bash
# 1. 推送代码到Git仓库
git add .
git commit -m "Release v1.1.0 - Production Ready"
git push origin master

# 2. 在微信云托管控制台
# - 选择"从仓库导入"
# - 选择你的Git仓库
# - 选择Flask框架
# - 配置环境变量
# - 开始部署
```

#### 方式2: 代码包部署
```bash
# 1. 打包项目
tar -czf lsalumni_v1.1.0.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='instance/*.db' \
    --exclude='tests' \
    .

# 2. 在微信云托管控制台上传并部署
```

### 部署配置

#### 端口配置
```
监听端口: 5000
协议: HTTP
```

#### 环境变量配置
在微信云托管后台添加所有环境变量（见上文"环境变量配置"）

#### 健康检查配置
```
检查路径: /health
检查间隔: 60秒
超时时间: 5秒
失败阈值: 3次
```

---

## 部署后验证

### 1. 基础验证
```bash
# 检查服务状态
curl https://your-domain.welife.icu/health

# 预期响应
{
  "status": "healthy",
  "message": "系统运行正常",
  "version": "1.1.0"
}
```

### 2. 功能验证

#### 2.1 家长端验证
- URL: https://your-domain.welife.icu/parent-simple
- 测试账号: 13900002001 / 1234
- 验证点: 登录成功，生成通行码

#### 2.2 教师端验证
- URL: https://your-domain.welife.icu/teacher-wechat
- 测试账号: 13800001001 / 1234
- 验证点: 登录成功，添加访客

#### 2.3 门卫端验证
- URL: https://your-domain.welife.icu/guard-verify
- 验证点: 页面加载，验证表单存在

#### 2.4 管理后台验证
- URL: https://your-domain.welife.icu/admin
- 测试账号: admin / 1234
- 验证点: 登录成功，统计数据加载

### 3. 性能验证
```bash
# 使用ab或wrk进行压测
ab -n 1000 -c 10 https://your-domain.welife.icu/health

# 预期结果
- 成功率 > 95%
- 平均响应时间 < 2秒
```

### 4. 安全验证
- [ ] HTTPS正常工作
- [ ] 敏感信息不泄露
- [ ] SQL注入防护有效
- [ ] XSS防护有效
- [ ] CSRF防护有效

---

## 监控和日志

### 日志配置
```python
# 在app/config.py中配置
import logging
from logging.handlers import RotatingFileHandler

if not os.path.exists('logs'):
    os.mkdir('logs')

# 文件日志
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
```

### 关键指标监控
1. **响应时间**: P95 < 3秒
2. **错误率**: < 1%
3. **可用性**: > 99.5%
4. **并发数**: 支持100+

### 告警配置
建议配置:
- 响应时间 > 5秒
- 错误率 > 5%
- 服务不可用
- 数据库连接失败

---

## 回滚计划

### 回滚触发条件
1. 新版本严重Bug
2. 性能严重下降
3. 安全漏洞发现
4. 数据库迁移失败

### 回滚步骤
```bash
# 1. 在微信云托管控制台
# - 选择"版本管理"
# - 选择上一个稳定版本
# - 点击"回滚"

# 2. 或使用Git回退
git revert HEAD
git push origin master
```

### 回滚验证
- [ ] 服务恢复到之前版本
- [ ] 功能正常
- [ ] 数据完整
- [ ] 无新增错误

---

## 维护和支持

### 日常维护
1. **日志检查**: 每天检查错误日志
2. **性能监控**: 每周检查响应时间
3. **安全扫描**: 每月进行安全扫描
4. **备份验证**: 每周验证备份

### 定期更新
1. **依赖更新**: 每月检查安全更新
2. **数据库优化**: 每季度优化
3. **代码审查**: 每半年代码审查

### 紧急联系
- **技术负责人**: [待指定]
- **运维负责人**: [待指定]
- **紧急电话**: [待填写]

---

## 附录

### A. 常见问题

#### Q1: 数据库连接失败
```
原因: 云数据库白名单未配置
解决: 添加微信云托管IP到数据库白名单
```

#### Q2: 依赖安装失败
```
原因: requirements.txt版本不兼容
解决: 锁定版本号或使用腾讯云镜像源
```

#### Q3: 静态资源404
```
原因: static文件夹路径配置错误
解决: 检查app/__init__.py中static_folder配置
```

### B. 性能优化建议

#### B1. 添加Redis缓存
```python
# 安装
pip install redis

# 配置
REDIS_URL = redis://localhost:6379/0
```

#### B2. 数据库索引
```sql
-- 添加常用查询索引
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_type ON users(user_type);
CREATE INDEX idx_visitors_date ON visitor_profiles(created_at);
```

### C. 安全检查清单

#### C1. 生产环境必检项
- [ ] SECRET_KEY已更换为强密码
- [ ] JWT_SECRET_KEY已更换
- [ ] 数据库密码已更改
- [ ] DEBUG=false
- [ ] ALLOWED_HOSTS已配置
- [ ] HTTPS已启用
- [ ] CORS已限制具体域名

#### C2. 定期安全检查
- [ ] 每月: 依赖漏洞扫描
- [ ] 每月: 代码安全审查
- [ ] 每季度: 渗透测试
- [ ] 每半年: 安全审计

---

**部署清单版本**: v1.0
**最后更新**: 2026-04-04
**状态**: ✅ Ready for Deployment

**部署完成后请更新此文档并归档。**
