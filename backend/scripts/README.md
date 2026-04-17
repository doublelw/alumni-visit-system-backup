# 微信云数据库同步脚本使用说明

## 📁 文件说明

- `sync_wechat_approvals.py` - 主同步脚本
- `sync_daemon.py` - 守护进程（每分钟自动运行）
- `test_sync.py` - 测试服务器（模拟微信云数据库）
- `sync_wechat.log` - 同步脚本日志
- `sync_daemon.log` - 守护进程日志

---

## 🚀 快速开始

### 方式1: 直接运行同步脚本

```bash
cd backend

# 设置环境变量
export WECHAT_CLOUD_FUNCTION_URL=https://your-cloud-function-url

# 运行一次同步
python scripts/sync_wechat_approvals.py
```

### 方式2: 运行守护进程（推荐）

```bash
cd backend

# 设置环境变量
export WECHAT_CLOUD_FUNCTION_URL=https://your-cloud-function-url

# 启动守护进程（每60秒同步一次）
python scripts/sync_daemon.py

# 后台运行（Linux/Mac）
nohup python scripts/sync_daemon.py > /dev/null 2>&1 &

# 后台运行（Windows）
start /B python scripts\sync_daemon.py
```

### 方式3: 配置定时任务

**Linux/Mac (crontab)**:
```bash
# 编辑crontab
crontab -e

# 添加以下行（每分钟运行一次）
* * * * * cd /path/to/project/backend && export WECHAT_CLOUD_FUNCTION_URL=https://your-cloud-function-url && python scripts/sync_wechat_approvals.py >> logs/sync.log 2>&1
```

**Windows (任务计划程序)**:
1. 打开"任务计划程序"
2. 创建基本任务
   - 名称: "同步微信审批"
   - 触发器: 每分钟
   - 操作: 启动程序
     - 程序: `python`
     - 参数: `scripts\sync_wechat_approvals.py`
     - 起始于: `D:\Project\校友入校登记\backend`

---

## 🧪 测试模式

在配置微信云开发之前，可以使用测试服务器进行测试：

### 步骤1: 启动测试服务器

```bash
cd backend

# 启动模拟微信云数据库服务器（默认端口8765）
python scripts/test_sync.py
```

服务器会自动创建3条测试审批记录：
- 审批码 `123456` - 家长进校，批准
- 审批码 `654321` - 学生请假，批准
- 审批码 `111111` - 家长进校，拒绝

### 步骤2: 在另一个终端运行同步脚本

```bash
cd backend

# 设置环境变量指向测试服务器
export WECHAT_CLOUD_FUNCTION_URL=http://localhost:8765

# 运行同步脚本
python scripts/sync_wechat_approvals.py
```

### 步骤3: 检查结果

1. 查看日志输出
2. 检查校内数据库是否更新
3. 运行第二次同步，确认不会重复处理

---

## 📝 环境变量配置

创建 `backend/.env` 文件（如果不存在）：

```bash
# 微信云函数URL（必须）
WECHAT_CLOUD_FUNCTION_URL=https://xxx.bj.cloudfunction.net/approval-api

# 可选：同步间隔（秒），默认60秒
SYNC_INTERVAL=60
```

---

## 📊 日志说明

### sync_wechat.log
同步脚本的日志，包含：
- 连接微信云数据库的状态
- 获取到的审批记录数量
- 每条记录的处理结果
- 同步成功/失败的统计

示例日志：
```
2026-03-27 10:30:00 - INFO - ============================================================
2026-03-27 10:30:00 - INFO - 开始同步微信审批记录
2026-03-27 10:30:00 - INFO - 时间: 2026-03-27 10:30:00
2026-03-27 10:30:00 - INFO - 正在连接微信云数据库: https://xxx.bj.cloudfunction.net/approval-api
2026-03-27 10:30:01 - INFO - 成功获取 3 条待同步记录
2026-03-27 10:30:01 - INFO - 📥 找到 3 条待同步记录
2026-03-27 10:30:01 - INFO - 正在处理审批码: 123456, 操作: approve, 类型: parent-visit
2026-03-27 10:30:01 - INFO -   ✅ 审批通过: 123456, 类型: parent-visit, 日期: 2026-03-28
2026-03-27 10:30:01 - INFO - 正在处理审批码: 654321, 操作: approve, 类型: student-leave
2026-03-27 10:30:01 - INFO -   ✅ 审批通过: 654321, 类型: student-leave, 日期: 2026-03-27
2026-03-27 10:30:01 - INFO - 正在处理审批码: 111111, 操作: reject, 类型: parent-visit
2026-03-27 10:30:01 - INFO -   ❌ 审批拒绝: 111111, 理由: 未提供理由
2026-03-27 10:30:01 - INFO - 正在标记 3 条记录为已同步
2026-03-27 10:30:02 - INFO -   ✅ 成功标记 3 条记录为已同步
2026-03-27 10:30:02 - INFO - ------------------------------------------------------------
2026-03-27 10:30:02 - INFO - ✅ 同步完成: 成功 3 条, 失败 0 条
2026-03-27 10:30:02 - INFO - ============================================================
```

### sync_daemon.log
守护进程的日志，包含：
- 启动和停止时间
- 每轮循环的执行状态
- 异常和错误信息

---

## 🔍 故障排查

### 问题1: "未配置 WECHAT_CLOUD_FUNCTION_URL 环境变量"

**原因**: 没有设置环境变量

**解决**:
```bash
export WECHAT_CLOUD_FUNCTION_URL=https://your-cloud-function-url
```

或在 `.env` 文件中添加：
```bash
WECHAT_CLOUD_FUNCTION_URL=https://your-cloud-function-url
```

### 问题2: "连接微信云数据库超时"

**原因**: 网络问题或URL配置错误

**解决**:
1. 检查URL是否正确
2. 检查网络连接
3. 尝试手动访问URL验证可访问性

### 问题3: "未找到审批码对应的申请记录"

**原因**: 校内数据库中没有对应的申请记录

**解决**:
1. 确认审批码是否正确
2. 确认申请记录是否已创建
3. 检查申请记录的 access_code 字段

### 问题4: "审批码状态为 approved，跳过"

**原因**: 该审批码已经被处理过

**解决**: 这是正常情况，脚本会自动跳过已处理的记录

---

## 🎯 生产环境部署

### 1. 创建systemd服务（Linux）

创建 `/etc/systemd/system/wechat-sync.service`:

```ini
[Unit]
Description=WeChat Approval Sync Daemon
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/project/backend
Environment="WECHAT_CLOUD_FUNCTION_URL=https://your-cloud-function-url"
ExecStart=/usr/bin/python3 scripts/sync_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wechat-sync
sudo systemctl start wechat-sync
sudo systemctl status wechat-sync
```

### 2. 创建Windows服务

使用NSSM（Non-Sucking Service Manager）:

```bash
# 下载NSSM
https://nssm.cc/download

# 安装服务
nssm install WechatSync

# 配置
Path: C:\Python39\python.exe
Startup directory: D:\Project\校友入校登记\backend
Arguments: scripts\sync_daemon.py
Environment: WECHAT_CLOUD_FUNCTION_URL=https://your-cloud-function-url

# 启动服务
nssm start WechatSync
```

---

## 📈 监控和维护

### 查看同步状态

```bash
# 查看最近的同步日志
tail -f backend/scripts/sync_wechat.log

# 查看守护进程日志
tail -f backend/scripts/sync_daemon.log

# 检查进程是否运行
ps aux | grep sync_daemon
```

### 性能监控

脚本会自动记录：
- 同步成功率
- 每次同步的记录数
- 错误和异常信息

建议定期检查日志，确保同步正常。

---

## 🎉 总结

这套脚本实现了：

✅ **自动同步**: 每分钟自动拉取微信云数据库的审批记录
✅ **安全可靠**: 内网主动往外连，不暴露内网服务
✅ **容错机制**: 失败自动跳过，不影响其他记录
✅ **日志完善**: 详细记录每次同步的过程和结果
✅ **易于部署**: 支持守护进程、cron、Windows服务等多种方式

**下一步**: 配置微信云开发环境，替换测试URL为实际URL！
