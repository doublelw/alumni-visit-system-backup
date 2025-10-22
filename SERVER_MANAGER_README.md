# Flask服务器管理工具使用说明

本项目提供了一个完整的服务器管理工具，方便您启动、停止和重启Flask服务器。

## 文件说明

### 核心文件
- `server_manager.py` - Python服务器管理器（核心脚本）
- `start_server.bat` - Windows用户界面化管理脚本
- `quick_restart.bat` - Windows快速重启脚本
- `start_server.sh` - Linux/Mac用户界面化管理脚本
- `quick_restart.sh` - Linux/Mac快速重启脚本

### 依赖要求
```bash
pip install psutil flask
```

## 使用方法

### Windows用户

#### 方法1：使用图形界面（推荐）
双击运行 `start_server.bat`，会显示菜单界面：
```
========================================
  校友入校登记系统 - 服务器管理工具
========================================

请选择操作:
1. 启动服务器 (开发模式)
2. 启动服务器 (生产模式)
3. 重启服务器
4. 停止服务器
5. 查看服务器状态
6. 安装项目依赖
7. 强制停止所有服务器
0. 退出
```

#### 方法2：快速重启
双击运行 `quick_restart.bat` 可以直接重启服务器。

#### 方法3：命令行使用
```cmd
# 启动服务器（开发模式）
python server_manager.py start --debug

# 重启服务器
python server_manager.py restart --debug

# 停止服务器
python server_manager.py stop

# 查看状态
python server_manager.py status

# 强制停止
python server_manager.py stop --force
```

### Linux/Mac用户

#### 方法1：使用图形界面（推荐）
```bash
# 首先给脚本执行权限
chmod +x start_server.sh quick_restart.sh

# 运行管理脚本
./start_server.sh
```

#### 方法2：快速重启
```bash
./quick_restart.sh
```

#### 方法3：命令行使用
```bash
# 启动服务器（开发模式）
python3 server_manager.py start --debug --env development

# 重启服务器
python3 server_manager.py restart --debug --env development

# 停止服务器
python3 server_manager.py stop

# 查看状态
python3 server_manager.py status

# 安装依赖
python3 server_manager.py install
```

## 功能特性

### 1. 智能进程管理
- 自动查找并管理Flask进程
- 支持优雅停止和强制停止
- 检测端口占用情况

### 2. 详细的日志记录
- 所有操作都会记录到 `server_restart.log`
- 服务器运行日志保存在 `logs/` 目录
- 按日期分类的日志文件

### 3. 服务器状态监控
- 查看进程PID、内存使用、CPU占用
- 实时监控服务器运行状态
- 错误诊断和问题排查

### 4. 灵活的配置选项
- 支持自定义端口和主机
- 开发/生产环境切换
- 调试模式开关

## 常用命令示例

### 开发环境
```bash
# 启动开发服务器（带自动重载）
python server_manager.py start --debug --env development --port 5000

# 重启开发服务器
python server_manager.py restart --debug --env development
```

### 生产环境
```bash
# 启动生产服务器
python server_manager.py start --env production --host 0.0.0.0 --port 5000

# 重启生产服务器
python server_manager.py restart --env production --host 0.0.0.0
```

### 故障处理
```bash
# 查看服务器状态
python server_manager.py status

# 强制停止所有相关进程
python server_manager.py stop --force

# 安装依赖
python server_manager.py install
```

## 日志文件位置

- **操作日志**: `server_restart.log`
- **服务器日志**: `logs/server_YYYYMMDD.log`

## 故障排除

### 1. 端口被占用
```bash
# 查看端口占用
python server_manager.py status

# 强制停止进程
python server_manager.py stop --force
```

### 2. 权限问题
```bash
# Linux/Mac系统可能需要权限
sudo python3 server_manager.py start
```

### 3. 依赖问题
```bash
# 安装或重新安装依赖
python server_manager.py install

# 手动安装psutil
pip install psutil flask
```

### 4. 进程无法停止
```bash
# 强制停止所有相关进程
python server_manager.py stop --force

# 或者手动杀死进程
# Windows: taskkill /F /PID 进程号
# Linux/Mac: kill -9 进程号
```

## 高级用法

### 自定义配置
```bash
# 指定应用目录
python server_manager.py start --app-dir /path/to/your/app

# 自定义端口和主机
python server_manager.py start --host 192.168.1.100 --port 8080

# 生产模式 + 指定环境变量
FLASK_ENV=production python server_manager.py start --env production
```

### 批量操作
```bash
# 可以在脚本中组合使用
python server_manager.py stop --force
python server_manager.py install
python server_manager.py start --debug
```

## 注意事项

1. **首次使用前**请确保安装了所有依赖：`pip install psutil flask`
2. **生产环境**建议使用 `--env production` 参数
3. **重要更新**前请备份数据库
4. **服务器运行时**不要关闭命令行窗口
5. **日志文件**会不断增长，请定期清理

## 支持与反馈

如果遇到问题或有改进建议，请检查日志文件或联系开发者。