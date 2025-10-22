# Mobile.js 版本保护记录

## 📋 版本信息
- **文件名**: mobile.js
- **版本**: 5.0
- **更新时间**: 2025-10-17
- **原始位置**: `frontend/static/js/mobile-new.js`

## 🔒 保护措施
1. **原始备份**: `frontend/static/js/mobile-v5.0-original.js` (不可修改)
2. **生产版本**:
   - `frontend/static/js/mobile.js` (服务器使用)
   - `backend/static/js/mobile.js` (服务器使用)
3. **HTML引用**: `frontend/templates/index.html` 已更新为 v5.0

## ⚙️ 配置修正
- **API_BASE_URL**: 已修正为 `http://localhost:5000/api`
- **端口配置**: 从 8000 端口改为 5000 端口

## 🚫 禁止操作
- ❌ 不可覆盖 `mobile-v5.0-original.js` 文件
- ❌ 不可修改 `frontend/static/js/mobile.js` 和 `backend/static/js/mobile.js` 的核心逻辑
- ❌ 不可回退到旧版本

## ✅ 允许操作
- ✅ 可以基于 `mobile-v5.0-original.js` 创建新版本
- ✅ 可以修改HTML中的版本号缓存控制
- ✅ 可以在新的分支上进行开发和测试

## 📝 更新日志
- 2025-10-17: 从 mobile-new.js (v5.0) 更新到生产环境
- 修正API URL从localhost:8000改为localhost:5000
- 更新HTML版本号引用从3.2到5.0

---
**保护状态**: 🟢 已激活
**维护人员**: Claude Code Assistant