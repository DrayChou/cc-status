#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-status - Claude Code Status Bar Manager
状态栏管理器主入口

显示信息：
- AI模型名称
- 所有启用平台的API余额和订阅信息
- 今日使用量统计
- 当前时间和会话信息
- Git分支状态
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
import concurrent.futures
import threading

# 添加项目路径到 Python 路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from cc_status.core.config import ConfigManager
    from cc_status.core.cache import CacheManager
    from cc_status.platforms.manager import PlatformManager
    from cc_status.display.formatter import StatusFormatter
    from cc_status.display.renderer import StatusRenderer
    from cc_status.utils.logger import get_logger
    from background_manager import BackgroundTaskManager
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed.")
    sys.exit(1)


def get_session_info():
    """获取Claude Code传入的session信息"""
    try:
        # 尝试从stdin读取session信息
        if not sys.stdin.isatty():
            stdin_content = sys.stdin.read()
            if stdin_content.strip():
                return json.loads(stdin_content)

        # 如果没有stdin输入，返回基本session信息
        return {
            "session_id": None,
            "model": {"display_name": "Unknown"},
            "workspace": {"current_dir": os.getcwd()}
        }
    except (json.JSONDecodeError, Exception):
        return {
            "session_id": None,
            "model": {"display_name": "Unknown"},
            "workspace": {"current_dir": os.getcwd()}
        }


def get_git_info(directory):
    """获取Git分支信息"""
    try:
        import subprocess
        if not directory or not Path(directory).exists():
            return None

        original_cwd = os.getcwd()
        os.chdir(directory)

        try:
            # 检查是否在Git仓库中
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                check=True,
                timeout=5
            )

            # 获取当前分支
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            branch = result.stdout.strip()

            # 检查是否有未提交的更改
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            is_dirty = bool(result.stdout.strip())

            return {"branch": branch or "detached", "is_dirty": is_dirty}
        finally:
            os.chdir(original_cwd)

    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def get_all_platforms_data(platform_manager: PlatformManager, config: dict) -> dict:
    """获取所有启用平台的数据"""
    platforms_data = {}
    platforms_config = config_manager.get_platforms_config()

    def get_single_platform_data(platform_id: str, platform_config: dict) -> tuple:
        """获取单个平台数据"""
        try:
            if not platform_config.get("enabled", False):
                return platform_id, None

            # 检查是否有认证信息
            has_auth = any([
                platform_config.get("api_key"),
                platform_config.get("auth_token"),
                platform_config.get("login_token")
            ])

            if not has_auth:
                return platform_id, {
                    "id": platform_id,
                    "name": platform_config.get("name", platform_id),
                    "enabled": False,
                    "has_auth": False,
                    "balance": None
                }

            # 创建平台实例并获取数据
            platform_instance = platform_manager.get_platform_by_name(
                platform_id, platform_config
            )

            if not platform_instance:
                return platform_id, {
                    "id": platform_id,
                    "name": platform_config.get("name", platform_id),
                    "enabled": True,
                    "has_auth": True,
                    "balance": None,
                    "error": "Failed to create platform instance"
                }

            try:
                # 获取余额数据
                balance_data = platform_manager.fetch_balance_data(platform_instance)

                # 获取订阅数据
                subscription_data = None
                try:
                    subscription_data = platform_manager.fetch_subscription_data(platform_instance)
                except Exception as e:
                    logger.debug(f"Failed to get subscription for {platform_id}: {e}")

                return platform_id, {
                    "id": platform_id,
                    "name": platform_config.get("name", platform_id),
                    "enabled": True,
                    "has_auth": True,
                    "balance": balance_data,
                    "subscription": subscription_data
                }
            finally:
                if hasattr(platform_instance, 'close'):
                    platform_instance.close()

        except Exception as e:
            logger.warning(f"Failed to get data for platform {platform_id}: {e}")
            return platform_id, {
                "id": platform_id,
                "name": platform_config.get("name", platform_id),
                "enabled": True,
                "has_auth": True,
                "balance": None,
                "error": str(e)
            }

    # 使用线程池并发获取所有平台数据
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_platform = {}

        for platform_id, platform_config in platforms_config.get("platforms", {}).items():
            if platform_config.get("enabled", False):
                future = executor.submit(get_single_platform_data, platform_id, platform_config)
                future_to_platform[future] = platform_id

        for future in concurrent.futures.as_completed(future_to_platform, timeout=10):
            platform_id = future_to_platform[future]
            try:
                _, platform_data = future.result()
                if platform_data:
                    platforms_data[platform_id] = platform_data
            except Exception as e:
                logger.warning(f"Future failed for platform {platform_id}: {e}")

    return platforms_data


def init_config():
    """初始化配置文件"""
    try:
        config_manager = ConfigManager()
        # 触发配置文件创建（通过读取配置）
        config_manager.get_platforms_config()
        config_manager.get_status_config()
        config_manager.get_launcher_config()
        print("[OK] Configuration files initialized successfully")
        print(f"Configuration location: {config_manager.config_dir}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to initialize configuration: {e}")
        return False


def check_config():
    """检查配置文件"""
    try:
        config_manager = ConfigManager()

        # 检查配置文件是否存在
        if not config_manager.platforms_file.exists():
            print("[FAIL] Platform configuration file not found")
            print(f"  Expected at: {config_manager.platforms_file}")
            return False

        # 检查配置格式
        try:
            platforms_config = config_manager.get_platforms_config()
            print("[OK] Platform configuration format is valid")
        except Exception as e:
            print(f"[FAIL] Invalid platform configuration: {e}")
            return False

        # 检查启用的平台
        enabled_platforms = []
        for platform_id, platform_config in platforms_config.get("platforms", {}).items():
            if platform_config.get("enabled", False):
                has_auth = any([
                    platform_config.get("api_key"),
                    platform_config.get("auth_token"),
                    platform_config.get("login_token")
                ])
                if has_auth:
                    enabled_platforms.append(platform_id)

        if enabled_platforms:
            print(f"[OK] Found {len(enabled_platforms)} configured platform(s):")
            for platform in enabled_platforms:
                print(f"  - {platform}")
        else:
            print("[FAIL] No configured platforms found")
            print("  Please configure API keys in ~/.claude/config/platforms.json")

        return len(enabled_platforms) > 0

    except Exception as e:
        print(f"[FAIL] Configuration check failed: {e}")
        return False


def ensure_background_tasks():
    """确保后台任务正在运行"""
    try:
        background_manager = BackgroundTaskManager()

        # 检查后台管理器是否在运行
        if not background_manager.is_running():
            logger.info("Starting background task manager...")
            success = background_manager.start()
            if success:
                logger.info("Background task manager started successfully")
            else:
                logger.warning("Failed to start background task manager")
        else:
            logger.debug("Background task manager already running")

        return True
    except Exception as e:
        logger.warning(f"Error ensuring background tasks: {e}")
        return False


def get_today_usage():
    """获取今日使用量（支持后台自动更新）"""
    try:
        from datetime import datetime

        # 确保后台任务正在运行
        ensure_background_tasks()

        # 获取缓存管理器
        cache_manager = CacheManager()
        today = datetime.now().strftime("%Y%m%d")

        # 尝试从缓存获取今日使用量
        cache_entry = cache_manager.get(f"usage_daily_{today}")
        if cache_entry is not None:
            logger.debug(f"Found cached usage data: ${cache_entry.get('total_cost', 0):.2f}")
            return cache_entry

        # 如果没有缓存数据，触发后台更新
        logger.debug("No cached usage data found, background update will be triggered")
        try:
            from update_usage import UsageUpdater
            updater = UsageUpdater()

            # 在后台线程中触发更新（不等待结果）
            import threading
            def trigger_update():
                try:
                    updater.update_usage()
                except Exception as e:
                    logger.debug(f"Background usage update failed: {e}")

            update_thread = threading.Thread(target=trigger_update, daemon=True)
            update_thread.start()
            logger.debug("Background usage update triggered")

        except Exception as e:
            logger.debug(f"Failed to trigger usage update: {e}")

        return None

    except Exception as e:
        if 'logger' in globals():
            logger.warning(f"Failed to get today usage: {e}")
        return None


def main():
    """主函数"""
    # 处理命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--init-config":
            return init_config()
        elif sys.argv[1] == "--check-config":
            return check_config()
        elif sys.argv[1] in ["--help", "-h"]:
            print("cc-status - Claude Code Multi-Platform Status Bar Manager")
            print()
            print("Usage:")
            print("  python statusline.py              # Run status bar")
            print("  python statusline.py --init-config    # Initialize configuration")
            print("  python statusline.py --check-config   # Check configuration")
            print("  python statusline.py --help           # Show this help")
            return
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for available options")
            return 1

    try:
        # 初始化组件
        global config_manager, logger
        config_manager = ConfigManager()
        cache_manager = CacheManager()
        platform_manager = PlatformManager(config_manager)
        formatter = StatusFormatter()
        renderer = StatusRenderer()
        logger = get_logger("statusline")

        # 确保配置文件存在
        if not config_manager.platforms_file.exists():
            print("Configuration not found. Please run:")
            print("  python statusline.py --init-config")
            return 1

        # 获取配置
        config = config_manager.get_status_config()

        # 获取session信息
        session_info = get_session_info()
        session_id = session_info.get("session_id")

        # 收集基础信息
        current_time = datetime.now().strftime("%H:%M:%S")
        model_name = session_info.get("model", {}).get("display_name", "Unknown")
        current_dir = session_info.get("workspace", {}).get("current_dir", "")
        git_info = get_git_info(current_dir)

        # 确保后台任务正在运行（启用自动更新）
        ensure_background_tasks()

        # 获取所有启用平台的数据
        platforms_data = {}
        if config.get("show_balance", True):
            platforms_data = get_all_platforms_data(platform_manager, config)
            logger.info(f"Retrieved data for {len(platforms_data)} platforms")

        # 获取今日使用量
        usage_data = get_today_usage()

        # 构建状态数据
        status_data = {
            "model": model_name,
            "time": current_time,
            "session_id": session_id,
            "directory": Path(current_dir).name if current_dir else "Unknown",
            "git": git_info,
            "platforms": platforms_data,
            "usage": usage_data
        }

        # 格式化状态
        formatted_status = formatter.format_status(status_data, config)

        # 渲染输出
        renderer.render(formatted_status, config)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Error in statusline: {e}")
        # 显示错误信息而不是完全失败
        print("Status Error", end="")


if __name__ == "__main__":
    main()