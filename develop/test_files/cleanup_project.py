#!/usr/bin/env python3
"""
项目清理脚本 - 将测试和临时文件移动到develop目录
"""

import os
import shutil
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path("/d/Project/校友入校登记")

# 目标目录
DEVELOP_DIR = PROJECT_ROOT / "develop"
TEST_FILES_DIR = DEVELOP_DIR / "test_files"
REPORTS_DIR = DEVELOP_DIR / "reports"
SCREENSHOTS_DIR = DEVELOP_DIR / "screenshots"
BACKUPS_DIR = DEVELOP_DIR / "backups"
TEMP_FILES_DIR = DEVELOP_DIR / "temp_files"
LOGS_DIR = DEVELOP_DIR / "logs"
DATABASES_DIR = DEVELOP_DIR / "databases"


def move_file(src, dst_dir):
    """移动文件到目标目录"""
    if not src.exists():
        return False

    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name

    # 如果目标文件已存在，添加序号
    counter = 1
    while dst.exists():
        stem = src.stem
        suffix = src.suffix
        dst = dst_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    shutil.move(str(src), str(dst))
    print(f"✓ 移动: {src.name} -> {dst.relative_to(PROJECT_ROOT)}")
    return True


def move_directory(src, dst_dir):
    """移动目录到目标目录"""
    if not src.exists():
        return False

    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name

    # 如果目标目录已存在，添加序号
    counter = 1
    while dst.exists():
        dst = dst_dir / f"{src.name}_{counter}"
        counter += 1

    shutil.move(str(src), str(dst))
    print(f"✓ 移动目录: {src.name} -> {dst.relative_to(PROJECT_ROOT)}")
    return True


def cleanup_project():
    """执行项目清理"""
    print("=" * 60)
    print("开始清理项目文件...")
    print("=" * 60)

    # 1. 移动测试文件
    print("\n[1/7] 移动测试Python文件...")
    test_patterns = [
        "test_*.py",
        "check_*.py",
        "debug_*.py",
        "create_*.py",
        "e2e_*.py",
        "fix_*.py",
        "quick_*.py",
        "simple_*.py",
        "*_test.py",
        "add_*.py",
        "comprehensive_*.py",
        "delete_*.py",
        "manual_*.py",
        "migrate_*.py",
        "init_*.py",
        "run_*.py",
        "verify_*.py",
        "prepare_*.py",
        "cleanup_*.py",
        "clear_*.py",
        "reset_*.py",
        "establish_*.py",
        "import_*.py",
        "populate_*.py",
        "diagnose_*.py",
        "activate_*.py",
        "end_to_end_*.py",
        "performance_*.py",
        "final_*.py",
        "backfill_*.py"
    ]

    for pattern in test_patterns:
        for file in PROJECT_ROOT.glob(pattern):
            # 排除backend目录下的文件
            if "backend" not in str(file):
                move_file(file, TEST_FILES_DIR)

    # 移动backend目录下的测试文件
    backend_test_files = [
        "add_dining_companions_column.py",
        "add_special_approval_fields.py",
        "add_test_alumni.py",
        "add_wechat_field.py",
        "check_admin_user.py",
        "check_db_fields.py",
        "check_visit_applications.py",
        "cleanup_old_records.py",
        "create_admin_user.py",
        "create_key_history_table.py",
        "create_test_statistics_data.py",
        "debug_teacher_verify.py",
        "diagnose_hmac.py",
        "diagnose_user_mismatch.py",
        "external_network.py",
        "init_key_history.py",
        "instant_test_data.py",
        "modify_email_field.py",
        "populate_key_history_test.py",
        "quick_test_data.py",
        "remove_username_constraint.py",
        "remove_username_constraint_simple.py",
        "run_e2e_test.py",
        "show_visit_records.py",
        "simple_test_data.py"
    ]

    for filename in backend_test_files:
        file = PROJECT_ROOT / "backend" / filename
        if file.exists():
            move_file(file, TEST_FILES_DIR / "backend")

    # 2. 移动测试报告
    print("\n[2/7] 移动测试报告...")
    report_files = [
        "*_TEST_*.html",
        "*_TEST_*.md",
        "*test*.html",
        "*test*.md",
        "*REPORT*.html",
        "*REPORT*.md",
        "CHANGELOG_*.md",
        "KNOWLEDGE_BASE.md"
    ]

    for pattern in report_files:
        for file in PROJECT_ROOT.glob(pattern):
            move_file(file, REPORTS_DIR)

    # 3. 移动截图目录
    print("\n[3/7] 移动截图...")
    screenshot_dirs = [
        "screenshots",
        "e2e_screenshots_*",
        "test_screenshots*"
    ]

    for pattern in screenshot_dirs:
        for dir in PROJECT_ROOT.glob(pattern):
            move_directory(dir, SCREENSHOTS_DIR)

    # 移动单个图片文件
    image_files = [
        "check_*.png",
        "debug_*.png",
        "test*.png",
        "captcha.png"
    ]

    for pattern in image_files:
        for file in PROJECT_ROOT.glob(pattern):
            move_file(file, SCREENSHOTS_DIR)

    # 4. 移动备份文件
    print("\n[4/7] 移动备份文件...")
    backup_patterns = [
        "backup_*.tar.gz",
        "backup_*.bat",
        "backup_*.sh",
        "lsalumni_*.zip",
        "lsalumni_*.tar.gz",
        "*_package_*.zip"
    ]

    for pattern in backup_patterns:
        for file in PROJECT_ROOT.glob(pattern):
            move_file(file, BACKUPS_DIR)

    # 移动备份发布目录
    if (PROJECT_ROOT / "lsalumni_v1.1.0_release").exists():
        move_directory(PROJECT_ROOT / "lsalumni_v1.1.0_release", BACKUPS_DIR)

    # 5. 移动临时文件
    print("\n[5/7] 移动临时文件...")
    temp_patterns = [
        "*.db",
        "server.pid",
        "cookies.txt",
        "*.log",
        "template_preview.csv",
        "token_response.json",
        "test_output*.log",
        "test_final.log",
        "insert_test_code.sql",
        "debug_*.html",
        "debug_*.js",
        "debug_*.py",
        "test_*.html",
        "test_*.js",
        "logout_debug.js"
    ]

    for pattern in temp_patterns:
        for file in PROJECT_ROOT.glob(pattern):
            if "logs" not in str(file):  # 排除logs目录
                move_file(file, TEMP_FILES_DIR)

    # 移动日志文件到logs目录
    log_patterns = ["*.log"]
    for pattern in log_patterns:
        for file in PROJECT_ROOT.glob(pattern):
            if file.parent.name != "logs":  # 排除已在logs目录的文件
                move_file(file, LOGS_DIR)

    # 移动数据库文件
    db_patterns = ["*.db"]
    for pattern in db_patterns:
        for file in PROJECT_ROOT.glob(pattern):
            if "databases" not in str(file):
                move_file(file, DATABASES_DIR)

    # 6. 移动部署包
    print("\n[6/7] 移动部署包...")
    deployment_dirs = ["upload_package"]
    for dir_name in deployment_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            move_directory(dir_path, BACKUPS_DIR / "deployment_packages")

    # 7. 移动其他临时文件
    print("\n[7/7] 移动其他临时文件...")
    other_patterns = [
        "production_config.json",
        "test_requirements.txt",
        "delete_modules.py",
        "frontend\"",
        "gunicorn_config.py",
        "nginx_config.conf",
        "systemd_service.service",
        "setup_*.sql",
        "start.py",
        "comprehensive_api_test.py",
        "setup_production.py",
        "create_deployment_package.py"
    ]

    for pattern in other_patterns:
        for file in PROJECT_ROOT.glob(pattern):
            move_file(file, TEMP_FILES_DIR)

    print("\n" + "=" * 60)
    print("项目清理完成！")
    print("=" * 60)
    print(f"\n文件已移动到以下目录：")
    print(f"  - 测试文件: {TEST_FILES_DIR.relative_to(PROJECT_ROOT)}")
    print(f"  - 测试报告: {REPORTS_DIR.relative_to(PROJECT_ROOT)}")
    print(f"  - 截图: {SCREENSHOTS_DIR.relative_to(PROJECT_ROOT)}")
    print(f"  - 备份: {BACKUPS_DIR.relative_to(PROJECT_ROOT)}")
    print(f"  - 临时文件: {TEMP_FILES_DIR.relative_to(PROJECT_ROOT)}")
    print(f"  - 日志: {LOGS_DIR.relative_to(PROJECT_ROOT)}")
    print(f"  - 数据库: {DATABASES_DIR.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    # 确认操作
    print("警告：此操作将移动大量文件到develop目录！")
    print("建议先提交Git更改，或确保重要文件已备份。")
    print()

    response = input("确认继续？(y/n): ")
    if response.lower() == 'y':
        cleanup_project()
    else:
        print("操作已取消")
