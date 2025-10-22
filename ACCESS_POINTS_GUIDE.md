# 校友入校登记系统 - 访问入口指南

## 🌐 所有访问入口地址

部署完成后，系统将提供以下访问入口：

### 1. 主页（移动端界面）
- **本地开发**: http://127.0.0.1:5000/
- **生产环境**: https://www.pofeclife.top/lsalumni/
- **功能描述**: 校友主要访问界面，包含预约申请、二维码生成等功能
- **特点**: 移动端优化，响应式设计

### 2. 管理后台登录页
- **本地开发**: http://127.0.0.1:5000/admin-login
- **生产环境**: https://www.pofeclife.top/lsalumni/admin-login
- **功能描述**: 管理员登录入口
- **默认账户**: admin / admin123

### 3. 管理后台主页面
- **本地开发**: http://127.0.0.1:5000/admin
- **生产环境**: https://www.pofeclife.top/lsalumni/admin
- **功能描述**: 管理员操作界面，包含用户管理、预约审核、数据统计等功能

### 4. 保安专用端
- **本地开发**: http://127.0.0.1:5000/security-portal
- **生产环境**: https://www.pofeclife.top/lsalumni/security-portal
- **功能描述**: 保安人员使用界面，用于扫码核验、登记管理

### 5. 校友注册页面
- **本地开发**: http://127.0.0.1:5000/register
- **生产环境**: https://www.pofeclife.top/lsalumni/register
- **功能描述**: 校友账号注册页面

---

## 📱 各端功能说明

### 📋 主页（移动端）
- ✅ 校友登录
- ✅ 预约申请
- ✅ 查看预约记录
- ✅ 二维码生成
- ✅ 个人信息管理
- ✅ 人脸识别注册

### 🖥️ 管理后台
- ✅ 用户管理（增删改查）
- ✅ 预约审核
- ✅ 访问记录查看
- ✅ 数据统计报表
- ✅ 系统设置
- ✅ 目标人员管理

### 🛡️ 保安门户
- ✅ 二维码扫描
- ✅ 访客登记
- ✅ 记录查询
- ✅ 实时核验

### 📝 注册页面
- ✅ 校友信息注册
- ✅ 账号激活
- ✅ 人脸信息录入

---

## 🔐 默认账户信息

### 管理员账户
- **用户名**: admin
- **密码**: admin123
- **权限**: 超级管理员
- **首次登录**: 建议立即修改密码

### 测试账户
系统会预置多个测试账户，详见 `测试用户密码表.md` 文件。

---

## 🚀 快速访问测试

### 部署完成后测试步骤：

1. **测试主页访问**
   ```
   https://www.pofeclife.top/lsalumni/
   ```

2. **测试管理后台**
   ```
   https://www.pofeclife.top/lsalumni/admin-login
   用户名: admin
   密码: admin123
   ```

3. **测试保安门户**
   ```
   https://www.pofeclife.top/lsalumni/security-portal
   ```

4. **测试注册页面**
   ```
   https://www.pofeclife.top/lsalumni/register
   ```

---

## 📋 文件清单验证

部署包包含以下前端文件：

### HTML页面文件
- ✅ `frontend/index.html` - 主页（移动端界面）
- ✅ `frontend/admin.html` - 管理后台主页面
- ✅ `frontend/security-portal.html` - 保安专用端
- ✅ `frontend/templates/register.html` - 校友注册页面
- ✅ `frontend/templates/admin-login.html` - 管理后台登录页

### 模板文件
- ✅ `backend/templates/` - Flask模板文件
- ✅ `frontend/templates/` - 前端模板文件

### 静态资源
- ✅ `frontend/static/css/` - 样式文件
- ✅ `frontend/static/js/` - JavaScript文件
- ✅ `frontend/static/images/` - 图片资源

---

## 🔧 Nginx配置说明

Nginx配置已优化支持：
- ✅ HTTP自动重定向到HTTPS
- ✅ 静态文件缓存优化
- ✅ API请求代理
- ✅ 子路径 `/lsalumni` 支持
- ✅ 安全头部配置
- ✅ Gzip压缩

---

## 📱 移动端适配

### 响应式设计
- ✅ 主页完全移动端优化
- ✅ 管理后台支持平板访问
- ✅ 保安门户适配手机屏幕

### 触摸优化
- ✅ 按钮尺寸适合手指点击
- ✅ 表单输入优化
- ✅ 滑动手势支持

---

## 🌍 跨域配置

系统已配置完整的CORS支持：
- ✅ API跨域访问
- ✅ 静态资源跨域
- ✅ 多域名支持

---

## 📞 技术支持

如遇访问问题，请检查：

1. **服务器状态**
   ```bash
   systemctl status lsalumni nginx
   ```

2. **端口监听**
   ```bash
   netstat -tlnp | grep -E ':(80|443|5000)'
   ```

3. **日志查看**
   ```bash
   tail -f /var/log/nginx/lsalumni_*.log
   journalctl -u lsalumni -f
   ```

4. **SSL证书状态**
   ```bash
   certbot certificates
   ```

---

## 📈 性能优化

### 已启用优化
- ✅ 静态文件长期缓存
- ✅ Gzip压缩
- ✅ Keep-Alive连接
- ✅ SSL/TLS优化
- ✅ 安全头部配置

### 监控指标
- 页面加载时间
- API响应时间
- 错误率监控
- 用户访问统计

---

部署完成后，所有入口都将通过 `https://www.pofeclife.top/lsalumni/` 前缀访问。