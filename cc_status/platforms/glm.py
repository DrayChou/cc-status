#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLM platform implementation
"""

from typing import Dict, Any, Optional
from .base import BasePlatform
from ..utils.logger import get_logger
import requests


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
        # GLM使用统一API基础地址
        return "https://bigmodel.cn/api"

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

        # 方法3: 通过token格式判断（GLM token 以数字开头或 eyJ 开头）
        if token and (token[0].isdigit() or token.startswith("eyJ")):
            self.logger.debug(
                "GLM token format detected",
                {"method": "token_prefix", "token_prefix": token[:10] + "..."},
            )
            return True

        self.logger.debug("GLM platform not detected")
        return False

    def fetch_balance_data(self) -> Optional[Dict[str, Any]]:
        """Fetch balance/quota data from GLM API using auth_token (API Key)"""
        try:
            # 验证认证token是否配置（支持 auth_token, api_key）
            auth_token = (
                self.config.get("auth_token") or
                self.config.get("api_key")
            )
            if not auth_token or not isinstance(auth_token, str) or len(auth_token.strip()) == 0:
                self.logger.debug("GLM authentication token not configured, skipping balance query")
                return None

            self.logger.debug(
                "Starting GLM balance fetch with authentication token",
                {"token_length": len(auth_token) if auth_token else 0},
            )

            # 使用新的配额查询API
            quota_data = self.make_request("/monitor/usage/quota/limit")

            if quota_data:
                self.logger.info(
                    "GLM quota data fetched successfully",
                    {
                        "data_keys": list(quota_data.keys()),
                        "has_limits": "limits" in quota_data.get("data", {}),
                    },
                )

                # 同时获取订阅信息以显示到期时间
                subscription_data = self.make_request("/biz/subscription/list?pageSize=9999&pageNum=1")

                # 合并配额和订阅数据
                combined_data = {
                    "quota_data": quota_data,
                    "subscription_data": subscription_data
                }

                return combined_data
            else:
                self.logger.warning(
                    "GLM quota API returned None or empty data",
                    {"possible_cause": "API request failed or returned empty data"},
                )
                return {
                    "api_unavailable": True,
                    "reason": "API returned empty response - token may be expired or invalid"
                }

        except Exception as e:
            self.logger.error(f"GLM balance fetch failed: {e}")
            return {
                "api_error": True,
                "error_msg": str(e),
                "reason": "Exception during API call"
            }

    def make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """重写make_request方法，使用auth_token (API Key) 进行认证"""
        # 获取认证token（支持 auth_token, api_key）
        auth_token = (
            self.config.get("auth_token") or
            self.config.get("api_key")
        )

        if not auth_token:
            self.logger.warning("No authentication token available (auth_token or api_key)")
            return None

        # 构建完整的URL
        if hasattr(self, 'api_base'):
            api_base = self.api_base
        else:
            api_base = self.config.get("api_base_url", "")

        if not api_base:
            self.logger.error("No API base URL configured for GLM")
            return None

        # 基于真实浏览器请求构建headers
        url = f"{api_base}{endpoint}"

        # 使用 Bearer 格式进行认证
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh',
            'authorization': f"Bearer {auth_token}",
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://bigmodel.cn/finance-center/subscribe-manage',
            'sec-ch-ua': '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'set-language': 'zh',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
        }

        try:
            self.logger.debug(f"Making GLM API request to: {url}")
            response = requests.get(url, headers=headers, timeout=10)

            self.logger.debug(
                "GLM API response received",
                {"status": response.status_code, "url": url},
            )

            if response.status_code == 200:
                # 检查响应内容是否为空
                if not response.text.strip():
                    self.logger.warning("GLM API returned empty response")
                    return None

                try:
                    import json
                    json_data = response.json()

                    # 只记录关键字段，不记录完整响应（防止敏感信息泄漏）
                    self.logger.debug(
                        "GLM API response parsed",
                        {
                            "code": json_data.get("code"),
                            "has_data": "data" in json_data,
                            "url": url,
                        },
                    )

                    # 检查业务错误码
                    if json_data.get("code") == 401:
                        self.logger.error("GLM API returned 401 - Token expired or invalid")
                        return {
                            "api_error": True,
                            "error_code": 401,
                            "error_msg": "Token expired or invalid",
                            "reason": "Authentication failed"
                        }
                    elif json_data.get("code") != 200:
                        self.logger.warning(f"GLM API business error: {json_data.get('msg', 'Unknown error')}")
                        return {
                            "api_error": True,
                            "error_code": json_data.get("code", "ERROR"),
                            "error_msg": json_data.get("msg", "Unknown error"),
                        }

                    return json_data
                except json.JSONDecodeError as e:
                    self.logger.error(f"GLM API response is not valid JSON: {e}")
                    return None
            else:
                # 返回HTTP状态码错误（不打印响应内容）
                self.logger.warning(
                    f"GLM API request failed with status {response.status_code}",
                    {"status": response.status_code, "url": url},
                )
                return {
                    "api_error": True,
                    "error_code": response.status_code,
                    "error_msg": f"HTTP {response.status_code}",
                }

        except Exception as e:
            self.logger.error(f"GLM API request error: {e}")
            return None

    def fetch_subscription_data(self) -> Optional[Dict[str, Any]]:
        """GLM uses pay-as-you-go billing, no subscription concept"""
        # GLM使用按量付费模式，没有订阅概念
        return None

    def _format_number(self, num: int) -> str:
        """格式化大数字，支持亿、万"""
        if num >= 100000000:
            return f"{num / 100000000:.1f}亿"
        elif num >= 10000:
            return f"{num / 10000:.1f}万"
        else:
            return f"{num}"

    def format_balance_display(self, combined_data: Dict[str, Any]) -> str:
        """Format GLM quota usage and subscription for display"""
        if combined_data is None:
            self.logger.info("No combined data available for display")
            return "\033[91mNoData\033[0m"

        self.logger.debug(
            "Starting GLM combined data formatting",
            {
                "combined_data_keys": list(combined_data.keys()),
                "combined_data_type": type(combined_data).__name__,
            },
        )

        try:
            # 检查API错误状态
            if combined_data.get("api_error"):
                error_code = combined_data.get("error_code", "ERROR")
                self.logger.warning(f"GLM API error, displaying error code: {error_code}")
                return f"\033[91mAPI{error_code}\033[0m"

            if combined_data.get("api_unavailable"):
                self.logger.warning("GLM API unavailable")
                return f"\033[91mUnavail\033[0m"

            # 提取配额数据
            quota_data = combined_data.get("quota_data", {})
            subscription_data = combined_data.get("subscription_data", {})

            # 从 limits 数组中提取信息
            # API字段: usage=配额总量, currentValue=已用量, remaining=剩余量
            total_quota = 0
            used = 0
            remaining = 0
            next_reset_time = 0

            if quota_data and isinstance(quota_data, dict):
                data = quota_data.get("data", {})
                limits = data.get("limits", [])
                if limits and len(limits) > 0:
                    # 查找 TOKENS_LIMIT
                    for limit in limits:
                        if limit.get("type") == "TOKENS_LIMIT":
                            total_quota = limit.get("usage", 0)
                            used = limit.get("currentValue", 0)
                            remaining = limit.get("remaining", 0)
                            next_reset_time = limit.get("nextResetTime", 0)
                            break

            # 计算使用率和颜色
            usage_pct = (used / total_quota * 100) if total_quota > 0 else 0
            remaining_pct = 100 - usage_pct

            # 颜色基于剩余量（剩余越少越红）
            if remaining_pct <= 10:
                usage_color = "\033[91m"  # 红色 - 告警
            elif remaining_pct <= 30:
                usage_color = "\033[93m"  # 黄色 - 警告
            else:
                usage_color = "\033[92m"  # 绿色 - 充足

            # 格式化刷新时间
            from datetime import datetime
            if next_reset_time > 0:
                try:
                    reset_time = datetime.fromtimestamp(next_reset_time / 1000)
                    reset_short = reset_time.strftime("%m-%d %H:%M")
                except:
                    reset_short = "Unknown"
            else:
                reset_short = "Unknown"

            # 格式化用量显示
            used_str = self._format_number(used)
            remaining_str = self._format_number(remaining)
            total_str = self._format_number(total_quota)

            # 处理订阅部分 - 使用中括号显示到期时间
            subscription_display = ""
            if subscription_data and isinstance(subscription_data, dict):
                subscriptions = subscription_data.get("data", [])
                if subscriptions and len(subscriptions) > 0:
                    current_sub = None
                    for sub in subscriptions:
                        if sub.get("status") == "VALID" and sub.get("inCurrentPeriod"):
                            current_sub = sub
                            break

                    if current_sub:
                        next_renew = current_sub.get("nextRenewTime", "")
                        if next_renew:
                            try:
                                date_obj = datetime.fromisoformat(next_renew[:10])
                                renew_short = date_obj.strftime("%m-%d")
                                subscription_display = f" [{renew_short}]"
                            except:
                                subscription_display = f" [{next_renew[:5]}]"

            reset = "\033[0m"

            # 组合显示：剩余/总量(刷新时间)[到期时间]
            # 格式参考 Minimaxi: `4261万/2亿(01-15 12:00) [01-09]`
            usage_display = f"{remaining_str}/{total_str}({reset_short})"

            final_display = f"{usage_color}{usage_display}{reset}{subscription_display}"

            self.logger.debug(
                "GLM combined formatting completed",
                {
                    "final_display": final_display,
                    "used": used_str,
                    "remaining": remaining_str,
                    "total": total_str,
                    "reset_time": reset_short,
                    "has_subscription": bool(subscription_display),
                },
            )

            return final_display
        except Exception as e:
            self.logger.error(f"GLM combined formatting failed: {e}")
            return f"Error({str(e)[:20]})"

    def format_subscription_display(self, subscription_data: Dict[str, Any]) -> str:
        """Format GLM subscription for display"""
        if subscription_data is None:
            self.logger.info("No subscription data available for display")
            return "\033[91mNoData\033[0m"

        try:
            # 新API返回的是数组格式
            subscriptions = subscription_data.get("data", [])
            if not subscriptions or len(subscriptions) == 0:
                return "\033[91mNoSub\033[0m"

            # 获取第一个有效订阅
            current_sub = None
            for sub in subscriptions:
                if sub.get("status") == "VALID" and sub.get("inCurrentPeriod"):
                    current_sub = sub
                    break

            if not current_sub:
                return "\033[91mNoSub\033[0m"

            product_name = current_sub.get("productName", "Unknown")

            self.logger.debug(
                "GLM subscription data structure",
                {
                    "product_name": product_name,
                    "status": current_sub.get("status"),
                },
            )

            reset = "\033[0m"
            color = "\033[94m"  # 蓝色

            subscription_text = f"Sub:{product_name}"
            return f"{color}{subscription_text}{reset}"
        except Exception as e:
            self.logger.error(f"GLM subscription formatting failed: {e}")
            return f"Error({str(e)[:20]})"