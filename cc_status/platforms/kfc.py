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
        """Fetch balance data from KFC API using login_token (JWT) or auth_token"""
        try:
            # KFC 余额查询需要 JWT 格式的 login_token
            # auth_token (sk-kimi-xxx) 是 API Key，不能用于余额查询
            login_token = self.config.get("login_token")
            auth_token = self.config.get("auth_token")

            # 优先使用 login_token (JWT)
            token = None
            token_type = None
            if login_token:
                token = login_token
                token_type = "login_token"
            elif auth_token and auth_token.startswith("eyJ"):
                # 如果 auth_token 是 JWT 格式，也可以使用
                token = auth_token
                token_type = "auth_token (JWT)"

            # 验证是否有可用的 token
            if not token:
                self.logger.debug(
                    "KFC login_token not configured, skipping balance query. "
                    "Note: auth_token (sk-kimi-xxx) cannot be used for balance query. "
                    "Please set login_token with JWT from browser cookie."
                )
                return None

            self.logger.debug(
                "Starting KFC balance fetch",
                {
                    "token_type": token_type,
                    "has_token": bool(token),
                    "token_length": len(token) if token else 0,
                },
            )

            # 使用 token 调用 KFC API
            balance_data = self._make_kfc_request(token)

            if balance_data:
                self.logger.info(
                    f"KFC balance data fetched successfully with {token_type}",
                    {
                        "data_keys": list(balance_data.keys()),
                        "data_type": type(balance_data).__name__,
                        "has_balance_data": "data" in balance_data,
                    },
                )
                # 添加原始数据字段
                balance_data["raw_data"] = balance_data.copy()
                return balance_data
            else:
                self.logger.warning(f"KFC {token_type} query failed")

            return None

        except Exception as e:
            self.logger.error(f"KFC balance fetch failed: {e}")
            return None

    def _make_kfc_request(self, token: str) -> Optional[Dict[str, Any]]:
        """Make KFC usage query using KFC-specific API with auth_token"""
        import requests

        # KFC专用API端点 - 查询使用量 (2025-01更新)
        url = "https://www.kimi.com/apiv2/kimi.gateway.billing.v1.BillingService/GetUsages"

        # Request headers - 使用Bearer Token认证
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'accept': '*/*',
            'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8',
            'cache-control': 'no-cache',
            'connect-protocol-version': '1',
            'origin': 'https://www.kimi.com',
            'pragma': 'no-cache',
            'referer': 'https://www.kimi.com/code/console',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/144.0.0.0 Safari/537.36'
            ),
            'x-language': 'zh-CN',
            'x-msh-platform': 'web',
            'x-msh-version': '1.0.0',
        }

        # Request data - 新版API格式
        data = {
            "scope": ["FEATURE_CODING"]
        }

        try:
            self.logger.debug(f"Making KFC API request to: {url}")
            self.logger.debug(
                f"Using auth_token (first 20 chars): {token[:20]}..."
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
                    f"{response.status_code}: {response.text[:200]}"
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
        """Format KFC balance for display with both short-term and weekly limits"""
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
            # KFC API 返回 usages 数组
            usages = balance_data.get("usages", [])
            if not usages:
                self.logger.warning("No usages data found in KFC response")
                return "\033[91mNoUsage\033[0m"

            # 找到 FEATURE_CODING 的使用数据
            usage = None
            for u in usages:
                if u.get("scope") == "FEATURE_CODING":
                    usage = u
                    break

            if not usage:
                self.logger.warning("No FEATURE_CODING usage found in KFC response")
                return "\033[91mNoCodingUsage\033[0m"

            # 解析周限额数据 (detail)
            weekly_detail = usage.get("detail", {})
            weekly_limit = int(weekly_detail.get("limit", "0") or "0")
            weekly_remaining = int(weekly_detail.get("remaining", "0") or "0")
            weekly_reset_time = weekly_detail.get("resetTime", "")

            # 解析短期限额数据 (limits 数组中的第一个，通常是5分钟窗口)
            limits = usage.get("limits", [])
            short_limit = 0
            short_remaining = 0
            short_reset_time = ""

            if limits:
                # 使用第一个limit（短期5分钟窗口）
                short_detail = limits[0].get("detail", {})
                short_limit = int(short_detail.get("limit", "0") or "0")
                short_remaining = int(short_detail.get("remaining", "0") or "0")
                short_reset_time = short_detail.get("resetTime", "")

            self.logger.debug(
                "KFC usage data structure",
                {
                    "short_limit": short_limit,
                    "short_remaining": short_remaining,
                    "weekly_limit": weekly_limit,
                    "weekly_remaining": weekly_remaining,
                },
            )

            # 格式化两个重置时间
            short_reset_display = self._format_reset_time(short_reset_time)
            weekly_reset_display = self._format_reset_time(weekly_reset_time)

            # 颜色代码基于短期剩余次数（更关键的指标）
            if short_remaining <= 20:
                color = "\033[91m"  # 红色
                color_name = "red"
            elif short_remaining <= 50:
                color = "\033[93m"  # 黄色
                color_name = "yellow"
            else:
                color = "\033[92m"  # 绿色
                color_name = "green"

            reset = "\033[0m"

            # 格式化显示: 5h:短期剩余/短期总数(短期刷新时间)|wk:周剩余/周总数(周刷新时间)
            if short_limit > 0 and weekly_limit > 0:
                balance_str = f"{color}5h:{short_remaining}/{short_limit}{short_reset_display}{reset}|wk:{weekly_remaining}/{weekly_limit}{weekly_reset_display}"
            elif weekly_limit > 0:
                balance_str = f"{color}wk:{weekly_remaining}/{weekly_limit}{weekly_reset_display}{reset}"
            else:
                balance_str = f"{color}N/A{reset}"

            self.logger.debug(
                "KFC balance formatting completed",
                {
                    "final_display": balance_str,
                    "color_used": color_name,
                    "short_remaining": short_remaining,
                    "short_limit": short_limit,
                    "short_reset_time": short_reset_time,
                    "weekly_remaining": weekly_remaining,
                    "weekly_limit": weekly_limit,
                    "weekly_reset_time": weekly_reset_time,
                },
            )

            return balance_str
        except Exception as e:
            self.logger.error(f"KFC balance formatting failed: {e}")
            return f"Error({str(e)[:20]})"

    def _format_reset_time(self, reset_time: str) -> str:
        """Format reset time for display with timezone conversion"""
        if not reset_time:
            return "(NoReset)"

        try:
            from datetime import datetime, timezone
            # 解析ISO格式时间：2026-02-12T17:27:08.139540Z (UTC)
            if 'T' in reset_time:
                # 处理带Z后缀的UTC时间
                if reset_time.endswith('Z'):
                    reset_time = reset_time[:-1] + '+00:00'

                # 解析为带时区的datetime对象
                try:
                    utc_dt = datetime.fromisoformat(reset_time.replace('Z', '+00:00'))
                except ValueError:
                    # 兼容旧格式：手动解析
                    date_part = reset_time.split('T')[0]
                    time_part = reset_time.split('T')[1].split('.')[0]
                    utc_dt = datetime.strptime(f"{date_part}T{time_part}", "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)

                # 转换为本地时区
                local_dt = utc_dt.astimezone()

                # 获取当前本地时间
                today = datetime.now().astimezone()

                if local_dt.date() == today.date():
                    # 今天刷新，只显示时间 (HH:MM)
                    reset_short = local_dt.strftime('%H:%M')
                else:
                    # 其他日期显示 月-日 时:分
                    reset_short = f"{local_dt.strftime('%m-%d')} {local_dt.strftime('%H:%M')}"

                return f"({reset_short})"
            else:
                return f"({reset_time[:16]})"  # 备用方案
        except Exception:
            return f"({reset_time[:16]})"

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
