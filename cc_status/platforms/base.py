#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Platform class
"""

from typing import Dict, Any, Optional
from ..utils.logger import get_logger


class BasePlatform:
    """基础平台类"""

    def __init__(self, platform_name: str, config: Dict[str, Any]):
        """初始化基础平台"""
        self.name = platform_name
        self.config = config
        self.logger = get_logger(f"platform.{platform_name}")

    def _get_auth_token(self) -> Optional[str]:
        """获取认证令牌"""
        # 按优先级获取认证信息
        return (
            self.config.get("api_key") or
            self.config.get("auth_token") or
            self.config.get("login_token")
        )

    def make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """发起API请求"""
        import requests

        # 获取认证令牌
        auth_token = self._get_auth_token()
        if not auth_token:
            self.logger.warning("No authentication token available")
            return None

        # 使用平台特定的 API 基础地址
        if hasattr(self, 'api_base'):
            api_base = self.api_base
        else:
            api_base = self.config.get("api_base_url", "")

        if not api_base:
            self.logger.error("No API base URL configured")
            return None

        url = f"{api_base}{endpoint}"
        headers = {"Authorization": f"Bearer {auth_token}"}

        try:
            self.logger.debug(f"Making API request to: {url}")
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"API request failed with status {response.status_code}: {url}")
                return None

        except Exception as e:
            self.logger.error(f"API request error: {e}")
            return None

    def close(self):
        """关闭平台，清理资源"""
        pass

    def fetch_balance_data(self) -> Optional[Dict[str, Any]]:
        """获取余额数据 - 默认实现，子类可重写"""
        return None

    def fetch_subscription_data(self) -> Optional[Dict[str, Any]]:
        """获取订阅数据 - 默认实现，子类可重写"""
        return None