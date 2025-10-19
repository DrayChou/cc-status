#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Background Manager - 后台任务管理系统
管理cc-status的后台任务，包括缓存更新、余额监控等
"""

import sys
import json
import time
import signal
import argparse
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# 添加项目路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from cc_status.core.cache import CacheManager
from cc_status.core.config import ConfigManager
from cc_status.platforms.manager import PlatformManager
from cc_status.utils.logger import get_logger
from update_usage import UsageUpdater


class BackgroundTaskManager:
    """后台任务管理器"""

    def __init__(self):
        self.logger = get_logger("background_manager")
        self.cache_manager = CacheManager()
        self.config_manager = ConfigManager()
        self.platform_manager = PlatformManager(self.config_manager)
        self.usage_updater = UsageUpdater()

        # 后台任务状态
        self.running = False
        self.threads = []
        self.last_status = {}

        # 配置参数
        self.data_dir = Path.home() / ".claude" / "background"
        self.status_file = self.data_dir / "status.json"
        self.pid_file = self.data_dir / "daemon.pid"

        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 任务配置
        self.tasks = {
            "balance_update": {"interval": 300, "enabled": True},  # 5分钟
            "usage_update": {"interval": 1800, "enabled": True},  # 30分钟
            "cache_cleanup": {"interval": 3600, "enabled": True},  # 1小时
        }

    def start(self):
        """启动后台任务管理器"""
        if self.is_running():
            self.logger.warning("Background manager is already running")
            return False

        self.logger.info("Starting background task manager...")

        # 写入PID文件
        try:
            with open(self.pid_file, "w") as f:
                f.write(str(os.getpid()))
        except Exception as e:
            self.logger.error(f"Failed to write PID file: {e}")

        self.running = True

        # 启动各个后台任务
        for task_name, task_config in self.tasks.items():
            if task_config["enabled"]:
                thread = threading.Thread(
                    target=self._run_task,
                    args=(task_name, task_config["interval"]),
                    daemon=True,
                    name=f"Task-{task_name}"
                )
                thread.start()
                self.threads.append(thread)
                self.logger.info(f"Started background task: {task_name}")

        # 启动状态更新线程
        status_thread = threading.Thread(
            target=self._update_status_loop,
            daemon=True,
            name="StatusUpdater"
        )
        status_thread.start()
        self.threads.append(status_thread)

        self.logger.info(f"Background manager started with {len(self.threads)} tasks")
        return True

    def stop(self):
        """停止后台任务管理器"""
        if not self.running:
            self.logger.info("Background manager is not running")
            return

        self.logger.info("Stopping background task manager...")
        self.running = False

        # 等待所有线程结束
        for thread in self.threads:
            if thread.is_alive():
                self.logger.debug(f"Waiting for thread {thread.name} to stop...")
                thread.join(timeout=5)

        # 清理PID文件
        if self.pid_file.exists():
            self.pid_file.unlink()

        self.logger.info("Background manager stopped")

    def is_running(self) -> bool:
        """检查后台管理器是否正在运行"""
        if not self.pid_file.exists():
            return False

        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())

            # 检查进程是否存在
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:  # Unix-like
                return os.kill(pid, 0) is None
        except Exception:
            return False

    def _run_task(self, task_name: str, interval: int):
        """运行后台任务"""
        self.logger.info(f"Starting task: {task_name} (interval: {interval}s)")

        while self.running:
            try:
                start_time = time.time()

                if task_name == "balance_update":
                    self._update_balances()
                elif task_name == "usage_update":
                    self._update_usage()
                elif task_name == "cache_cleanup":
                    self._cleanup_cache()

                execution_time = time.time() - start_time
                self.logger.debug(f"Task {task_name} completed in {execution_time:.2f}s")

                # 更新任务状态
                self.last_status[task_name] = {
                    "last_run": datetime.now().isoformat(),
                    "execution_time": execution_time,
                    "success": True
                }

            except Exception as e:
                self.logger.error(f"Error in task {task_name}: {e}")
                self.last_status[task_name] = {
                    "last_run": datetime.now().isoformat(),
                    "execution_time": 0,
                    "success": False,
                    "error": str(e)
                }

            # 等待下次执行
            time.sleep(interval)

    def _update_balances(self):
        """更新所有平台的余额信息"""
        try:
            platforms_config = self.config_manager.get_platforms_config()

            # 确保platforms_config是字典
            if not isinstance(platforms_config, dict):
                self.logger.error(f"Invalid platforms config type: {type(platforms_config)}")
                return

            updated_count = 0

            for platform_id, platform_config in platforms_config.items():
                if not isinstance(platform_config, dict) or not platform_config.get("enabled", False):
                    continue

                try:
                    # 创建平台实例
                    platform_instance = self.platform_manager.create_platform(platform_id, platform_config)
                    if platform_instance:
                        # 获取余额数据
                        balance_data = platform_instance.fetch_balance_data()
                        if balance_data:
                            # 更新缓存
                            cache_key = f"balance_{platform_id}"
                            self.cache_manager.set(cache_key, balance_data)
                            updated_count += 1

                        platform_instance.close()

                except Exception as e:
                    self.logger.debug(f"Failed to update balance for {platform_id}: {e}")

            self.logger.info(f"Updated balances for {updated_count} platforms")

        except Exception as e:
            self.logger.error(f"Error updating balances: {e}")

    def _update_usage(self):
        """更新使用量信息"""
        try:
            success = self.usage_updater.update_usage()
            if success:
                self.logger.info("Usage update completed successfully")
            else:
                self.logger.warning("Usage update failed")
        except Exception as e:
            self.logger.error(f"Error updating usage: {e}")

    def _cleanup_cache(self):
        """清理过期缓存"""
        try:
            cleaned_count = self.cache_manager.cleanup_expired()
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} expired cache files")
            else:
                self.logger.debug("No expired cache files found")
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}")

    def _update_status_loop(self):
        """更新状态信息循环"""
        while self.running:
            try:
                self._update_status()
                time.sleep(60)  # 每分钟更新一次状态
            except Exception as e:
                self.logger.error(f"Error updating status: {e}")

    def _update_status(self):
        """更新状态文件"""
        try:
            status_data = {
                "manager_status": "running" if self.running else "stopped",
                "pid": os.getpid(),
                "started_at": datetime.now().isoformat(),
                "tasks": self.last_status.copy(),
                "threads": [thread.name for thread in self.threads if thread.is_alive()]
            }

            with open(self.status_file, "w") as f:
                json.dump(status_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error updating status file: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取后台管理器状态"""
        try:
            if self.status_file.exists():
                with open(self.status_file, "r") as f:
                    return json.load(f)
            else:
                return {
                    "manager_status": "not_running",
                    "message": "Status file not found"
                }
        except Exception as e:
            return {
                "manager_status": "error",
                "error": str(e)
            }

    def run_forever(self):
        """持续运行（主循环）"""
        if not self.start():
            return False

        try:
            self.logger.info("Background manager is running. Press Ctrl+C to stop.")
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            self.stop()

        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Background task manager for cc-status")
    parser.add_argument("command", choices=["start", "stop", "status", "restart", "daemon"],
                       help="Command to execute")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    manager = BackgroundTaskManager()

    if args.command == "start":
        if manager.run_forever():
            return 0
        else:
            return 1

    elif args.command == "stop":
        if manager.is_running():
            manager.stop()
            print("Background manager stopped")
            return 0
        else:
            print("Background manager is not running")
            return 1

    elif args.command == "status":
        status = manager.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0

    elif args.command == "restart":
        if manager.is_running():
            manager.stop()
            time.sleep(2)

        if manager.run_forever():
            return 0
        else:
            return 1

    elif args.command == "daemon":
        # 守护进程模式
        if os.name == 'nt':  # Windows不支持daemon模式
            print("Daemon mode is not supported on Windows")
            return 1

        # Unix-like系统的daemon实现
        try:
            import os
            if os.fork() > 0:
                os._exit(0)  # 父进程退出

            os.setsid()
            if os.fork() > 0:
                os._exit(0)  # 第二次fork

            # 重定向标准输入输出
            sys.stdout.flush()
            sys.stderr.flush()

            with open('/dev/null', 'r') as dev_null:
                os.dup2(dev_null.fileno(), sys.stdin.fileno())

            with open('/dev/null', 'w') as dev_null:
                os.dup2(dev_null.fileno(), sys.stdout.fileno())
                os.dup2(dev_null.fileno(), sys.stderr.fileno())

            return manager.run_forever()

        except Exception as e:
            print(f"Failed to start daemon: {e}")
            return 1


if __name__ == "__main__":
    import os
    import subprocess
    sys.exit(main())