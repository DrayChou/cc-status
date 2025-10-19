#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Lock - API调用锁机制
防止并发API调用冲突，确保API调用的顺序性和一致性
"""

import time
import threading
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
from datetime import datetime, timedelta

from .logger import get_logger


class APILock:
    """API调用锁"""

    def __init__(self, lock_dir: Optional[Path] = None):
        """
        初始化API锁

        Args:
            lock_dir: 锁文件目录，默认为~/.claude/locks
        """
        self.logger = get_logger("api_lock")

        if lock_dir is None:
            lock_dir = Path.home() / ".claude" / "locks"

        self.lock_dir = lock_dir
        self.lock_dir.mkdir(parents=True, exist_ok=True)

        # 内存锁字典
        self._memory_locks: Dict[str, threading.Lock] = {}
        self._lock_registry: Dict[str, Dict[str, Any]] = {}

        # 默认锁超时时间
        self.default_timeout = 60  # 60秒
        self.default_wait_interval = 0.1  # 100毫秒

        # 清理过期锁的线程
        self._cleanup_thread = None
        self._cleanup_running = False

        # 启动清理线程
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """启动清理过期锁的后台线程"""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_running = True
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_expired_locks,
                daemon=True,
                name="APILock-Cleanup"
            )
            self._cleanup_thread.start()
            self.logger.debug("Started API lock cleanup thread")

    def _cleanup_expired_locks(self):
        """清理过期锁的后台任务"""
        while self._cleanup_running:
            try:
                self.cleanup_expired_locks()
                time.sleep(30)  # 每30秒清理一次
            except Exception as e:
                self.logger.error(f"Error in cleanup thread: {e}")
                time.sleep(30)

    def acquire_lock(self, lock_key: str, timeout: Optional[float] = None,
                    wait_interval: Optional[float] = None) -> bool:
        """
        获取API锁

        Args:
            lock_key: 锁的键名（通常是平台名称或API端点）
            timeout: 超时时间（秒），None表示使用默认值
            wait_interval: 等待间隔（秒），None表示使用默认值

        Returns:
            是否成功获取锁
        """
        if timeout is None:
            timeout = self.default_timeout
        if wait_interval is None:
            wait_interval = self.default_wait_interval

        lock_file = self.lock_dir / f"{lock_key}.lock"

        self.logger.debug(f"Attempting to acquire lock: {lock_key}")

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 尝试获取文件锁
                if self._try_acquire_file_lock(lock_file, lock_key):
                    self.logger.debug(f"Successfully acquired lock: {lock_key}")
                    return True

                # 等待后重试
                time.sleep(wait_interval)

            except Exception as e:
                self.logger.error(f"Error acquiring lock {lock_key}: {e}")
                time.sleep(wait_interval)

        self.logger.warning(f"Failed to acquire lock {lock_key} after {timeout}s")
        return False

    def release_lock(self, lock_key: str) -> bool:
        """
        释放API锁

        Args:
            lock_key: 锁的键名

        Returns:
            是否成功释放锁
        """
        try:
            lock_file = self.lock_dir / f"{lock_key}.lock"

            # 检查锁是否属于当前进程
            if self._is_lock_owner(lock_file, lock_key):
                lock_file.unlink(missing_ok=True)

                # 清理内存锁
                if lock_key in self._memory_locks:
                    del self._memory_locks[lock_key]

                # 清理注册信息
                if lock_key in self._lock_registry:
                    del self._lock_registry[lock_key]

                self.logger.debug(f"Successfully released lock: {lock_key}")
                return True
            else:
                self.logger.warning(f"Attempted to release lock {lock_key} owned by another process")
                return False

        except Exception as e:
            self.logger.error(f"Error releasing lock {lock_key}: {e}")
            return False

    @contextmanager
    def lock(self, lock_key: str, timeout: Optional[float] = None):
        """
        上下文管理器形式的锁

        Args:
            lock_key: 锁的键名
            timeout: 超时时间（秒）
        """
        if self.acquire_lock(lock_key, timeout):
            try:
                yield
            finally:
                self.release_lock(lock_key)
        else:
            raise TimeoutError(f"Failed to acquire lock {lock_key} within {timeout or self.default_timeout}s")

    def _try_acquire_file_lock(self, lock_file: Path, lock_key: str) -> bool:
        """尝试获取文件锁"""
        try:
            # 检查锁文件是否已存在
            if lock_file.exists():
                # 检查锁是否过期
                if self._is_lock_expired(lock_file):
                    lock_file.unlink(missing_ok=True)
                else:
                    return False

            # 创建锁文件
            lock_info = {
                "lock_key": lock_key,
                "pid": os.getpid(),
                "thread_id": threading.get_ident(),
                "created_at": datetime.now().isoformat(),
                "hostname": os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "unknown"))
            }

            # 写入锁文件
            with open(lock_file, "w", encoding="utf-8") as f:
                import json
                json.dump(lock_info, f, indent=2)

            # 创建内存锁
            if lock_key not in self._memory_locks:
                self._memory_locks[lock_key] = threading.Lock()

            # 注册锁信息
            self._lock_registry[lock_key] = {
                "acquired_at": datetime.now().isoformat(),
                "pid": os.getpid(),
                "thread_id": threading.get_ident()
            }

            return True

        except Exception as e:
            self.logger.error(f"Error creating lock file {lock_file}: {e}")
            return False

    def _is_lock_owner(self, lock_file: Path, lock_key: str) -> bool:
        """检查当前进程是否是锁的所有者"""
        try:
            if not lock_file.exists():
                return True

            with open(lock_file, "r", encoding="utf-8") as f:
                lock_info = json.load(f)

            return (lock_info.get("pid") == os.getpid() and
                   lock_info.get("thread_id") == threading.get_ident())

        except Exception:
            return False

    def _is_lock_expired(self, lock_file: Path) -> bool:
        """检查锁是否过期"""
        try:
            if not lock_file.exists():
                return True

            with open(lock_file, "r", encoding="utf-8") as f:
                lock_info = json.load(f)

            created_at_str = lock_info.get("created_at")
            if not created_at_str:
                return True

            created_at = datetime.fromisoformat(created_at_str)
            if datetime.now() - created_at > timedelta(seconds=self.default_timeout):
                self.logger.debug(f"Lock {lock_file} has expired")
                return True

            return False

        except Exception as e:
            self.logger.debug(f"Error checking lock expiration: {e}")
            return True  # 出错时认为锁已过期

    def cleanup_expired_locks(self) -> int:
        """清理所有过期的锁文件

        Returns:
            清理的锁文件数量
        """
        cleaned_count = 0
        try:
            for lock_file in self.lock_dir.glob("*.lock"):
                if self._is_lock_expired(lock_file):
                    lock_file.unlink(missing_ok=True)
                    cleaned_count += 1

            if cleaned_count > 0:
                self.logger.debug(f"Cleaned up {cleaned_count} expired lock files")

        except Exception as e:
            self.logger.error(f"Error cleaning up expired locks: {e}")

        return cleaned_count

    def get_active_locks(self) -> Dict[str, Dict[str, Any]]:
        """获取当前活跃的锁信息

        Returns:
            锁信息字典
        """
        active_locks = {}
        try:
            for lock_file in self.lock_dir.glob("*.lock"):
                try:
                    with open(lock_file, "r", encoding="utf-8") as f:
                        lock_info = json.load(f)

                    lock_key = lock_file.stem
                    active_locks[lock_key] = lock_info

                except Exception as e:
                    self.logger.debug(f"Error reading lock file {lock_file}: {e}")

        except Exception as e:
            self.logger.error(f"Error getting active locks: {e}")

        return active_locks

    def is_locked(self, lock_key: str) -> bool:
        """检查指定的锁是否被占用

        Args:
            lock_key: 锁的键名

        Returns:
            锁是否被占用
        """
        lock_file = self.lock_dir / f"{lock_key}.lock"

        if not lock_file.exists():
            return False

        # 检查锁是否过期
        if self._is_lock_expired(lock_file):
            lock_file.unlink(missing_ok=True)
            return False

        return True

    def force_release_lock(self, lock_key: str) -> bool:
        """强制释放锁（用于清理死锁）

        Args:
            lock_key: 锁的键名

        Returns:
            是否成功强制释放
        """
        try:
            lock_file = self.lock_dir / f"{lock_key}.lock"

            if lock_file.exists():
                lock_file.unlink(missing_ok=True)
                self.logger.info(f"Forcefully released lock: {lock_key}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error force releasing lock {lock_key}: {e}")
            return False

    def __del__(self):
        """析构函数，清理资源"""
        try:
            self._cleanup_running = False
            if self._cleanup_thread and self._cleanup_thread.is_alive():
                self._cleanup_thread.join(timeout=1)
        except Exception:
            pass


# 全局API锁实例
_global_api_lock = None


def get_api_lock() -> APILock:
    """获取全局API锁实例"""
    global _global_api_lock
    if _global_api_lock is None:
        _global_api_lock = APILock()
    return _global_api_lock


def with_api_lock(lock_key: str, timeout: Optional[float] = None):
    """API锁装饰器

    Args:
        lock_key: 锁的键名
        timeout: 超时时间（秒）
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            api_lock = get_api_lock()
            with api_lock.lock(lock_key, timeout):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# 预定义的锁键常量
class LockKeys:
    """API锁键常量"""
    BALANCE_UPDATE = "balance_update"
    USAGE_UPDATE = "usage_update"
    PLATFORM_CONFIG = "platform_config"
    CACHE_UPDATE = "cache_update"

    # 平台特定的锁键
    @staticmethod
    def platform_balance(platform_name: str) -> str:
        return f"balance_{platform_name}"

    @staticmethod
    def platform_subscription(platform_name: str) -> str:
        return f"subscription_{platform_name}"