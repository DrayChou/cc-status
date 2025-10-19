#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Status formatter - 格式化状态信息显示
"""

from typing import Dict, Any, List
from datetime import datetime
from ..utils.logger import get_logger


class StatusFormatter:
    """状态格式化器"""

    def __init__(self):
        self.logger = get_logger("formatter")

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
            formatted_parts.append(f"Model:{model_name}")

        if config.get("show_time", True):
            current_time = status_data.get("time", datetime.now().strftime("%H:%M:%S"))
            formatted_parts.append(f"Time:{current_time}")

        # 今日使用量
        if config.get("show_today_usage", True):
            usage_info = self._format_usage(status_data)
            if usage_info:
                formatted_parts.append(usage_info)

        # 所有启用平台的余额信息
        if config.get("show_balance", True):
            platform_balances = self._format_platform_balances(status_data)
            formatted_parts.extend(platform_balances)

        # Git信息
        if config.get("show_git_branch", True):
            git_info = status_data.get("git")
            if git_info:
                branch_text = git_info.get("branch", "detached")
                if git_info.get("is_dirty", False):
                    branch_text += "*"
                formatted_parts.append(f"Git:{branch_text}")

        return formatted_parts

    def _format_usage(self, status_data: Dict[str, Any]) -> str:
        """格式化使用量信息"""
        try:
            usage_data = status_data.get("usage", {})
            if usage_data:
                total_cost = usage_data.get("total_cost", 0)
                if total_cost > 0:
                    return f"Today:${total_cost:.2f}"
        except Exception as e:
            self.logger.warning(f"Failed to format usage: {e}")
        return ""

    def _format_platform_balances(self, status_data: Dict[str, Any]) -> List[str]:
        """格式化所有平台的余额信息"""
        balance_parts = []
        platforms_data = status_data.get("platforms", {})

        for platform_id, platform_info in platforms_data.items():
            try:
                if not platform_info.get("enabled", False):
                    continue

                platform_name = platform_info.get("name", platform_id)
                balance_info = self._format_single_platform_balance(platform_info)

                if balance_info:
                    balance_parts.append(f"{platform_name}:{balance_info}")

            except Exception as e:
                self.logger.warning(f"Failed to format balance for {platform_id}: {e}")

        return balance_parts

    def _format_single_platform_balance(self, platform_info: Dict[str, Any]) -> str:
        """格式化单个平台的余额信息"""
        try:
            balance_data = platform_info.get("balance", {})
            if not balance_data:
                # 如果没有余额数据，显示配置状态
                if platform_info.get("has_auth", False):
                    return "Configured"
                else:
                    return "Not Configured"

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
            else:
                return self._format_generic_balance(balance_data)

        except Exception as e:
            self.logger.warning(f"Failed to format single platform balance: {e}")
            return "Error"

    def _format_gaccode_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化 GAC Code 余额信息"""
        try:
            balance = balance_data.get("balance", 0)
            limit = balance_data.get("limit", 0)

            if limit > 0:
                percentage = (balance / limit) * 100
                return f"{balance}/{limit} ({percentage:.1f}%)"
            else:
                return str(balance)
        except:
            return "Error"

    def _format_deepseek_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化 DeepSeek 余额信息"""
        try:
            balance = balance_data.get("balance", 0)
            currency = balance_data.get("currency", "USD")

            if currency == "CNY":
                return f"¥{balance:.2f}"
            else:
                return f"${balance:.2f}"
        except:
            return "Error"

    def _format_kimi_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化 Kimi 余额信息"""
        try:
            balance = balance_data.get("balance", 0)
            currency = balance_data.get("currency", "CNY")

            if currency == "CNY":
                return f"¥{balance:.2f}"
            else:
                return f"${balance:.2f}"
        except:
            return "Error"

    def _format_siliconflow_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化 SiliconFlow 余额信息"""
        try:
            balance = balance_data.get("balance", 0)
            currency = balance_data.get("currency", "CNY")

            if currency == "CNY":
                return f"¥{balance:.2f}"
            else:
                return f"${balance:.2f}"
        except:
            return "Error"

    def _format_generic_balance(self, balance_data: Dict[str, Any]) -> str:
        """格式化通用余额信息"""
        try:
            balance = balance_data.get("balance", 0)
            currency = balance_data.get("currency", "USD")

            if currency == "CNY":
                return f"¥{balance:.2f}"
            else:
                return f"${balance:.2f}"
        except:
            return "Error"