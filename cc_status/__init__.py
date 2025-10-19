#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-status - Claude Code Status Bar Manager
"""

__version__ = "1.0.0"
__author__ = "Claude Code Community"
__description__ = "Claude Code Status Bar Manager"

from .core.config import ConfigManager
from .core.cache import CacheManager
from .core.detector import PlatformDetector

__all__ = [
    "ConfigManager",
    "CacheManager",
    "PlatformDetector",
    "__version__",
]