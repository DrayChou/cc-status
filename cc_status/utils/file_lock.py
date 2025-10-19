#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File locking utilities for safe JSON operations
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


class FileLock:
    """简单的文件锁实现"""

    def __init__(self, file_path: Path, timeout: float = 5.0):
        self.file_path = file_path
        self.timeout = timeout
        self.lock_file = file_path.with_suffix(file_path.suffix + '.lock')
        self.lock_fd = None

    def __enter__(self):
        """获取文件锁"""
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                # Windows兼容的文件锁实现
                if not self.lock_file.exists():
                    # 尝试创建锁文件
                    self.lock_file.touch()
                    return self
                else:
                    # 检查锁文件是否过期
                    try:
                        lock_age = time.time() - self.lock_file.stat().st_mtime
                        if lock_age > self.timeout:
                            # 锁文件过期，删除并重新创建
                            self.lock_file.unlink(missing_ok=True)
                            self.lock_file.touch()
                            return self
                    except OSError:
                        pass

                    # 等待一段时间后重试
                    time.sleep(0.1)
                    continue
            except (OSError, IOError) as e:
                time.sleep(0.1)
                continue

        raise TimeoutError(f"Could not acquire lock on {self.file_path} within {self.timeout} seconds")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """释放文件锁"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except OSError:
            pass


def safe_json_read(file_path: Path, default: Any = None) -> Any:
    """安全读取JSON文件"""
    if not file_path.exists():
        return default

    try:
        with FileLock(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError, TimeoutError) as e:
        # 如果读取失败，返回默认值
        return default


def safe_json_write(file_path: Path, data: Any) -> bool:
    """安全写入JSON文件"""
    try:
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with FileLock(file_path):
            # 写入临时文件，然后原子性重命名
            temp_file = file_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 原子性重命名
            temp_file.replace(file_path)

        return True
    except (IOError, TimeoutError) as e:
        return False