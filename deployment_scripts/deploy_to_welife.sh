#!/bin/bash

# =============================================================================
# 微信云托管部署脚本
# 功能: 准备并打包项目用于微信云托管部署
# 使用: bash deployment_scripts/deploy_to_welife.sh
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
PROJECT_NAME="lsalumni"
PACKAGE_NAME="welife_deploy_package"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUILD_DIR="build"
PACKAGE_FILE="${PACKAGE_NAME}_${TIMESTAMP}.zip"

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

# 显示横幅
show_banner() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "    微信云托管部署准备脚本"
    echo "=============================================="
    echo -e "${NC}"
    echo ""
}

# 检查必要的文件
check_required_files() {
    log_step "检查必要的文件..."

    local required_files=(
        "app.py"
        "wsgi.py"
        "Dockerfile"
        "requirements.txt"
        "backend/app/__init__.py"
        "backend/app/config.py"
        "frontend/templates"
        "frontend/static"
    )

    local missing_files=()

    for file in "${required_files[@]}"; do
        if [[ ! -e "$file" ]]; then
            missing_files+=("$file")
        fi
    done

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "缺少必要的文件:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi

    log_success "所有必要文件检查通过"
}

# 清理构建目录
clean_build_dir() {
    log_step "清理构建目录..."

    if [[ -d "$BUILD_DIR" ]]; then
        rm -rf "$BUILD_DIR"
    fi

    mkdir -p "$BUILD_DIR"
    log_success "构建目录已清理"
}

# 复制项目文件
copy_project_files() {
    log_step "复制项目文件..."

    # 复制核心文件
    cp app.py wsgi.py requirements.txt Dockerfile .dockerignore "$BUILD_DIR/"

    # 复制backend目录
    cp -r backend "$BUILD_DIR/"

    # 复制frontend目录
    cp -r frontend "$BUILD_DIR/"

    # 复制配置文件（如果存在）
    if [[ -f ".env.welife" ]]; then
        cp .env.welife "$BUILD_DIR/.env"
        log_info "已复制环境变量配置"
    else
        log_warn "未找到.env.welife文件，请在微信云托管控制台配置环境变量"
    fi

    # 复制初始化脚本（如果存在）
    if [[ -d "backend/scripts" ]]; then
        mkdir -p "$BUILD_DIR/backend/scripts"
        cp -r backend/scripts/* "$BUILD_DIR/backend/scripts/" 2>/dev/null || true
    fi

    # 创建必要的目录
    mkdir -p "$BUILD_DIR/uploads"
    mkdir -p "$BUILD_DIR/logs"
    mkdir -p "$BUILD_DIR/instance"

    log_success "项目文件复制完成"
}

# 清理不需要的文件
cleanup_unnecessary_files() {
    log_step "清理不需要的文件..."

    cd "$BUILD_DIR"

    # 删除测试文件
    find . -type f -name "*_test.py" -delete
    find . -type f -name "test_*.py" -delete
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".git" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type f -name ".DS_Store" -delete

    # 删除本地数据库文件
    find . -type f -name "*.db" -delete
    find . -type f -name "*.db-journal" -delete

    cd ..
    log_success "清理完成"
}

# 创建部署包
create_package() {
    log_step "创建部署包..."

    cd "$BUILD_DIR"
    zip -r "../$PACKAGE_FILE" . > /dev/null
    cd ..

    log_success "部署包创建完成: $PACKAGE_FILE"

    # 显示文件大小
    local size=$(du -h "$PACKAGE_FILE" | cut -f1)
    log_info "包大小: $size"
}

# 生成部署说明
generate_deployment_guide() {
    log_step "生成部署说明..."

    local guide_file="${PACKAGE_NAME}_README_${TIMESTAMP}.md"

    cat > "$guide_file" << 'EOF'
# 微信云托管部署说明

## 📦 部署包信息

- **包名称**: PACKAGE_FILE
- **创建时间**: TIMESTAMP
- **项目名称**: 校友入校登记系统

## 🚀 部署步骤

### 方式一：上传代码包部署

1. **登录微信公众平台**
   - 访问: https://mp.weixin.qq.com/
   - 进入"开发" → "云托管"

2. **创建服务**
   - 点击"新建服务"
   - 服务名称: `lsalumni-api`
   - 服务描述: `校友入校登记系统后端API`

3. **上传代码**
   - 选择"本地上传"
   - 上传部署包: `PACKAGE_FILE`

4. **配置环境变量**

   在"环境变量"部分添加以下配置:

   ```bash
   # 基础配置
   FLASK_APP=app.py
   FLASK_ENV=production
   SECRET_KEY=your-production-secret-key

   # 数据库配置（重要！）
   # 使用腾讯云MySQL或微信云数据库
   DATABASE_URL=mysql+pymysql://用户名:密码@主机:端口/数据库名

   # JWT配置
   JWT_SECRET_KEY=your-jwt-secret-key
   JWT_ACCESS_TOKEN_EXPIRES=86400

   # 其他配置
   WECHAT_CLOUD=true
   ELECTRONIC_CARD_SECRET_KEY=your-card-secret
   HMAC_SECRET_KEY=your-hmac-secret
   ```

5. **配置云数据库（推荐）**

   方式A - 使用微信云数据库:
   - 在云托管控制台开通"云数据库"
   - 创建MySQL实例
   - 获取数据库连接信息并填写到DATABASE_URL

   方式B - 使用腾讯云MySQL:
   - 在腾讯云控制台创建云数据库MySQL
   - 设置白名单允许微信云托管访问
   - 填写连接信息到DATABASE_URL

6. **启动服务**
   - 点击"部署"
   - 等待部署完成（通常需要2-5分钟）

### 方式二：使用Git仓库部署（推荐）

1. **推送代码到Git仓库**
   ```bash
   git add .
   git commit -m "准备微信云托管部署"
   git push origin main
   ```

2. **在云托管控制台**
   - 选择"从仓库导入"
   - 授权Git账号
   - 选择项目和分支
   - 配置环境变量（同上）

3. **开启自动部署**
   - 启用"自动部署"
   - 代码推送后自动触发部署

## 🔧 环境变量说明

### 必须配置的变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| DATABASE_URL | 数据库连接字符串 | mysql+pymysql://user:pass@host:3306/db |
| SECRET_KEY | Flask密钥 | 随机字符串 |
| JWT_SECRET_KEY | JWT令牌密钥 | 随机字符串 |

### 可选配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| REDIS_HOST | Redis主机 | localhost |
| REDIS_PORT | Redis端口 | 6379 |
| CACHE_ENABLED | 启用缓存 | true |
| UPLOAD_FOLDER | 上传目录 | /app/uploads |

## ✅ 部署验证

部署完成后，访问以下地址验证:

- **健康检查**: `https://your-service.welife.icu/api/health`
- **主页**: `https://your-service.welife.icu/`
- **API文档**: 查看项目README.md

## 📊 监控和日志

### 查看日志
- 云托管控制台 → 服务 → 日志

### 监控指标
- CPU使用率
- 内存使用率
- 请求响应时间
- 错误率

### 告警配置
- 建议配置CPU使用率>80%告警
- 建议配置错误率>5%告警

## 🔄 更新部署

### 自动更新（Git仓库方式）
```bash
git add .
git commit -m "更新功能"
git push origin main
# 云托管会自动部署最新代码
```

### 手动更新（上传代码包方式）
1. 构建新的部署包
2. 在云托管控制台上传新包
3. 点击"部署"

## 🆘 常见问题

### 1. 数据库连接失败
**原因**: 数据库连接信息错误或白名单未配置
**解决**:
- 检查DATABASE_URL格式
- 确认数据库白名单包含微信云托管IP段
- 测试数据库连接

### 2. 500错误
**原因**: 应用代码错误或配置问题
**解决**:
- 查看云托管日志
- 检查环境变量是否正确
- 验证数据库连接

### 3. 服务启动超时
**原因**: 依赖安装失败或数据库连接慢
**解决**:
- 优化requirements.txt
- 调整数据库连接池配置
- 增加健康检查超时时间

## 📞 技术支持

如遇问题，请检查:
1. 云托管控制台的错误日志
2. 环境变量是否正确配置
3. 数据库是否可访问
4. Dockerfile是否正确

---
*部署包生成时间: TIMESTAMP*
EOF

    # 替换变量
    sed -i "s/PACKAGE_FILE/$PACKAGE_FILE/g" "$guide_file"
    sed -i "s/TIMESTAMP/$TIMESTAMP/g" "$guide_file"

    log_success "部署说明已生成: $guide_file"
}

# 显示部署清单
show_deployment_checklist() {
    echo ""
    echo -e "${CYAN}=============================================="
    echo "    部署前检查清单"
    echo "==============================================${NC}"
    echo ""
    echo -e "${YELLOW}□ 数据库准备${NC}"
    echo "  □ 已创建腾讯云MySQL或微信云数据库"
    echo "  □ 已获取数据库连接信息"
    echo "  □ 已配置数据库白名单"
    echo ""
    echo -e "${YELLOW}□ 环境变量准备${NC}"
    echo "  □ 已生成SECRET_KEY"
    echo "  □ 已生成JWT_SECRET_KEY"
    echo "  □ 已填写DATABASE_URL"
    echo ""
    echo -e "${YELLOW}□ 微信公众平台配置${NC}"
    echo "  □ 已开通云托管服务"
    echo "  □ 已创建服务"
    echo ""
    echo -e "${YELLOW}□ 部署包${NC}"
    echo "  □ 部署包: $PACKAGE_FILE"
    echo "  □ 部署说明: ${PACKAGE_NAME}_README_${TIMESTAMP}.md"
    echo ""
}

# 显示部署指引
show_deployment_guide() {
    echo ""
    echo -e "${CYAN}=============================================="
    echo "    下一步操作指引"
    echo "==============================================${NC}"
    echo ""
    echo -e "${GREEN}1. 登录微信公众平台${NC}"
    echo "   https://mp.weixin.qq.com/"
    echo ""
    echo -e "${GREEN}2. 进入云托管控制台${NC}"
    echo "   开发 → 云托管 → 新建服务"
    echo ""
    echo -e "${GREEN}3. 上传部署包${NC}"
    echo "   选择: $PACKAGE_FILE"
    echo ""
    echo -e "${GREEN}4. 配置环境变量${NC}"
    echo "   参考部署说明文档"
    echo ""
    echo -e "${GREEN}5. 启动服务${NC}"
    echo "   点击部署并等待完成"
    echo ""
}

# 主函数
main() {
    # 显示横幅
    show_banner

    # 执行部署步骤
    log_step "开始准备微信云托管部署包..."

    check_required_files
    clean_build_dir
    copy_project_files
    cleanup_unnecessary_files
    create_package
    generate_deployment_guide

    # 显示清单和指引
    show_deployment_checklist
    show_deployment_guide

    echo ""
    log_success "✅ 部署包准备完成！"
    echo ""
    log_info "部署包文件: $PACKAGE_FILE"
    log_info "部署说明文档: ${PACKAGE_NAME}_README_${TIMESTAMP}.md"
    echo ""
    log_warn "⚠️  请先完成'部署前检查清单'中的所有项目后再进行部署"
    echo ""
}

# 执行主函数
main
