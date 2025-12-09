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
from .minimaxi import MinimaxiPlatform


class PlatformManager:
    """平台管理器"""

    def __init__(self, config_manager):
        """初始化平台管理器"""
        self.config_manager = config_manager
        self.logger = get_logger("platform_manager")

    def get_platform_by_name(self, platform_name: str, platform_config: Dict[str, Any]):
        """根据平台名称和配置创建平台实例

        Args:
            platform_name: 平台实例ID（如 "minimaxi", "minimaxi-user1", "gaccode"）
            platform_config: 平台配置，包含 platform_type 字段

        Returns:
            平台实例或 None
        """
        try:
            # 获取平台类型，优先使用 platform_type
            platform_type = platform_config.get("platform_type", "").lower()

            # 如果没有 platform_type，尝试从平台名称推断
            if not platform_type:
                platform_type = self._infer_platform_type(platform_name)

            # 根据平台类型创建对应的平台实例
            if platform_type == "deepseek":
                platform = DeepSeekPlatform(platform_name, platform_config)
                return platform
            elif platform_type == "kimi":
                platform = KimiPlatform(platform_name, platform_config)
                return platform
            elif platform_type == "glm":
                platform = GLMPlatform(platform_name, platform_config)
                return platform
            elif platform_type == "siliconflow":
                platform = SiliconFlowPlatform(platform_name, platform_config)
                return platform
            elif platform_type == "kfc":
                platform = KfcPlatform(platform_name, platform_config)
                return platform
            elif platform_type == "minimaxi":
                platform = MinimaxiPlatform(platform_name, platform_config)
                return platform
            elif platform_type == "gaccode":
                # GAC Code 使用原有的基础实现
                from .base import BasePlatform

                platform = BasePlatform(platform_name, platform_config)
                return platform
            elif platform_type == "doubao":
                # 豆包使用基础实现
                from .base import BasePlatform
                platform = BasePlatform(platform_name, platform_config)
                return platform
            elif platform_type == "vanchin":
                # Vanchin 使用原有的基础实现
                from .base import BasePlatform
                platform = BasePlatform(platform_name, platform_config)
                return platform
            else:
                self.logger.warning(
                    f"Unsupported platform type: {platform_type} (platform_name: {platform_name})"
                )
                return None
        except Exception as e:
            self.logger.error(f"Failed to create platform {platform_name}: {e}")
            return None

    def _infer_platform_type(self, platform_name: str) -> str:
        """从平台名称推断平台类型

        支持多种命名模式：
        - exact match: "minimaxi" -> "minimaxi"
        - with suffix: "minimaxi-user1" -> "minimaxi"
        - with prefix: "gaccodeuser1" -> "gaccode"

        Args:
            platform_name: 平台实例ID

        Returns:
            推断的平台类型
        """
        platform_name_lower = platform_name.lower()

        # 已知平台类型列表（按长度排序，优先匹配更长的类型）
        known_types = [
            "siliconflow", "minimaxi", "deepseek", "kimi",
            "glm", "kfc", "gaccode", "doubao", "vanchin"
        ]

        # 1. 精确匹配
        if platform_name_lower in known_types:
            return platform_name_lower

        # 2. 查找以已知类型开头的平台名称（使用分隔符）
        for known_type in known_types:
            if platform_name_lower.startswith(known_type) and \
               len(platform_name_lower) > len(known_type):
                # 检查是否有分隔符
                next_char = platform_name_lower[len(known_type)]
                if next_char in "-_":
                    return known_type

        # 3. 查找以已知类型结尾的平台名称（使用分隔符）
        for known_type in known_types:
            if platform_name_lower.endswith(known_type) and \
               len(platform_name_lower) > len(known_type):
                # 检查是否有分隔符
                prev_char = platform_name_lower[-(len(known_type) + 1)]
                if prev_char in "-_":
                    return known_type

        # 4. 查找包含已知类型的平台名称（更严格的匹配）
        for known_type in known_types:
            if known_type in platform_name_lower:
                # 特殊处理：避免误匹配
                if known_type == "siliconflow":
                    # 必须包含 "silicon" 或完整匹配
                    if "silicon" in platform_name_lower:
                        return known_type
                elif known_type == "minimaxi":
                    # 必须包含 "minimax" 或完整匹配
                    if "minimax" in platform_name_lower:
                        return known_type
                elif known_type == "gaccode":
                    # 必须以 "gaccode" 开头或包含完整匹配
                    if platform_name_lower.startswith("gaccode") or \
                       platform_name_lower.endswith("gaccode") or \
                       platform_name_lower == "gaccode":
                        return known_type
                else:
                    # 其他类型，使用完整匹配
                    if platform_name_lower == known_type:
                        return known_type

        # 5. 默认返回原始名称（保持向后兼容）
        return platform_name_lower

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

    def fetch_usage_data(self, platform_instance) -> Optional[Dict[str, Any]]:
        """获取平台用量数据的代理方法"""
        if platform_instance and hasattr(platform_instance, 'fetch_usage_data'):
            return platform_instance.fetch_usage_data()
        else:
            self.logger.debug(f"Platform {platform_instance.name if hasattr(platform_instance, 'name') else 'unknown'} does not have fetch_usage_data method")
            return None

    def close(self):
        """关闭平台管理器，清理资源"""
        pass