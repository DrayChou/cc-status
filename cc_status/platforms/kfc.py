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
        """Fetch balance data from KFC API using auth_token"""
        try:
            # 只使用auth_token（KFC的API Key）
            auth_token = self.config.get("auth_token")

            # 验证是否有可用的token
            if not auth_token:
                self.logger.debug(
                    "KFC auth_token not configured, skipping balance query"
                )
                return None

            self.logger.debug(
                "Starting KFC balance fetch",
                {
                    "has_auth_token": bool(auth_token),
                    "auth_token_length": len(auth_token) if auth_token else 0,
                },
            )

            # 使用auth_token调用Kimi标准API
            self.logger.debug("Attempting balance query with auth_token")
            balance_data = self._make_kfc_request(auth_token)

            if balance_data:
                self.logger.info(
                    "KFC balance data fetched successfully with auth_token",
                    {
                        "data_keys": list(balance_data.keys()),
                        "data_type": type(balance_data).__name__,
                        "has_balance_data": "data" in balance_data,
                    },
                )
                return balance_data
            else:
                self.logger.warning("KFC auth_token query failed")

            return None

        except Exception as e:
            self.logger.error(f"KFC balance fetch failed: {e}")
            return None

    def _make_kfc_request(self, token: str) -> Optional[Dict[str, Any]]:
        """Make KFC usage query using KFC-specific API with auth_token"""
        import requests

        # KFC专用API端点 - 查询使用量
        url = "https://www.kimi.com/coding/kimi.billing.v1.BillingService/GetUsage"

        # Request headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/142.0.0.0 Safari/537.36'
            ),
        }

        # Request data - 使用auth_token作为credential key
        data = {
            "credential": {
                "key": token,
                "scope": "FEATURE_CODING"
            }
        }

        try:
            self.logger.debug(f"Making KFC API request to: {url}")
            self.logger.debug(
                f"Using auth_token (first 10 chars): {token[:10]}..."
            )
            response = requests.post(url, headers=headers, json=data, timeout=10)

            self.logger.debug(f"KFC API response status: {response.status_code}")

            if response.status_code == 200:
                json_data = response.json()
                self.logger.debug(f"KFC API response: {json_data}")
                return json_data
            else:
                self.logger.warning(
                    f"KFC API request failed with status "
                    f"{response.status_code}: {response.text}"
                )
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
            return "\033[91mNoData\033[0m"

        self.logger.debug(
            "Starting KFC balance formatting",
            {
                "balance_data_keys": list(balance_data.keys()),
                "balance_data_type": type(balance_data).__name__,
            },
        )

        try:
            # KFC API 返回直接的 usage 对象（不是usages数组）
            usage = balance_data.get("usage", {})
            if not usage:
                self.logger.warning("No usage data found in KFC response")
                return "\033[91mNoUsage\033[0m"

            # 解析使用数据
            limit_str = usage.get("limit", "0")
            used_str = usage.get("used", "0")
            remaining_str = usage.get("remaining", "0")
            reset_time = usage.get("resetTime", "")  # 获取重置时间

            # 转换为整数
            try:
                limit = int(limit_str)
                used = int(used_str)
                remaining = int(remaining_str)
            except (ValueError, TypeError):
                self.logger.warning(
                    f"Failed to parse usage numbers: "
                    f"limit={limit_str}, used={used_str}, "
                    f"remaining={remaining_str}"
                )
                return "\033[91mParseError\033[0m"

            self.logger.debug(
                "KFC usage data structure",
                {
                    "limit": limit,
                    "used": used,
                    "remaining": remaining,
                },
            )

            # 格式化重置时间
            reset_display = ""
            if reset_time:
                try:
                    from datetime import datetime
                    # 解析ISO格式时间：2025-11-22T03:21:23.580297585Z
                    if 'T' in reset_time:
                        # 提取日期和时间部分
                        date_part = reset_time.split('T')[0]  # 2025-11-22
                        time_part = (
                            reset_time.split('T')[1].split('.')[0]
                        )  # 03:21:23

                        # 格式化时间
                        date_obj = datetime.strptime(date_part, "%Y-%m-%d")
                        time_obj = datetime.strptime(time_part, "%H:%M:%S")

                        # 检查是否是今天
                        today = datetime.now()
                        if date_obj.date() == today.date():
                            # 今天刷新，只显示时间 (HH:MM)
                            reset_short = time_obj.strftime('%H:%M')
                        else:
                            # 其他日期显示月-日 时:分
                            reset_short = (
                                f"{date_obj.strftime('%m-%d')} "
                                f"{time_obj.strftime('%H:%M')}"
                            )

                        reset_display = f"({reset_short})"  # 使用圆括号
                    else:
                        reset_display = f"({reset_time[:16]})"  # 备用方案
                except Exception as e:
                    self.logger.warning(f"Failed to parse reset time: {e}")
                    reset_display = f"({reset_time[:16]})"
            else:
                reset_display = "(NoReset)"

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

            # 格式化显示 - 显示重置时间而不是百分比（去掉平台名称前缀，由formatter统一添加）
            balance_str = f"{color}{remaining}/{limit}{reset}{reset_display}"

            self.logger.debug(
                "KFC balance formatting completed",
                {
                    "final_display": balance_str,
                    "color_used": color_name,
                    "remaining": remaining,
                    "limit": limit,
                    "reset_time": reset_time,
                },
            )

            return balance_str
        except Exception as e:
            self.logger.error(f"KFC balance formatting failed: {e}")
            return f"Error({str(e)[:20]})"

    def format_subscription_display(
        self, subscription_data: Dict[str, Any]
    ) -> str:
        """Format KFC subscription for display"""
        if subscription_data is None:
            self.logger.info("No subscription data available for display")
            return "\033[94mUsageBased\033[0m"

        try:
            # KFC是按使用量计费，显示使用状态
            color = "\033[94m"  # 蓝色
            reset = "\033[0m"

            subscription_text = "Coding.Usage"
            return f"{color}{subscription_text}{reset}"
        except Exception as e:
            self.logger.error(f"KFC subscription formatting failed: {e}")
            return f"Error({str(e)[:20]})"
