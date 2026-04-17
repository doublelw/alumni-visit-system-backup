#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask服务器重启管理工具
用于方便地重启和管理Flask开发服务器
"""

import os
import sys
import time
import signal
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# 尝试导入所需模块，如果失败则安装
def check_and_install_dependencies():
    """检查并安装所需依赖"""
    required_packages = {
        'psutil': 'psutil>=5.8.0',
        'flask': 'Flask>=2.0.0'
    }

    missing_packages = []

    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            print(f"[OK] {module_name} 已安装")
        except ImportError:
            print(f"[ERROR] {module_name} 未安装")
            missing_packages.append(package_name)

    if missing_packages:
        print(f"\n正在安装缺少的依赖: {', '.join(missing_packages)}")
        try:
            for package in missing_packages:
                print(f"安装 {package}...")
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package
                ])
            print("[OK] 所有依赖安装完成！\n")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] 依赖安装失败: {e}")
            print("\n请手动安装依赖:")
            print(f"pip install {' '.join(missing_packages)}")
            return False

    return True

# 检查并安装依赖
if not check_and_install_dependencies():
    print("依赖安装失败，程序退出")
    sys.exit(1)

# 导入已确认存在的模块
import psutil
try:
    import flask
except ImportError:
    print("警告: Flask 未安装，某些功能可能无法使用")


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_restart.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ServerManager:
    def __init__(self, app_dir=None, port=5000, host='127.0.0.1'):
        """
        初始化服务器管理器

        Args:
            app_dir: Flask应用目录
            port: 服务器端口
            host: 服务器主机地址
        """
        if isinstance(app_dir, str):
            self.app_dir = Path(app_dir)
        elif app_dir:
            self.app_dir = app_dir
        else:
            self.app_dir = Path(__file__).parent / 'backend'
        self.port = port
        self.host = host
        self.process_name = 'flask'
        self.python_executable = sys.executable

        # 日志文件路径
        self.log_dir = self.app_dir / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        self.server_log = self.log_dir / f'server_{datetime.now().strftime("%Y%m%d")}.log'

    def find_flask_processes(self):
        """查找正在运行的Flask进程"""
        flask_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('flask' in str(cmd).lower() or 'app.py' in str(cmd) for cmd in cmdline):
                    if any(f'--port={self.port}' in str(cmd) for cmd in cmdline):
                        flask_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return flask_processes

    def stop_server(self, force=False):
        """
        停止Flask服务器

        Args:
            force: 是否强制停止
        """
        logger.info("正在查找运行中的Flask服务器...")
        processes = self.find_flask_processes()

        if not processes:
            logger.info("没有发现运行中的Flask服务器")
            return True

        stopped_count = 0
        for proc in processes:
            try:
                pid = proc.info['pid']
                logger.info(f"发现Flask进程 PID: {pid}")

                if force:
                    proc.kill()
                    logger.info(f"强制终止进程 {pid}")
                else:
                    proc.terminate()
                    logger.info(f"优雅终止进程 {pid}")

                stopped_count += 1

                # 等待进程结束
                try:
                    proc.wait(timeout=5)
                    logger.info(f"进程 {pid} 已停止")
                except psutil.TimeoutExpired:
                    logger.warning(f"进程 {pid} 停止超时，强制终止")
                    proc.kill()

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error(f"无法停止进程 {proc.info.get('pid', 'unknown')}: {e}")

        logger.info(f"成功停止 {stopped_count} 个Flask进程")
        return stopped_count > 0

    def start_server(self, debug=True, env='development'):
        """
        启动Flask服务器

        Args:
            debug: 是否启用调试模式
            env: 环境名称 (development/production)
        """
        logger.info(f"正在启动Flask服务器 (端口: {self.port}, 环境: {env})")

        # 设置环境变量
        env_vars = os.environ.copy()
        env_vars['FLASK_ENV'] = env
        env_vars['FLASK_DEBUG'] = '1' if debug else '0'
        env_vars['PYTHONPATH'] = str(self.app_dir)

        # 启动命令
        cmd = [
            self.python_executable,
            '-m', 'flask',
            'run',
            '--host', self.host,
            '--port', str(self.port)
        ]

        if debug:
            cmd.append('--reload')

        try:
            # 切换到应用目录
            os.chdir(self.app_dir)

            logger.info(f"启动命令: {' '.join(cmd)}")
            logger.info(f"工作目录: {self.app_dir}")

            # 启动服务器进程
            # 确保日志目录存在
            self.server_log.parent.mkdir(parents=True, exist_ok=True)

            with open(self.server_log, 'a', encoding='utf-8') as log_file:
                log_file.write(f"\n{'='*50}\n")
                log_file.write(f"服务器启动时间: {datetime.now()}\n")
                log_file.write(f"启动命令: {' '.join(cmd)}\n")
                log_file.write(f"环境变量: FLASK_ENV={env}, FLASK_DEBUG={env_vars['FLASK_DEBUG']}\n")
                log_file.write(f"{'='*50}\n\n")

                process = subprocess.Popen(
                    cmd,
                    env=env_vars,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )

                # 实时输出日志
                for line in process.stdout:
                    print(line.strip())
                    log_file.write(line)
                    log_file.flush()

                return process

        except Exception as e:
            logger.error(f"启动服务器失败: {e}")
            return None

    def restart_server(self, debug=True, env='development', force_stop=False):
        """
        重启Flask服务器

        Args:
            debug: 是否启用调试模式
            env: 环境名称
            force_stop: 是否强制停止现有进程
        """
        logger.info("=" * 50)
        logger.info("开始重启Flask服务器")
        logger.info("=" * 50)

        # 停止现有服务器
        if self.stop_server(force=force_stop):
            time.sleep(2)  # 等待端口释放

        # 启动新服务器
        return self.start_server(debug=debug, env=env)

    def get_server_status(self):
        """获取服务器状态"""
        processes = self.find_flask_processes()

        if not processes:
            return {
                'status': 'stopped',
                'processes': 0,
                'message': '服务器未运行'
            }

        process_info = []
        for proc in processes:
            try:
                memory_info = proc.memory_info()
                cpu_percent = proc.cpu_percent()
                process_info.append({
                    'pid': proc.info['pid'],
                    'memory_mb': memory_info.rss / 1024 / 1024,
                    'cpu_percent': cpu_percent,
                    'status': proc.status()
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            'status': 'running',
            'processes': len(processes),
            'process_info': process_info,
            'message': f'服务器运行中 ({len(processes)} 个进程)'
        }

    def install_dependencies(self):
        """安装项目依赖"""
        requirements_file = self.app_dir / 'requirements.txt'

        if requirements_file.exists():
            logger.info("正在安装项目依赖...")
            cmd = [
                self.python_executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("依赖安装成功")
                    return True
                else:
                    logger.error(f"依赖安装失败: {result.stderr}")
                    return False
            except Exception as e:
                logger.error(f"安装依赖时出错: {e}")
                return False
        else:
            logger.warning("未找到 requirements.txt 文件")
            return True

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Flask服务器管理工具')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'install'],
                       help='要执行的操作')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口 (默认: 5000)')
    parser.add_argument('--host', default='127.0.0.1', help='服务器主机 (默认: 127.0.0.1)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--env', default='development', choices=['development', 'production'],
                       help='运行环境 (默认: development)')
    parser.add_argument('--force', action='store_true', help='强制停止进程')
    parser.add_argument('--app-dir', help='Flask应用目录路径')

    args = parser.parse_args()

    # 创建服务器管理器
    manager = ServerManager(
        app_dir=args.app_dir,
        port=args.port,
        host=args.host
    )

    try:
        if args.action == 'start':
            process = manager.start_server(debug=args.debug, env=args.env)
            if process:
                logger.info("服务器启动成功")
            else:
                logger.error("服务器启动失败")
                sys.exit(1)

        elif args.action == 'stop':
            if manager.stop_server(force=args.force):
                logger.info("服务器停止成功")
            else:
                logger.warning("没有运行中的服务器需要停止")

        elif args.action == 'restart':
            process = manager.restart_server(debug=args.debug, env=args.env, force_stop=args.force)
            if process:
                logger.info("服务器重启成功")
            else:
                logger.error("服务器重启失败")
                sys.exit(1)

        elif args.action == 'status':
            status = manager.get_server_status()
            logger.info(f"服务器状态: {status['status']}")
            logger.info(f"进程数量: {status['processes']}")
            logger.info(f"消息: {status['message']}")

            if status['status'] == 'running':
                logger.info("进程详情:")
                for info in status['process_info']:
                    logger.info(f"  PID: {info['pid']}, 内存: {info['memory_mb']:.1f}MB, "
                              f"CPU: {info['cpu_percent']:.1f}%, 状态: {info['status']}")

        elif args.action == 'install':
            if manager.install_dependencies():
                logger.info("依赖安装完成")
            else:
                logger.error("依赖安装失败")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
        manager.stop_server(force=True)
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行操作时出错: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()