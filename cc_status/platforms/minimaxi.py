#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimaxi platform implementation
"""

import json
from typing import Dict, Any, Optional
from .base import BasePlatform
from ..utils.logger import get_logger


class MinimaxiPlatform(BasePlatform):
    """Minimaxi platform implementation"""

    def __init__(self, platform_name: str, config: Dict[str, Any]):
        """初始化Minimaxi平台"""
        self._name = "minimaxi"
        self.config = config
        self.logger = get_logger(f"platform.{platform_name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def api_base(self) -> str:
        # Minimaxi使用特定的API基础地址
        return "https://www.minimaxi.com/v1/api"

    def detect_platform(self, session_info: Dict[str, Any], token: str) -> bool:
        """Detect Minimaxi platform"""
        # 方法1: 检查模型是否是MiniMax系列
        try:
            model_id = session_info.get("model", {}).get("id", "")
            if "minimax" in model_id.lower() or "m2" in model_id.lower():
                self.logger.info(
                    "Minimaxi detected by model ID",
                    {"method": "model_id", "model_id": model_id},
                )
                return True
        except Exception as e:
            self.logger.debug(f"Model ID detection failed: {e}")

        # 方法2: 检查配置中是否显式指定了minimaxi平台
        platform_type = self.config.get("platform_type", "").lower()
        if platform_type == "minimaxi":
            self.logger.info(
                "Minimaxi detected by config",
                {"method": "config_platform_type", "platform_type": platform_type},
            )
            return True

        # 方法3: 通过token格式判断
        if token and token.startswith("eyJ"):
            self.logger.debug(
                "Minimaxi JWT token format detected",
                {"method": "token_prefix", "token_prefix": token[:10] + "..."},
            )
            return True

        self.logger.debug("Minimaxi platform not detected")
        return False

    def _make_minimaxi_request_with_auth_token(
        self, endpoint: str, auth_token: str
    ) -> Optional[Dict[str, Any]]:
        """Make Minimaxi API request with auth_token (fallback)"""
        import requests

        # 构建完整的URL
        if hasattr(self, 'api_base'):
            api_base = self.api_base
        else:
            api_base = self.config.get("api_base_url", "")

        if not api_base:
            self.logger.error("No API base URL configured for Minimaxi")
            return None

        # 构建带参数的完整URL（auth_token模式下可能不需要group_id）
        url = f"{api_base}{endpoint}"

        # 对于auth_token，尝试不带group_id参数（某些API可能支持）
        params = {}

        # 请求头 - 使用auth_token
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en,zh-CN;q=0.9,zh-TW;q=0.7,zh;q=0.6,en-US;q=0.5',
            'authorization': f'Bearer {auth_token}',
            'dnt': '1',
            'origin': 'https://platform.minimaxi.com',
            'priority': 'u=1, i',
            'referer': 'https://platform.minimaxi.com/',
            'sec-ch-ua': (
                '"Chromium";v="142", "Google Chrome";v="142", '
                '"Not_A Brand";v="99"'
            ),
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/142.0.0.0 Safari/537.36'
            ),
        }

        try:
            self.logger.debug(f"Making Minimaxi API request to: {url}")
            self.logger.debug(f"With auth_token (first 10 chars): {auth_token[:10]}...")
            response = requests.get(url, headers=headers, params=params, timeout=10)

            self.logger.debug(f"Minimaxi API response status: {response.status_code}")

            if response.status_code == 200:
                # 检查响应内容是否为空
                if not response.text.strip():
                    self.logger.warning("Minimaxi API returned empty response")
                    return None

                try:
                    json_data = response.json()
                    self.logger.debug(f"Minimaxi API response: {json_data}")
                    return json_data
                except json.JSONDecodeError as e:
                    self.logger.error(
                        f"Minimaxi API response is not valid JSON: {e}"
                    )
                    self.logger.error(f"Response text: {response.text}")
                    return None
            else:
                self.logger.warning(
                    f"Minimaxi API request failed with status "
                    f"{response.status_code}: {response.text}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Minimaxi API request error: {e}")
            return None

    def fetch_balance_data(self) -> Optional[Dict[str, Any]]:
        """Fetch subscription data from Minimaxi API using auth_token"""
        try:
            # Use only auth_token (Minimax API Key)
            auth_token = self.config.get("auth_token")

            # Check if auth_token is available
            if not auth_token:
                self.logger.debug(
                    "Minimaxi auth_token not configured, "
                    "skipping balance query"
                )
                return None

            self.logger.debug(
                "Starting Minimaxi subscription fetch",
                {
                    "has_auth_token": bool(auth_token),
                    "auth_token_length": len(auth_token) if auth_token else 0,
                },
            )

            # Use auth_token to call Minimax-specific API
            self.logger.debug("Attempting balance query with auth_token")
            subscription_data = self._make_minimaxi_request_with_auth_token(
                "/openplatform/charge/combo/cycle_audio_resource_package",
                auth_token
            )

            if subscription_data:
                self.logger.info(
                    "Minimaxi subscription data fetched successfully",
                    {
                        "data_keys": list(subscription_data.keys()),
                        "data_type": type(subscription_data).__name__,
                        "has_current_subscribe": "current_subscribe" in subscription_data,
                    },
                )
                # 添加原始数据字段
                subscription_data["raw_data"] = subscription_data.copy()
                return subscription_data
            else:
                self.logger.warning("Minimaxi auth_token query failed")

            return None

        except Exception as e:
            self.logger.error(f"Minimaxi subscription fetch failed: {e}")
            return None

    def fetch_subscription_data(self) -> Optional[Dict[str, Any]]:
        """Minimaxi uses package-based billing"""
        # Minimaxi使用套餐计费模式，已经在fetch_balance_data中获取
        return None

    def format_balance_display(self, subscription_data: Dict[str, Any]) -> str:
        """Format Minimaxi subscription for display"""
        # 处理空数据情况
        if subscription_data is None:
            self.logger.info("No subscription data available for display")
            return "\033[91mNoData\033[0m"

        self.logger.debug(
            "Starting Minimaxi subscription formatting",
            {
                "subscription_data_keys": list(subscription_data.keys()),
                "subscription_data_type": type(subscription_data).__name__,
            },
        )

        try:
            # 提取当前订阅数据
            current_subscribe = subscription_data.get("current_subscribe", {})
            if not current_subscribe:
                self.logger.warning("Minimaxi subscription data missing 'current_subscribe' field")
                return "\033[91mNoSub\033[0m"

            # 获取订阅结束时间
            end_time = current_subscribe.get("current_subscribe_end_time", "")
            if not end_time:
                self.logger.warning("Minimaxi subscription data missing 'current_subscribe_end_time' field")
                return "\033[91mNoDate\033[0m"

            self.logger.debug(
                "Minimaxi subscription data structure",
                {
                    "end_time": end_time,
                    "title": current_subscribe.get("current_subscribe_title", "Unknown"),
                },
            )

            # Parse date (format: "12/15/2025")
            try:
                from datetime import datetime
                # Minimaxi返回格式: MM/DD/YYYY
                date_obj = datetime.strptime(end_time, "%m/%d/%Y")
                expiry_short = date_obj.strftime("%m-%d")

                # 计算天数差
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                expiry_date = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
                days_left = (expiry_date - today).days

                # 颜色代码基于剩余天数
                if days_left <= 3:
                    color = "\033[91m"  # 红色
                elif days_left <= 7:
                    color = "\033[93m"  # 黄色
                else:
                    color = "\033[92m"  # 绿色

                reset = "\033[0m"

                # 格式化显示，使用中括号（不包含平台名称，由formatter统一添加）
                subscription_str = f"{color}[{expiry_short}]{reset}"

                self.logger.debug(
                    "Minimaxi formatting completed",
                    {
                        "final_display": subscription_str,
                        "color_used": "red" if days_left <= 3 else "yellow" if days_left <= 7 else "green",
                        "days_left": days_left,
                        "expiry_date": end_time,
                    },
                )

                return subscription_str
            except Exception as e:
                self.logger.error(f"Failed to parse Minimaxi date format: {e}")
                # 如果解析失败，直接显示原始日期（取前5个字符）
                return f"{end_time[:5]}"

        except Exception as e:
            self.logger.error(f"Minimaxi subscription formatting failed: {e}")
            return f"Error({str(e)[:20]})"

    def format_subscription_display(self, subscription_data: Dict[str, Any]) -> str:
        """Format Minimaxi subscription details for display"""
        if subscription_data is None:
            self.logger.info("No subscription data available for display")
            return "\033[94mPackage\033[0m"

        try:
            # Minimaxi使用套餐模式
            reset_color = "\033[0m"
            color = "\033[94m"  # 蓝色

            subscription_text = "Package.Subscription"
            return f"{color}{subscription_text}{reset_color}"
        except Exception as e:
            self.logger.error(f"Minimaxi subscription details formatting failed: {e}")
            return f"Error({str(e)[:20]})"

    def fetch_usage_data(self) -> Optional[Dict[str, Any]]:
        """Fetch usage data from Minimaxi API using auth_token"""
        try:
            # 只使用auth_token
            auth_token = self.config.get("auth_token")
            if not auth_token or not isinstance(auth_token, str) or len(auth_token.strip()) == 0:
                self.logger.debug("Minimaxi auth_token not configured, skipping usage query")
                return None

            self.logger.debug(
                "Starting Minimaxi usage fetch",
                {"token_length": len(auth_token) if auth_token else 0},
            )

            # 使用auth_token查询用量数据
            usage_data = self._make_minimaxi_request_with_auth_token(
                "/openplatform/coding_plan/remains",
                auth_token
            )

            if usage_data:
                self.logger.info(
                    "Minimaxi usage data fetched successfully",
                    {
                        "data_keys": list(usage_data.keys()),
                        "data_type": type(usage_data).__name__,
                        "has_model_remains": "model_remains" in usage_data,
                        "base_resp_status": usage_data.get("base_resp", {}).get("status_code"),
                    },
                )
                return usage_data
            else:
                self.logger.warning(
                    "Minimaxi usage API returned None",
                    {"possible_cause": "API request failed or returned empty data"},
                )
                return None

        except Exception as e:
            self.logger.error(f"Minimaxi usage fetch failed: {e}")
            return None

    def format_usage_display(self, usage_data: Dict[str, Any]) -> str:
        """Format Minimaxi usage for display with interval and weekly data (KFC style)"""
        if usage_data is None:
            self.logger.info("No usage data available for display")
            return "\033[91mNoData\033[0m"

        try:
            # 检查API响应状态
            base_resp = usage_data.get("base_resp", {})
            if base_resp and base_resp.get("status_code") != 0:
                error_msg = base_resp.get("status_msg", "Unknown error")
                self.logger.warning(f"Minimaxi usage API returned error: {error_msg}")
                return f"\033[91m{error_msg}\033[0m"

            # 提取模型剩余用量数据
            model_remains = usage_data.get("model_remains", [])
            if not model_remains:
                self.logger.warning("Minimaxi usage data missing 'model_remains' field")
                return "\033[91mNoUsage\033[0m"

            # 找到 MiniMax-M* 模型（主要编程模型）
            coding_model = None
            for model in model_remains:
                model_name = model.get("model_name", "")
                if "MiniMax-M" in model_name or "minimax-m" in model_name.lower():
                    coding_model = model
                    break

            # 如果没找到 M 系列，取第一个
            if not coding_model:
                coding_model = model_remains[0]

            # 提取 interval 数据（当前周期）
            interval_total = coding_model.get("current_interval_total_count", 0)
            interval_used = coding_model.get("current_interval_usage_count", 0)
            interval_remaining = interval_used  # API命名就是usage是剩余
            interval_end_time = coding_model.get("end_time", 0)
            interval_start_time = coding_model.get("start_time", 0)

            # 提取 weekly 数据
            weekly_total = coding_model.get("current_weekly_total_count", 0)
            weekly_used = coding_model.get("current_weekly_usage_count", 0)
            weekly_end_time = coding_model.get("weekly_end_time", 0)

            # 格式化时间
            from datetime import datetime
            interval_reset = self._format_timestamp(interval_end_time)
            weekly_reset = self._format_timestamp(weekly_end_time)

            # 颜色基于 interval 剩余比例
            interval_pct = (interval_remaining / interval_total * 100) if interval_total > 0 else 0
            if interval_pct <= 10:
                usage_color = "\033[91m"  # 红色
            elif interval_pct <= 30:
                usage_color = "\033[93m"  # 黄色
            else:
                usage_color = "\033[92m"  # 绿色

            reset = "\033[0m"

            # KFC 风格: interval:remaining/total(reset)|wk:weekly_remaining/weekly_total(weekly_reset)
            # Show weekly data if weekly_total > 0 (has limit) OR weekly_used > 0 (has usage)
            # When weekly_total is 0, it means unlimited (VIP) - show as ∞
            if weekly_total > 0:
                usage_str = f"{usage_color}interval:{interval_remaining}/{interval_total}{interval_reset}{reset}|wk:{weekly_used}/{weekly_total}{weekly_reset}"
            elif weekly_used > 0:
                # Has usage but no limit (VIP unlimited) - show usage with ∞
                usage_str = f"{usage_color}interval:{interval_remaining}/{interval_total}{interval_reset}{reset}|wk:{weekly_used}/∞{weekly_reset}{reset}"
            else:
                usage_str = f"{usage_color}interval:{interval_remaining}/{interval_total}{interval_reset}{reset}"

            self.logger.debug(
                "Minimaxi usage formatting completed",
                {
                    "final_display": usage_str,
                    "interval": f"{interval_remaining}/{interval_total}",
                    "weekly": f"{weekly_used}/{weekly_total}" if weekly_total > 0 else "N/A",
                    "interval_reset": interval_reset,
                    "weekly_reset": weekly_reset,
                },
            )

            return usage_str

        except Exception as e:
            self.logger.error(f"Minimaxi usage formatting failed: {e}")
            return f"Error({str(e)[:20]})"

    def _format_timestamp(self, timestamp: int) -> str:
        """Format millisecond timestamp to display string"""
        if not timestamp or timestamp <= 0:
            return "(NoReset)"

        try:
            from datetime import datetime
            dt = datetime.fromtimestamp(timestamp / 1000)
            now = datetime.now()

            if dt.date() == now.date():
                reset_short = dt.strftime("%H:%M")
            else:
                reset_short = dt.strftime("%m-%d %H:%M")

            return f"({reset_short})"
        except Exception:
            return "(Err)"
