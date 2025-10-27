#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLM platform implementation
"""

from typing import Dict, Any, Optional
from .base import BasePlatform
from ..utils.logger import get_logger


class GLMPlatform(BasePlatform):
    """GLM platform implementation"""

    def __init__(self, platform_name: str, config: Dict[str, Any]):
        """初始化GLM平台"""
        self._name = "glm"
        self.config = config
        self.logger = get_logger(f"platform.{platform_name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def api_base(self) -> str:
        # GLM余额查询使用基础API地址
        return "https://open.bigmodel.cn/api"

    def detect_platform(self, session_info: Dict[str, Any], token: str) -> bool:
        """Detect GLM platform"""
        # 方法1: 检查模型是否是glm系列
        try:
            model_id = session_info.get("model", {}).get("id", "")
            if "glm" in model_id.lower():
                self.logger.info(
                    "GLM detected by model ID",
                    {"method": "model_id", "model_id": model_id},
                )
                return True
        except Exception as e:
            self.logger.debug(f"Model ID detection failed: {e}")

        # 方法2: 检查配置中是否显式指定了glm平台
        platform_type = self.config.get("platform_type", "").lower()
        if platform_type == "glm":
            self.logger.info(
                "GLM detected by config",
                {"method": "config_platform_type", "platform_type": platform_type},
            )
            return True

        # 方法3: 通过token格式判断
        if token and (token.startswith("8ef0c8d") or token.startswith("eyJ")):
            self.logger.debug(
                "GLM token format detected",
                {"method": "token_prefix", "token_prefix": token[:10] + "..."},
            )
            return True

        self.logger.debug("GLM platform not detected")
        return False

    def fetch_balance_data(self) -> Optional[Dict[str, Any]]:
        """Fetch balance data from GLM API"""
        try:
            auth_token = self._get_auth_token()
            self.logger.debug(
                "Starting GLM balance fetch",
                {"token_length": len(auth_token) if auth_token else 0},
            )

            # 使用GLM的余额查询端点
            balance_data = self.make_request("/anthropic/user/balance")

            if balance_data:
                self.logger.info(
                    "GLM balance data fetched successfully",
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
                    "GLM balance API returned None",
                    {"possible_cause": "API request failed or returned empty data"},
                )
                return None

        except Exception as e:
            self.logger.error(f"GLM balance fetch failed: {e}")
            return None

    def fetch_subscription_data(self) -> Optional[Dict[str, Any]]:
        """GLM uses pay-as-you-go billing, no subscription concept"""
        # GLM使用按量付费模式，没有订阅概念
        return None

    def format_balance_display(self, balance_data: Dict[str, Any]) -> str:
        """Format GLM balance for display"""
        # 处理空数据情况
        if balance_data is None:
            self.logger.info("No balance data available for display")
            return "GLM.B:\033[91mNoData\033[0m"

        self.logger.debug(
            "Starting GLM balance formatting",
            {
                "balance_data_keys": list(balance_data.keys()),
                "balance_data_type": type(balance_data).__name__,
            },
        )

        try:
            # GLM API 返回结构可能不同，需要适配
            balance = balance_data.get("balance", 0)
            currency = balance_data.get("currency", "CNY")

            self.logger.debug(
                "GLM balance data structure",
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
                if balance <= 5:
                    color = "\033[91m"  # 红色
                    color_name = "red"
                elif balance <= 25:
                    color = "\033[93m"  # 黄色
                    color_name = "yellow"
                else:
                    color = "\033[92m"  # 绿色
                    color_name = "green"

            reset = "\033[0m"

            # 格式化显示
            if currency == "CNY":
                balance_str = f"GLM.B:{color}{balance:.2f}CNY{reset}"
            else:
                balance_str = f"GLM.B:{color}${balance:.2f}{reset}"

            self.logger.debug(
                "GLM balance formatting completed",
                {
                    "final_display": balance_str,
                    "color_used": color_name,
                    "balance": balance,
                    "currency": currency,
                },
            )

            return balance_str
        except Exception as e:
            self.logger.error(f"GLM balance formatting failed: {e}")
            return f"GLM.B:Error({str(e)[:20]})"

    def format_subscription_display(self, subscription_data: Dict[str, Any]) -> str:
        """Format GLM subscription for display"""
        if subscription_data is None:
            self.logger.info("No subscription data available for display")
            return "GLM.Sub:\033[91mNoData\033[0m"

        try:
            plan = subscription_data.get("plan", "Unknown")
            model = subscription_data.get("model", "GLM")

            self.logger.debug(
                "GLM subscription data structure",
                {
                    "plan": plan,
                    "model": model,
                },
            )

            reset = "\033[0m"
            color = "\033[94m"  # 蓝色

            subscription_text = f"Sub:{plan}({model})"
            return f"{color}{subscription_text}{reset}"
        except Exception as e:
            self.logger.error(f"GLM subscription formatting failed: {e}")
            return f"GLM.Sub:Error({str(e)[:20]})"