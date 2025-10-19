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
        api_lock = get_api_lock()
        lock_key = LockKeys.platform_balance(self.name)

        try:
            # 使用API锁防止并发调用
            with api_lock.lock(lock_key, timeout=30):
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
                elif self.name.lower() == "glm":
                    return self._fetch_glm_balance(auth_token)
                else:
                    self.logger.warning(f"Unsupported platform: {self.name}")
                    return None

        except TimeoutError:
            self.logger.warning(f"Timeout waiting for API lock: {lock_key}")
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
            api_base = self.config.get("api_base_url", "https://api.deepseek.com")
            url = f"{api_base}/user/balance"

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # DeepSeek API 返回格式: {"balance_infos": [{"total_balance": 45.67, "currency": "CNY"}]}
                balance_infos = data.get("balance_infos", [])
                if balance_infos:
                    primary_balance = balance_infos[0]
                    return {
                        "balance": float(primary_balance.get("total_balance", 0)),
                        "currency": primary_balance.get("currency", "CNY")
                    }
                else:
                    return None
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
            api_base = self.config.get("api_base_url", "https://api.moonshot.cn/v1")
            url = f"{api_base}/users/me/balance"

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Kimi API 返回格式: {"code": 0, "data": {"available_balance": 23.40, "currency": "CNY"}}
                if data.get("code") == 0 and "data" in data:
                    balance_data = data["data"]
                    return {
                        "balance": float(balance_data.get("available_balance", 0)),
                        "currency": "CNY"
                    }
                else:
                    return None
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

    def _fetch_glm_balance(self, token: str) -> Optional[Dict[str, Any]]:
        """获取 GLM 余额"""
        try:
            import requests
            api_base = self.config.get("api_base_url", "https://open.bigmodel.cn/api/anthropic")
            url = f"{api_base}/user/balance"

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # GLM API 返回格式可能类似: {"balance": 45.67, "currency": "CNY"}
                return {
                    "balance": float(data.get("balance", 0)),
                    "currency": data.get("currency", "CNY")
                }
            else:
                self.logger.warning(f"GLM API error: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching GLM balance: {e}")
            return None

    def fetch_subscription_data(self) -> Optional[Dict[str, Any]]:
        """获取订阅数据"""
        try:
            # 检查认证信息
            auth_token = self._get_auth_token()
            if not auth_token:
                return None

            # 根据平台类型调用不同的API
            if self.name.lower() == "glm":
                return self._fetch_glm_subscription(auth_token)
            elif self.name.lower() == "deepseek":
                return self._fetch_deepseek_subscription(auth_token)
            elif self.name.lower() == "kimi":
                return self._fetch_kimi_subscription(auth_token)
            else:
                # 其他平台暂时不支持订阅信息
                return None

        except Exception as e:
            self.logger.error(f"Error fetching subscription data: {e}")
            return None

    def _fetch_glm_subscription(self, token: str) -> Optional[Dict[str, Any]]:
        """获取 GLM 订阅信息"""
        try:
            import requests
            api_base = self.config.get("api_base_url", "https://open.bigmodel.cn/api/anthropic")
            url = f"{api_base}/users/me"

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # 解析GLM订阅信息
                return {
                    "plan": data.get("plan", "Unknown"),
                    "expiry": data.get("expiry", ""),
                    "model": data.get("model", "GLM")
                }
            else:
                self.logger.warning(f"GLM subscription API error: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching GLM subscription: {e}")
            return None

    def _fetch_deepseek_subscription(self, token: str) -> Optional[Dict[str, Any]]:
        """获取 DeepSeek 订阅信息"""
        try:
            import requests
            api_base = self.config.get("api_base_url", "https://api.deepseek.com")
            url = f"{api_base}/user/info"

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "plan": data.get("plan", "Free"),
                    "expiry": data.get("expiry", "")
                }
            else:
                self.logger.warning(f"DeepSeek subscription API error: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching DeepSeek subscription: {e}")
            return None

    def _fetch_kimi_subscription(self, token: str) -> Optional[Dict[str, Any]]:
        """获取 Kimi 订阅信息"""
        try:
            import requests
            api_base = self.config.get("api_base_url", "https://api.moonshot.cn/v1")
            url = f"{api_base}/users/me"

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and "data" in data:
                    user_data = data["data"]
                    return {
                        "plan": user_data.get("plan", "Free"),
                        "expiry": user_data.get("expire_date", "")
                    }
                else:
                    return None
            else:
                self.logger.warning(f"Kimi subscription API error: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching Kimi subscription: {e}")
            return None

    def close(self):
        """关闭平台实例，清理资源"""
        pass