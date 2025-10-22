#!/bin/bash

# =============================================================================
# 校友入校登记系统 - 系统管理脚本
# 功能: 启动、停止、重启、监控整个系统
# 使用: sudo bash manage_system.sh [start|stop|restart|status|logs|health]
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 系统配置
SERVICE_NAME="lsalumni"
NGINX_SERVICE="nginx"
MYSQL_SERVICE="mysql"
DEPLOY_PATH="/var/www/lsalumni"
LOG_DIR="/var/log/lsalumni"
BACKUP_DIR="/var/www/lsalumni/backups"

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

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_failure() {
    echo -e "${RED}[FAILURE]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "校友入校登记系统 - 系统管理脚本"
    echo ""
    echo "用法: $0 <命令> [选项]"
    echo ""
    echo "基本命令:"
    echo "  start           启动整个系统"
    echo "  stop            停止整个系统"
    echo "  restart         重启整个系统"
    echo "  status          查看系统状态"
    echo "  logs            查看系统日志"
    echo "  health          健康检查"
    echo ""
    echo "服务管理:"
    echo "  start-app       仅启动应用服务"
    echo "  stop-app        仅停止应用服务"
    echo "  restart-app     仅重启应用服务"
    echo "  start-web       仅启动Web服务"
    echo "  stop-web        仅停止Web服务"
    echo "  restart-web     仅重启Web服务"
    echo "  start-db        仅启动数据库"
    echo "  stop-db         仅停止数据库"
    echo "  restart-db      仅重启数据库"
    echo ""
    echo "维护命令:"
    echo "  backup          备份数据库"
    echo "  restore <file>  恢复数据库"
    echo "  clean           清理日志和临时文件"
    echo "  update          更新系统和应用"
    echo "  monitor         实时监控系统"
    echo ""
    echo "配置:"
    echo "  --config        显示系统配置"
    echo "  --version       显示版本信息"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start                    # 启动整个系统"
    echo "  $0 restart-app              # 重启应用服务"
    echo "  $0 logs --follow            # 实时查看日志"
    echo "  $0 backup                   # 备份数据库"
    echo "  $0 restore backup_file.sql  # 恢复数据库"
    echo ""
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要以root权限运行"
        exit 1
    fi
}

# 检查系统是否已安装
check_system_installed() {
    if [[ ! -d "$DEPLOY_PATH" ]]; then
        log_error "系统未安装，请先运行部署脚本"
        exit 1
    fi
}

# 获取服务状态
get_service_status() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}运行中${NC}"
    elif systemctl is-enabled --quiet "$service"; then
        echo -e "${YELLOW}已启用但未运行${NC}"
    else
        echo -e "${RED}未启用${NC}"
    fi
}

# 获取端口状态
get_port_status() {
    local port=$1
    local service=$2

    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        local pid=$(netstat -tlnp 2>/dev/null | grep ":$port " | head -1 | awk '{print $7}' | cut -d'/' -f1)
        if [[ -n "$pid" ]] && [[ -d "/proc/$pid" ]]; then
            local process=$(ps -p "$pid" -o comm= 2>/dev/null)
            echo -e "${GREEN}监听中 ($process)${NC}"
        else
            echo -e "${GREEN}监听中${NC}"
        fi
    else
        echo -e "${RED}未监听${NC}"
    fi
}

# 启动应用服务
start_application() {
    log_step "启动应用服务..."

    # 检查虚拟环境
    if [[ ! -d "$DEPLOY_PATH/venv" ]]; then
        log_error "Python虚拟环境不存在"
        return 1
    fi

    # 启动systemd服务
    systemctl start "$SERVICE_NAME"
    systemctl enable "$SERVICE_NAME"

    # 等待服务启动
    sleep 3

    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "应用服务启动成功"
    else
        log_failure "应用服务启动失败"
        return 1
    fi
}

# 停止应用服务
stop_application() {
    log_step "停止应用服务..."

    systemctl stop "$SERVICE_NAME"

    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_failure "应用服务停止失败"
        return 1
    else
        log_success "应用服务已停止"
    fi
}

# 启动Web服务
start_web() {
    log_step "启动Web服务..."

    systemctl start "$NGINX_SERVICE"
    systemctl enable "$NGINX_SERVICE"

    sleep 2

    if systemctl is-active --quiet "$NGINX_SERVICE"; then
        log_success "Web服务启动成功"
    else
        log_failure "Web服务启动失败"
        return 1
    fi
}

# 停止Web服务
stop_web() {
    log_step "停止Web服务..."

    systemctl stop "$NGINX_SERVICE"

    if systemctl is-active --quiet "$NGINX_SERVICE"; then
        log_failure "Web服务停止失败"
        return 1
    else
        log_success "Web服务已停止"
    fi
}

# 启动数据库
start_database() {
    log_step "启动数据库服务..."

    systemctl start "$MYSQL_SERVICE"
    systemctl enable "$MYSQL_SERVICE"

    sleep 3

    if systemctl is-active --quiet "$MYSQL_SERVICE"; then
        log_success "数据库服务启动成功"
    else
        log_failure "数据库服务启动失败"
        return 1
    fi
}

# 停止数据库
stop_database() {
    log_step "停止数据库服务..."

    systemctl stop "$MYSQL_SERVICE"

    if systemctl is-active --quiet "$MYSQL_SERVICE"; then
        log_failure "数据库服务停止失败"
        return 1
    else
        log_success "数据库服务已停止"
    fi
}

# 启动整个系统
start_system() {
    echo "=============================================="
    echo "校友入校登记系统 - 启动系统"
    echo "=============================================="
    echo ""

    # 按顺序启动服务
    start_database
    start_application
    start_web

    echo ""
    echo "=============================================="
    log_success "系统启动完成！"
    echo "=============================================="
}

# 停止整个系统
stop_system() {
    echo "=============================================="
    echo "校友入校登记系统 - 停止系统"
    echo "=============================================="
    echo ""

    # 按相反顺序停止服务
    stop_web
    stop_application
    stop_database

    echo ""
    echo "=============================================="
    log_success "系统已停止！"
    echo "=============================================="
}

# 重启整个系统
restart_system() {
    echo "=============================================="
    echo "校友入校登记系统 - 重启系统"
    echo "=============================================="
    echo ""

    stop_system
    sleep 2
    start_system
}

# 显示系统状态
show_status() {
    echo "=============================================="
    echo "校友入校登记系统 - 系统状态"
    echo "=============================================="
    echo ""

    # 服务状态
    echo -e "${CYAN}服务状态:${NC}"
    printf "  %-20s %s\n" "应用服务" "$(get_service_status $SERVICE_NAME)"
    printf "  %-20s %s\n" "Web服务" "$(get_service_status $NGINX_SERVICE)"
    printf "  %-20s %s\n" "数据库服务" "$(get_service_status $MYSQL_SERVICE)"
    echo ""

    # 端口状态
    echo -e "${CYAN}端口状态:${NC}"
    printf "  %-20s %s\n" "HTTP (80)" "$(get_port_status 80 nginx)"
    printf "  %-20s %s\n" "HTTPS (443)" "$(get_port_status 443 nginx)"
    printf "  %-20s %s\n" "应用 (5000)" "$(get_port_status 5000 gunicorn)"
    printf "  %-20s %s\n" "MySQL (3306)" "$(get_port_status 3306 mysqld)"
    echo ""

    # 系统资源
    echo -e "${CYAN}系统资源:${NC}"
    echo "  CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "  内存使用: $(free -h | grep '^Mem:' | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
    echo "  磁盘使用: $(df -h / | tail -1 | awk '{print $5}')"
    echo "  系统负载: $(uptime | awk -F'load average:' '{print $2}' | xargs)"
    echo ""

    # 应用信息
    echo -e "${CYAN}应用信息:${NC}"
    if [[ -f "$DEPLOY_PATH/backend/app/__init__.py" ]]; then
        echo "  应用路径: $DEPLOY_PATH"
        echo "  配置文件: $DEPLOY_PATH/config/database.conf"
    else
        echo "  应用状态: 未安装"
    fi
    echo ""

    # 最近错误
    echo -e "${CYAN}最近错误 (最近10条):${NC}"
    if [[ -f "/var/log/nginx/lsalumni_error.log" ]]; then
        tail -10 /var/log/nginx/lsalumni_error.log | grep -i error || echo "  无错误记录"
    else
        echo "  无错误日志文件"
    fi
}

# 查看日志
show_logs() {
    local follow=false
    local lines=50

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--follow)
                follow=true
                shift
                ;;
            -n|--lines)
                lines="$2"
                shift 2
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done

    echo "=============================================="
    echo "校友入校登记系统 - 系统日志"
    echo "=============================================="
    echo ""

    # 应用服务日志
    echo -e "${CYAN}应用服务日志:${NC}"
    if $follow; then
        journalctl -u "$SERVICE_NAME" -f
    else
        journalctl -u "$SERVICE_NAME" -n "$lines"
    fi
}

# 健康检查
health_check() {
    echo "=============================================="
    echo "校友入校登记系统 - 健康检查"
    echo "=============================================="
    echo ""

    local errors=0

    # 检查服务状态
    echo -e "${CYAN}检查服务状态...${NC}"
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        log_error "应用服务未运行"
        ((errors++))
    fi

    if ! systemctl is-active --quiet "$NGINX_SERVICE"; then
        log_error "Web服务未运行"
        ((errors++))
    fi

    if ! systemctl is-active --quiet "$MYSQL_SERVICE"; then
        log_error "数据库服务未运行"
        ((errors++))
    fi

    # 检查端口监听
    echo -e "${CYAN}检查端口监听...${NC}"
    if ! netstat -tlnp | grep -q ":5000 "; then
        log_error "应用端口5000未监听"
        ((errors++))
    fi

    if ! netstat -tlnp | grep -q ":80 "; then
        log_error "HTTP端口80未监听"
        ((errors++))
    fi

    # 检查文件系统
    echo -e "${CYAN}检查文件系统...${NC}"
    if [[ ! -d "$DEPLOY_PATH" ]]; then
        log_error "应用目录不存在: $DEPLOY_PATH"
        ((errors++))
    fi

    if [[ ! -f "$DEPLOY_PATH/config/database.conf" ]]; then
        log_error "数据库配置文件不存在"
        ((errors++))
    fi

    # 检查数据库连接
    echo -e "${CYAN}检查数据库连接...${NC}"
    if [[ -f "$DEPLOY_PATH/config/database.conf" ]]; then
        source "$DEPLOY_PATH/config/database.conf"
        if mysql -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT 1;" >/dev/null 2>&1; then
            log_info "数据库连接正常"
        else
            log_error "数据库连接失败"
            ((errors++))
        fi
    fi

    # 检查应用响应
    echo -e "${CYAN}检查应用响应...${NC}"
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/health | grep -q "200"; then
        log_info "应用健康检查通过"
    else
        log_error "应用健康检查失败"
        ((errors++))
    fi

    # 显示结果
    echo ""
    if [[ $errors -eq 0 ]]; then
        echo "=============================================="
        log_success "🎉 系统健康检查通过！"
        echo "=============================================="
    else
        echo "=============================================="
        log_failure "❌ 发现 $errors 个健康问题"
        echo "=============================================="
        return 1
    fi
}

# 备份数据库
backup_database() {
    log_step "备份数据库..."

    if [[ ! -f "$DEPLOY_PATH/scripts/backup_database.sh" ]]; then
        log_error "数据库备份脚本不存在"
        return 1
    fi

    bash "$DEPLOY_PATH/scripts/backup_database.sh"
    log_success "数据库备份完成"
}

# 恢复数据库
restore_database() {
    if [[ $# -eq 0 ]]; then
        log_error "请指定备份文件"
        echo "用法: $0 restore <backup_file>"
        return 1
    fi

    local backup_file="$1"

    if [[ ! -f "$backup_file" ]]; then
        log_error "备份文件不存在: $backup_file"
        return 1
    fi

    log_step "恢复数据库从: $backup_file"

    if [[ ! -f "$DEPLOY_PATH/scripts/restore_database.sh" ]]; then
        log_error "数据库恢复脚本不存在"
        return 1
    fi

    bash "$DEPLOY_PATH/scripts/restore_database.sh" "$backup_file"
    log_success "数据库恢复完成"
}

# 清理系统
clean_system() {
    log_step "清理系统..."

    # 清理日志文件
    echo "清理日志文件..."
    find /var/log -name "*.log.*" -mtime +30 -delete
    find "$LOG_DIR" -name "*.log.*" -mtime +7 -delete

    # 清理临时文件
    echo "清理临时文件..."
    find /tmp -name "lsalumni_*" -mtime +1 -delete

    # 清理备份文件
    echo "清理旧备份文件..."
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

    # 清理Docker镜像（如果使用）
    if command -v docker &> /dev/null; then
        echo "清理Docker资源..."
        docker system prune -f
    fi

    log_success "系统清理完成"
}

# 更新系统
update_system() {
    log_step "更新系统..."

    # 更新系统包
    echo "更新系统包..."
    apt update && apt upgrade -y

    # 更新Python依赖
    if [[ -d "$DEPLOY_PATH/venv" ]]; then
        echo "更新Python依赖..."
        source "$DEPLOY_PATH/venv/bin/activate"
        pip install --upgrade -r "$DEPLOY_PATH/requirements_prod.txt"
    fi

    # 重启服务
    restart_system

    log_success "系统更新完成"
}

# 实时监控
monitor_system() {
    echo "=============================================="
    echo "校友入校登记系统 - 实时监控"
    echo "=============================================="
    echo "按 Ctrl+C 退出监控"
    echo ""

    while true; do
        clear
        show_status
        echo ""
        echo -e "${CYAN}最后更新: $(date)${NC}"
        echo -e "${CYAN}按 Ctrl+C 退出监控${NC}"
        sleep 5
    done
}

# 显示系统配置
show_config() {
    echo "=============================================="
    echo "校友入校登记系统 - 系统配置"
    echo "=============================================="
    echo ""

    if [[ -f "$DEPLOY_PATH/config/database.conf" ]]; then
        echo -e "${CYAN}数据库配置:${NC}"
        source "$DEPLOY_PATH/config/database.conf"
        echo "  主机: $DB_HOST"
        echo "  端口: $DB_PORT"
        echo "  数据库: $DB_NAME"
        echo "  用户: $DB_USER"
        echo ""
    fi

    echo -e "${CYAN}路径配置:${NC}"
    echo "  应用路径: $DEPLOY_PATH"
    echo "  日志路径: $LOG_DIR"
    echo "  备份路径: $BACKUP_DIR"
    echo ""

    echo -e "${CYAN}服务配置:${NC}"
    echo "  应用服务: $SERVICE_NAME"
    echo "  Web服务: $NGINX_SERVICE"
    echo "  数据库服务: $MYSQL_SERVICE"
    echo ""
}

# 显示版本信息
show_version() {
    echo "=============================================="
    echo "校友入校登记系统 - 版本信息"
    echo "=============================================="
    echo ""

    echo -e "${CYAN}系统版本:${NC}"
    if [[ -f "$DEPLOY_PATH/backend/app/__init__.py" ]]; then
        source "$DEPLOY_PATH/venv/bin/activate"
        python -c "
import sys
sys.path.append('$DEPLOY_PATH/backend')
from app import create_app
app = create_app()
print(f'  应用版本: {app.config.get(\"VERSION\", \"unknown\")}')
" 2>/dev/null || echo "  应用版本: unknown"
    fi

    echo -e "${CYAN}软件版本:${NC}"
    echo "  操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "  内核: $(uname -r)"
    echo "  Python: $(python3 --version 2>/dev/null || echo 'Not installed')"
    echo "  Nginx: $(nginx -v 2>&1 | cut -d'/' -f2 || echo 'Not installed')"
    echo "  MySQL: $(mysql --version 2>/dev/null || echo 'Not installed')"
    echo ""
}

# 主函数
main() {
    # 检查root权限
    check_root

    # 检查系统是否已安装
    check_system_installed

    # 解析命令
    case "${1:-help}" in
        start)
            start_system
            ;;
        stop)
            stop_system
            ;;
        restart)
            restart_system
            ;;
        status)
            show_status
            ;;
        logs)
            shift
            show_logs "$@"
            ;;
        health)
            health_check
            ;;
        start-app)
            start_application
            ;;
        stop-app)
            stop_application
            ;;
        restart-app)
            stop_application
            sleep 2
            start_application
            ;;
        start-web)
            start_web
            ;;
        stop-web)
            stop_web
            ;;
        restart-web)
            stop_web
            sleep 2
            start_web
            ;;
        start-db)
            start_database
            ;;
        stop-db)
            stop_database
            ;;
        restart-db)
            stop_database
            sleep 2
            start_database
            ;;
        backup)
            backup_database
            ;;
        restore)
            shift
            restore_database "$@"
            ;;
        clean)
            clean_system
            ;;
        update)
            update_system
            ;;
        monitor)
            monitor_system
            ;;
        --config)
            show_config
            ;;
        --version)
            show_version
            ;;
        --help|help)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"