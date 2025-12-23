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

import concurrent.futures
import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

# 添加项目路径到 Python 路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from background_manager import BackgroundTaskManager
    from cc_status.core.cache import CacheManager
    from cc_status.core.config import ConfigManager
    from cc_status.display.formatter import StatusFormatter
    from cc_status.display.renderer import StatusRenderer
    from cc_status.platforms.manager import PlatformManager
    from cc_status.utils.logger import get_logger
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
            "workspace": {"current_dir": os.getcwd()},
        }
    except (json.JSONDecodeError, Exception):
        return {
            "session_id": None,
            "model": {"display_name": "Unknown"},
            "workspace": {"current_dir": os.getcwd()},
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
                timeout=5,
            )

            # 获取当前分支
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            branch = result.stdout.strip()

            # 检查是否有未提交的更改
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            is_dirty = bool(result.stdout.strip())

            # 获取 ahead/behind 计数
            ahead = 0
            behind = 0
            try:
                result = subprocess.run(
                    ["git", "rev-list", "--count", "--left-right", "HEAD...@{u}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.stdout.strip():
                    ahead_str, behind_str = result.stdout.strip().split()
                    ahead = int(ahead_str)
                    behind = int(behind_str)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError, IndexError) as e:
                logger.debug(f"Failed to get ahead/behind count: {e}")

            # 获取 stash 数量
            stashed = 0
            try:
                result = subprocess.run(
                    ["git", "stash", "list", "--count"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.stdout.strip():
                    stashed = int(result.stdout.strip())
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as e:
                logger.debug(f"Failed to get stash count: {e}")

            return {
                "branch": branch or "detached",
                "is_dirty": is_dirty,
                "ahead": ahead,
                "behind": behind,
                "stashed": stashed
            }
        finally:
            os.chdir(original_cwd)

    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
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
            has_auth = any(
                [
                    platform_config.get("api_key"),
                    platform_config.get("auth_token"),
                    platform_config.get("login_token"),
                ]
            )

            if not has_auth:
                return platform_id, {
                    "id": platform_id,
                    "name": platform_config.get("name", platform_id),
                    "enabled": False,
                    "has_auth": False,
                    "balance": None,
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
                    "error": "Failed to create platform instance",
                }

            try:
                # 获取余额数据
                balance_data = platform_manager.fetch_balance_data(platform_instance)

                # 获取订阅数据
                subscription_data = None
                try:
                    subscription_data = platform_manager.fetch_subscription_data(
                        platform_instance
                    )
                except Exception as e:
                    logger.debug(f"Failed to get subscription for {platform_id}: {e}")

                # 获取用量数据
                usage_data = None
                try:
                    usage_data = platform_manager.fetch_usage_data(platform_instance)
                except Exception as e:
                    logger.debug(f"Failed to get usage for {platform_id}: {e}")

                return (
                    platform_id,
                    {
                        "id": platform_id,
                        "name": platform_config.get("name", platform_id),
                        "enabled": True,
                        "has_auth": True,
                        "balance": balance_data,
                        "subscription": subscription_data,
                        "usage": usage_data,
                        "platform_instance": platform_instance,  # 添加平台实例供formatter使用
                    },
                )
            finally:
                if hasattr(platform_instance, "close"):
                    platform_instance.close()

        except Exception as e:
            logger.warning(f"Failed to get data for platform {platform_id}: {e}")
            return platform_id, {
                "id": platform_id,
                "name": platform_config.get("name", platform_id),
                "enabled": True,
                "has_auth": True,
                "balance": None,
                "error": str(e),
            }

    # 使用线程池并发获取所有平台数据
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_platform = {}

        for platform_id, platform_config in platforms_config.get(
            "platforms", {}
        ).items():
            if platform_config.get("enabled", False):
                future = executor.submit(
                    get_single_platform_data, platform_id, platform_config
                )
                future_to_platform[future] = platform_id

        # 增加超时时间到30秒，并改进错误处理
        timeout_seconds = 30
        try:
            for future in concurrent.futures.as_completed(future_to_platform, timeout=timeout_seconds):
                platform_id = future_to_platform[future]
                try:
                    _, platform_data = future.result()
                    if platform_data:
                        platforms_data[platform_id] = platform_data
                except Exception as e:
                    logger.warning(f"Future failed for platform {platform_id}: {e}")
        except concurrent.futures.TimeoutError:
            logger.warning(f"Platform data collection timed out after {timeout_seconds} seconds")
            # 即使超时也继续，不让整个状态栏失败

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
        for platform_id, platform_config in platforms_config.get(
            "platforms", {}
        ).items():
            if platform_config.get("enabled", False):
                has_auth = any(
                    [
                        platform_config.get("api_key"),
                        platform_config.get("auth_token"),
                        platform_config.get("login_token"),
                    ]
                )
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
            logger.debug(
                f"Found cached usage data: ${cache_entry.get('total_cost', 0):.2f}"
            )
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
        if "logger" in globals():
            logger.warning(f"Failed to get today usage: {e}")
        return None


def get_ccusage_data():
    """
    获取 ccusage 统计数据（今日 token 消耗）
    使用锁机制 + 缓存策略，确保每分钟只执行一次
    """
    import subprocess
    import platform
    import time
    from datetime import datetime
    from pathlib import Path

    # 获取 logger 和 config
    global logger, config_manager
    if 'logger' not in globals():
        logger = get_logger("statusline")
    if 'config_manager' not in globals():
        config_manager = ConfigManager()

    cache_manager = CacheManager()
    config = config_manager.get_status_config()
    today = datetime.now().strftime("%Y%m%d")
    cache_key = f"ccusage_{today}"

    # 获取配置参数
    cache_ttl = config.get("cache_timeout", {}).get("ccusage", 60)
    lock_timeout = config.get("lock_config", {}).get("timeout_seconds", 30)
    wait_timeout = config.get("lock_config", {}).get("wait_timeout_seconds", 15)
    recent_exec_window = config.get("lock_config", {}).get("recent_exec_window", 60)

    # 定义锁文件路径（用于防止并发执行）
    lock_dir = Path.home() / ".claude" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_file = lock_dir / "ccusage.lock"

    # 定义执行时间记录文件（用于检查最近一分钟是否执行过）
    exec_record_file = lock_dir / "ccusage_last_exec.json"

    # 先尝试从缓存获取
    cached_data = cache_manager.get(cache_key, ttl=cache_ttl)
    if cached_data is not None:
        logger.debug(
            f"Found cached ccusage data: {cached_data.get('totalTokens', 0)} tokens"
        )
        # 在后台触发更新（不阻塞）
        _trigger_ccusage_update_async(cache_key, today)
        return cached_data

    # 没有缓存，使用锁机制获取数据
    fcntl_lock_fp = None

    try:
        # 检查最近执行窗口内是否已经执行过
        if exec_record_file.exists():
            try:
                with open(exec_record_file, 'r') as f:
                    exec_data = json.load(f)
                    last_exec_time = exec_data.get('timestamp', 0)
                    current_time = time.time()

                    # 如果在最近执行窗口内已经执行过，等待结果或返回旧缓存
                    if current_time - last_exec_time < recent_exec_window:
                        logger.debug(f"ccusage recently executed within {recent_exec_window}s window, waiting for result...")

                        # 等待锁释放（最多等待 wait_timeout 秒）
                        wait_start = time.time()
                        while time.time() - wait_start < wait_timeout:
                            time.sleep(0.1)

                            # 检查是否有新缓存
                            cached_data = cache_manager.get(cache_key, ttl=cache_ttl)
                            if cached_data is not None:
                                logger.debug("Found updated cache during wait")
                                return cached_data

                        # 如果等待后还是没有缓存，返回旧数据或None
                        logger.debug("No updated cache found after wait")
                        return cached_data
            except (json.JSONDecodeError, IOError):
                logger.debug("Failed to read execution record, proceeding with lock acquisition")

        # 获取锁并执行 ccusage
        is_lock_owner = False

        # 检查平台并尝试获取锁
        if platform.system() in ('Linux', 'Darwin'):  # Linux 或 macOS
            try:
                import fcntl
                fcntl_lock_fp = open(lock_file, 'w')
                try:
                    # 尝试获取排他锁（Linux/macOS）
                    fcntl.flock(fcntl_lock_fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    is_lock_owner = True
                    logger.debug(f"Acquired fcntl lock")
                except (IOError, OSError):
                    # 无法获取锁，等待其他进程完成
                    fcntl_lock_fp.close()
                    fcntl_lock_fp = None
                    is_lock_owner = False
                    logger.debug("Failed to acquire fcntl lock, will wait")
            except ImportError:
                # fcntl 不可用，使用基于文件的简单锁
                is_lock_owner = _try_acquire_simple_lock(lock_file, lock_timeout)
                if is_lock_owner:
                    logger.debug(f"Acquired simple file lock")
        else:
            # Windows 或其他平台，使用基于文件的简单锁
            is_lock_owner = _try_acquire_simple_lock(lock_file, lock_timeout)
            if is_lock_owner:
                logger.debug(f"Acquired simple file lock")

        # 记录执行时间
        with open(exec_record_file, 'w') as f:
            json.dump({
                'timestamp': time.time()
            }, f)

        if is_lock_owner:
            logger.debug(f"Lock owner executing ccusage command...")
            # 只有获得锁的进程才执行实际的 ccusage 命令
            try:
                data = _fetch_ccusage_sync(today)
                if data:
                    # 缓存数据
                    cache_manager.set(cache_key, data, ttl=cache_ttl)
                    logger.debug(f"ccusage data fetched and cached: {data.get('totalTokens', 0)} tokens")
                return data
            except Exception as e:
                logger.warning(f"Failed to fetch ccusage data: {e}")
                return None
        else:
            # 没有获得锁，等待其他进程完成
            logger.debug(f"Waiting for other process to fetch ccusage data (max {wait_timeout}s)...")
            wait_start = time.time()
            while time.time() - wait_start < wait_timeout:
                time.sleep(0.2)
                cached_data = cache_manager.get(cache_key, ttl=cache_ttl)
                if cached_data is not None:
                    logger.debug("Found cached data while waiting")
                    return cached_data

            # 等待超时，返回None
            logger.warning(f"Timeout waiting for ccusage data after {wait_timeout}s")
            return None

    except Exception as e:
        logger.warning(f"Error in get_ccusage_data: {e}")
        return None
    finally:
        # 确保fcntl锁被正确释放
        if fcntl_lock_fp:
            try:
                fcntl.flock(fcntl_lock_fp.fileno(), fcntl.LOCK_UN)
                fcntl_lock_fp.close()
            except:
                pass


def _try_acquire_simple_lock(lock_marker: Path, lock_timeout: int = 30) -> bool:
    """
    简单的基于文件的锁机制（用于 Windows 或 fcntl 不可用的情况）

    Args:
        lock_marker: 锁标记文件路径
        lock_timeout: 锁超时时间（秒）

    Returns:
        bool: 是否获得锁
    """
    try:
        # 尝试创建锁标记文件
        if not lock_marker.exists():
            lock_marker.touch()
            return True
        else:
            # 检查锁文件是否过期
            lock_age = time.time() - lock_marker.stat().st_mtime
            if lock_age > lock_timeout:
                # 锁文件过期，删除并重新创建
                lock_marker.unlink(missing_ok=True)
                lock_marker.touch()
                return True
            return False
    except (OSError, IOError):
        return False


def _trigger_ccusage_update_async(cache_key: str, today: str):
    """
    在后台异步更新 ccusage 数据（仅作为缓存预热）
    注意：由于主函数已经有锁保护，这里不保证实时性
    """
    def update_task():
        try:
            data = _fetch_ccusage_sync(today)
            if data:
                cache_manager = CacheManager()
                cache_manager.set(cache_key, data, ttl=60)
        except:
            pass  # 静默失败，不影响主流程

    threading.Thread(target=update_task, daemon=True).start()


def _fetch_ccusage_sync(today: str) -> dict:
    """
    同步获取 ccusage 数据
    优先使用全局安装的 ccusage，fallback 到 npx
    """
    import subprocess
    import shutil

    try:
        # 首先尝试使用全局安装的 ccusage
        result = subprocess.run(
            ["ccusage", "daily", "-j", "-s", today],
            capture_output=True,
            text=True,
            timeout=30,  # 30秒超时
            env={**os.environ, "NO_COLOR": "1"},  # 禁用颜色输出
        )

        if result.returncode != 0:
            # 如果全局安装的 ccusage 失败，尝试使用 npx
            logger.debug("Global ccusage failed, trying npx...")
            result = subprocess.run(
                ["npx", "--yes", "ccusage", "daily", "-j", "-s", today],
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "NO_COLOR": "1"},
            )

        if result.returncode != 0:
            logger.debug(f"ccusage command failed: {result.stderr}")
            return None

        # 解析 JSON 输出
        output = result.stdout.strip()
        if not output:
            return None

        data = json.loads(output)

        # 提取 totals 数据
        totals = data.get("totals", {})
        return {
            "totalTokens": totals.get("totalTokens", 0),
            "totalCost": totals.get("totalCost", 0),
            "inputTokens": totals.get("inputTokens", 0),
            "outputTokens": totals.get("outputTokens", 0),
            "cacheReadTokens": totals.get("cacheReadTokens", 0),
            "cacheCreationTokens": totals.get("cacheCreationTokens", 0),
        }

    except subprocess.TimeoutExpired:
        logger.warning("ccusage command timed out")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse ccusage output: {e}")
        return None
    except FileNotFoundError:
        logger.warning("ccusage not found, please install it with: npm install -g ccusage")
        return None
    except Exception as e:
        logger.warning(f"Failed to get ccusage data: {e}")
        return None


def main():
    """主函数"""
    # 解析命令行参数
    selected_platform = None

    # 处理命令行参数
    for arg in sys.argv[1:]:
        if arg == "--init-config":
            return init_config()
        elif arg == "--check-config":
            return check_config()
        elif arg in ["--help", "-h"]:
            print("cc-status - Claude Code Multi-Platform Status Bar Manager")
            print()
            print("Usage:")
            print("  python statusline.py                    # Run status bar")
            print("  python statusline.py --platform=minimax # Highlight specific platform")
            print("  python statusline.py --init-config      # Initialize configuration")
            print("  python statusline.py --check-config     # Check configuration")
            print("  python statusline.py --help             # Show this help")
            return
        elif arg.startswith("--platform="):
            selected_platform = arg.split("=", 1)[1]
        elif not arg.startswith("--"):
            print(f"Unknown argument: {arg}")
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

        # 获取 ccusage 数据（token 消耗统计）
        ccusage_data = None
        if config.get("show_ccusage", True):
            ccusage_data = get_ccusage_data()

        # 构建状态数据
        status_data = {
            "model": model_name,
            "time": current_time,
            "session_id": session_id,
            "directory": Path(current_dir).name if current_dir else "Unknown",
            "git": git_info,
            "platforms": platforms_data,
            "usage": usage_data,
            "ccusage": ccusage_data,
            "selected_platform": selected_platform  # 添加选中的平台
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
