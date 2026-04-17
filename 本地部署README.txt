# 校友入校登记系统 - 本地部署指南

## 关于 OpenClaw API Rate Limit 错误

如果您遇到 "⚠️ API rate limit reached" 错误，不用担心！

**重要说明:**
- OpenClaw 的 AI 聊天功能有 rate limit 限制
- 但 OpenClaw 的**本地自动化功能**完全正常
- 我们的部署准备工作**不需要 AI 接口**

## 解决方案：使用纯本地工具

本项目已经为您准备好了完整的本地部署工具集：

### ✅ 已准备好的文件

1. **部署包** (4.4 MB)
   - `welife_deploy_package_20260406_191348.zip`
   - 包含所有项目文件

2. **配置文件** (3.3 KB)
   - `部署配置-微信云托管.txt`
   - 包含所有环境变量和密钥

3. **部署指南** (4.7 KB)
   - `纯本地部署-最终状态报告.txt`
   - 详细的操作步骤说明

4. **本地工具**
   - `本地部署助手.py` - 纯 Python 脚本
   - `部署状态检查.bat` - Windows 批处理
   - `开始部署.bat` - 一键启动部署

## 🚀 快速开始

### 方法1: 双击运行 (推荐)

1. 双击: `开始部署.bat`
2. 会自动打开:
   - 配置文件 (记事本)
   - 微信云托管控制台 (浏览器)

### 方法2: 命令行运行

```bash
cd D:\Project\校友入校登记
python 本地部署助手.py
```

## 📋 部署步骤 (在微信云托管控制台)

### 1. 创建服务
- 服务名称: `lsalumni-api`
- 部署方式: `本地上传代码包`

### 2. 上传部署包
- 选择: `welife_deploy_package_20260406_191348.zip`

### 3. 配置环境变量
从配置文件中复制以下变量:
```
FLASK_APP=app.py
FLASK_ENV=production
WECHAT_CLOUD=true
DATABASE_URL=sqlite:///alumni_system.db
SECRET_KEY=A1fPI8NHU31gyjSNykCYBLTRJV95P2aF4003WL8I3Z0=
JWT_SECRET_KEY=V3ihfrJ6TsvnHygiK/lNgcZ68ittme4Co8JlefG5NHY=
ELECTRONIC_CARD_SECRET_KEY=1k3qURyemMKQEk9jRgx+FiYn6cqA+gNKRT7vQF1ytLI=
HMAC_SECRET_KEY=qnD+I/U1tzLnXwGte4kadD3M0CngHeo4pRIdIEK76X8=
```

### 4. 开始部署
- 版本: `v1.0.0`
- 规格: `1C 2G`
- 点击: `开始部署`

### 5. 验证部署
- 访问: `https://你的服务地址.welife.icu/api/health`
- 访问: `https://你的服务地址.welife.icu/`

## 🔧 工具说明

### 本地部署助手.py
完全使用 Python 标准库编写，无外部依赖：
- 检查部署包
- 检查配置文件
- 显示部署状态
- 提供操作指引

**运行方式:**
```bash
python 本地部署助手.py
```

### 部署状态检查.bat
Windows 批处理脚本：
- 快速检查文件状态
- 自动打开必要文件
- 启动浏览器

**运行方式:**
双击 `部署状态检查.bat`

### 开始部署.bat
一键启动部署流程：
- 检查所有文件
- 打开配置文件
- 打开云托管控制台

**运行方式:**
双击 `开始部署.bat`

## 📚 详细文档

- **配置信息**: `部署配置-微信云托管.txt`
- **完整指南**: `纯本地部署-最终状态报告.txt`
- **操作步骤**: `微信云托管部署操作步骤.md`

## ⚠️ 常见问题

### 1. OpenClaw 显示 rate limit 错误
**影响**: 仅影响 AI 聊天功能
**解决**: 使用本地工具，无需 AI 接口

### 2. 部署包不存在
**解决**: 运行 `python deployment_scripts/deploy_to_welife.py`

### 3. 配置文件缺失
**解决**: 运行 `python 本地部署助手.py` 会自动生成

### 4. 微信云托管连接失败
**解决**:
- 检查网络连接
- 确认微信账号登录状态
- 尝试刷新页面

## 🎯 总结

✅ **所有部署准备工作已完成**
✅ **使用纯本地工具，无需 AI 接口**
✅ **详细配置和步骤说明已准备**
✅ **OpenClaw rate limit 错误不影响部署**

**现在可以开始部署！** 双击 `开始部署.bat` 即可。

---

**最后更新**: 2026-04-06 19:40
**状态**: ✅ 可用
**依赖**: 无 (纯本地工具)
