#!/bin/bash

# =============================================================================
# 校友入校登记系统 - 服务器初始化脚本
# 功能: 系统基础环境安装和配置
# 使用: sudo bash 01_server_init.sh
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要以root权限运行"
        exit 1
    fi
}

# 系统信息
show_system_info() {
    log_info "=== 系统信息 ==="
    echo "操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "内核版本: $(uname -r)"
    echo "CPU信息: $(lscpu | grep 'Model name' | cut -d':' -f2 | xargs)"
    echo "内存信息: $(free -h | grep '^Mem:' | awk '{print $2}')"
    echo "磁盘信息: $(df -h / | tail -1 | awk '{print $2}')"
    echo "IP地址: $(ip route get 8.8.8.8 | awk '{print $7; exit}')"
    echo ""
}

# 更新系统
update_system() {
    log_step "更新系统软件包..."
    apt update
    apt upgrade -y
    apt autoremove -y
    apt autoclean
    log_info "系统更新完成"
}

# 安装基础工具
install_basic_tools() {
    log_step "安装基础工具..."
    apt install -y \
        curl \
        wget \
        git \
        unzip \
        htop \
        vim \
        nano \
        tree \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        build-essential \
        supervisor \
        cron

    log_info "基础工具安装完成"
}

# 设置时区
set_timezone() {
    log_step "设置时区为 Asia/Shanghai..."
    timedatectl set-timezone Asia/Shanghai
    log_info "时区设置完成: $(timedatectl | grep 'Time zone')"
}

# 配置防火墙
configure_firewall() {
    log_step "配置防火墙..."

    # 安装ufw（如果没有）
    if ! command -v ufw &> /dev/null; then
        apt install -y ufw
    fi

    # 默认策略
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing

    # 允许SSH
    ufw allow ssh

    # 允许HTTP和HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp

    # 启用防火墙
    ufw --force enable

    log_info "防火墙配置完成"
    ufw status
}

# 创建系统用户
create_system_user() {
    log_step "创建应用用户..."

    if ! id "lsalumni" &>/dev/null; then
        useradd -m -s /bin/bash lsalumni
        log_info "用户 lsalumni 创建成功"
    else
        log_warn "用户 lsalumni 已存在"
    fi
}

# 创建目录结构
create_directories() {
    log_step "创建目录结构..."

    # 主目录
    mkdir -p /var/www/lsalumni
    mkdir -p /var/www/lsalumni/{backend,frontend,config,scripts,logs,backups,static,uploads}

    # 日志目录
    mkdir -p /var/log/lsalumni

    # SSL证书目录
    mkdir -p /etc/ssl/certs
    mkdir -p /etc/ssl/private

    # 设置权限
    chown -R lsalumni:lsalumni /var/www/lsalumni
    chown -R lsalumni:lsalumni /var/log/lsalumni
    chmod 755 /var/www/lsalumni
    chmod 755 /var/log/lsalumni

    log_info "目录结构创建完成"
}

# 配置系统限制
configure_system_limits() {
    log_step "配置系统限制..."

    # 添加系统限制配置
    cat >> /etc/security/limits.conf << 'EOF'

# LS Alumni System Limits
lsalumni soft nofile 65536
lsalumni hard nofile 65536
lsalumni soft nproc 32768
lsalumni hard nproc 32768
EOF

    # 配置内核参数
    cat >> /etc/sysctl.conf << 'EOF'

# LS Alumni System Kernel Parameters
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 5000
EOF

    # 应用内核参数
    sysctl -p

    log_info "系统限制配置完成"
}

# 配置SSH安全
configure_ssh_security() {
    log_step "配置SSH安全..."

    # 备份原配置
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

    # 修改SSH配置
    sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
    sed -i 's/#MaxAuthTries 6/MaxAuthTries 3/' /etc/ssh/sshd_config
    sed -i 's/#ClientAliveInterval 0/ClientAliveInterval 300/' /etc/ssh/sshd_config
    sed -i 's/#ClientAliveCountMax 3/ClientAliveCountMax 2/' /etc/ssh/sshd_config

    # 重启SSH服务
    systemctl restart sshd

    log_info "SSH安全配置完成"
}

# 安装fail2ban
install_fail2ban() {
    log_step "安装和配置fail2ban..."

    apt install -y fail2ban

    # 配置fail2ban
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
destemail = root@localhost

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 3
EOF

    systemctl enable fail2ban
    systemctl restart fail2ban

    log_info "fail2ban配置完成"
}

# 创建监控脚本
create_monitoring_script() {
    log_step "创建监控脚本..."

    cat > /var/www/lsalumni/scripts/system_monitor.sh << 'EOF'
#!/bin/bash

# 系统监控脚本
LOG_FILE="/var/log/lsalumni/system_monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# CPU使用率
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

# 内存使用率
MEM_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')

# 磁盘使用率
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | cut -d'%' -f1)

# 系统负载
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | xargs)

# 记录日志
echo "[$DATE] CPU: ${CPU_USAGE}% | MEM: ${MEM_USAGE}% | DISK: ${DISK_USAGE}% | LOAD: ${LOAD_AVG}" >> $LOG_FILE

# 检查阈值
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "[$DATE] WARNING: CPU usage is high: ${CPU_USAGE}%" >> $LOG_FILE
fi

if (( $(echo "$MEM_USAGE > 80" | bc -l) )); then
    echo "[$DATE] WARNING: Memory usage is high: ${MEM_USAGE}%" >> $LOG_FILE
fi

if [ "$DISK_USAGE" -gt 80 ]; then
    echo "[$DATE] WARNING: Disk usage is high: ${DISK_USAGE}%" >> $LOG_FILE
fi
EOF

    chmod +x /var/www/lsalumni/scripts/system_monitor.sh
    chown lsalumni:lsalumni /var/www/lsalumni/scripts/system_monitor.sh

    # 添加到定时任务（每5分钟执行一次）
    (crontab -l 2>/dev/null; echo "*/5 * * * * /var/www/lsalumni/scripts/system_monitor.sh") | crontab -

    log_info "监控脚本创建完成"
}

# 创建日志轮转配置
create_logrotate_config() {
    log_step "配置日志轮转..."

    cat > /etc/logrotate.d/lsalumni << 'EOF'
/var/log/lsalumni/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 lsalumni lsalumni
    postrotate
        systemctl reload lsalumni >/dev/null 2>&1 || true
    endscript
}
EOF

    log_info "日志轮转配置完成"
}

# 主函数
main() {
    echo "=============================================="
    echo "校友入校登记系统 - 服务器初始化脚本"
    echo "=============================================="
    echo ""

    # 检查root权限
    check_root

    # 显示系统信息
    show_system_info

    # 执行初始化步骤
    update_system
    install_basic_tools
    set_timezone
    configure_firewall
    create_system_user
    create_directories
    configure_system_limits
    configure_ssh_security
    install_fail2ban
    create_monitoring_script
    create_logrotate_config

    echo ""
    echo "=============================================="
    log_info "服务器初始化完成！"
    echo "=============================================="
    echo ""
    echo "下一步操作："
    echo "1. 运行 02_install_dependencies.sh 安装依赖环境"
    echo "2. 运行 03_database_setup.sh 配置数据库"
    echo "3. 运行 04_deploy_application.sh 部署应用"
    echo ""
    echo "系统用户: lsalumni"
    echo "应用目录: /var/www/lsalumni"
    echo "日志目录: /var/log/lsalumni"
    echo ""
}

# 执行主函数
main "$@"