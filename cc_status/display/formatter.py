#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Status formatter - 格式化状态信息显示
"""

from typing import Dict, Any, List
from datetime import datetime
from ..utils.logger import get_logger
from ..utils.colors import ColorScheme


class StatusFormatter:
    """状态格式化器"""

    def __init__(self):
        self.logger = get_logger("formatter")
        self.colors = ColorScheme.get_status_colors()
        self.use_colors = ColorScheme.is_color_supported()

    def format_status(self, status_data: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
        """
        格式化状态信息

        Args:
            status_data: 状态数据
            config: 配置信息

        Returns:
            格式化后的状态信息列表
        """
        formatted_parts = []

        # 基础信息
        if config.get("show_model", True):
            model_name = status_data.get("model", "Unknown")
            if self.use_colors:
                formatted_parts.append(f"Model:{self.colors['model']}{model_name}{self.colors['reset']}")
            else:
                formatted_parts.append(f"Model:{model_name}")

        if config.get("show_time", True):
            current_time = status_data.get("time", datetime.now().strftime("%H:%M:%S"))
            if self.use_colors:
                formatted_parts.append(f"Time:{self.colors['time']}{current_time}{self.colors['reset']}")
            else:
                formatted_parts.append(f"Time:{current_time}")

        # 今日使用量
        if config.get("show_today_usage", True):
            usage_info = self._format_usage(status_data)
            if usage_info:
                formatted_parts.append(usage_info)

        # 所有启用平台的余额和订阅信息
        if config.get("show_balance", True):
            platform_balances = self._format_platform_balances(status_data)
            formatted_parts.extend(platform_balances)

        # 工作目录信息
        if config.get("show_directory", True):
            directory_info = self._format_directory(status_data)
            if directory_info:
                formatted_parts.append(directory_info)

        # Git信息
        if config.get("show_git_branch", True):
            git_info = status_data.get("git")
            if git_info:
                branch_text = git_info.get("branch", "detached")
                is_dirty = git_info.get("is_dirty", False)
                if is_dirty:
                    branch_text += "*"

                if self.use_colors:
                    git_color = self.colors['git_dirty'] if is_dirty else self.colors['git_clean']
                    formatted_parts.append(f"Git:{git_color}{branch_text}{self.colors['reset']}")
                else:
                    formatted_parts.append(f"Git:{branch_text}")

        return formatted_parts

    def _format_usage(self, status_data: Dict[str, Any]) -> str:
        """格式化使用量信息"""
        try:
            usage_data = status_data.get("usage", {})
            if usage_data:
                total_cost = usage_data.get("total_cost", 0)
                if total_cost > 0:
                    if self.use_colors:
                        usage_color = ColorScheme.get_usage_color(total_cost)
                        return f"Today:{usage_color}${total_cost:.2f}{self.colors['reset']}"
                    else:
                        return f"Today:${total_cost:.2f}"
        except Exception as e:
            self.logger.warning(f"Failed to format usage: {e}")
        return ""

    def _format_directory(self, status_data: Dict[str, Any]) -> str:
        """格式化目录信息"""
        try:
            directory = status_data.get("directory", "")
            if directory:
                if self.use_colors:
                    return f"Dir:{self.colors['directory']}{directory}{self.colors['reset']}"
                else:
                    return f"Dir:{directory}"
        except Exception as e:
            self.logger.warning(f"Failed to format directory: {e}")
        if self.use_colors:
            return f"Dir:{self.colors['directory']}Unknown{self.colors['reset']}"
        else:
            return "Dir:Unknown"

    def _format_platform_balances(self, status_data: Dict[str, Any]) -> List[str]:
        """格式化所有平台的余额和订阅信息"""
        balance_parts = []
        platforms_data = status_data.get("platforms", {})

        for platform_id, platform_info in platforms_data.items():
            try:
                if not platform_info.get("enabled", False):
                    continue

                platform_name = platform_info.get("name", platform_id)
                balance_info = self._format_single_platform_balance(platform_info)
                subscription_info = self._format_single_platform_subscription(platform_info)

                # 构建平台信息，过滤掉Error和None值
                platform_parts = []
                if balance_info and balance_info != "Error":
                    platform_parts.append(balance_info)
                if subscription_info and subscription_info != "Error":
                    platform_parts.append(subscription_info)

                # 只有有有效的余额或订阅信息才显示
                if platform_parts:
                    display_text = " ".join(platform_parts)
                    balance_parts.append(f"{platform_name}:{display_text}")

            except Exception as e:
                self.logger.warning(f"Failed to format balance for {platform_id}: {e}")

        return balance_parts

    def _format_single_platform_balance(self, platform_info: Dict[str, Any]) -> str:
        """格式化单个平台的余额信息"""
        try:
            balance_data = platform_info.get("balance", {})
            if not balance_data:
                # 如果没有余额数据，不显示余额部分
                return None

            # 根据不同平台格式化余额
            platform_id = platform_info.get("id", "").lower()

            if platform_id == "gaccode":
                return self._format_gaccode_balance(balance_data)
            elif platform_id == "deepseek":
                return self._format_deepseek_balance(balance_data)
            elif platform_id == "kimi":
                return self._format_kimi_balance(balance_data)
            elif platform_id == "siliconflow":
                return self._format_siliconflow_balance(balance_data)
            elif platform_id == "glm":
                return self._format_glm_balance(balance_data)
            elif platform_id == "kfc":
                return self._format_kfc_balance(balance_data)
            else:
                return self._format_generic_balance(balance_data)

        except Exception as e:
            self.logger.warning(f"Failed to format single platform balance: {e}")
            return None

    def _format_balance_with_color(self, balance_text: str, balance: float, currency: str = "USD") -> str:
        """为余额文本添加颜色"""
        if self.use_colors:
            balance_color = ColorScheme.get_balance_color(balance, currency)
            return f"{balance_color}{balance_text}{self.colors['reset']}"
        else:
            return balance_text

    def _format_gaccode_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化 GAC Code 余额信息"""
        try:
            balance = balance_data.get("balance", 0)
            limit = balance_data.get("limit", 0)

            if limit > 0:
                percentage = (balance / limit) * 100
                balance_text = f"{balance}/{limit} ({percentage:.1f}%)"
            else:
                balance_text = str(balance)

            return self._format_balance_with_color(balance_text, balance, "points")
        except:
            return "Error"

    def _format_deepseek_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化 DeepSeek 余额信息"""
        try:
            balance = balance_data.get("balance", 0)
            currency = balance_data.get("currency", "USD")

            if currency == "CNY":
                balance_text = f"¥{balance:.2f}"
            else:
                balance_text = f"${balance:.2f}"

            return self._format_balance_with_color(balance_text, balance, currency)
        except:
            return "Error"

    def _format_kimi_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化 Kimi 余额信息"""
        try:
            balance = balance_data.get("balance", 0)
            currency = balance_data.get("currency", "CNY")

            if currency == "CNY":
                balance_text = f"¥{balance:.2f}"
            else:
                balance_text = f"${balance:.2f}"

            return self._format_balance_with_color(balance_text, balance, currency)
        except:
            return "Error"

    def _format_siliconflow_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化 SiliconFlow 余额信息"""
        try:
            balance = balance_data.get("balance", 0)
            currency = balance_data.get("currency", "CNY")

            if currency == "CNY":
                balance_text = f"¥{balance:.2f}"
            else:
                balance_text = f"${balance:.2f}"

            return self._format_balance_with_color(balance_text, balance, currency)
        except:
            return "Error"

    def _format_glm_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化 GLM 余额信息"""
        try:
            balance = balance_data.get("balance", 0)
            currency = balance_data.get("currency", "CNY")

            if currency == "CNY":
                balance_text = f"¥{balance:.2f}"
            else:
                balance_text = f"${balance:.2f}"

            return self._format_balance_with_color(balance_text, balance, currency)
        except:
            return "Error"

    def _format_generic_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化通用余额信息"""
        try:
            balance = balance_data.get("balance", 0)
            currency = balance_data.get("currency", "USD")

            if currency == "CNY":
                balance_text = f"¥{balance:.2f}"
            else:
                balance_text = f"${balance:.2f}"

            return self._format_balance_with_color(balance_text, balance, currency)
        except:
            return "Error"

    def _format_kfc_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化 KFC 余额信息"""
        try:
            # KFC 返回的是使用次数信息，不是货币余额
            usages = balance_data.get("usages", [])
            if not usages:
                return None

            # 获取FEATURE_CODING的使用情况
            coding_usage = None
            for usage in usages:
                if usage.get("scope") == "FEATURE_CODING":
                    coding_usage = usage.get("detail", {})
                    break

            if not coding_usage:
                return None

            limit = int(coding_usage.get("limit", 0))
            used = int(coding_usage.get("used", 0))
            remaining = int(coding_usage.get("remaining", 0))

            if limit > 0:
                balance_text = f"{remaining}/{limit} ({(used/limit)*100:.1f}%)"
            else:
                balance_text = str(remaining)

            # KFC 使用点数系统，不是货币
            return self._format_balance_with_color(balance_text, remaining, "points")
        except:
            return "Error"

    def _format_single_platform_subscription(self, platform_info: Dict[str, Any]) -> str:
        """格式化单个平台的订阅信息"""
        try:
            subscription_data = platform_info.get("subscription", {})
            if not subscription_data:
                return None

            platform_id = platform_info.get("id", "").lower()

            # 根据不同平台格式化订阅信息
            if platform_id == "glm":
                plan = subscription_data.get("plan", "Unknown")
                model = subscription_data.get("model", "GLM")
                subscription_text = f"Sub:{plan}({model})"
            elif platform_id == "deepseek":
                plan = subscription_data.get("plan", "Free")
                subscription_text = f"Sub:{plan}"
            elif platform_id == "kimi":
                plan = subscription_data.get("plan", "Free")
                expiry = subscription_data.get("expiry", "")
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
            else:
                plan = subscription_data.get("plan", "Unknown")
                subscription_text = f"Sub:{plan}"

            # 添加颜色
            if self.use_colors:
                return f"{self.colors['subscription']}{subscription_text}{self.colors['reset']}"
            else:
                return subscription_text

        except Exception as e:
            self.logger.warning(f"Failed to format subscription: {e}")
            return None