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


class PlatformManager:
    """平台管理器"""

    def __init__(self, config_manager):
        """初始化平台管理器"""
        self.config_manager = config_manager
        self.logger = get_logger("platform_manager")

    def get_platform_by_name(self, platform_name: str, platform_config: Dict[str, Any]):
        """根据平台名称创建平台实例"""
        try:
            # 基础平台实现，后续可以扩展为具体的平台类
            return BasePlatform(platform_name, platform_config)
        except Exception as e:
            self.logger.error(f"Failed to create platform {platform_name}: {e}")
            return None


class BasePlatform:
    """基础平台类"""

    def __init__(self, platform_name: str, config: Dict[str, Any]):
        """初始化基础平台"""
        self.name = platform_name
        self.config = config
        self.logger = get_logger(f"platform.{platform_name}")

    def fetch_balance_data(self) -> Optional[Dict[str, Any]]:
        """获取余额数据"""
        try:
            # 检查认证信息
            auth_token = self._get_auth_token()
            if not auth_token:
                return None

            # 根据平台类型调用不同的API
            if self.name.lower() == "gaccode":
                return self._fetch_gaccode_balance(auth_token)
            elif self.name.lower() == "deepseek":
                return self._fetch_deepseek_balance(auth_token)
            elif self.name.lower() == "kimi":
                return self._fetch_kimi_balance(auth_token)
            elif self.name.lower() == "siliconflow":
                return self._fetch_siliconflow_balance(auth_token)
            else:
                self.logger.warning(f"Unsupported platform: {self.name}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching balance data: {e}")
            return None

    def _get_auth_token(self) -> Optional[str]:
        """获取认证令牌"""
        # 按优先级获取认证信息
        return (
            self.config.get("api_key") or
            self.config.get("auth_token") or
            self.config.get("login_token")
        )

    def _fetch_gaccode_balance(self, token: str) -> Optional[Dict[str, Any]]:
        """获取 GAC Code 余额"""
        try:
            import requests
            api_base = self.config.get("api_base_url", "https://relay05.gaccode.com/claudecode")
            url = f"{api_base}/api/balance"

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "balance": data.get("balance", 0),
                    "limit": data.get("limit", 0),
                    "currency": "points"
                }
            else:
                self.logger.warning(f"GAC Code API error: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching GAC Code balance: {e}")
            return None

    def _fetch_deepseek_balance(self, token: str) -> Optional[Dict[str, Any]]:
        """获取 DeepSeek 余额"""
        try:
            import requests
            api_base = self.config.get("api_base_url", "https://api.deepseek.com/anthropic")
            url = f"{api_base}/api/v1/user/balance"

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                balance = data.get("balance", 0)
                currency = data.get("currency", "CNY")
                return {
                    "balance": float(balance),
                    "currency": currency
                }
            else:
                self.logger.warning(f"DeepSeek API error: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching DeepSeek balance: {e}")
            return None

    def _fetch_kimi_balance(self, token: str) -> Optional[Dict[str, Any]]:
        """获取 Kimi 余额"""
        try:
            import requests
            api_base = self.config.get("api_base_url", "https://api.moonshot.cn/anthropic")
            url = f"{api_base}/api/v1/user/balance"

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                balance = data.get("balance", 0)
                currency = data.get("currency", "CNY")
                return {
                    "balance": float(balance),
                    "currency": currency
                }
            else:
                self.logger.warning(f"Kimi API error: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching Kimi balance: {e}")
            return None

    def _fetch_siliconflow_balance(self, token: str) -> Optional[Dict[str, Any]]:
        """获取 SiliconFlow 余额"""
        try:
            import requests
            api_base = self.config.get("api_base_url", "https://api.siliconflow.cn/")
            url = f"{api_base}/api/v1/user/balance"

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                balance = data.get("balance", 0)
                currency = data.get("currency", "CNY")
                return {
                    "balance": float(balance),
                    "currency": currency
                }
            else:
                self.logger.warning(f"SiliconFlow API error: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching SiliconFlow balance: {e}")
            return None

    def close(self):
        """关闭平台实例，清理资源"""
        pass