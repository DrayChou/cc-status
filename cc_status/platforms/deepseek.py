#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek platform implementation
"""

from typing import Dict, Any, Optional
from .base import BasePlatform
from ..utils.logger import get_logger


class DeepSeekPlatform(BasePlatform):
    """DeepSeek platform implementation"""

    def __init__(self, platform_name: str, config: Dict[str, Any]):
        """初始化DeepSeek平台"""
        self._name = "deepseek"
        self.config = config
        self.logger = get_logger(f"platform.{platform_name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def api_base(self) -> str:
        # DeepSeek余额查询使用基础API地址
        return "https://api.deepseek.com"

    def detect_platform(self, session_info: Dict[str, Any], token: str) -> bool:
        """Detect DeepSeek platform"""
        # 方法1: 检查模型是否是deepseek系列
        try:
            model_id = session_info.get("model", {}).get("id", "")
            if "deepseek" in model_id.lower():
                self.logger.info(
                    "DeepSeek detected by model ID",
                    {"method": "model_id", "model_id": model_id},
                )
                return True
        except Exception as e:
            self.logger.debug(f"Model ID detection failed: {e}")

        # 方法2: 检查配置中是否显式指定了deepseek平台
        platform_type = self.config.get("platform_type", "").lower()
        if platform_type == "deepseek":
            self.logger.info(
                "DeepSeek detected by config",
                {"method": "config_platform_type", "platform_type": platform_type},
            )
            return True

        # 方法3: 通过token格式判断
        if token and token.startswith("sk-"):
            self.logger.debug(
                "DeepSeek token format detected",
                {"method": "token_prefix", "token_prefix": token[:10] + "..."},
            )
            # 注意：这里不直接返回True，因为很多平台的token都以sk-开头
            # 需要结合其他条件判断

        self.logger.debug("DeepSeek platform not detected")
        return False

    def fetch_balance_data(self) -> Optional[Dict[str, Any]]:
        """Fetch balance data from DeepSeek API"""
        try:
            auth_token = self._get_auth_token()
            if not auth_token:
                self.logger.warning("No auth token available for DeepSeek balance fetch")
                return None

            self.logger.debug(
                "Starting DeepSeek balance fetch",
                {"token_length": len(auth_token) if auth_token else 0},
            )

            # 使用DeepSeek的余额查询端点
            balance_data = self.make_request("/user/balance")

            if balance_data:
                self.logger.info(
                    "DeepSeek balance data fetched successfully",
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
                    "DeepSeek balance API returned None",
                    {"possible_cause": "API request failed or returned empty data"},
                )
                return None

        except Exception as e:
            self.logger.error(f"DeepSeek balance fetch failed: {e}")
            return None

    def fetch_subscription_data(self) -> Optional[Dict[str, Any]]:
        """DeepSeek doesn't have subscription endpoint, return None"""
        # DeepSeek API 没有订阅信息接口
        return None

    def format_balance_display(self, balance_data: Dict[str, Any]) -> str:
        """Format DeepSeek balance for display"""
        # 处理空数据情况
        if balance_data is None:
            self.logger.info("No balance data available for display")
            return "DeepSeek.B:\033[91mNoData\033[0m"

        self.logger.debug(
            "Starting DeepSeek balance formatting",
            {
                "balance_data_keys": list(balance_data.keys()),
                "balance_data_type": type(balance_data).__name__,
            },
        )

        try:
            is_available = balance_data.get("is_available", False)
            balance_infos = balance_data.get("balance_infos", [])

            self.logger.debug(
                "DeepSeek balance data structure",
                {
                    "is_available": is_available,
                    "balance_infos_count": len(balance_infos),
                    "has_balance_infos": bool(balance_infos),
                },
            )

            if not is_available:
                self.logger.warning(
                    "DeepSeek balance unavailable",
                    {"is_available": is_available},
                )
                return "DeepSeek.B:\033[91mUnavailable\033[0m"

            if not balance_infos:
                self.logger.warning(
                    "DeepSeek balance info empty",
                    {"balance_infos": balance_infos},
                )
                return "DeepSeek.B:\033[91mNo Info\033[0m"

            # 获取总余额（通常第一个 balance_info 包含总余额信息）
            primary_balance = balance_infos[0]
            total_balance = float(primary_balance.get("total_balance", 0))
            currency = primary_balance.get("currency", "USD")

            self.logger.debug(
                "DeepSeek primary balance info",
                {
                    "total_balance": total_balance,
                    "currency": currency,
                    "primary_balance_keys": (
                        list(primary_balance.keys())
                        if isinstance(primary_balance, dict)
                        else "not_dict"
                    ),
                },
            )

            # 颜色代码基于余额
            if total_balance <= 1:
                color = "\033[91m"  # 红色
                color_name = "red"
            elif total_balance <= 10:
                color = "\033[93m"  # 黄色
                color_name = "yellow"
            else:
                color = "\033[92m"  # 绿色
                color_name = "green"
            reset = "\033[0m"

            # 格式化显示
            if currency == "CNY":
                balance_str = f"DeepSeek.B:{color}{total_balance:.2f}CNY{reset}"
            else:
                balance_str = f"DeepSeek.B:{color}${total_balance:.2f}{reset}"

            # 如果有多个余额信息，显示详细信息
            if len(balance_infos) > 1:
                details = []
                for info in balance_infos[1:]:
                    balance = info.get("total_balance", 0)
                    curr = info.get("currency", "USD")
                    if balance > 0:
                        if curr == "CNY":
                            details.append(f"{balance:.2f}CNY")
                        else:
                            details.append(f"${balance:.2f}")
                if details:
                    balance_str += f" ({', '.join(details)})"

            self.logger.debug(
                "DeepSeek balance formatting completed",
                {
                    "final_display": balance_str,
                    "color_used": color_name,
                    "total_balance": total_balance,
                    "currency": currency,
                },
            )

            return balance_str
        except Exception as e:
            self.logger.error(f"DeepSeek balance formatting failed: {e}")
            return f"DeepSeek.B:Error({str(e)[:20]})"