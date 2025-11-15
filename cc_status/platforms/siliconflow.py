#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SiliconFlow platform implementation
"""

from typing import Dict, Any, Optional
from .base import BasePlatform
from ..utils.logger import get_logger


class SiliconFlowPlatform(BasePlatform):
    """SiliconFlow platform implementation"""

    def __init__(self, platform_name: str, config: Dict[str, Any]):
        """初始化SiliconFlow平台"""
        self._name = "siliconflow"
        self.config = config
        self.logger = get_logger(f"platform.{platform_name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def api_base(self) -> str:
        # SiliconFlow余额查询使用基础API地址
        return "https://api.siliconflow.cn"

    def detect_platform(self, session_info: Dict[str, Any], token: str) -> bool:
        """Detect SiliconFlow platform"""
        # 方法1: 检查模型是否是siliconflow系列
        try:
            model_id = session_info.get("model", {}).get("id", "")
            if "siliconflow" in model_id.lower() or "deepseek-ai" in model_id.lower():
                self.logger.info(
                    "SiliconFlow detected by model ID",
                    {"method": "model_id", "model_id": model_id},
                )
                return True
        except Exception as e:
            self.logger.debug(f"Model ID detection failed: {e}")

        # 方法2: 检查配置中是否显式指定了siliconflow平台
        platform_type = self.config.get("platform_type", "").lower()
        if platform_type == "siliconflow":
            self.logger.info(
                "SiliconFlow detected by config",
                {"method": "config_platform_type", "platform_type": platform_type},
            )
            return True

        # 方法3: 通过token格式判断
        if token and token.startswith("sk-pnuhmx"):
            self.logger.debug(
                "SiliconFlow token format detected",
                {"method": "token_prefix", "token_prefix": token[:10] + "..."},
            )
            return True

        self.logger.debug("SiliconFlow platform not detected")
        return False

    def fetch_balance_data(self) -> Optional[Dict[str, Any]]:
        """Fetch balance data from SiliconFlow API"""
        try:
            auth_token = self._get_auth_token()
            self.logger.debug(
                "Starting SiliconFlow balance fetch",
                {"token_length": len(auth_token) if auth_token else 0},
            )

            # 使用SiliconFlow的余额查询端点
            balance_data = self.make_request("/v1/user/info")

            if balance_data:
                self.logger.info(
                    "SiliconFlow balance data fetched successfully",
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
                    "SiliconFlow balance API returned None",
                    {"possible_cause": "API request failed or returned empty data"},
                )
                return None

        except Exception as e:
            self.logger.error(f"SiliconFlow balance fetch failed: {e}")
            return None

    def fetch_subscription_data(self) -> Optional[Dict[str, Any]]:
        """SiliconFlow doesn't have subscription endpoint, return None"""
        # SiliconFlow API 没有订阅信息接口
        return None

    def format_balance_display(self, balance_data: Dict[str, Any]) -> str:
        """Format SiliconFlow balance for display"""
        # 处理空数据情况
        if balance_data is None:
            self.logger.info("No balance data available for display")
            return "SiliconFlow.B:\033[91mNoData\033[0m"

        self.logger.debug(
            "Starting SiliconFlow balance formatting",
            {
                "balance_data_keys": list(balance_data.keys()),
                "balance_data_type": type(balance_data).__name__,
            },
        )

        try:
            # SiliconFlow API 返回结构：{"code": 20000, "data": {"balance": "24.671", "totalBalance": "32.1293"}}
            data = balance_data.get("data", {})
            balance = float(data.get("balance", 0))  # 可用余额
            total_balance = float(data.get("totalBalance", 0))  # 总余额
            currency = "CNY"  # SiliconFlow只支持人民币

            self.logger.debug(
                "SiliconFlow balance data structure",
                {
                    "balance": balance,
                    "currency": currency,
                },
            )

            # 颜色代码基于余额 - 支持负值显示
            if currency == "CNY":
                if balance < 0:  # 负余额 - 红色
                    color = "\033[91m"
                    color_name = "red"
                elif balance <= 10:
                    color = "\033[91m"  # 红色
                    color_name = "red"
                elif balance <= 50:
                    color = "\033[93m"  # 黄色
                    color_name = "yellow"
                else:
                    color = "\033[92m"  # 绿色
                    color_name = "green"
            else:
                if balance < 0:  # 负余额 - 红色
                    color = "\033[91m"
                    color_name = "red"
                elif balance <= 5:
                    color = "\033[91m"  # 红色
                    color_name = "red"
                elif balance <= 25:
                    color = "\033[93m"  # 黄色
                    color_name = "yellow"
                else:
                    color = "\033[92m"  # 绿色
                    color_name = "green"

            reset = "\033[0m"

            # 格式化显示（去掉平台名称前缀，由formatter统一添加）
            if currency == "CNY":
                balance_str = f"{color}{balance:.2f}CNY{reset}"

            self.logger.debug(
                "SiliconFlow balance formatting completed",
                {
                    "final_display": balance_str,
                    "color_used": color_name,
                    "balance": balance,
                    "total_balance": total_balance,
                    "currency": currency,
                },
            )

            return balance_str
        except Exception as e:
            self.logger.error(f"SiliconFlow balance formatting failed: {e}")
            return f"SiliconFlow.B:Error({str(e)[:20]})"

    def format_subscription_display(self, subscription_data: Dict[str, Any]) -> str:
        """SiliconFlow doesn't have subscription info"""
        return ""