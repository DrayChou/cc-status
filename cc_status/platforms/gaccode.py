#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GACCode platform implementation
GACCode 平台余额查询实现

API 文档来源: docs/gaccode1.md
- 余额查询: GET https://gaccode.com/api/credits/balance
- 认证: Authorization: Bearer {JWT token}
- 返回: {"balance": 13850, "creditCap": 5400, "refillRate": 100, ...}
"""

import requests

from typing import Dict, Any, Optional
from .base import BasePlatform
from ..utils.logger import get_logger


class GACCodePlatform(BasePlatform):
    """GACCode 平台实现"""

    # GACCode 余额查询 API
    API_BASE = "https://gaccode.com"
    BALANCE_ENDPOINT = "/api/credits/balance"

    def __init__(self, platform_name: str, config: Dict[str, Any]):
        """初始化 GACCode 平台"""
        self._name = "gaccode"
        self.config = config
        self.logger = get_logger(f"platform.{platform_name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def api_base(self) -> str:
        # GACCode 代理地址（用于 API 调用，非余额查询）
        return self.config.get("api_base_url", "") or "https://relay08.gaccode.com/claudecode"

    def _get_auth_token(self) -> Optional[str]:
        """获取 GACCode 认证令牌（JWT 格式）"""
        # 优先级：gaccode_token > login_token > auth_token > api_key
        return (
            self.config.get("gaccode_token") or
            self.config.get("login_token") or
            self.config.get("auth_token") or
            self.config.get("api_key")
        )

    def fetch_balance_data(self) -> Optional[Dict[str, Any]]:
        """Fetch balance data from GACCode API

        Returns:
            {"balance": 13850, "creditCap": 5400, "refillRate": 100, ...}
        """
        try:
            # 获取认证令牌
            auth_token = self._get_auth_token()
            if not auth_token:
                self.logger.debug("GACCode auth token not configured, skipping balance query")
                return None

            self.logger.debug(
                "Starting GACCode balance fetch",
                {"token_length": len(auth_token) if auth_token else 0},
            )

            # 调用 gaccode.com 余额 API
            url = f"{self.API_BASE}{self.BALANCE_ENDPOINT}"
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Accept": "*/*",
                "Content-Type": "application/json",
            }

            self.logger.debug(f"Making GACCode API request: {url}")

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                balance_data = response.json()
                self.logger.info(
                    "GACCode balance data fetched successfully",
                    {
                        "balance": balance_data.get("balance"),
                        "creditCap": balance_data.get("creditCap"),
                    },
                )
                balance_data["raw_data"] = balance_data.copy()
                return balance_data
            elif response.status_code == 401:
                self.logger.warning(
                    "GACCode API unauthorized - token may be invalid or expired",
                    {"status_code": response.status_code},
                )
                return {"success": False, "message": "Invalid or expired token"}
            else:
                self.logger.warning(
                    "GACCode balance API returned non-200 status",
                    {"status_code": response.status_code},
                )
                return None

        except Exception as e:
            self.logger.error(f"GACCode balance fetch failed: {e}")
            return None

    def fetch_subscription_data(self) -> Optional[Dict[str, Any]]:
        """GACCode doesn't have separate subscription endpoint"""
        return None

    def format_balance_display(self, balance_data: Dict[str, Any]) -> str:
        """Format GACCode balance for display

        GACCode 使用 credits 作为单位:
        - balance: 当前余额 (credits)
        - creditCap: 信用额度 (credits)
        - refillRate: 每日充值 rate (credits/day)
        """
        if balance_data is None:
            self.logger.info("No balance data available for display")
            return "GACCode.B:\033[91mNoData\033[0m"

        # 检查是否是错误响应
        if not balance_data.get("success", True) is True:
            msg = balance_data.get("message", "Unknown error")
            self.logger.warning(f"GACCode balance query failed: {msg}")
            return f"GACCode.B:\033[91mError\033[0m"

        try:
            # GACCode 使用 credits
            balance = float(balance_data.get("balance", 0))
            credit_cap = float(balance_data.get("creditCap", 0))

            self.logger.debug(
                "GACCode balance data structure",
                {
                    "balance": balance,
                    "creditCap": credit_cap,
                    "unit": "credits",
                },
            )

            # 颜色代码基于余额 (credits)
            # 假设 1000 credits 以下为低余额
            if balance < 100:
                color = "\033[91m"  # 红色 - 余额不足
                color_name = "red"
            elif balance < 500:
                color = "\033[93m"  # 黄色 - 余额一般
                color_name = "yellow"
            elif balance < credit_cap:
                color = "\033[92m"  # 绿色 - 余额充足
                color_name = "green"
            else:
                color = "\033[94m"  # 蓝色 - 超过信用额度
                color_name = "blue"

            reset = "\033[0m"

            # 格式化余额显示（保留整数）
            if 0 < balance < 1:
                display_balance = 1
            else:
                display_balance = int(balance)

            # 显示格式: 余额(信用额度) 单位
            balance_str = f"{color}{display_balance}{reset}"

            self.logger.debug(
                "GACCode balance formatting completed",
                {
                    "final_display": balance_str,
                    "color_used": color_name,
                    "balance": balance,
                    "creditCap": credit_cap,
                },
            )

            return balance_str
        except Exception as e:
            self.logger.error(f"GACCode balance formatting failed: {e}")
            return f"GACCode.B:Error({str(e)[:20]})"

    def format_subscription_display(self, subscription_data: Dict[str, Any]) -> str:
        """GACCode doesn't have subscription info"""
        return ""
