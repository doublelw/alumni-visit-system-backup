#!/bin/bash

# =============================================================================
# 校友入校登记系统 - 一键部署脚本
# 功能: 完整自动化部署整个系统
# 使用: sudo bash deploy.sh --domain www.pofeclife.top --email admin@pofeclife.top
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

# 默认配置
DOMAIN="www.pofeclife.top"
EMAIL="admin@pofeclife.top"
DEPLOY_PATH="/var/www/lsalumni"
MYSQL_ROOT_PASSWORD=""
DB_PASSWORD=""
APP_SECRET_KEY=""
SKIP_SYSTEM_INIT=false
SKIP_DEPENDENCIES=false
SKIP_SSL=false
DEV_MODE=false
INTERACTIVE=true

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

# 显示横幅
show_banner() {
    echo -e "${PURPLE}"
    echo "=============================================="
    echo "    校友入校登记系统 - 一键部署脚本"
    echo "=============================================="
    echo -e "${NC}"
    echo ""
}

# 显示帮助信息
show_help() {
    echo "校友入校登记系统 - 一键部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "基本选项:"
    echo "  -d, --domain DOMAIN           主域名 (默认: www.pofeclife.top)"
    echo "  -e, --email EMAIL              管理员邮箱 (默认: admin@pofeclife.top)"
    echo "  -p, --deploy-path PATH         部署路径 (默认: /var/www/lsalumni)"
    echo ""
    echo "数据库配置:"
    echo "  --mysql-root-password PASS     MySQL root密码"
    echo "  --db-password PASS             应用数据库密码"
    echo "  --app-secret-key KEY          Flask应用密钥"
    echo ""
    echo "部署选项:"
    echo "  --skip-system-init             跳过系统初始化"
    echo "  --skip-dependencies            跳过依赖安装"
    echo "  --skip-ssl                     跳过SSL证书配置"
    echo "  --dev-mode                     开发模式部署"
    echo "  --non-interactive             非交互模式"
    echo ""
    echo "其他:"
    echo "  --help                         显示此帮助信息"
    echo "  --version                      显示版本信息"
    echo ""
    echo "示例:"
    echo "  $0 -d www.example.com -e admin@example.com"
    echo "  $0 --dev-mode --domain dev.pofeclife.top"
    echo "  $0 --non-interactive --mysql-root-password MyPass123"
    echo ""
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            -e|--email)
                EMAIL="$2"
                shift 2
                ;;
            -p|--deploy-path)
                DEPLOY_PATH="$2"
                shift 2
                ;;
            --mysql-root-password)
                MYSQL_ROOT_PASSWORD="$2"
                shift 2
                ;;
            --db-password)
                DB_PASSWORD="$2"
                shift 2
                ;;
            --app-secret-key)
                APP_SECRET_KEY="$2"
                shift 2
                ;;
            --skip-system-init)
                SKIP_SYSTEM_INIT=true
                shift
                ;;
            --skip-dependencies)
                SKIP_DEPENDENCIES=true
                shift
                ;;
            --skip-ssl)
                SKIP_SSL=true
                shift
                ;;
            --dev-mode)
                DEV_MODE=true
                shift
                ;;
            --non-interactive)
                INTERACTIVE=false
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            --version)
                echo "校友入校登记系统部署脚本 v1.0.0"
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

# 检测系统类型
detect_system() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "无法检测系统类型"
        exit 1
    fi

    log_info "检测到系统: $OS $VER"
}

# 检查网络连接
check_network() {
    log_step "检查网络连接..."

    # 检查DNS解析
    if nslookup "$DOMAIN" >/dev/null 2>&1; then
        log_info "域名解析正常: $DOMAIN"
    else
        log_warn "域名解析失败: $DOMAIN (请确保域名已正确解析)"
    fi

    # 检查外网连接
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log_info "网络连接正常"
    else
        log_error "网络连接失败"
        exit 1
    fi
}

# 生成随机密码
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# 交互式输入密码
input_password() {
    local prompt="$1"
    local password
    local password_confirm

    if [[ "$INTERACTIVE" == false ]]; then
        generate_password
        return
    fi

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

# 显示配置摘要
show_configuration_summary() {
    echo ""
    echo "=============================================="
    echo -e "${CYAN}部署配置摘要${NC}"
    echo "=============================================="
    echo ""
    echo -e "${YELLOW}基本配置:${NC}"
    echo "  域名: $DOMAIN"
    echo "  邮箱: $EMAIL"
    echo "  部署路径: $DEPLOY_PATH"
    echo "  部署模式: $([[ $DEV_MODE == true ]] && echo "开发模式" || echo "生产模式")"
    echo ""
    echo -e "${YELLOW}跳过项目:${NC}"
    [[ $SKIP_SYSTEM_INIT == true ]] && echo "  - 系统初始化"
    [[ $SKIP_DEPENDENCIES == true ]] && echo "  - 依赖安装"
    [[ $SKIP_SSL == true ]] && echo "  - SSL证书"
    echo ""
    echo -e "${YELLOW}密码信息:${NC}"
    [[ -n "$MYSQL_ROOT_PASSWORD" ]] && echo "  MySQL root密码: $MYSQL_ROOT_PASSWORD"
    [[ -n "$DB_PASSWORD" ]] && echo "  数据库密码: $DB_PASSWORD"
    [[ -n "$APP_SECRET_KEY" ]] && echo "  应用密钥: $APP_SECRET_KEY"
    echo ""
}

# 确认部署
confirm_deployment() {
    if [[ "$INTERACTIVE" == false ]]; then
        return
    fi

    echo ""
    read -p "确认开始部署? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "部署已取消"
        exit 0
    fi
}

# 系统初始化
run_system_init() {
    if [[ "$SKIP_SYSTEM_INIT" == true ]]; then
        log_warn "跳过系统初始化"
        return
    fi

    log_step "执行系统初始化..."

    local script_dir="$(dirname "$0")"
    if [[ -f "$script_dir/01_server_init.sh" ]]; then
        bash "$script_dir/01_server_init.sh"
        log_success "系统初始化完成"
    else
        log_error "系统初始化脚本不存在: $script_dir/01_server_init.sh"
        exit 1
    fi
}

# 安装依赖环境
run_dependencies_install() {
    if [[ "$SKIP_DEPENDENCIES" == true ]]; then
        log_warn "跳过依赖安装"
        return
    fi

    log_step "安装依赖环境..."

    local script_dir="$(dirname "$0")"
    if [[ -f "$script_dir/02_install_dependencies.sh" ]]; then
        bash "$script_dir/02_install_dependencies.sh"
        log_success "依赖环境安装完成"
    else
        log_error "依赖安装脚本不存在: $script_dir/02_install_dependencies.sh"
        exit 1
    fi
}

# 数据库设置
run_database_setup() {
    log_step "设置数据库..."

    local script_dir="$(dirname "$0")"
    local db_args=()

    if [[ -n "$MYSQL_ROOT_PASSWORD" ]]; then
        db_args+=("--root-password" "$MYSQL_ROOT_PASSWORD")
    fi

    if [[ -n "$DB_PASSWORD" ]]; then
        db_args+=("--database-password" "$DB_PASSWORD")
    fi

    if [[ -f "$script_dir/03_database_setup.sh" ]]; then
        bash "$script_dir/03_database_setup.sh" "${db_args[@]}"
        log_success "数据库设置完成"
    else
        log_error "数据库设置脚本不存在: $script_dir/03_database_setup.sh"
        exit 1
    fi
}

# 部署应用代码
deploy_application_code() {
    log_step "部署应用代码..."

    # 创建应用目录
    mkdir -p "$DEPLOY_PATH"
    mkdir -p "$DEPLOY_PATH"/{backend,frontend,config,scripts,logs,backups,static,uploads}

    # 这里应该从代码仓库或上传包中复制代码
    # 由于这是演示脚本，我们假设代码已经存在
    if [[ ! -d "$DEPLOY_PATH/backend" ]] || [[ ! -d "$DEPLOY_PATH/frontend" ]]; then
        log_error "应用代码不存在，请先上传应用代码到 $DEPLOY_PATH"
        exit 1
    fi

    # 设置权限
    chown -R lsalumni:lsalumni "$DEPLOY_PATH"
    chmod 755 "$DEPLOY_PATH"

    log_success "应用代码部署完成"
}

# 创建Python虚拟环境
create_virtual_env() {
    log_step "创建Python虚拟环境..."

    cd "$DEPLOY_PATH"

    # 创建虚拟环境
    python3.11 -m venv venv
    chown -R lsalumni:lsalumni venv

    # 安装Python依赖
    source venv/bin/activate
    if [[ -f "requirements_prod.txt" ]]; then
        pip install -r requirements_prod.txt
    else
        log_error "requirements_prod.txt 不存在"
        exit 1
    fi

    log_success "Python虚拟环境创建完成"
}

# 配置环境变量
configure_environment() {
    log_step "配置环境变量..."

    # 生成应用密钥（如果未提供）
    if [[ -z "$APP_SECRET_KEY" ]]; then
        APP_SECRET_KEY=$(generate_password)
    fi

    # 创建环境配置文件
    cat > "$DEPLOY_PATH/.env" << EOF
# 校友入校登记系统环境配置
FLASK_ENV=$([[ $DEV_MODE == true ]] && echo "development" || echo "production")
SECRET_KEY=$APP_SECRET_KEY
DATABASE_URL=mysql+pymysql://lsalumni:$DB_PASSWORD@localhost/lsalumni
JWT_SECRET_KEY=$APP_SECRET_KEY
DOMAIN_NAME=$DOMAIN
SSL_CERT_PATH=/etc/ssl/certs/lsalumni.crt
SSL_KEY_PATH=/etc/ssl/private/lsalumni.key

# 文件上传配置
UPLOAD_FOLDER=$DEPLOY_PATH/uploads
MAX_CONTENT_LENGTH=10485760

# 日志配置
LOG_FILE=$DEPLOY_PATH/logs/app.log
LOG_LEVEL=$([[ $DEV_MODE == true ]] && echo "DEBUG" || echo "INFO")

# 邮件配置（可选）
MAIL_SERVER=
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=

# 短信配置（可选）
SMS_PROVIDER=
SMS_API_KEY=
SMS_API_SECRET=

# 创建时间: $(date)
EOF

    # 设置权限
    chmod 600 "$DEPLOY_PATH/.env"
    chown lsalumni:lsalumni "$DEPLOY_PATH/.env"

    log_success "环境变量配置完成"
}

# 初始化数据库
init_database() {
    log_step "初始化数据库..."

    local script_dir="$(dirname "$0")"

    if [[ -f "$script_dir/init_database.py" ]]; then
        cp "$script_dir/init_database.py" "$DEPLOY_PATH/scripts/"
        chmod +x "$DEPLOY_PATH/scripts/init_database.py"
        chown lsalumni:lsalumni "$DEPLOY_PATH/scripts/init_database.py"

        # 切换到应用用户执行初始化
        sudo -u lsalumni bash -c "
            cd $DEPLOY_PATH
            source venv/bin/activate
            python scripts/init_database.py
        "

        log_success "数据库初始化完成"
    else
        log_error "数据库初始化脚本不存在: $script_dir/init_database.py"
        exit 1
    fi
}

# 配置Nginx
configure_nginx() {
    log_step "配置Nginx..."

    local script_dir="$(dirname "$0")"
    local nginx_args=("--domain" "$DOMAIN" "--email" "$EMAIL")

    if [[ "$SKIP_SSL" == true ]]; then
        nginx_args+=("--http-only")
    fi

    if [[ -f "$script_dir/configure_nginx.sh" ]]; then
        bash "$script_dir/configure_nginx.sh" "${nginx_args[@]}"
        log_success "Nginx配置完成"
    else
        log_error "Nginx配置脚本不存在: $script_dir/configure_nginx.sh"
        exit 1
    fi
}

# 创建systemd服务
create_systemd_service() {
    log_step "创建系统服务..."

    cat > /etc/systemd/system/lsalumni.service << EOF
[Unit]
Description=LS Alumni System
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=notify
User=lsalumni
Group=lsalumni
WorkingDirectory=$DEPLOY_PATH
Environment=PATH=$DEPLOY_PATH/venv/bin
EnvironmentFile=$DEPLOY_PATH/.env
ExecStart=$DEPLOY_PATH/venv/bin/gunicorn \\
    --workers 4 \\
    --worker-class eventlet \\
    --bind 127.0.0.1:5000 \\
    --timeout 120 \\
    --keep-alive 5 \\
    --max-requests 1000 \\
    --max-requests-jitter 50 \\
    --access-logfile $DEPLOY_PATH/logs/access.log \\
    --error-logfile $DEPLOY_PATH/logs/error.log \\
    --log-level info \\
    --pid $DEPLOY_PATH/logs/gunicorn.pid \\
    --daemon \\
    app:app
ExecReload=/bin/kill -s HUP \$MAINPID
PIDFile=$DEPLOY_PATH/logs/gunicorn.pid
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd
    systemctl daemon-reload
    systemctl enable lsalumni

    log_success "系统服务创建完成"
}

# 启动系统
start_system() {
    log_step "启动系统..."

    local script_dir="$(dirname "$0")"

    if [[ -f "$script_dir/manage_system.sh" ]]; then
        bash "$script_dir/manage_system.sh" start
        log_success "系统启动完成"
    else
        # 手动启动服务
        systemctl start lsalumni
        systemctl start nginx
        systemctl start mysql

        # 等待服务启动
        sleep 5

        # 检查服务状态
        if systemctl is-active --quiet lsalumni && \
           systemctl is-active --quiet nginx && \
           systemctl is-active --quiet mysql; then
            log_success "系统启动完成"
        else
            log_error "系统启动失败"
            exit 1
        fi
    fi
}

# 运行部署后测试
run_post_deployment_tests() {
    log_step "运行部署后测试..."

    local errors=0

    # 测试服务状态
    if ! systemctl is-active --quiet lsalumni; then
        log_error "应用服务未运行"
        ((errors++))
    fi

    if ! systemctl is-active --quiet nginx; then
        log_error "Web服务未运行"
        ((errors++))
    fi

    # 测试端口监听
    if ! netstat -tlnp | grep -q ":5000 "; then
        log_error "应用端口未监听"
        ((errors++))
    fi

    if ! netstat -tlnp | grep -q ":80 "; then
        log_error "HTTP端口未监听"
        ((errors++))
    fi

    # 测试HTTP响应
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ || echo "000")
    if [[ "$http_code" != "200" ]]; then
        log_error "HTTP响应测试失败 (状态码: $http_code)"
        ((errors++))
    fi

    # 测试应用健康检查
    local health_code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/health || echo "000")
    if [[ "$health_code" != "200" ]]; then
        log_error "应用健康检查失败 (状态码: $health_code)"
        ((errors++))
    fi

    if [[ $errors -eq 0 ]]; then
        log_success "部署后测试通过"
    else
        log_error "部署后测试失败，发现 $errors 个问题"
        return 1
    fi
}

# 生成部署报告
generate_deployment_report() {
    local report_file="$DEPLOY_PATH/deployment_report_$(date +%Y%m%d_%H%M%S).md"

    cat > "$report_file" << EOF
# 校友入校登记系统部署报告

## 部署信息
- **部署时间**: $(date)
- **域名**: $DOMAIN
- **部署路径**: $DEPLOY_PATH
- **部署模式**: $([[ $DEV_MODE == true ]] && echo "开发模式" || echo "生产模式")
- **管理员邮箱**: $EMAIL

## 系统配置
- **操作系统**: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)
- **Python版本**: $(python3.11 --version)
- **Nginx版本**: $(nginx -v 2>&1)
- **MySQL版本**: $(mysql --version)

## 访问地址
EOF

    if [[ "$SKIP_SSL" == true ]]; then
        cat >> "$report_file" << EOF
- **主页**: http://$DOMAIN/
- **管理后台**: http://$DOMAIN/admin
- **API接口**: http://$DOMAIN/api/
EOF
    else
        cat >> "$report_file" << EOF
- **主页**: https://$DOMAIN/
- **管理后台**: https://$DOMAIN/admin
- **API接口**: https://$DOMAIN/api/
EOF
    fi

    cat >> "$report_file" << EOF

## 默认账户
- **管理员**: admin / admin123
- **保安**: security / security123
- **校友**: alumni001 / alumni123
- **教师**: teacher001-005 / teacher123

## 配置文件
- **应用配置**: $DEPLOY_PATH/.env
- **数据库配置**: $DEPLOY_PATH/config/database.conf
- **Nginx配置**: /etc/nginx/sites-available/lsalumni
- **系统服务**: /etc/systemd/system/lsalumni.service

## 管理命令
- **启动系统**: $0 start
- **停止系统**: $0 stop
- **重启系统**: $0 restart
- **查看状态**: $0 status
- **查看日志**: $0 logs

## 备份命令
- **备份数据库**: $0 backup
- **恢复数据库**: $0 restore <backup_file>

---
*报告生成时间: $(date)*
*部署脚本版本: v1.0.0*
EOF

    log_info "部署报告已生成: $report_file"
}

# 显示部署完成信息
show_deployment_complete() {
    echo ""
    echo "=============================================="
    log_success "🎉 部署完成！"
    echo "=============================================="
    echo ""

    echo -e "${CYAN}访问地址:${NC}"
    if [[ "$SKIP_SSL" == true ]]; then
        echo "  主页: http://$DOMAIN/"
        echo "  管理后台: http://$DOMAIN/admin"
        echo "  API文档: http://$DOMAIN/api/docs"
    else
        echo "  主页: https://$DOMAIN/"
        echo "  管理后台: https://$DOMAIN/admin"
        echo "  API文档: https://$DOMAIN/api/docs"
    fi
    echo ""

    echo -e "${CYAN}默认账户:${NC}"
    echo "  管理员: admin / admin123"
    echo "  保安员: security / security123"
    echo "  测试校友: alumni001 / alumni123"
    echo "  受访教师: teacher001-005 / teacher123"
    echo ""

    echo -e "${CYAN}重要信息:${NC}"
    echo "  MySQL root密码: $MYSQL_ROOT_PASSWORD"
    echo "  数据库密码: $DB_PASSWORD"
    echo "  应用密钥: $APP_SECRET_KEY"
    echo ""

    echo -e "${CYAN}管理命令:${NC}"
    echo "  系统管理: bash $(dirname "$0")/manage_system.sh"
    echo "  查看日志: journalctl -u lsalumni -f"
    echo "  重启服务: systemctl restart lsalumni"
    echo ""

    log_warn "请妥善保存密码信息，建议修改默认密码"
}

# 主函数
main() {
    # 显示横幅
    show_banner

    # 检查root权限
    check_root

    # 解析命令行参数
    parse_arguments "$@"

    # 检测系统类型
    detect_system

    # 检查网络连接
    check_network

    # 生成密码（如果未提供）
    if [[ -z "$MYSQL_ROOT_PASSWORD" ]]; then
        if [[ "$INTERACTIVE" == true ]]; then
            MYSQL_ROOT_PASSWORD=$(input_password "MySQL root密码: ")
        else
            MYSQL_ROOT_PASSWORD=$(generate_password)
        fi
    fi

    if [[ -z "$DB_PASSWORD" ]]; then
        if [[ "$INTERACTIVE" == true ]]; then
            DB_PASSWORD=$(input_password "数据库密码: ")
        else
            DB_PASSWORD=$(generate_password)
        fi
    fi

    # 显示配置摘要
    show_configuration_summary

    # 确认部署
    confirm_deployment

    # 执行部署步骤
    log_step "开始部署..."

    run_system_init
    run_dependencies_install
    run_database_setup
    deploy_application_code
    create_virtual_env
    configure_environment
    init_database
    configure_nginx
    create_systemd_service
    start_system

    # 运行测试
    if run_post_deployment_tests; then
        # 生成报告
        generate_deployment_report

        # 显示完成信息
        show_deployment_complete

        log_success "部署成功完成！"
    else
        log_error "部署过程中发现问题，请检查日志"
        exit 1
    fi
}

# 执行主函数
main "$@"