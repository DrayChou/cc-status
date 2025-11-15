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
        # GLM余额查询使用正确的API基础地址
        # 基于真实浏览器请求，使用 https://bigmodel.cn/api
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
        """Fetch balance data from GLM API using login_token"""
        try:
            # GLM需要使用login_token而不是auth_token
            login_token = self.config.get("login_token")
            if not login_token:
                self.logger.warning("GLM platform requires login_token for balance queries")
                return None

            self.logger.debug(
                "Starting GLM balance fetch with login_token",
                {"token_length": len(login_token) if login_token else 0},
            )

            # 使用GLM正确的余额查询端点
            # 基于真实浏览器请求，使用/biz/account/query-customer-account-report获取余额信息
            balance_data = self.make_request("/biz/account/query-customer-account-report")

            if balance_data:
                # 从余额数据中提取信息
                # 响应结构：{"code":200,"msg":"操作成功","data":{"balance":-0.00043896,"availableBalance":-0.00043896}}
                self.logger.info(
                    "GLM balance data fetched successfully",
                    {
                        "data_keys": list(balance_data.keys()),
                        "data_type": type(balance_data).__name__,
                        "has_data": "data" in balance_data,
                        "success": balance_data.get("success"),
                    },
                )

                # 同时获取订阅信息以显示到期时间
                subscription_data = self.make_request("/biz/subscription/list")

                # 合并余额和订阅数据
                combined_data = {
                    "balance_data": balance_data,
                    "subscription_data": subscription_data
                }

                return combined_data
            else:
                self.logger.warning(
                    "GLM balance API returned None or empty data",
                    {"possible_cause": "API request failed or returned empty data"},
                )
                # 返回API不可用状态
                return {
                    "api_unavailable": True,
                    "reason": "API returned empty response"
                }

            if balance_data:
                # 检查API是否返回错误
                if balance_data.get("code") == 500 or balance_data.get("success") == False:
                    error_msg = balance_data.get("msg", "Unknown API error")
                    self.logger.warning(f"GLM API returned error: {error_msg}")
                    # 返回错误信息，让前端显示API错误状态
                    return {
                        "api_error": True,
                        "error_code": balance_data.get("code"),
                        "error_msg": error_msg,
                        "raw_response": balance_data
                    }

                self.logger.info(
                    "GLM balance data fetched successfully",
                    {
                        "data_keys": list(balance_data.keys()),
                        "data_type": type(balance_data).__name__,
                        "has_data": "data" in balance_data,
                        "success": balance_data.get("success"),
                    },
                )
                return balance_data
            else:
                self.logger.warning(
                    "GLM balance API returned None or empty data",
                    {"possible_cause": "API request failed or returned empty data"},
                )
                # 返回API不可用状态
                return {
                    "api_unavailable": True,
                    "reason": "API returned empty response"
                }

        except Exception as e:
            self.logger.error(f"GLM balance fetch failed: {e}")
            return {
                "api_error": True,
                "error_msg": str(e),
                "reason": "Exception during API call"
            }

    def make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """重写make_request方法，使用login_token进行认证"""
        login_token = self.config.get("login_token")
        if not login_token:
            self.logger.warning("No login_token available for GLM request")
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
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh',
            'authorization': login_token,  # GLM使用完整的JWT token
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

        # 添加组织ID和项目ID（从配置或默认）
        org_id = self.config.get("bigmodel_organization", "org-0157fc0012064f86B6261289788959ae")
        project_id = self.config.get("bigmodel_project", "proj_CE4Eb8359E0842F19c5f497a8A5Dd7b5")
        if org_id:
            headers['bigmodel-organization'] = org_id
        if project_id:
            headers['bigmodel-project'] = project_id

        try:
            self.logger.info(f"Making GLM API request to: {url}")
            self.logger.info(f"GLM request headers: {headers}")
            response = requests.get(url, headers=headers, timeout=10)

            self.logger.info(f"GLM API response status: {response.status_code}")
            self.logger.info(f"GLM API response headers: {dict(response.headers)}")
            self.logger.info(f"GLM API response text: {response.text[:500]}")

            if response.status_code == 200:
                # 检查响应内容是否为空
                if not response.text.strip():
                    self.logger.warning("GLM API returned empty response")
                    return None

                try:
                    json_data = response.json()
                    self.logger.info(f"GLM API response JSON: {json_data}")

                    # 检查业务错误码
                    if json_data.get("code") == 401:
                        self.logger.error("GLM API returned 401 - Token expired or invalid")
                        return {
                            "api_error": True,
                            "error_code": 401,
                            "error_msg": "Token expired or invalid",
                            "http_status": response.status_code,
                            "reason": "Authentication failed"
                        }
                    elif json_data.get("code") != 200:
                        self.logger.warning(f"GLM API business error: {json_data.get('msg', 'Unknown error')}")
                        return {
                            "api_error": True,
                            "error_code": json_data.get("code", "ERROR"),
                            "error_msg": json_data.get("msg", "Unknown error"),
                            "http_status": response.status_code,
                            "raw_response": json_data
                        }

                    return json_data
                except json.JSONDecodeError as e:
                    self.logger.error(f"GLM API response is not valid JSON: {e}")
                    self.logger.error(f"Response text: {response.text}")
                    return None
            else:
                # 返回HTTP状态码错误
                self.logger.warning(f"GLM API request failed with status {response.status_code}: {response.text}")
                return {
                    "api_error": True,
                    "error_code": response.status_code,
                    "error_msg": f"HTTP {response.status_code}",
                    "http_status": response.status_code,
                    "raw_response": response.text
                }

        except Exception as e:
            self.logger.error(f"GLM API request error: {e}")
            return None

    def fetch_subscription_data(self) -> Optional[Dict[str, Any]]:
        """GLM uses pay-as-you-go billing, no subscription concept"""
        # GLM使用按量付费模式，没有订阅概念
        return None

    def format_balance_display(self, combined_data: Dict[str, Any]) -> str:
        """Format GLM balance and subscription for display"""
        # 处理空数据情况
        if combined_data is None:
            self.logger.info("No combined data available for display")
            return "GLM.B:\033[91mNoData\033[0m"

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
                return f"GLM.B:\033[91mAPI{error_code}\033[0m"

            if combined_data.get("api_unavailable"):
                self.logger.warning("GLM API unavailable")
                return f"GLM.B:\033[91mUnavail\033[0m"

            # 提取余额数据
            balance_data = combined_data.get("balance_data", {})
            subscription_data = combined_data.get("subscription_data", {})

            # 处理余额部分
            if "data" not in balance_data:
                self.logger.warning("GLM balance data missing 'data' field")
                balance_display = "\033[91mNoData\033[0m"
            else:
                data = balance_data.get("data", {})
                balance = data.get("availableBalance", 0)
                currency = "CNY"  # GLM只支持人民币

                # 颜色代码基于余额 - 支持负值显示
                if currency == "CNY":
                    if balance < 0:  # 负余额 - 红色
                        color = "\033[91m"
                    elif balance <= 10:
                        color = "\033[93m"  # 黄色
                    else:
                        color = "\033[92m"  # 绿色
                else:
                    if balance <= 5:
                        color = "\033[91m"  # 红色
                    elif balance <= 25:
                        color = "\033[93m"  # 黄色
                    else:
                        color = "\033[92m"  # 绿色

                reset = "\033[0m"

                # 格式化余额显示（保留6位小数）
                if currency == "CNY":
                    balance_display = f"{color}{balance:.6f}CNY{reset}"
                else:
                    balance_display = f"{color}${balance:.2f}{reset}"

            # 处理订阅部分
            subscription_display = ""
            if subscription_data and isinstance(subscription_data, dict) and "data" in subscription_data:
                subscriptions = subscription_data.get("data", [])
                if subscriptions and len(subscriptions) > 0:
                    # 找到当前有效的订阅
                    current_sub = None
                    for sub in subscriptions:
                        if sub.get("status") == "VALID" and sub.get("inCurrentPeriod"):
                            current_sub = sub
                            break

                    if current_sub:
                        product_name = current_sub.get("productName", "Unknown")
                        next_renew = current_sub.get("nextRenewTime", "")
                        if next_renew:
                            try:
                                from datetime import datetime
                                # 格式化到期时间 (MM-DD)
                                if len(next_renew) >= 10:
                                    date_obj = datetime.fromisoformat(next_renew[:10])
                                    renew_short = date_obj.strftime("%m-%d")
                                    subscription_display = f" Sub:{renew_short}"
                                else:
                                    subscription_display = f" Sub:{next_renew[:5]}"
                            except:
                                subscription_display = f" Sub:{next_renew[:5]}"
                        else:
                            subscription_display = " Sub:NoRenew"
                    else:
                        subscription_display = " Sub:NoActive"
                else:
                    subscription_display = " Sub:NoData"
            else:
                subscription_display = " Sub:NoInfo"

            # 组合最终显示（去掉平台名称前缀，由formatter统一添加）
            final_display = f"{balance_display}{subscription_display}"

            self.logger.debug(
                "GLM combined formatting completed",
                {
                    "final_display": final_display,
                    "balance": balance if 'balance' in locals() else 'N/A',
                    "has_subscription": bool(subscription_display),
                },
            )

            return final_display
        except Exception as e:
            self.logger.error(f"GLM combined formatting failed: {e}")
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