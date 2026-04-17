#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校友入校登记系统 - 微信云托管自动部署检查
"""

import os
import sys
import zipfile
from pathlib import Path
from datetime import datetime

class Colors:
    """终端颜色"""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def log_info(msg):
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {msg}")

def log_warn(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def log_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

def log_step(msg):
    print(f"{Colors.BLUE}[STEP]{Colors.NC} {msg}")

def log_success(msg):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")

def show_banner():
    print(f"{Colors.CYAN}")
    print("=" * 70)
    print("校友入校登记系统 - 微信云托管自动部署检查")
    print("=" * 70)
    print(f"{Colors.NC}")
    print()

def check_deployment_package():
    """检查部署包"""
    log_step("检查部署包...")

    # 查找最新的部署包
    deploy_packages = list(Path(".").glob("welife_deploy_package_*.zip"))

    if not deploy_packages:
        log_error("未找到部署包")
        log_info("请运行: python deployment_scripts/deploy_to_welife.py")
        return None

    # 获取最新的部署包
    latest_package = max(deploy_packages, key=lambda p: p.stat().st_mtime)

    # 检查文件大小
    size = latest_package.stat().st_size
    size_mb = size / (1024 * 1024)

    # 验证ZIP文件
    try:
        with zipfile.ZipFile(latest_package, 'r') as zipf:
            files = zipf.namelist()
            log_success(f"部署包有效: {latest_package.name}")
            log_info(f"文件大小: {size_mb:.2f} MB")
            log_info(f"包含文件: {len(files)} 个")

            # 检查关键文件
            key_files = ['app.py', 'wsgi.py', 'Dockerfile', 'requirements.txt']
            missing_files = []
            for kf in key_files:
                if not any(kf in f for f in files):
                    missing_files.append(kf)

            if missing_files:
                log_warn(f"缺少关键文件: {', '.join(missing_files)}")
            else:
                log_success("所有关键文件都存在")

            return latest_package

    except zipfile.BadZipFile:
        log_error("部署包损坏")
        return None

def check_config_file():
    """检查配置文件"""
    log_step("检查配置文件...")

    config_file = Path("部署配置-微信云托管.txt")

    if not config_file.exists():
        log_error("配置文件不存在")
        log_info("将自动生成配置文件...")
        return create_config_file()

    log_success(f"配置文件已存在: {config_file.name}")
    return config_file

def create_config_file():
    """创建配置文件"""
    import subprocess

    log_info("正在生成安全密钥...")

    # 生成密钥
    keys = {}
    try:
        keys['SECRET_KEY'] = subprocess.check_output(['openssl', 'rand', '-base64', '32']).decode().strip()
        keys['JWT_SECRET_KEY'] = subprocess.check_output(['openssl', 'rand', '-base64', '32']).decode().strip()
        keys['ELECTRONIC_CARD_SECRET_KEY'] = subprocess.check_output(['openssl', 'rand', '-base64', '32']).decode().strip()
        keys['HMAC_SECRET_KEY'] = subprocess.check_output(['openssl', 'rand', '-base64', '32']).decode().strip()
    except:
        # 如果openssl不可用，使用Python生成
        import secrets
        keys['SECRET_KEY'] = secrets.token_urlsafe(32)
        keys['JWT_SECRET_KEY'] = secrets.token_urlsafe(32)
        keys['ELECTRONIC_CARD_SECRET_KEY'] = secrets.token_urlsafe(32)
        keys['HMAC_SECRET_KEY'] = secrets.token_urlsafe(32)

    # 查找部署包
    deploy_packages = list(Path(".").glob("welife_deploy_package_*.zip"))
    if deploy_packages:
        latest_package = max(deploy_packages, key=lambda p: p.stat().st_mtime)
        package_name = latest_package.name
        package_size = latest_package.stat().st_size / (1024 * 1024)
    else:
        package_name = "请先运行部署脚本生成部署包"
        package_size = 0

    # 创建配置内容
    config_content = f"""# 微信云托管部署配置
# 文件生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}

==========================================
📦 部署包信息
==========================================
部署包文件: {package_name}
部署包大小: {package_size:.2f} MB
部署包位置: {Path.cwd()}\\

==========================================
🔑 环境变量配置（复制到微信云托管）
==========================================

# 基础配置
FLASK_APP=app.py
FLASK_ENV=production
WECHAT_CLOUD=true

# 数据库配置（测试阶段使用SQLite，正式环境建议改用腾讯云MySQL）
DATABASE_URL=sqlite:///alumni_system.db

# 安全密钥（已自动生成）
SECRET_KEY={keys['SECRET_KEY']}
JWT_SECRET_KEY={keys['JWT_SECRET_KEY']}
ELECTRONIC_CARD_SECRET_KEY={keys['ELECTRONIC_CARD_SECRET_KEY']}
HMAC_SECRET_KEY={keys['HMAC_SECRET_KEY']}

==========================================
📋 部署操作步骤
==========================================

步骤1: 登录微信云托管
- 访问: https://cloud.weixin.qq.com/cloudrun/service
- 如果未登录，使用微信扫码登录

步骤2: 创建新服务
- 点击 "新建服务" 按钮
- 填写服务信息:
  * 服务名称: lsalumni-api
  * 服务简介: 校友入校登记系统API
  * 部署方式: 选择 "本地上传代码包"

步骤3: 上传部署包
- 点击 "选择文件"
- 选择: {Path.cwd()}\\{package_name}
- 等待上传完成

步骤4: 配置环境变量
- 点击 "环境变量" 标签
- 点击 "添加变量"
- 将上面的环境变量逐一复制粘贴进去

步骤5: 部署配置
- 版本描述: v1.0.0 - 初始部署
- 实例规格: 选择 1C 2G（基础版）
- 实例数量: 1个
- 点击 "开始部署"

步骤6: 等待部署完成
- 部署过程约需 2-5 分钟
- 看到 "部署成功" 提示即为完成

步骤7: 获取访问地址
- 复制服务访问地址，格式类似:
  https://lsalumni-xxx.welife.icu

步骤8: 验证部署
- 访问健康检查: https://你的服务地址.welife.icu/api/health
- 访问主页: https://你的服务地址.welife.icu/

==========================================
⚠️  重要提示
==========================================

1. 数据库配置:
   - 当前使用SQLite，适合测试
   - 正式环境建议改用腾讯云MySQL
   - 修改 DATABASE_URL 为: mysql+pymysql://user:pass@host:port/db

2. 安全密钥:
   - 已自动生成随机密钥
   - 请妥善保管，不要泄露

3. 域名配置:
   - 微信云托管提供默认域名
   - 可在服务管理中配置自定义域名

4. 监控和维护:
   - 在微信云托管控制台查看日志
   - 在服务管理中监控运行状态
   - 更新代码后重新打包上传

==========================================
📞 技术支持
==========================================

部署问题检查清单:
✅ 部署包是否正确上传
✅ 环境变量是否全部配置
✅ 服务状态是否显示"运行中"
✅ 健康检查接口是否返回正常

如遇问题，请查看:
- 微信云托管控制台 → 服务日志
- 部署配置 → 环境变量
- 服务管理 → 运行状态
"""

    # 写入配置文件
    config_file = Path("部署配置-微信云托管.txt")
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)

    log_success(f"配置文件已创建: {config_file.name}")
    return config_file

def generate_deployment_summary(package, config):
    """生成部署摘要"""
    print()
    print("=" * 70)
    print("[SUCCESS] 部署准备完成！")
    print("=" * 70)
    print()

    print("[INFO] 部署包信息:")
    print(f"   文件名: {package.name}")
    print(f"   位置: {package.absolute()}")
    print(f"   大小: {package.stat().st_size / (1024 * 1024):.2f} MB")
    print()

    print("[INFO] 配置文件:")
    print(f"   文件名: {config.name}")
    print(f"   位置: {config.absolute()}")
    print()

    print("[INFO] 下一步操作:")
    print()
    print("1. 双击运行: 一键部署准备.bat")
    print("   (会自动打开配置文件和微信云托管控制台)")
    print()
    print("2. 在微信云托管控制台:")
    print("   - 点击 '新建服务'")
    print("   - 上传部署包")
    print("   - 配置环境变量（从配置文件复制）")
    print("   - 开始部署")
    print()
    print("3. 部署完成后，验证服务:")
    print("   - 访问: https://你的服务地址.welife.icu/api/health")
    print("   - 访问: https://你的服务地址.welife.icu/")
    print()

    print("[INFO] 提示:")
    print("   - 所有配置信息都在配置文件中")
    print("   - 部署过程约需 2-5 分钟")
    print("   - 遇到问题请查看微信云托管控制台日志")
    print()

def main():
    """主函数"""
    try:
        # 显示横幅
        show_banner()

        # 执行检查
        log_step("开始检查部署准备情况...")
        print()

        # 检查部署包
        package = check_deployment_package()
        if not package:
            return

        print()

        # 检查配置文件
        config = check_config_file()
        if not config:
            return

        print()

        # 生成部署摘要
        log_success("所有检查通过！")
        generate_deployment_summary(package, config)

        # 询问是否打开配置文件
        print("是否打开配置文件？(Y/n): ", end='')
        choice = input().strip().lower()

        if choice != 'n':
            import os
            os.startfile(config.absolute())
            log_info("已打开配置文件")

        # 询问是否打开微信云托管
        print("是否打开微信云托管控制台？(Y/n): ", end='')
        choice = input().strip().lower()

        if choice != 'n':
            import webbrowser
            webbrowser.open("https://cloud.weixin.qq.com/cloudrun/service")
            log_info("已打开微信云托管控制台")

    except KeyboardInterrupt:
        print()
        log_warn("操作已取消")
        sys.exit(1)
    except Exception as e:
        print()
        log_error(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
