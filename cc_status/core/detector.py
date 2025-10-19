#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Platform Detector - 平台检测器
检测当前使用的平台
"""

from typing import Optional, Dict, Any
from ..utils.logger import get_logger


class PlatformDetector:
    """平台检测器"""

    def __init__(self):
        """初始化平台检测器"""
        self.logger = get_logger("detector")

    def detect_platform(self, session_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        检测当前平台

        Args:
            session_id: 会话ID
            config: 配置信息

        Returns:
            检测到的平台名称
        """
        try:
            # 简单的平台检测逻辑，可以后续扩展
            if session_id:
                return self._detect_from_session_id(session_id)
            else:
                return self._get_default_platform()

        except Exception as e:
            self.logger.error(f"Error detecting platform: {e}")
            return None

    def _detect_from_session_id(self, session_id: str) -> Optional[str]:
        """从session ID检测平台"""
        try:
            # 检查session ID前缀
            if len(session_id) >= 2:
                prefix = session_id[:2].lower()
                prefix_map = {
                    "01": "gaccode",
                    "02": "deepseek",
                    "03": "kimi",
                    "04": "siliconflow",
                    "05": "local_proxy"
                }
                return prefix_map.get(prefix)

        except Exception as e:
            self.logger.warning(f"Error detecting from session ID: {e}")

        return None

    def _get_default_platform(self) -> Optional[str]:
        """获取默认平台"""
        try:
            from .config import ConfigManager
            config_manager = ConfigManager()
            platforms_config = config_manager.get_platforms_config()
            return platforms_config.get("default_platform", "gaccode")

        except Exception as e:
            self.logger.warning(f"Error getting default platform: {e}")
            return "gaccode"

    def get_platform_info(self, platform_name: str, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取平台信息

        Args:
            platform_name: 平台名称
            session_id: 会话ID

        Returns:
            平台信息字典
        """
        try:
            from .config import ConfigManager
            config_manager = ConfigManager()
            platform_config = config_manager.get_platform_config(platform_name)

            if not platform_config:
                return None

            return {
                "platform": platform_name,
                "name": platform_config.get("name", platform_name),
                "model": platform_config.get("model", "unknown"),
                "api_base_url": platform_config.get("api_base_url", ""),
                "has_auth": any([
                    platform_config.get("api_key"),
                    platform_config.get("auth_token"),
                    platform_config.get("login_token")
                ])
            }

        except Exception as e:
            self.logger.error(f"Error getting platform info for {platform_name}: {e}")
            return None