# SSL证书问题解决方案

## 问题描述
当访问校友入校登记系统时，可能会遇到SSL证书错误，显示类似以下错误：
- `net::ERR_CERT_AUTHORITY_INVALID`
- `加载活动失败: TypeError: Failed to fetch`

这是因为开发环境使用自签名SSL证书，浏览器默认不信任这种证书。

## 解决方案

### 方法一：使用SSL设置指南（推荐）
1. 访问 `https://localhost:5000/ssl-setup`
2. 按照页面上的步骤操作
3. 接受SSL证书后刷新原页面

### 方法二：直接访问服务器
1. 直接访问 `https://localhost:5000`
2. 在浏览器显示的警告页面：
   - **Chrome/Edge**: 点击"高级" → "继续前往 localhost (不安全)"
   - **Firefox**: 点击"高级" → "接受风险并继续"
   - **Safari**: 点击"访问此网站"或"显示详细信息" → "访问此网站"
3. 返回原页面并刷新

### 方法三：使用SSL错误页面
1. 如果遇到SSL错误，系统会自动跳转到 `https://localhost:5000/ssl-error`
2. 在该页面可以选择不同的解决方案
3. 按照指引完成SSL证书设置

## 验证是否成功
设置成功后，您应该能够：
- 看到浏览器地址栏的锁图标（可能有警告标记）
- 正常访问系统的所有功能
- 校历活动正常加载
- 所有API调用正常工作

## 注意事项
- 此设置仅在开发环境中需要
- SSL证书有效期很长，通常只需设置一次
- 不同浏览器需要分别设置证书信任
- 清除浏览器缓存可能需要重新设置

## 快速链接
- 系统主页: `https://127.0.0.1:5000/`
- SSL设置指南: `https://localhost:5000/ssl-setup`
- SSL错误页面: `https://localhost:5000/ssl-error`

---

## 技术说明（供开发者参考）

### 实现的功能
1. **SSL设置指南页面** (`/ssl-setup`)：详细的SSL证书设置步骤
2. **SSL错误页面** (`/ssl-error`)：当检测到SSL错误时自动跳转
3. **JavaScript错误处理**：自动检测SSL错误并重定向到帮助页面
4. **公共API端点**：`/api/public/calendar/events` 无需认证即可访问

### 文件修改
- `backend/app/routes/web.py`: 添加SSL设置和错误页面路由
- `frontend/templates/ssl-setup.html`: SSL设置指南页面
- `frontend/templates/ssl-error.html`: SSL错误处理页面
- `frontend/static/js/mobile.js`: SSL错误检测和自动重定向
- `backend/app/routes/calendar.py`: 公开API端点（已实现）

### 系统状态
- ✅ 后端服务器运行正常 (https://localhost:5000)
- ✅ 公开API正常工作 (返回200状态码和5个活动)
- ✅ SSL帮助页面可访问
- ✅ JavaScript错误处理已实现
- ✅ 访问记录功能已完成
- ✅ 所有核心功能正常