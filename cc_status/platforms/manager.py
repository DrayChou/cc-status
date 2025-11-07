#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Platform Manager - 平台管理器
负责管理和创建各种平台实例
"""

from typing import Dict, Any, Optional
import sys
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.api_lock import get_api_lock, LockKeys

# 导入新的平台实现
from .deepseek import DeepSeekPlatform
from .kimi import KimiPlatform
from .glm import GLMPlatform
from .siliconflow import SiliconFlowPlatform
from .kfc import KfcPlatform


class PlatformManager:
    """平台管理器"""

    def __init__(self, config_manager):
        """初始化平台管理器"""
        self.config_manager = config_manager
        self.logger = get_logger("platform_manager")

    def get_platform_by_name(self, platform_name: str, platform_config: Dict[str, Any]):
        """根据平台名称创建平台实例"""
        try:
            # 根据平台名称创建对应的平台实例
            if platform_name.lower() == "deepseek":
                platform = DeepSeekPlatform(platform_name, platform_config)
                return platform
            elif platform_name.lower() == "kimi":
                platform = KimiPlatform(platform_name, platform_config)
                return platform
            elif platform_name.lower() == "glm":
                platform = GLMPlatform(platform_name, platform_config)
                return platform
            elif platform_name.lower() == "siliconflow":
                platform = SiliconFlowPlatform(platform_name, platform_config)
                return platform
            elif platform_name.lower() == "kfc":
                platform = KfcPlatform(platform_name, platform_config)
                return platform
            elif platform_name.lower() == "gaccode":
                # GAC Code 使用原有的基础实现
                from .base import BasePlatform
                
                platform = BasePlatform(platform_name, platform_config)
                return platform
            elif platform_name.lower() == "vanchin":
                # Vanchin 使用原有的基础实现
                from .base import BasePlatform
                platform = BasePlatform(platform_name, platform_config)
                return platform
            else:
                self.logger.warning(f"Unsupported platform: {platform_name}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to create platform {platform_name}: {e}")
            return None

    def fetch_balance_data(self, platform_instance) -> Optional[Dict[str, Any]]:
        """获取平台余额数据"""
        if platform_instance and hasattr(platform_instance, 'fetch_balance_data'):
            return platform_instance.fetch_balance_data()
        else:
            self.logger.warning(f"Platform {platform_instance.name if hasattr(platform_instance, 'name') else 'unknown'} does not have fetch_balance_data method, no balance data available")
            return None

    def fetch_subscription_data(self, platform_instance) -> Optional[Dict[str, Any]]:
        """获取平台订阅数据的代理方法"""
        if platform_instance and hasattr(platform_instance, 'fetch_subscription_data'):
            return platform_instance.fetch_subscription_data()
        else:
            self.logger.warning(f"Platform {platform_instance.name if hasattr(platform_instance, 'name') else 'unknown'} does not have fetch_subscription_data method")
            return None

    def close(self):
        """关闭平台管理器，清理资源"""
        pass