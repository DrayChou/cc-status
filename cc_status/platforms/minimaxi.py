#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimaxi platform implementation
"""

from typing import Dict, Any, Optional
from .base import BasePlatform
from ..utils.logger import get_logger
import requests


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

    def make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """重写make_request方法，使用login_token进行认证并添加必需参数"""
        login_token = self.config.get("login_token")
        if not login_token:
            self.logger.warning("No login_token available for Minimaxi request")
            return None

        # 构建完整的URL
        if hasattr(self, 'api_base'):
            api_base = self.api_base
        else:
            api_base = self.config.get("api_base_url", "")

        if not api_base:
            self.logger.error("No API base URL configured for Minimaxi")
            return None

        # 获取必需的参数
        group_id = self.config.get("group_id")
        if not group_id:
            self.logger.error("No group_id configured for Minimaxi")
            return None

        # 构建带参数的完整URL
        url = f"{api_base}{endpoint}"
        params = {
            "biz_line": 2,
            "cycle_type": 1,
            "resource_package_type": 7,
            "GroupId": group_id
        }

        # 请求头 - 基于真实浏览器请求
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en,zh-CN;q=0.9,zh-TW;q=0.7,zh;q=0.6,en-US;q=0.5',
            'authorization': f'Bearer {login_token}',
            'dnt': '1',
            'origin': 'https://platform.minimaxi.com',
            'priority': 'u=1, i',
            'referer': 'https://platform.minimaxi.com/',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        }

        try:
            self.logger.debug(f"Making Minimaxi API request to: {url}")
            self.logger.debug(f"With params: {params}")
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
                    self.logger.error(f"Minimaxi API response is not valid JSON: {e}")
                    self.logger.error(f"Response text: {response.text}")
                    return None
            else:
                self.logger.warning(f"Minimaxi API request failed with status {response.status_code}: {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"Minimaxi API request error: {e}")
            return None

    def fetch_balance_data(self) -> Optional[Dict[str, Any]]:
        """Fetch subscription data from Minimaxi API using the provided curl command pattern"""
        try:
            # 验证login_token是否配置
            login_token = self.config.get("login_token")
            if not login_token or not isinstance(login_token, str) or len(login_token.strip()) == 0:
                self.logger.debug("Minimaxi login_token not configured, skipping balance query")
                return None

            # 验证group_id是否配置
            group_id = self.config.get("group_id")
            if not group_id:
                self.logger.warning("Minimaxi group_id not configured")
                return None

            self.logger.debug(
                "Starting Minimaxi subscription fetch",
                {"token_length": len(login_token) if login_token else 0},
            )

            # 使用Minimaxi的订阅查询端点
            subscription_data = self.make_request("/openplatform/charge/combo/cycle_audio_resource_package")

            if subscription_data:
                self.logger.info(
                    "Minimaxi subscription data fetched successfully",
                    {
                        "data_keys": list(subscription_data.keys()),
                        "data_type": type(subscription_data).__name__,
                        "has_current_subscribe": "current_subscribe" in subscription_data,
                    },
                )
                return subscription_data
            else:
                self.logger.warning(
                    "Minimaxi subscription API returned None",
                    {"possible_cause": "API request failed or returned empty data"},
                )
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
            return "Minimaxi:\033[91mNoData\033[0m"

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
                return "Minimaxi:\033[91mNoSub\033[0m"

            # 获取订阅结束时间
            end_time = current_subscribe.get("current_subscribe_end_time", "")
            if not end_time:
                self.logger.warning("Minimaxi subscription data missing 'current_subscribe_end_time' field")
                return "Minimaxi:\033[91mNoDate\033[0m"

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

                # 格式化显示（不包含平台名称，由formatter统一添加）
                subscription_str = f"{color}{expiry_short}{reset}"

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
                return f"Minimaxi:{end_time[:5]}"

        except Exception as e:
            self.logger.error(f"Minimaxi subscription formatting failed: {e}")
            return f"Minimaxi:Error({str(e)[:20]})"

    def format_subscription_display(self, subscription_data: Dict[str, Any]) -> str:
        """Format Minimaxi subscription details for display"""
        if subscription_data is None:
            self.logger.info("No subscription data available for display")
            return "Minimaxi.Sub:\033[94mPackage\033[0m"

        try:
            # Minimaxi使用套餐模式
            reset_color = "\033[0m"
            color = "\033[94m"  # 蓝色

            subscription_text = "Package.Subscription"
            return f"{color}{subscription_text}{reset}"
        except Exception as e:
            self.logger.error(f"Minimaxi subscription details formatting failed: {e}")
            return f"Minimaxi.Sub:Error({str(e)[:20]})"
