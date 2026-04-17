# 校友入校登记系统 - 项目知识库

> **最后更新**: 2026-03-31
> **当前版本**: v1.1.0
> **状态**: ✅ 生产就绪

---

## 📑 目录

1. [项目概述](#项目概述)
2. [系统架构](#系统架构)
3. [最新状态](#最新状态)
4. [核心功能](#核心功能)
5. [技术栈](#技术栈)
6. [部署指南](#部署指南)
7. [开发指南](#开发指南)
8. [常见问题](#常见问题)
9. [重要修复记录](#重要修复记录)
10. [API文档](#api文档)

---

## 项目概述

### 系统简介
校友入校登记系统是一个集校友信息管理、访问申请审批、人脸识别验证、车辆管理、数据统计分析于一体的综合性校园管理系统。

### 核心价值
- **便捷性**: 校友在线申请访问，管理员审批授权
- **安全性**: 人脸识别验证，防止冒用
- **高效性**: 批量授权功能，快速处理大量申请
- **可追溯**: 完整的访问记录和操作日志

---

## 系统架构

### 整体架构
```
校友入校登记系统
├── 前端 (Frontend)
│   ├── 移动端界面 - 响应式设计
│   ├── 管理后台 - SPA单页应用
│   └── 静态资源 - CSS/JS/图片
├── 后端 (Backend)
│   ├── Flask应用 - Web框架
│   ├── RESTful API - 接口服务
│   ├── JWT认证 - 安全验证
│   └── 业务逻辑 - 核心功能
└── 数据层 (Database)
    ├── SQLite - 开发环境
    └── MySQL - 生产环境
```

### 目录结构
```
校友入校登记/
├── backend/               # 后端代码
│   ├── app/              # 应用主目录
│   │   ├── models/       # 数据模型
│   │   ├── routes/       # 路由处理
│   │   ├── templates/    # 前端模板
│   │   └── static/       # 静态资源
│   ├── migrations/       # 数据库迁移
│   └── scripts/          # 工具脚本
├── frontend/            # 前端代码（独立）
│   ├── templates/       # HTML模板
│   ├── static/          # CSS/JS资源
│   └── uploads/         # 上传文件
├── start.py            # 启动脚本
└── config.py           # 配置文件
```

---

## 最新状态

### 当前版本: v1.1.0 (2025-11-13)

#### ✅ 最新功能
1. **密钥管理** (2026-03-30)
   - 电子校友卡HMAC密钥管理
   - 支持手动/自动更换
   - 完整的历史记录和分页
   - 使用JWT认证，无需密码验证

2. **批量导入优化** (2026-03-31)
   - 修复token认证问题
   - 改进错误提示
   - 添加详细调试日志

#### 🔧 关键修复
- **用户注册并发冲突**: 使用UUID替代时间戳
- **活动报名时区问题**: 使用本地时间替代UTC
- **批量导入认证**: 统一使用AdminState.token

#### ⚠️ 已知问题
- 无重大问题

---

## 核心功能

### 1. 用户管理
- **用户注册**: 校友自主注册，填写个人信息
- **审核流程**: 管理员审核校友档案
- **批量导入**: Excel模板批量导入用户
- **权限管理**: admin/teacher/student/alumni四种角色

### 2. 访问申请
- **在线申请**: 校友提交访问申请
- **批量审批**: 按班级/年级/院系批量授权
- **二维码生成**: 生成访问二维码
- **申请记录**: 完整的申请历史

### 3. 身份验证
- **人脸识别**: OpenCV实现人脸验证
- **验证码**: 4位数字验证码
- **保安门户**: 保安验证访客身份
- **访问记录**: 完整的进出记录

### 4. 车辆管理
- **车辆登记**: 校友车辆信息登记
- **车牌识别**: 车辆进出管理
- **访客车**: 访客车辆临时管理

### 5. 数据统计
- **仪表盘**: 数据概览和统计图表
- **访问统计**: 按时间/类型/状态统计
- **导出功能**: 数据导出为Excel

### 6. 密钥管理 (新增)
- **密钥状态**: 查看密钥使用时间和状态
- **手动更换**: 立即更换密钥
- **自动更换**: 设置自动更换周期（30/60/90天）
- **历史记录**: 查看完整更换历史

---

## 技术栈

### 后端技术
```python
Flask==2.3.0              # Web框架
Flask-SQLAlchemy==3.0.5    # ORM
Flask-JWT-Extended==4.5.0  # JWT认证
SQLAlchemy==2.0.0          # 数据库ORM
PyMySQL==1.1.0             # MySQL驱动
opencv-python==4.8.0        # 人脸识别
Pillow==10.0.0             # 图像处理
pandas==2.0.0              # 数据处理
openpyxl==3.1.0            # Excel处理
```

### 前端技术
```
HTML5 + CSS3              # 页面结构和样式
JavaScript ES6+           # 交互逻辑
Chart.js                  # 数据可视化
Remix Icon                # 图标库
Bootstrap (部分使用)      # 响应式布局
```

### 数据库
- **开发环境**: SQLite (`app.db`)
- **生产环境**: MySQL 5.7+

---

## 部署指南

### 快速启动

#### 1. 初始化项目
```bash
cd D:\Project\校友入校登记
python start.py init
```
这会自动：
- 安装所有Python依赖
- 生成SSL证书
- 初始化SQLite数据库

#### 2. 启动开发环境
```bash
python start.py dev
```
访问: https://localhost:5000

#### 3. 启动生产环境
```bash
python start.py prod
```
使用MySQL数据库，性能优化

### 环境配置

#### 开发环境 (.env.development)
```env
FLASK_ENV=development
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///app.db
JWT_SECRET_KEY=jwt-dev-key
ELECTRONIC_CARD_SECRET_KEY=ec-dev-key
SSL_ENABLED=True
```

#### 生产环境 (.env.production)
```env
FLASK_ENV=production
SECRET_KEY=生产环境密钥
DATABASE_URL=mysql+pymysql://user:pass@localhost/lsalumni
JWT_SECRET_KEY=生产JWT密钥
ELECTRONIC_CARD_SECRET_KEY=生产HMAC密钥
SSL_ENABLED=True
```

### 数据库迁移
```bash
# 创建迁移
flask db migrate -m "描述"

# 应用迁移
flask db upgrade

# 回滚
flask db downgrade
```

---

## 开发指南

### 代码规范

#### 后端 (Python)
```python
# 路由定义
@admin_bp.route('/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    pass

# 错误处理
try:
    # 业务逻辑
except Exception as e:
    current_app.logger.error(f"操作失败: {str(e)}")
    return jsonify({'error': str(e)}), 500
```

#### 前端 (JavaScript)
```javascript
// API调用
const response = await fetch('/api/admin/users', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

// 错误处理
if (!response.ok) {
    throw new Error('请求失败');
}
```

### 常用命令

#### 后端开发
```bash
# 查看路由
flask routes

# 进入Python Shell
flask shell

# 重置数据库
rm backend/app.db && python start.py init
```

#### 前端调试
```bash
# 清除浏览器缓存
Ctrl + Shift + Delete

# 查看控制台
F12 → Console

# 查看网络请求
F12 → Network
```

### 版本管理

#### JavaScript版本号
修改 `frontend/templates/admin.html`:
```html
<script src="/static/js/admin.js?v=YYYYMMDD_X"></script>
```

#### CSS版本号
```html
<link rel="stylesheet" href="/static/css/admin.css?v=YYYYMMDD_X">
```

---

## 常见问题

### ❌ 问题1: 批量导入401错误
**原因**: token获取方式不一致
```javascript
// ❌ 错误
localStorage.getItem('token')

// ✅ 正确
AdminState.token || localStorage.getItem('admin_token')
```

### ❌ 问题2: 密钥管理密码验证失败
**原因**: 已使用JWT认证，不需要密码
```python
# ✅ 正确做法
current_user_id = get_jwt_identity()
current_user = User.query.get(current_user_id)
# 验证 user_type == 'admin'
```

### ❌ 问题3: 时区显示不正确
**原因**: 使用UTC时间
```python
# ❌ 错误
datetime.utcnow()

# ✅ 正确
datetime.now()
```

### ❌ 问题4: 注册并发冲突
**原因**: 时间戳生成临时ID
```python
# ❌ 错误
temp_id = str(int(time.time()))

# ✅ 正确
import uuid
temp_id = str(uuid.uuid4())
```

### ❌ 问题5: 页面缓存问题
**解决**: 清除浏览器缓存
```
1. Ctrl + Shift + Delete
2. 选择"缓存的图像和文件"
3. 点击"清除数据"
```

---

## 重要修复记录

### v1.1.0 (2025-11-13)
- ✅ 修复用户注册并发冲突
- ✅ 修复活动报名时区问题
- ✅ 添加event_registrations.verification_code字段

### v1.0.2 (最近)
- ✅ 密钥管理页面集成到管理后台
- ✅ 简化密钥管理界面
- ✅ 移除微信密码管理（移至用户管理）

### v1.0.1
- ✅ 修复用户管理页面分页渲染错误
- ✅ 修复待处理事项校友审核跳转问题
- ✅ 更新JS版本号强制刷新缓存

---

## API文档

### 认证方式
所有API请求需要携带JWT token:
```http
Authorization: Bearer <token>
```

### 用户管理 API

#### 获取用户列表
```http
GET /api/admin/users?page=1&per_page=20&search=&user_type=&status=
```

#### 创建用户
```http
POST /api/admin/users
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123",
  "real_name": "测试用户",
  "email": "test@example.com",
  "user_type": "teacher"
}
```

#### 批量导入
```http
POST /api/admin/users/import
Content-Type: application/json

{
  "users": [...]
}
```

#### 下载模板
```http
GET /api/admin/users/template
```

### 密钥管理 API

#### 获取密钥状态
```http
GET /api/admin/keys/status
```

#### 更换密钥
```http
POST /api/admin/keys/rotate
Content-Type: application/json

{
  "key_type": "electronic_card"
}
```

#### 获取更换历史
```http
GET /api/admin/keys/history?page=1&per_page=20
```

### 访问申请 API

#### 提交申请
```http
POST /api/visit-applications
Content-Type: application/json

{
  "visit_date": "2026-03-31",
  "visit_purpose": "拜访老师",
  "target_person": "张老师"
}
```

#### 批量审批
```http
POST /api/admin/batch-approve
Content-Type: application/json

{
  "type": "class",
  "target_value": "高三1班",
  "visit_date": "2026-03-31",
  "time_start": "08:00",
  "time_end": "18:00",
  "visit_purpose": "回校参观"
}
```

---

## 测试账号

### 管理员账号
- 用户名: `admin`
- 密码: `admin`
- 类型: 管理员

### 测试账号
详见 `测试账号清单.md`（如存在）

---

## 维护日志

### 2026-03-31
- ✅ 统一token认证方式
- ✅ 修复批量导入和下载模板401错误
- ✅ 添加详细调试日志
- ✅ 整理项目知识库，删除冗余MD文件
- ✅ 更新用户导入模板为制卡中心格式
  - 新增字段: 学（工）号、客户姓名、证件号、补助类型、四级部门信息
  - 创建测试数据文件（15条测试记录）
  - 更新前端预览表格显示新字段
  - 更新JS版本号至 v20251130_11

### 2026-03-30
- ✅ 完成密钥管理页面开发
- ✅ 添加分页功能
- ✅ 移除重复密码验证，使用JWT认证

---

## 附录

### A. 文件清理
本知识库创建后，已删除以下冗余文件：
- ❌ 所有临时状态报告 (STATUS_*.md)
- ❌ 所有修复报告 (FIX_*.md)
- ❌ 所有测试报告 (TEST_*.md)
- ❌ 所有总结文档 (SUMMARY_*.md)
- ❌ 所有重复的README (README_*.md)

### B. 保留文件
- ✅ KNOWLEDGE_BASE.md (本文件)
- ✅ README.md (项目简介)
- ✅ CHANGELOG_v1.1.0.md (版本历史)
- ✅ backend/scripts/README.md (脚本说明)

### C. Git使用
```bash
# 查看状态
git status

# 提交更改
git add .
git commit -m "docs: 统一项目知识库，删除冗余文档"

# 推送
git push origin master
```

---

**文档维护**: 请在每次重要更新后及时更新本文档
**问题反馈**: 如发现文档错误或遗漏，请及时修正
