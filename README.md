# 校友入校登记系统

## 项目简介

校友入校登记系统是一个集校友信息管理、访问申请审批、人脸识别验证、车辆管理、数据统计分析于一体的综合性校园管理系统。

## 系统特性

### 🎯 核心功能
- **校友注册与认证** - 完整的校友信息审核流程
- **访问申请管理** - 便捷的在线访问申请和审批
- **人脸识别验证** - 智能快速的身份验证
- **车辆信息管理** - 校友车辆登记和进出管理
- **批量授权功能** - 支持按班级、年级、院系批量授权
- **数据统计分析** - 全面的访问数据统计和分析

### 📱 多端支持
- **移动端** - 响应式设计，完美适配手机和平板
- **PC端** - 功能完善的管理后台系统
- **自动适配** - 根据设备自动切换界面

### 🔒 安全特性
- **HTTPS加密** - 全程SSL/TLS加密传输
- **权限管理** - 细粒度的角色权限控制
- **数据加密** - 敏感数据加密存储
- **人脸特征保护** - 人脸数据安全处理

## 技术架构

### 后端技术栈
- **Python 3.7+**
- **Flask** - Web框架
- **SQLAlchemy** - ORM数据库操作
- **JWT** - 用户认证
- **OpenCV** - 人脸识别
- **MySQL/SQLite** - 数据存储

### 前端技术栈
- **HTML5 + CSS3** - 响应式布局
- **JavaScript ES6+** - 现代化交互
- **Chart.js** - 数据可视化
- **Remix Icon** - 图标库

### 部署特性
- **环境自动切换** - 开发/生产环境无缝切换
- **数据库自动迁移** - SQLite开发环境，MySQL生产环境
- **SSL证书管理** - 开发自签名证书，生产环境支持正式证书
- **一键启动** - 简单的命令行启动方式

## 快速开始

### 环境要求
- Python 3.7 或更高版本
- pip 包管理器

### 安装和启动

1. **克隆项目**
```bash
git clone <项目地址>
cd 校友入校登记
```

2. **初始化项目**
```bash
python start.py init
```
这个命令会：
- 安装所有依赖包
- 生成开发环境自签名证书
- 初始化数据库

3. **启动开发环境**
```bash
python start.py dev
```
系统将在 https://localhost:5000 启动

4. **启动生产环境**
```bash
python start.py prod
```
系统将使用MySQL数据库和生产配置

### 访问地址
- **移动端界面**: https://localhost:5000
- **管理后台**: https://localhost:5000/admin
- **API接口**: https://localhost:5000/api/*

## 使用说明

### 移动端使用
1. 访问 https://localhost:5000
2. 点击"立即注册"创建账户
3. 填写校友信息并提交审核
4. 等待管理员审核通过
5. 登录后即可使用各项功能：
   - 提交访问申请
   - 进行人脸注册
   - 管理车辆信息
   - 查看访问记录

### 管理后台使用
1. 访问 https://localhost:5000/admin
2. 使用管理员账户登录
3. 在仪表板查看系统概况
4. 管理用户和审核申请
5. 查看统计数据和报表

### 默认账户
系统初始化时会创建一个默认管理员账户：
- 用户名: admin
- 密码: admin123

**重要**: 首次登录后请立即修改默认密码！

## 系统配置

### 开发环境配置
开发环境使用SQLite数据库，所有配置在 `config/dev.py` 中：
- 数据库: `alumni_system_dev.db`
- 自签名证书: `config/certificates/`
- 调试模式: 开启
- 热重载: 支持

### 生产环境配置
生产环境使用MySQL数据库，配置在 `config/prod.py` 中：
- 需要配置MySQL连接信息
- SSL证书路径配置
- 安全设置加强
- 性能优化配置

### 环境变量
可以通过环境变量覆盖配置：
```bash
export MYSQL_HOST=localhost
export MYSQL_USER=alumni_user
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=alumni_system
```

## API文档

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/profile` - 获取用户信息
- `POST /api/auth/change-password` - 修改密码

### 用户管理
- `GET /api/users/alumni` - 获取校友列表
- `GET /api/users/alumni/<id>` - 获取校友详情
- `PUT /api/users/alumni/<id>/profile` - 更新校友档案

### 访问管理
- `POST /api/visits/applications` - 创建访问申请
- `GET /api/visits/applications` - 获取申请列表
- `POST /api/visits/applications/<id>/approve` - 审核申请
- `GET /api/visits/records` - 获取访问记录

### 人脸识别
- `POST /api/faces/register` - 注册人脸
- `GET /api/faces/status` - 获取注册状态
- `POST /api/faces/verify` - 人脸验证

### 车辆管理
- `POST /api/vehicles/` - 登记车辆
- `GET /api/vehicles/` - 获取车辆列表
- `PUT /api/vehicles/<id>` - 更新车辆信息

### 管理员接口
- `GET /api/admin/dashboard` - 仪表板数据
- `GET /api/admin/users` - 用户管理
- `GET /api/admin/statistics` - 数据统计
- `POST /api/admin/batch-approve` - 批量授权

## 目录结构

```
校友入校登记/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── routes/         # API路由
│   │   └── utils/          # 工具函数
│   ├── migrations/         # 数据库迁移
│   ├── requirements.txt    # 依赖包
│   └── run.py             # 应用入口
├── frontend/              # 前端代码
│   ├── static/           # 静态资源
│   │   ├── css/          # 样式文件
│   │   ├── js/           # JavaScript文件
│   │   └── images/       # 图片资源
│   └── templates/        # HTML模板
├── config/               # 配置文件
│   ├── dev.py           # 开发环境配置
│   ├── prod.py          # 生产环境配置
│   └── certificates/    # SSL证书
├── start.py            # 启动脚本
└── README.md           # 项目说明
```

## 开发指南

### 添加新功能
1. 在 `backend/app/models/` 中定义数据模型
2. 在 `backend/app/routes/` 中实现API接口
3. 在前端添加相应的界面和交互逻辑
4. 更新数据库迁移文件

### 代码规范
- Python代码遵循PEP8规范
- JavaScript使用ES6+语法
- CSS使用BEM命名规范
- 所有API接口都需要错误处理
- 敏感信息不得提交到版本控制

### 测试
```bash
# 运行测试
python -m pytest

# 代码覆盖率
python -m pytest --cov=app
```

## 故障排除

### 常见问题

1. **证书生成失败**
   - 确保安装了pyOpenSSL: `pip install pyOpenSSL`
   - 检查证书目录权限

2. **数据库连接失败**
   - 检查数据库服务是否运行
   - 确认连接配置正确

3. **人脸识别失败**
   - 确保图片光线充足
   - 检查OpenCV是否正确安装

4. **HTTPS访问问题**
   - 确认证书文件存在
   - 检查防火墙设置

### 日志查看
开发环境日志在控制台输出，生产环境日志在 `/var/log/alumni_system/` 目录。

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请联系：
- 邮箱: support@example.com
- 项目地址: https://github.com/example/alumni-system

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 完整的校友注册和访问申请功能
- 人脸识别集成
- 移动端和PC端界面
- 数据统计和管理功能