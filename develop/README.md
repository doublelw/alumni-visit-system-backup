# Develop 目录说明

本目录用于存放项目开发过程中的测试文件、临时文件和过程文档。

## 📁 目录结构

```
develop/
├── test_files/          # 测试脚本和测试数据生成脚本
│   └── backend/         # backend目录下的测试文件
├── reports/             # 测试报告（HTML格式）
├── screenshots/         # 测试截图和调试图片
├── backups/             # 备份文件（压缩包、发布包等）
│   └── deployment_packages/
├── temp_files/          # 临时文件（配置、数据库、日志等）
├── logs/                # 运行日志
└── databases/           # 开发测试数据库文件
```

## 📝 文件分类

### 1. test_files/ - 测试文件
- `test_*.py` - 单元测试和集成测试脚本
- `check_*.py` - 数据检查和验证脚本
- `debug_*.py` - 调试脚本
- `create_*.py` - 测试数据创建脚本
- `e2e_*.py` - 端到端测试脚本
- 其他辅助测试脚本

### 2. reports/ - 测试报告
- 各种HTML格式的测试报告
- 功能验证报告
- E2E测试报告
- 性能测试报告

### 3. screenshots/ - 截图
- 测试执行截图
- UI调试截图
- 页面预览图

### 4. backups/ - 备份文件
- 项目部署压缩包
- 发布版本备份
- 数据库备份
- 部署脚本备份

### 5. temp_files/ - 临时文件
- 临时配置文件
- 模板文件
- Excel测试数据
- 文档草稿
- 调试输出文件

### 6. logs/ - 日志文件
- 服务器运行日志
- 错误日志
- 访问日志

### 7. databases/ - 数据库文件
- 开发测试用的SQLite数据库
- 测试数据快照

## ⚠️ 重要说明

1. **不要在生产环境使用develop目录下的任何文件**
2. 这些文件仅用于开发、测试和调试
3. 定期清理过期的测试数据和日志
4. 重要数据应该在 `backend/` 和 `frontend/` 核心目录中

## 🔄 清理建议

可以定期清理以下内容：
- 超过30天的日志文件
- 旧的测试报告
- 重复的截图
- 临时测试数据库

## 📂 核心项目结构

清理后的项目根目录主要包含：

```
校友入校登记/
├── backend/              # 后端核心代码（Flask应用）
├── frontend/             # 前端核心代码（HTML/CSS/JS）
├── config/               # 配置文件
├── deployment_scripts/   # 部署脚本
├── logs/                 # 生产环境日志
├── uploads/              # 用户上传文件
├── README.md             # 项目说明文档
├── requirements.txt      # Python依赖
├── .env.template         # 环境变量模板
└── develop/              # 本目录（开发测试文件）
```

---

*最后更新：2026-04-01*
