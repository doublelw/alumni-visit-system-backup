"""
数据库备份管理API
支持增量备份、恢复到指定日期、定时自动备份
"""

import os
import json
import sqlite3
import shutil
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
import threading
import schedule

backup_bp = Blueprint('backup', __name__)

# 备份配置
BACKUP_DIR = '/var/backups/lsalumni'
BACKUP_SETTINGS_FILE = os.path.join(BACKUP_DIR, 'backup_settings.json')

class DatabaseBackup:
    def __init__(self):
        self.ensure_backup_dir()
        self.load_settings()

    def ensure_backup_dir(self):
        """确保备份目录存在"""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR, exist_ok=True)

    def load_settings(self):
        """加载备份设置"""
        default_settings = {
            'maxBackupFiles': 10,
            'backupPath': BACKUP_DIR,
            'autoBackup': True,
            'backupTime': '02:00',
            'incrementalBackup': True,
            'fullBackupInterval': 7  # 每7天一次完整备份
        }

        try:
            if os.path.exists(BACKUP_SETTINGS_FILE):
                with open(BACKUP_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # 合并默认设置，确保所有字段都存在
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    self.settings = settings
            else:
                self.settings = default_settings
                self.save_settings()
        except Exception as e:
            current_app.logger.error(f"加载备份设置失败: {str(e)}")
            self.settings = default_settings

    def save_settings(self):
        """保存备份设置"""
        try:
            with open(BACKUP_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            current_app.logger.error(f"保存备份设置失败: {str(e)}")

    def get_database_path(self):
        """获取数据库文件路径"""
        # 从应用配置获取数据库路径
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite:///'):
            return db_uri.replace('sqlite:///', '')
        return '/var/www/lsalumni/instance/app.db'

    def create_full_backup(self, backup_name=None):
        """创建完整备份"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f'full_backup_{timestamp}.db'

            backup_path = os.path.join(BACKUP_DIR, backup_name)
            db_path = self.get_database_path()

            # 复制数据库文件
            shutil.copy2(db_path, backup_path)

            # 记录备份信息
            backup_info = {
                'type': 'full',
                'filename': backup_name,
                'created_at': datetime.now().isoformat(),
                'size': os.path.getsize(backup_path),
                'base_backup': None
            }

            self.save_backup_info(backup_info)
            current_app.logger.info(f"完整备份创建成功: {backup_name}")

            return {
                'success': True,
                'filename': backup_name,
                'path': backup_path,
                'size': backup_info['size']
            }

        except Exception as e:
            current_app.logger.error(f"创建完整备份失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def create_incremental_backup(self, backup_name=None):
        """创建增量备份"""
        try:
            # 获取最后一次备份信息
            last_backup = self.get_last_backup()

            if not last_backup:
                # 如果没有备份记录，创建完整备份
                return self.create_full_backup()

            # 检查是否需要完整备份（超过配置的间隔天数）
            days_since_full = (datetime.now() - datetime.fromisoformat(last_backup['created_at'])).days
            if days_since_full >= self.settings.get('fullBackupInterval', 7) or last_backup['type'] == 'incremental':
                return self.create_full_backup()

            if not backup_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f'incremental_backup_{timestamp}.db'

            backup_path = os.path.join(BACKUP_DIR, backup_name)
            base_backup_path = os.path.join(BACKUP_DIR, last_backup['filename'])

            # 获取当前数据库路径
            current_db_path = self.get_database_path()

            # 使用SQLite的VACUUM INTO创建增量备份
            conn = sqlite3.connect(current_db_path)
            try:
                conn.execute(f'VACUUM INTO "{backup_path}"')
                conn.commit()
            finally:
                conn.close()

            # 记录备份信息
            backup_info = {
                'type': 'incremental',
                'filename': backup_name,
                'created_at': datetime.now().isoformat(),
                'size': os.path.getsize(backup_path),
                'base_backup': last_backup['filename']
            }

            self.save_backup_info(backup_info)
            current_app.logger.info(f"增量备份创建成功: {backup_name}")

            return {
                'success': True,
                'filename': backup_name,
                'path': backup_path,
                'size': backup_info['size']
            }

        except Exception as e:
            current_app.logger.error(f"创建增量备份失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def restore_from_backup(self, backup_filename, target_date=None):
        """从备份恢复数据库"""
        try:
            backup_path = os.path.join(BACKUP_DIR, backup_filename)
            if not os.path.exists(backup_path):
                return {'success': False, 'error': '备份文件不存在'}

            # 读取备份信息
            backup_info = self.get_backup_info(backup_filename)
            if not backup_info:
                return {'success': False, 'error': '无法读取备份信息'}

            # 如果指定了目标日期，需要找到合适的备份链
            if target_date:
                result = self.find_backup_chain_for_date(target_date)
                if not result['success']:
                    return result
                backup_path = result['backup_path']

            # 创建当前数据库的备份
            current_db_path = self.get_database_path()
            emergency_backup = os.path.join(BACKUP_DIR, f'emergency_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
            shutil.copy2(current_db_path, emergency_backup)

            try:
                # 恢复数据库
                shutil.copy2(backup_path, current_db_path)
                current_app.logger.info(f"数据库恢复成功: {backup_filename}")

                return {
                    'success': True,
                    'message': f'已成功恢复到备份: {backup_filename}',
                    'emergency_backup': emergency_backup
                }

            except Exception as restore_error:
                # 如果恢复失败，恢复紧急备份
                shutil.copy2(emergency_backup, current_db_path)
                return {'success': False, 'error': f'恢复失败，已回滚: {str(restore_error)}'}

        except Exception as e:
            current_app.logger.error(f"恢复数据库失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def find_backup_chain_for_date(self, target_date):
        """找到指定日期的备份链"""
        try:
            target_dt = datetime.fromisoformat(target_date) if isinstance(target_date, str) else target_date
            backup_history = self.get_backup_history()

            # 按创建时间倒序排列
            backup_history.sort(key=lambda x: x['created_at'], reverse=True)

            # 找到最接近目标日期的备份
            for backup in backup_history:
                backup_dt = datetime.fromisoformat(backup['created_at'])
                if backup_dt <= target_dt:
                    return {
                        'success': True,
                        'backup': backup,
                        'backup_path': os.path.join(BACKUP_DIR, backup['filename'])
                    }

            return {'success': False, 'error': f'未找到 {target_date} 或之前的备份'}

        except Exception as e:
            return {'success': False, 'error': f'查找备份失败: {str(e)}'}

    def get_backup_history(self):
        """获取备份历史"""
        try:
            history_file = os.path.join(BACKUP_DIR, 'backup_history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            current_app.logger.error(f"获取备份历史失败: {str(e)}")
            return []

    def save_backup_info(self, backup_info):
        """保存备份信息"""
        try:
            history = self.get_backup_history()
            history.append(backup_info)

            # 限制历史记录数量
            max_history = self.settings.get('maxBackupFiles', 10) * 2
            if len(history) > max_history:
                history = history[-max_history:]

            history_file = os.path.join(BACKUP_DIR, 'backup_history.json')
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

            # 清理旧文件
            self.cleanup_old_backups()

        except Exception as e:
            current_app.logger.error(f"保存备份信息失败: {str(e)}")

    def get_backup_info(self, backup_filename):
        """获取指定备份的信息"""
        history = self.get_backup_history()
        for backup in history:
            if backup['filename'] == backup_filename:
                return backup
        return None

    def get_last_backup(self):
        """获取最后一次备份"""
        history = self.get_backup_history()
        if history:
            # 按创建时间倒序排列，返回最新的
            history.sort(key=lambda x: x['created_at'], reverse=True)
            return history[0]
        return None

    def cleanup_old_backups(self):
        """清理旧的备份文件"""
        try:
            history = self.get_backup_history()
            max_files = self.settings.get('maxBackupFiles', 10)

            if len(history) > max_files:
                # 按创建时间排序，保留最新的
                history.sort(key=lambda x: x['created_at'])
                to_delete = history[:-max_files]

                for backup in to_delete:
                    backup_path = os.path.join(BACKUP_DIR, backup['filename'])
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                        current_app.logger.info(f"删除旧备份: {backup['filename']}")

                # 更新历史记录
                remaining_history = history[-max_files:]
                history_file = os.path.join(BACKUP_DIR, 'backup_history.json')
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(remaining_history, f, ensure_ascii=False, indent=2)

        except Exception as e:
            current_app.logger.error(f"清理旧备份失败: {str(e)}")

# 全局备份实例
backup_manager = DatabaseBackup()

def schedule_auto_backup():
    """调度自动备份"""
    if backup_manager.settings.get('autoBackup', True):
        backup_time = backup_manager.settings.get('backupTime', '02:00')
        schedule.every().day.at(backup_time).do(auto_backup_task)
        current_app.logger.info(f"已设置自动备份时间: {backup_time}")

def auto_backup_task():
    """自动备份任务"""
    try:
        if backup_manager.settings.get('incrementalBackup', True):
            result = backup_manager.create_incremental_backup()
        else:
            result = backup_manager.create_full_backup()

        if result['success']:
            current_app.logger.info(f"自动备份成功: {result['filename']}")
        else:
            current_app.logger.error(f"自动备份失败: {result['error']}")

    except Exception as e:
        current_app.logger.error(f"自动备份任务执行失败: {str(e)}")

# 启动调度器
def start_scheduler():
    """启动调度器"""
    schedule_auto_backup()

    def run_schedule():
        while True:
            schedule.run_pending()
            import time
            time.sleep(60)  # 每分钟检查一次

    # 在后台线程中运行调度器
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()
    current_app.logger.info("自动备份调度器已启动")

@backup_bp.route('/settings', methods=['GET'])
def get_backup_settings():
    """获取备份设置"""
    return jsonify({
        'success': True,
        'settings': backup_manager.settings
    })

@backup_bp.route('/settings', methods=['POST'])
def update_backup_settings():
    """更新备份设置"""
    try:
        data = request.get_json()

        # 验证设置
        valid_fields = ['maxBackupFiles', 'backupPath', 'autoBackup', 'backupTime', 'incrementalBackup', 'fullBackupInterval']
        for key in data:
            if key not in valid_fields:
                return jsonify({'success': False, 'message': f'无效的设置项: {key}'})

        # 更新设置
        backup_manager.settings.update(data)
        backup_manager.save_settings()

        # 重新调度自动备份
        schedule.clear()
        schedule_auto_backup()

        return jsonify({
            'success': True,
            'message': '设置更新成功',
            'settings': backup_manager.settings
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'更新设置失败: {str(e)}'})

@backup_bp.route('/server', methods=['POST'])
def create_server_backup():
    """创建服务器备份"""
    try:
        data = request.get_json() or {}
        backup_type = data.get('type', 'auto')  # auto, full, incremental

        if backup_type == 'full':
            result = backup_manager.create_full_backup()
        elif backup_type == 'incremental':
            result = backup_manager.create_incremental_backup()
        else:  # auto
            if backup_manager.settings.get('incrementalBackup', True):
                result = backup_manager.create_incremental_backup()
            else:
                result = backup_manager.create_full_backup()

        if result['success']:
            return jsonify({
                'success': True,
                'message': f'服务器备份成功: {result["filename"]}',
                'backup': result
            })
        else:
            return jsonify({
                'success': False,
                'message': f'服务器备份失败: {result["error"]}'
            })

    except Exception as e:
        current_app.logger.error(f"服务器备份失败: {str(e)}")
        return jsonify({'success': False, 'message': f'备份失败: {str(e)}'})

@backup_bp.route('/download', methods=['POST'])
def download_backup():
    """生成并下载备份文件"""
    try:
        data = request.get_json() or {}
        backup_type = data.get('type', 'auto')  # auto, full, incremental

        # 创建备份
        if backup_type == 'full':
            result = backup_manager.create_full_backup()
        elif backup_type == 'incremental':
            result = backup_manager.create_incremental_backup()
        else:  # auto
            if backup_manager.settings.get('incrementalBackup', True):
                result = backup_manager.create_incremental_backup()
            else:
                result = backup_manager.create_full_backup()

        if not result['success']:
            return jsonify({
                'success': False,
                'message': f'创建备份失败: {result["error"]}'
            })

        # 返回下载信息
        return jsonify({
            'success': True,
            'message': '备份文件已准备就绪',
            'download_url': f'/admin/backup/download_file/{result["filename"]}',
            'filename': result['filename'],
            'size': result['size']
        })

    except Exception as e:
        current_app.logger.error(f"下载备份失败: {str(e)}")
        return jsonify({'success': False, 'message': f'下载备份失败: {str(e)}'})

@backup_bp.route('/download_file/<filename>', methods=['GET'])
def download_backup_file(filename):
    """下载指定的备份文件"""
    try:
        safe_filename = secure_filename(filename)
        backup_path = os.path.join(BACKUP_DIR, safe_filename)

        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'message': '备份文件不存在'}), 404

        return send_file(
            backup_path,
            as_attachment=True,
            download_name=safe_filename,
            mimetype='application/x-sqlite3'
        )

    except Exception as e:
        current_app.logger.error(f"下载备份文件失败: {str(e)}")
        return jsonify({'success': False, 'message': f'下载失败: {str(e)}'})

@backup_bp.route('/dual', methods=['POST'])
def create_dual_backup():
    """创建双重备份（服务器+本地下载）"""
    try:
        data = request.get_json() or {}
        backup_type = data.get('type', 'auto')

        # 创建服务器备份
        if backup_type == 'full':
            server_result = backup_manager.create_full_backup()
        elif backup_type == 'incremental':
            server_result = backup_manager.create_incremental_backup()
        else:  # auto
            if backup_manager.settings.get('incrementalBackup', True):
                server_result = backup_manager.create_incremental_backup()
            else:
                server_result = backup_manager.create_full_backup()

        if not server_result['success']:
            return jsonify({
                'success': False,
                'message': f'服务器备份失败: {server_result["error"]}'
            })

        # 返回双重备份结果
        return jsonify({
            'success': True,
            'message': '双重备份创建成功',
            'server_backup': {
                'success': True,
                'filename': server_result['filename'],
                'size': server_result['size']
            },
            'download_info': {
                'download_url': f'/admin/backup/download_file/{server_result["filename"]}',
                'filename': server_result['filename'],
                'size': server_result['size']
            }
        })

    except Exception as e:
        current_app.logger.error(f"双重备份失败: {str(e)}")
        return jsonify({'success': False, 'message': f'双重备份失败: {str(e)}'})

@backup_bp.route('/restore', methods=['POST'])
def restore_database():
    """恢复数据库"""
    try:
        data = request.get_json()
        backup_filename = data.get('filename')
        target_date = data.get('targetDate')

        if not backup_filename and not target_date:
            return jsonify({'success': False, 'message': '请指定备份文件或目标日期'})

        if backup_filename:
            result = backup_manager.restore_from_backup(backup_filename)
        else:
            result = backup_manager.restore_from_backup(None, target_date)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'success': False, 'message': result['error']})

    except Exception as e:
        current_app.logger.error(f"恢复数据库失败: {str(e)}")
        return jsonify({'success': False, 'message': f'恢复失败: {str(e)}'})

@backup_bp.route('/history', methods=['GET'])
def get_backup_history():
    """获取备份历史"""
    try:
        history = backup_manager.get_backup_history()

        # 按创建时间倒序排列
        history.sort(key=lambda x: x['created_at'], reverse=True)

        # 格式化时间显示
        for backup in history:
            try:
                dt = datetime.fromisoformat(backup['created_at'])
                backup['created_at_formatted'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                backup['size_formatted'] = format_file_size(backup.get('size', 0))
            except:
                backup['created_at_formatted'] = backup['created_at']
                backup['size_formatted'] = '未知'

        return jsonify({
            'success': True,
            'history': history,
            'total': len(history)
        })

    except Exception as e:
        current_app.logger.error(f"获取备份历史失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取备份历史失败: {str(e)}'})

def format_file_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"

@backup_bp.route('/delete/<filename>', methods=['POST'])
def delete_backup(filename):
    """删除指定的备份文件"""
    try:
        safe_filename = secure_filename(filename)
        backup_path = os.path.join(BACKUP_DIR, safe_filename)

        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'message': '备份文件不存在'})

        # 删除文件
        os.remove(backup_path)

        # 更新历史记录
        history = backup_manager.get_backup_history()
        history = [backup for backup in history if backup['filename'] != safe_filename]

        # 保存更新后的历史记录
        history_file = os.path.join(BACKUP_DIR, 'backup_history.json')
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        current_app.logger.info(f"删除备份文件: {safe_filename}")

        return jsonify({
            'success': True,
            'message': '备份文件已删除'
        })

    except Exception as e:
        current_app.logger.error(f"删除备份文件失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

@backup_bp.route('/schedule', methods=['GET'])
def get_schedule_status():
    """获取自动备份调度状态"""
    try:
        next_run = schedule.next_run()

        return jsonify({
            'success': True,
            'auto_backup_enabled': backup_manager.settings.get('autoBackup', True),
            'backup_time': backup_manager.settings.get('backupTime', '02:00'),
            'next_run': next_run.isoformat() if next_run else None,
            'jobs': [str(job) for job in schedule.jobs]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'获取调度状态失败: {str(e)}'})