#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kimi platform implementation
"""

from typing import Dict, Any, Optional
from .base import BasePlatform
from ..utils.logger import get_logger


class KimiPlatform(BasePlatform):
    """Kimi platform implementation"""

    def __init__(self, platform_name: str, config: Dict[str, Any]):
        """初始化Kimi平台"""
        self._name = "kimi"
        self.config = config
        self.logger = get_logger(f"platform.{platform_name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def api_base(self) -> str:
        # Kimi余额查询使用基础API地址
        return "https://api.moonshot.cn/v1"

    def detect_platform(self, session_info: Dict[str, Any], token: str) -> bool:
        """Detect Kimi platform"""
        # 方法1: 检查模型是否是kimi系列
        try:
            model_id = session_info.get("model", {}).get("id", "")
            if "kimi" in model_id.lower() or "moonshot" in model_id.lower():
                self.logger.info(
                    "Kimi detected by model ID",
                    {"method": "model_id", "model_id": model_id},
                )
                return True
        except Exception as e:
            self.logger.debug(f"Model ID detection failed: {e}")

        # 方法2: 检查配置中是否显式指定了kimi平台
        platform_type = self.config.get("platform_type", "").lower()
        if platform_type == "kimi":
            self.logger.info(
                "Kimi detected by config",
                {"method": "config_platform_type", "platform_type": platform_type},
            )
            return True

        # 方法3: 通过token格式判断
        if token and token.startswith("sk-"):
            self.logger.debug(
                "Kimi token format detected",
                {"method": "token_prefix", "token_prefix": token[:10] + "..."},
            )
            # 注意：这里不直接返回True，因为很多平台的token都以sk-开头
            # 需要结合其他条件判断

        self.logger.debug("Kimi platform not detected")
        return False

    def fetch_balance_data(self) -> Optional[Dict[str, Any]]:
        """Fetch balance data from Kimi API"""
        try:
            auth_token = self._get_auth_token()
            self.logger.debug(
                "Starting Kimi balance fetch",
                {"token_length": len(auth_token) if auth_token else 0},
            )

            # 使用Kimi的余额查询端点
            balance_data = self.make_request("/users/me/balance")

            if balance_data:
                self.logger.info(
                    "Kimi balance data fetched successfully",
                    {
                        "data_keys": list(balance_data.keys()),
                        "data_type": type(balance_data).__name__,
                        "has_balance_infos": "balance_infos" in balance_data,
                        "is_available": balance_data.get("is_available"),
                    },
                )
                return balance_data
            else:
                self.logger.warning(
                    "Kimi balance API returned None",
                    {"possible_cause": "API request failed or returned empty data"},
                )
                return None

        except Exception as e:
            self.logger.error(f"Kimi balance fetch failed: {e}")
            return None

    def fetch_subscription_data(self) -> Optional[Dict[str, Any]]:
        """Kimi uses pay-as-you-go billing, no subscription concept"""
        # Kimi使用按量付费模式，没有订阅概念
        return None

    def format_balance_display(self, balance_data: Dict[str, Any]) -> str:
        """Format Kimi balance for display"""
        # 处理空数据情况
        if balance_data is None:
            self.logger.info("No balance data available for display")
            return "Kimi.B:\033[91mNoData\033[0m"

        self.logger.debug(
            "Starting Kimi balance formatting",
            {
                "balance_data_keys": list(balance_data.keys()),
                "balance_data_type": type(balance_data).__name__,
            },
        )

        try:
            # Kimi API 返回结构可能不同，需要适配
            balance = balance_data.get("balance", 0)
            currency = balance_data.get("currency", "CNY")

            self.logger.debug(
                "Kimi balance data structure",
                {
                    "balance": balance,
                    "currency": currency,
                },
            )

            # 颜色代码基于余额
            if currency == "CNY":
                if balance <= 10:
                    color = "\033[91m"  # 红色
                    color_name = "red"
                elif balance <= 50:
                    color = "\033[93m"  # 黄色
                    color_name = "yellow"
                else:
                    color = "\033[92m"  # 绿色
                    color_name = "green"
            else:
                if balance <= 1:
                    color = "\033[91m"  # 红色
                    color_name = "red"
                elif balance <= 5:
                    color = "\033[93m"  # 黄色
                    color_name = "yellow"
                else:
                    color = "\033[92m"  # 绿色
                    color_name = "green"

            reset = "\033[0m"

            # 格式化显示
            if currency == "CNY":
                balance_str = f"Kimi.B:{color}{balance:.2f}CNY{reset}"
            else:
                balance_str = f"Kimi.B:{color}${balance:.2f}{reset}"

            self.logger.debug(
                "Kimi balance formatting completed",
                {
                    "final_display": balance_str,
                    "color_used": color_name,
                    "balance": balance,
                    "currency": currency,
                },
            )

            return balance_str
        except Exception as e:
            self.logger.error(f"Kimi balance formatting failed: {e}")
            return f"Kimi.B:Error({str(e)[:20]})"

    def format_subscription_display(self, subscription_data: Dict[str, Any]) -> str:
        """Format Kimi subscription for display"""
        if subscription_data is None:
            self.logger.info("No subscription data available for display")
            return "Kimi.Sub:\033[91mNoData\033[0m"

        try:
            plan = subscription_data.get("plan", "Unknown")
            expiry = subscription_data.get("expiry", "")

            self.logger.debug(
                "Kimi subscription data structure",
                {
                    "plan": plan,
                    "expiry": expiry,
                },
            )

            reset = "\033[0m"
            color = "\033[94m"  # 蓝色

            if expiry:
                # 格式化日期显示 (MM-DD)
                try:
                    from datetime import datetime
                    if len(expiry) >= 10:  # YYYY-MM-DD format
                        date_obj = datetime.fromisoformat(expiry[:10])
                        expiry_short = date_obj.strftime("%m-%d")
                        subscription_text = f"Sub:{plan}({expiry_short})"
                    else:
                        subscription_text = f"Sub:{plan}"
                except:
                    subscription_text = f"Sub:{plan}"
            else:
                subscription_text = f"Sub:{plan}"

            return f"{color}{subscription_text}{reset}"
        except Exception as e:
            self.logger.error(f"Kimi subscription formatting failed: {e}")
            return f"Kimi.Sub:Error({str(e)[:20]})"