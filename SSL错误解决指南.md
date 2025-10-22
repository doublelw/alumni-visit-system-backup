# SSL协议错误解决指南

## ❌ 问题：ERR_SSL_PROTOCOL_ERROR

如果您在访问 `127.0.0.1:5000` 时遇到 "此站点的连接不安全" 或 "ERR_SSL_PROTOCOL_ERROR" 错误，这是因为浏览器尝试使用 HTTPS 协议访问 HTTP 服务器导致的。

## ✅ 解决方案

### 方案1：强制使用 HTTP（推荐）

在浏览器地址栏中明确输入 `http://` 前缀：

```
http://127.0.0.1:5000
```

而不是：
```
https://127.0.0.1:5000  ❌
```

### 方案2：清除浏览器缓存和设置

#### Chrome/Edge 浏览器：
1. 打开浏览器设置
2. 搜索 "SSL" 或 "安全"
3. 找到 "重置安全设置" 选项
4. 清除浏览器缓存和 Cookie

#### Firefox 浏览器：
1. 打开设置 → 隐私与安全
2. 清除浏览数据
3. 重置浏览器设置

### 方案3：使用无痕模式

- **Chrome**: Ctrl + Shift + N
- **Firefox**: Ctrl + Shift + P
- **Edge**: Ctrl + Shift + P

### 方案4：修改服务器配置（可选）

如果需要让服务器支持 HTTPS，可以修改服务器配置。

## 🔧 测试连接

### 方法1：使用命令行测试
```bash
# 测试 HTTP 连接
curl http://127.0.0.1:5000

# 或者使用 PowerShell
Invoke-WebRequest -Uri http://127.0.0.1:5000
```

### 方法2：使用不同的端口
```bash
# 使用其他端口启动服务器
python server_manager.py start --debug --port 8080 --app-dir backend
```

然后访问：`http://127.0.0.1:8080`

### 方法3：使用 0.0.0.0 而不是 127.0.0.1
```bash
# 允许外部访问
python server_manager.py start --debug --host 0.0.0.0 --app-dir backend
```

然后访问：`http://localhost:5000` 或 `http://127.0.0.1:5000`

## 🚀 推荐使用方法

### 最简单的方法：
1. 确保服务器正在运行
2. 在浏览器地址栏输入：`http://127.0.0.1:5000`
3. 确保地址以 `http://` 开头，不是 `https://`

### 启动服务器：
```bash
# 使用我们的管理脚本
python server_manager.py start --debug --app-dir backend

# 或者使用快速重启
quick_restart.bat
```

## 📋 故障排除清单

- [ ] 确保使用 `http://` 而不是 `https://`
- [ ] 检查服务器是否正在运行
- [ ] 尝试清除浏览器缓存
- [ ] 使用无痕模式测试
- [ ] 尝试不同的浏览器
- [ ] 检查端口是否被其他程序占用
- [ ] 确认防火墙没有阻止连接

## 🎯 重要提示

**开发服务器**默认只支持 HTTP，不支持 HTTPS。如果您在生产环境中需要 HTTPS，需要配置 SSL 证书。

对于开发环境，使用 HTTP 是完全正常和安全的。