#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger utility for cc-status
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """获取配置好的logger实例"""
    logger = logging.getLogger(f"cc-status.{name}")

    if not logger.handlers:
        # 避免重复添加handler
        logger.setLevel(level)

        # 创建formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)  # 控制台只显示WARNING及以上
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 文件handler
        try:
            log_dir = Path.home() / ".claude" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / "cc-status.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            # 如果无法创建日志文件，继续使用控制台输出
            pass

        logger.propagate = False

    return logger


def log_message(component: str, level: str, message: str, extra_data: Optional[dict] = None):
    """便捷的日志记录函数"""
    logger = get_logger(component)
    log_level = getattr(logging, level.upper(), logging.INFO)

    if extra_data:
        message = f"{message} | Extra: {extra_data}"

    logger.log(log_level, message)