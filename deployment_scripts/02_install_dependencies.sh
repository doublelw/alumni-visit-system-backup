#!/bin/bash

# =============================================================================
# 校友入校登记系统 - 依赖环境安装脚本
# 功能: 安装Python、Node.js、Nginx等运行环境
# 使用: sudo bash 02_install_dependencies.sh
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 版本配置
PYTHON_VERSION="3.11"
NODE_VERSION="18"
NGINX_VERSION="1.24.0"

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
    echo "校友入校登记系统 - 依赖环境安装脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --python-version VERSION    Python版本 (默认: 3.11)"
    echo "  --node-version VERSION      Node.js版本 (默认: 18)"
    echo "  --nginx-version VERSION     Nginx版本 (默认: 1.24.0)"
    echo "  --skip-python               跳过Python安装"
    echo "  --skip-node                 跳过Node.js安装"
    echo "  --skip-nginx                跳过Nginx安装"
    echo "  --skip-ssl                  跳过SSL工具安装"
    echo "  --help                      显示此帮助信息"
    echo ""
}

# 解析命令行参数
SKIP_PYTHON=false
SKIP_NODE=false
SKIP_NGINX=false
SKIP_SSL=false

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --python-version)
                PYTHON_VERSION="$2"
                shift 2
                ;;
            --node-version)
                NODE_VERSION="$2"
                shift 2
                ;;
            --nginx-version)
                NGINX_VERSION="$2"
                shift 2
                ;;
            --skip-python)
                SKIP_PYTHON=true
                shift
                ;;
            --skip-node)
                SKIP_NODE=true
                shift
                ;;
            --skip-nginx)
                SKIP_NGINX=true
                shift
                ;;
            --skip-ssl)
                SKIP_SSL=true
                shift
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

# 安装Python 3.11
install_python() {
    if [[ "$SKIP_PYTHON" == true ]]; then
        log_warn "跳过Python安装"
        return
    fi

    log_step "安装Python $PYTHON_VERSION..."

    case $OS in
        "Ubuntu"|"Debian"*)
            # 更新包列表
            apt update

            # 检查是否有可用的Python版本
            if apt-cache show python$PYTHON_VERSION >/dev/null 2>&1; then
                apt install -y python$PYTHON_VERSION python$PYTHON_VERSION-venv python$PYTHON_VERSION-dev python$PYTHON_VERSION-distutils
            else
                # 使用deadsnakes PPA
                apt install -y software-properties-common
                add-apt-repository ppa:deadsnakes/ppa -y
                apt update
                apt install -y python$PYTHON_VERSION python$PYTHON_VERSION-venv python$PYTHON_VERSION-dev python$PYTHON_VERSION-distutils
            fi

            # 安装pip
            if ! command -v pip3 &> /dev/null; then
                apt install -y python3-pip
            fi

            # 升级pip
            python$PYTHON_VERSION -m pip install --upgrade pip

            ;;
        "CentOS"*|"Red Hat"*)
            # 安装EPEL仓库
            yum install -y epel-release

            # 安装Python开发工具
            yum groupinstall -y "Development Tools"
            yum install -y gcc gcc-c++ make zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel xz-devel libffi-devel

            # 下载并编译Python
            cd /tmp
            wget https://www.python.org/ftp/python/$PYTHON_VERSION.0/Python-$PYTHON_VERSION.0.tgz
            tar xzf Python-$PYTHON_VERSION.0.tgz
            cd Python-$PYTHON_VERSION.0
            ./configure --enable-optimizations
            make altinstall

            # 安装pip
            python$PYTHON_VERSION -m ensurepip --upgrade
            ;;
        *)
            log_error "不支持的系统: $OS"
            exit 1
            ;;
    esac

    # 验证安装
    if command -v python$PYTHON_VERSION &> /dev/null; then
        PYTHON_VERSION_FULL=$(python$PYTHON_VERSION --version)
        log_info "Python安装成功: $PYTHON_VERSION_FULL"
    else
        log_error "Python安装失败"
        exit 1
    fi
}

# 安装Node.js
install_nodejs() {
    if [[ "$SKIP_NODE" == true ]]; then
        log_warn "跳过Node.js安装"
        return
    fi

    log_step "安装Node.js $NODE_VERSION..."

    # 使用NodeSource仓库安装
    if [[ "$NODE_VERSION" == "18" ]]; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    elif [[ "$NODE_VERSION" == "20" ]]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    else
        log_error "不支持的Node.js版本: $NODE_VERSION"
        exit 1
    fi

    # 安装Node.js
    apt install -y nodejs

    # 验证安装
    if command -v node &> /dev/null; then
        NODE_VERSION_FULL=$(node --version)
        NPM_VERSION_FULL=$(npm --version)
        log_info "Node.js安装成功: $NODE_VERSION_FULL"
        log_info "npm安装成功: $NPM_VERSION_FULL"
    else
        log_error "Node.js安装失败"
        exit 1
    fi

    # 配置npm镜像源（可选）
    npm config set registry https://registry.npmmirror.com/
    log_info "npm镜像源设置为: https://registry.npmmirror.com/"
}

# 安装Nginx
install_nginx() {
    if [[ "$SKIP_NGINX" == true ]]; then
        log_warn "跳过Nginx安装"
        return
    fi

    log_step "安装Nginx..."

    case $OS in
        "Ubuntu"|"Debian"*)
            apt install -y nginx
            ;;
        "CentOS"*|"Red Hat"*)
            yum install -y nginx
            ;;
        *)
            log_error "不支持的系统: $OS"
            exit 1
            ;;
    esac

    # 启动并启用Nginx
    systemctl start nginx
    systemctl enable nginx

    # 验证安装
    if systemctl is-active --quiet nginx; then
        NGINX_VERSION_FULL=$(nginx -v 2>&1)
        log_info "Nginx安装成功: $NGINX_VERSION_FULL"
    else
        log_error "Nginx安装失败"
        exit 1
    fi

    # 配置防火墙
    if command -v ufw &> /dev/null; then
        ufw allow 'Nginx Full'
        log_info "防火墙已配置Nginx访问"
    fi
}

# 安装SSL证书工具
install_ssl_tools() {
    if [[ "$SKIP_SSL" == true ]]; then
        log_warn "跳过SSL工具安装"
        return
    fi

    log_step "安装SSL证书工具..."

    # 安装Certbot
    apt install -y certbot python3-certbot-nginx

    # 验证安装
    if command -v certbot &> /dev/null; then
        CERTBOT_VERSION=$(certbot --version)
        log_info "Certbot安装成功: $CERTBOT_VERSION"
    else
        log_error "Certbot安装失败"
        exit 1
    fi
}

# 安装额外的系统工具
install_extra_tools() {
    log_step "安装额外的系统工具..."

    # 安装常用工具
    apt install -y \
        git \
        curl \
        wget \
        unzip \
        htop \
        tree \
        vim \
        supervisor \
        cron \
        logrotate \
        bc \
        jq \
        net-tools \
        iotop

    # 安装构建工具
    apt install -y \
        build-essential \
        pkg-config \
        libssl-dev \
        libffi-dev \
        libjpeg-dev \
        libpng-dev \
        libwebp-dev

    log_info "额外工具安装完成"
}

# 安装Python包管理工具
install_python_tools() {
    log_step "安装Python包管理工具..."

    # 安装虚拟环境工具
    python$PYTHON_VERSION -m pip install --upgrade virtualenv

    # 安装常用的Python包
    python$PYTHON_VERSION -m pip install --upgrade \
        setuptools \
        wheel \
        pip

    log_info "Python工具安装完成"
}

# 配置系统环境
configure_environment() {
    log_step "配置系统环境..."

    # 设置默认Python版本
    update-alternatives --install /usr/bin/python python /usr/bin/python$PYTHON_VERSION 1
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python$PYTHON_VERSION 1

    # 设置默认pip版本
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

    # 创建Python符号链接
    if [[ ! -L /usr/bin/python3 ]]; then
        ln -sf /usr/bin/python$PYTHON_VERSION /usr/bin/python3
    fi

    log_info "系统环境配置完成"
}

# 创建应用用户环境
setup_app_environment() {
    log_step "配置应用用户环境..."

    # 确保应用用户存在
    if ! id "lsalumni" &>/dev/null; then
        useradd -m -s /bin/bash lsalumni
    fi

    # 创建用户目录
    mkdir -p /home/lsalumni/.local/bin
    chown -R lsalumni:lsalumni /home/lsalumni

    # 添加用户环境变量
    cat >> /home/lsalumni/.bashrc << 'EOF'

# LS Alumni System Environment
export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH="/var/www/lsalumni/backend:$PYTHONPATH"
export FLASK_ENV="production"
EOF

    log_info "应用用户环境配置完成"
}

# 验证安装
verify_installation() {
    log_step "验证安装..."

    local errors=0

    # 检查Python
    if command -v python$PYTHON_VERSION &> /dev/null; then
        log_info "✅ Python $PYTHON_VERSION 可用"
    else
        log_error "❌ Python $PYTHON_VERSION 不可用"
        ((errors++))
    fi

    # 检查Node.js
    if command -v node &> /dev/null; then
        log_info "✅ Node.js 可用"
    else
        log_error "❌ Node.js 不可用"
        ((errors++))
    fi

    # 检查Nginx
    if systemctl is-active --quiet nginx; then
        log_info "✅ Nginx 运行中"
    else
        log_error "❌ Nginx 未运行"
        ((errors++))
    fi

    # 检查Certbot
    if command -v certbot &> /dev/null; then
        log_info "✅ Certbot 可用"
    else
        log_error "❌ Certbot 不可用"
        ((errors++))
    fi

    if [[ $errors -eq 0 ]]; then
        log_info "🎉 所有依赖安装验证通过！"
    else
        log_error "❌ 发现 $errors 个错误，请检查安装"
        exit 1
    fi
}

# 显示安装摘要
show_installation_summary() {
    echo ""
    echo "=============================================="
    log_info "依赖环境安装完成！"
    echo "=============================================="
    echo ""
    echo "已安装的软件版本:"
    if command -v python$PYTHON_VERSION &> /dev/null; then
        echo "  Python: $(python$PYTHON_VERSION --version)"
    fi
    if command -v node &> /dev/null; then
        echo "  Node.js: $(node --version)"
        echo "  npm: $(npm --version)"
    fi
    if command -v nginx &> /dev/null; then
        echo "  Nginx: $(nginx -v 2>&1)"
    fi
    if command -v certbot &> /dev/null; then
        echo "  Certbot: $(certbot --version)"
    fi
    echo ""
    echo "配置文件位置:"
    echo "  Nginx: /etc/nginx/"
    echo "  用户环境: /home/lsalumni/.bashrc"
    echo ""
    echo "下一步操作:"
    echo "1. 运行 03_database_setup.sh 配置数据库"
    echo "2. 运行 04_deploy_application.sh 部署应用"
    echo ""
}

# 主函数
main() {
    echo "=============================================="
    echo "校友入校登记系统 - 依赖环境安装脚本"
    echo "=============================================="
    echo ""

    # 检查root权限
    check_root

    # 解析命令行参数
    parse_arguments "$@"

    # 检测系统类型
    detect_system

    # 更新系统包
    log_step "更新系统包..."
    apt update && apt upgrade -y

    # 安装各种依赖
    install_python
    install_nodejs
    install_nginx
    install_ssl_tools
    install_extra_tools
    install_python_tools
    configure_environment
    setup_app_environment

    # 验证安装
    verify_installation

    # 显示摘要
    show_installation_summary
}

# 执行主函数
main "$@"