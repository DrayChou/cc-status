#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cache Manager - 缓存管理器
提供缓存功能，避免频繁的API调用
"""

import json
import time
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

from ..utils.logger import get_logger
from ..utils.file_lock import safe_json_read, safe_json_write


class CacheManager:
    """缓存管理器"""

    def __init__(self):
        """初始化缓存管理器"""
        self.cache_dir = Path.home() / ".claude" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("cache")

        # 缓存超时时间（秒）
        self.default_ttl = 300  # 5分钟

    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """
        获取缓存数据

        Args:
            key: 缓存键
            ttl: 超时时间（秒），None表示使用默认值

        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        try:
            cache_file = self.cache_dir / f"cache_{key}.json"
            cache_data = safe_json_read(cache_file)

            if not cache_data:
                return None

            # 检查是否过期
            cached_at = cache_data.get("cached_at", 0)
            cache_ttl = ttl or self.default_ttl

            if time.time() - cached_at > cache_ttl:
                self.logger.debug(f"Cache expired for key: {key}")
                cache_file.unlink(missing_ok=True)
                return None

            self.logger.debug(f"Cache hit for key: {key}")
            return cache_data.get("data")

        except Exception as e:
            self.logger.warning(f"Error getting cache for key {key}: {e}")
            return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存数据

        Args:
            key: 缓存键
            data: 要缓存的数据
            ttl: 超时时间（秒），None表示使用默认值

        Returns:
            是否成功设置缓存
        """
        try:
            cache_file = self.cache_dir / f"cache_{key}.json"
            cache_data = {
                "data": data,
                "cached_at": time.time(),
                "ttl": ttl or self.default_ttl
            }

            success = safe_json_write(cache_file, cache_data)
            if success:
                self.logger.debug(f"Cache set for key: {key}")
            return success

        except Exception as e:
            self.logger.warning(f"Error setting cache for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存数据

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        try:
            cache_file = self.cache_dir / f"cache_{key}.json"
            if cache_file.exists():
                cache_file.unlink()
                self.logger.debug(f"Cache deleted for key: {key}")
            return True

        except Exception as e:
            self.logger.warning(f"Error deleting cache for key {key}: {e}")
            return False

    def clear_all(self) -> bool:
        """清空所有缓存"""
        try:
            for cache_file in self.cache_dir.glob("cache_*.json"):
                cache_file.unlink(missing_ok=True)
            self.logger.info("All cache cleared")
            return True

        except Exception as e:
            self.logger.warning(f"Error clearing cache: {e}")
            return False

    def cleanup_expired(self) -> int:
        """清理过期的缓存文件"""
        cleaned_count = 0
        try:
            current_time = time.time()
            for cache_file in self.cache_dir.glob("cache_*.json"):
                try:
                    cache_data = safe_json_read(cache_file)
                    if cache_data:
                        cached_at = cache_data.get("cached_at", 0)
                        ttl = cache_data.get("ttl", self.default_ttl)

                        if current_time - cached_at > ttl:
                            cache_file.unlink(missing_ok=True)
                            cleaned_count += 1
                except Exception:
                    # 如果无法读取文件，也删除它
                    cache_file.unlink(missing_ok=True)
                    cleaned_count += 1

            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} expired cache files")

        except Exception as e:
            self.logger.warning(f"Error during cache cleanup: {e}")

        return cleaned_count