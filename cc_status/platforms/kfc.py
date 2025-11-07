#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KFC (Kimi For Coding) platform implementation
"""

import json
from typing import Dict, Any, Optional
from .base import BasePlatform
from ..utils.logger import get_logger


class KfcPlatform(BasePlatform):
    """KFC (Kimi For Coding) platform implementation"""

    def __init__(self, platform_name: str, config: Dict[str, Any]):
        """初始化KFC平台"""
        self._name = "kfc"
        self.config = config
        self.logger = get_logger(f"platform.{platform_name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def api_base(self) -> str:
        # KFC使用Kimi的API地址
        return "https://www.kimi.com"

    def detect_platform(self, session_info: Dict[str, Any], token: str) -> bool:
        """Detect KFC platform"""
        # 方法1: 检查模型是否是kimi-for-coding
        try:
            model_id = session_info.get("model", {}).get("id", "")
            if "kimi-for-coding" in model_id.lower() or "kfc" in model_id.lower():
                self.logger.info(
                    "KFC detected by model ID",
                    {"method": "model_id", "model_id": model_id},
                )
                return True
        except Exception as e:
            self.logger.debug(f"Model ID detection failed: {e}")

        # 方法2: 检查配置中是否显式指定了kfc平台
        platform_type = self.config.get("platform_type", "").lower()
        if platform_type == "kfc" or platform_type == "kimi-coding":
            self.logger.info(
                "KFC detected by config",
                {"method": "config_platform_type", "platform_type": platform_type},
            )
            return True

        # 方法3: 检查API基础URL是否包含kimi.com
        api_base = self.config.get("api_base_url", "")
        if "kimi.com" in api_base and "coding" in api_base.lower():
            self.logger.info(
                "KFC detected by API base URL",
                {"method": "api_base_url", "api_base_url": api_base},
            )
            return True

        self.logger.debug("KFC platform not detected")
        return False

    def fetch_balance_data(self) -> Optional[Dict[str, Any]]:
        """Fetch balance data from KFC API using the provided curl command pattern"""
        try:
            auth_token = self._get_auth_token()
            self.logger.debug(
                "Starting KFC balance fetch",
                {"token_length": len(auth_token) if auth_token else 0},
            )

            # 使用你提供的API端点进行余额查询
            balance_data = self._make_kfc_request()

            if balance_data:
                self.logger.info(
                    "KFC balance data fetched successfully",
                    {
                        "data_keys": list(balance_data.keys()),
                        "data_type": type(balance_data).__name__,
                        "has_usages": "usages" in balance_data,
                    },
                )
                return balance_data
            else:
                self.logger.warning(
                    "KFC balance API returned None",
                    {"possible_cause": "API request failed or returned empty data"},
                )
                return None

        except Exception as e:
            self.logger.error(f"KFC balance fetch failed: {e}")
            return None

    def _make_kfc_request(self) -> Optional[Dict[str, Any]]:
        """Make KFC-specific API request"""
        import requests

        # KFC需要单独的balance_token用于余额查询
        balance_token = self.config.get("balance_token") or self.config.get("login_token")
        if not balance_token:
            self.logger.warning("No balance/login token available for KFC")
            return None

        # KFC API端点
        url = "https://www.kimi.com/apiv2/kimi.gateway.billing.v1.BillingService/GetUsages"

        # 请求头 - 基于你提供的curl命令
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh-TW;q=0.9,zh-HK;q=0.8,zh;q=0.7,en-GB;q=0.6,en-US;q=0.5,en;q=0.4,ja;q=0.3,fr-FR;q=0.2,fr;q=0.1',
            'authorization': f'Bearer {balance_token}',
            'cache-control': 'no-cache',
            'connect-protocol-version': '1',
            'content-type': 'application/json',
            'origin': 'https://www.kimi.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'r-timezone': 'Asia/Shanghai',
            'referer': 'https://www.kimi.com/membership/pricing?from=upgrade_nav',
            'sec-ch-ua': '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
            'x-language': 'zh-CN',
            'x-msh-platform': 'web',
        }

        # 请求数据
        data = {
            "scope": ["FEATURE_CODING"]
        }

        try:
            self.logger.debug(f"Making KFC API request to: {url}")
            self.logger.debug(f"Using balance token (first 10 chars): {balance_token[:10]}...")
            response = requests.post(url, headers=headers, json=data, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"KFC API request failed with status {response.status_code}: {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"KFC API request error: {e}")
            return None

    def fetch_subscription_data(self) -> Optional[Dict[str, Any]]:
        """KFC uses usage-based billing with coding features"""
        # KFC使用基于使用量的计费模式，专注于编程功能
        return None

    def format_balance_display(self, balance_data: Dict[str, Any]) -> str:
        """Format KFC balance for display"""
        # 处理空数据情况
        if balance_data is None:
            self.logger.info("No balance data available for display")
            return "KFC:\033[91mNoData\033[0m"

        self.logger.debug(
            "Starting KFC balance formatting",
            {
                "balance_data_keys": list(balance_data.keys()),
                "balance_data_type": type(balance_data).__name__,
            },
        )

        try:
            # KFC API 返回 usages 数组
            usages = balance_data.get("usages", [])
            if not usages:
                self.logger.warning("No usages data found in KFC response")
                return "KFC:\033[91mNoUsage\033[0m"

            # 获取FEATURE_CODING的使用情况
            coding_usage = None
            for usage in usages:
                if usage.get("scope") == "FEATURE_CODING":
                    coding_usage = usage.get("detail", {})
                    break

            if not coding_usage:
                self.logger.warning("No FEATURE_CODING usage found")
                return "KFC:\033[91mNoCodingUsage\033[0m"

            limit = int(coding_usage.get("limit", 0))
            used = int(coding_usage.get("used", 0))
            remaining = int(coding_usage.get("remaining", 0))

            self.logger.debug(
                "KFC usage data structure",
                {
                    "limit": limit,
                    "used": used,
                    "remaining": remaining,
                },
            )

            # 计算使用率
            if limit > 0:
                usage_percentage = (used / limit) * 100
            else:
                usage_percentage = 0

            # 颜色代码基于剩余次数
            if remaining <= 50:
                color = "\033[91m"  # 红色
                color_name = "red"
            elif remaining <= 200:
                color = "\033[93m"  # 黄色
                color_name = "yellow"
            else:
                color = "\033[92m"  # 绿色
                color_name = "green"

            reset = "\033[0m"

            # 格式化显示
            balance_str = f"KFC:{color}{remaining}/{limit}({usage_percentage:.1f}%){reset}"

            self.logger.debug(
                "KFC balance formatting completed",
                {
                    "final_display": balance_str,
                    "color_used": color_name,
                    "remaining": remaining,
                    "limit": limit,
                    "usage_percentage": usage_percentage,
                },
            )

            return balance_str
        except Exception as e:
            self.logger.error(f"KFC balance formatting failed: {e}")
            return f"KFC:Error({str(e)[:20]})"

    def format_subscription_display(self, subscription_data: Dict[str, Any]) -> str:
        """Format KFC subscription for display"""
        if subscription_data is None:
            self.logger.info("No subscription data available for display")
            return "KFC.Sub:\033[94mUsageBased\033[0m"

        try:
            # KFC是按使用量计费，显示使用状态
            reset_color = "\033[0m"
            color = "\033[94m"  # 蓝色

            subscription_text = "Coding.Usage"
            return f"{color}{subscription_text}{reset}"
        except Exception as e:
            self.logger.error(f"KFC subscription formatting failed: {e}")
            return f"KFC.Sub:Error({str(e)[:20]})"