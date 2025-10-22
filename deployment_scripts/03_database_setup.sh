#!/bin/bash

# =============================================================================
# 校友入校登记系统 - 数据库初始化脚本
# 功能: 安装MySQL、创建数据库、配置用户、初始化表结构
# 使用: sudo bash 03_database_setup.sh
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
MYSQL_ROOT_PASSWORD=""
DB_NAME="lsalumni"
DB_USER="lsalumni"
DB_PASSWORD=""
DB_HOST="localhost"
DB_PORT="3306"

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

# 显示帮助信息
show_help() {
    echo "校友入校登记系统 - 数据库初始化脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -r, --root-password PASSWORD    MySQL root密码"
    echo "  -d, --database-name NAME         数据库名称 (默认: lsalumni)"
    echo "  -u, --database-user USER        数据库用户 (默认: lsalumni)"
    echo "  -p, --database-password PASS    数据库用户密码"
    echo "  -h, --host HOST                 数据库主机 (默认: localhost)"
    echo "  -P, --port PORT                 数据库端口 (默认: 3306)"
    echo "  --help                          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -r MyRootPassword123 -p MyDbPassword456"
    echo "  $0 --root-password MyRootPassword123 --database-password MyDbPassword456"
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -r|--root-password)
                MYSQL_ROOT_PASSWORD="$2"
                shift 2
                ;;
            -d|--database-name)
                DB_NAME="$2"
                shift 2
                ;;
            -u|--database-user)
                DB_USER="$2"
                shift 2
                ;;
            -p|--database-password)
                DB_PASSWORD="$2"
                shift 2
                ;;
            -h|--host)
                DB_HOST="$2"
                shift 2
                ;;
            -P|--port)
                DB_PORT="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要以root权限运行"
        exit 1
    fi
}

# 生成随机密码
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# 输入密码
input_password() {
    local prompt="$1"
    local password
    local password_confirm

    while true; do
        read -s -p "$prompt" password
        echo ""
        read -s -p "确认密码: " password_confirm
        echo ""

        if [[ "$password" == "$password_confirm" ]]; then
            if [[ ${#password} -ge 8 ]]; then
                echo "$password"
                break
            else
                log_error "密码长度至少8位"
            fi
        else
            log_error "两次输入的密码不一致"
        fi
    done
}

# 检查MySQL是否已安装
check_mysql_installed() {
    if command -v mysql &> /dev/null; then
        log_info "MySQL已安装: $(mysql --version)"
        return 0
    else
        log_warn "MySQL未安装"
        return 1
    fi
}

# 安装MySQL 8.0
install_mysql() {
    log_step "安装MySQL 8.0..."

    # 更新包列表
    apt update

    # 安装MySQL服务器
    DEBIAN_FRONTEND=noninteractive apt install -y mysql-server

    # 启动并启用MySQL服务
    systemctl start mysql
    systemctl enable mysql

    # 检查MySQL状态
    if systemctl is-active --quiet mysql; then
        log_info "MySQL安装并启动成功"
    else
        log_error "MySQL启动失败"
        exit 1
    fi
}

# 配置MySQL安全设置
configure_mysql_security() {
    log_step "配置MySQL安全设置..."

    # 如果没有提供root密码，生成一个
    if [[ -z "$MYSQL_ROOT_PASSWORD" ]]; then
        MYSQL_ROOT_PASSWORD=$(generate_password)
        log_info "生成的MySQL root密码: $MYSQL_ROOT_PASSWORD"
        log_warn "请妥善保存此密码"
    fi

    # 执行MySQL安全配置
    mysql << EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$MYSQL_ROOT_PASSWORD';
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
EOF

    log_info "MySQL安全配置完成"
}

# 创建配置文件
create_mysql_config() {
    log_step "创建MySQL客户端配置文件..."

    cat > /root/.my.cnf << EOF
[mysql]
user=root
password=$MYSQL_ROOT_PASSWORD
host=$DB_HOST
port=$DB_PORT

[mysqldump]
user=root
password=$MYSQL_ROOT_PASSWORD
host=$DB_HOST
port=$DB_PORT
EOF

    chmod 600 /root/.my.cnf

    # 为lsalumni用户创建配置文件
    cat > /var/www/lsalumni/.my.cnf << EOF
[mysql]
user=$DB_USER
password=$DB_PASSWORD
host=$DB_HOST
port=$DB_PORT

[mysqldump]
user=$DB_USER
password=$DB_PASSWORD
host=$DB_HOST
port=$DB_PORT
EOF

    chmod 600 /var/www/lsalumni/.my.cnf
    chown lsalumni:lsalumni /var/www/lsalumni/.my.cnf

    log_info "MySQL配置文件创建完成"
}

# 创建数据库和用户
create_database_and_user() {
    log_step "创建数据库和用户..."

    # 如果没有提供数据库密码，生成一个
    if [[ -z "$DB_PASSWORD" ]]; then
        DB_PASSWORD=$(generate_password)
        log_info "生成的数据库用户密码: $DB_PASSWORD"
        log_warn "请妥善保存此密码"
    fi

    # 创建数据库和用户
    mysql << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

    log_info "数据库和用户创建完成"
}

# 优化MySQL配置
optimize_mysql_config() {
    log_step "优化MySQL配置..."

    # 备份原配置
    cp /etc/mysql/mysql.conf.d/mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf.bak

    # 添加优化配置
    cat >> /etc/mysql/mysql.conf.d/mysqld.cnf << 'EOF'

# LS Alumni System MySQL Optimization
[mysqld]
# General Query Log
general_log = 0
general_log_file = /var/log/mysql/general.log

# Error Log
log_error = /var/log/mysql/error.log

# Slow Query Log
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# Binary Log
expire_logs_days = 7
max_binlog_size = 100M

# InnoDB Configuration
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# Connection Settings
max_connections = 200
max_connect_errors = 1000
wait_timeout = 28800
interactive_timeout = 28800

# Query Cache (disabled for MySQL 8.0, using performance schema instead)
# query_cache_type = 1
# query_cache_size = 256M

# Character Set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# Security
local-infile = 0
EOF

    # 重启MySQL
    systemctl restart mysql

    log_info "MySQL配置优化完成"
}

# 创建数据库管理脚本
create_database_scripts() {
    log_step "创建数据库管理脚本..."

    # 创建备份脚本
    cat > /var/www/lsalumni/scripts/backup_database.sh << EOF
#!/bin/bash

# 数据库备份脚本
BACKUP_DIR="/var/www/lsalumni/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="\$BACKUP_DIR/lsalumni_backup_\$DATE.sql"

# 创建备份目录
mkdir -p \$BACKUP_DIR

# 执行备份
mysqldump --single-transaction --routines --triggers \$DB_NAME > \$BACKUP_FILE

# 压缩备份文件
gzip \$BACKUP_FILE

# 删除7天前的备份
find \$BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "数据库备份完成: \$BACKUP_FILE.gz"
EOF

    # 创建恢复脚本
    cat > /var/www/lsalumni/scripts/restore_database.sh << 'EOF'
#!/bin/bash

# 数据库恢复脚本
if [ $# -eq 0 ]; then
    echo "用法: $0 <backup_file>"
    echo "示例: $0 /var/www/lsalumni/backups/lsalumni_backup_20231020_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

# 恢复数据库
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | mysql lsalumni
else
    mysql lsalumni < "$BACKUP_FILE"
fi

echo "数据库恢复完成"
EOF

    # 设置权限
    chmod +x /var/www/lsalumni/scripts/backup_database.sh
    chmod +x /var/www/lsalumni/scripts/restore_database.sh
    chown lsalumni:lsalumni /var/www/lsalumni/scripts/*.sh

    # 添加到定时任务（每天凌晨2点备份）
    (crontab -l 2>/dev/null; echo "0 2 * * * /var/www/lsalumni/scripts/backup_database.sh") | crontab -

    log_info "数据库管理脚本创建完成"
}

# 测试数据库连接
test_database_connection() {
    log_step "测试数据库连接..."

    # 测试root连接
    if mysql -e "SELECT 1;" >/dev/null 2>&1; then
        log_info "MySQL root用户连接测试成功"
    else
        log_error "MySQL root用户连接测试失败"
        exit 1
    fi

    # 测试应用用户连接
    if mysql -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT 1;" >/dev/null 2>&1; then
        log_info "MySQL应用用户连接测试成功"
    else
        log_error "MySQL应用用户连接测试失败"
        exit 1
    fi
}

# 创建数据库信息文件
create_database_info() {
    log_step "保存数据库配置信息..."

    cat > /var/www/lsalumni/config/database.conf << EOF
# 数据库配置信息
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD

# 创建时间: $(date)
EOF

    chmod 600 /var/www/lsalumni/config/database.conf
    chown lsalumni:lsalumni /var/www/lsalumni/config/database.conf

    log_info "数据库配置信息已保存"
}

# 显示安装结果
show_installation_result() {
    echo ""
    echo "=============================================="
    log_info "数据库初始化完成！"
    echo "=============================================="
    echo ""
    echo "数据库连接信息:"
    echo "  主机: $DB_HOST"
    echo "  端口: $DB_PORT"
    echo "  数据库名: $DB_NAME"
    echo "  用户名: $DB_USER"
    echo "  密码: $DB_PASSWORD"
    echo ""
    echo "MySQL root密码: $MYSQL_ROOT_PASSWORD"
    echo ""
    echo "配置文件位置:"
    echo "  应用配置: /var/www/lsalumni/config/database.conf"
    echo "  MySQL配置: /etc/mysql/mysql.conf.d/mysqld.cnf"
    echo ""
    echo "管理脚本:"
    echo "  备份: /var/www/lsalumni/scripts/backup_database.sh"
    echo "  恢复: /var/www/lsalumni/scripts/restore_database.sh"
    echo ""
    echo "下一步操作:"
    echo "1. 运行 04_deploy_application.sh 部署应用"
    echo ""
}

# 主函数
main() {
    echo "=============================================="
    echo "校友入校登记系统 - 数据库初始化脚本"
    echo "=============================================="
    echo ""

    # 检查root权限
    check_root

    # 解析命令行参数
    parse_arguments "$@"

    # 如果没有提供必要参数，交互式输入
    if [[ -z "$MYSQL_ROOT_PASSWORD" ]]; then
        echo "请输入MySQL root密码:"
        MYSQL_ROOT_PASSWORD=$(input_password "MySQL root密码: ")
    fi

    if [[ -z "$DB_PASSWORD" ]]; then
        echo "请输入数据库用户密码:"
        DB_PASSWORD=$(input_password "数据库用户密码: ")
    fi

    # 安装和配置MySQL
    if ! check_mysql_installed; then
        install_mysql
    fi

    configure_mysql_security
    create_mysql_config
    create_database_and_user
    optimize_mysql_config
    create_database_scripts
    test_database_connection
    create_database_info
    show_installation_result
}

# 执行主函数
main "$@"