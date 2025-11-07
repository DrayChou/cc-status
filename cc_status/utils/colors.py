#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Color utilities - 颜色工具类
提供状态栏颜色支持
"""

from typing import Dict


class ColorScheme:
    """颜色方案类"""

    # ANSI 颜色代码
    RESET = "\033[0m"

    # 基础颜色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # 明亮颜色
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # 256色支持
    ORANGE = "\033[38;5;208m"      # 橙色 - 传说 (Legendary)
    PURPLE = "\033[38;5;128m"      # 紫色 - 神器 (Artifact)
    PINK = "\033[38;5;201m"        # 品红 - 史诗 (Epic)
    DARK_BLUE = "\033[38;5;21m"    # 深蓝 - 稀有 (Rare)
    LIGHT_BLUE = "\033[38;5;117m"  # 浅蓝 - 卓越 (Exceptional)
    DARK_GREEN = "\033[38;5;34m"   # 深绿 - 精良 (Fine)
    LIGHT_GREEN = "\033[38;5;120m" # 浅绿 - 优秀 (Uncommon)
    GRAY = "\033[38;5;242m"        # 灰色 - 劣质 (Poor)
    EXOTIC_RED = "\033[38;5;196m"  # 红色 - 不朽 (Exotic)

    # 余额状态颜色
    BALANCE_POSITIVE = "\033[92m"   # 正常余额 - 绿色
    BALANCE_LOW = "\033[93m"        # 低余额 - 黄色
    BALANCE_NEGATIVE = "\033[91m"   # 负余额 - 红色

    @classmethod
    def get_status_colors(cls) -> Dict[str, str]:
        """获取状态栏颜色方案"""
        return {
            'reset': cls.RESET,
            'model': cls.GREEN,              # 模型名称 - 绿色
            'time': cls.MAGENTA,             # 时间 - 洋红色
            'usage': cls.BRIGHT_CYAN,        # 使用量 - 亮青色
            'balance_positive': cls.GREEN,   # 正余额 - 绿色
            'balance_negative': cls.RED,     # 负余额 - 红色
            'balance_low': cls.YELLOW,       # 低余额 - 黄色
            'directory': cls.CYAN,           # 目录 - 青色
            'git_clean': cls.GREEN,          # Git干净状态 - 绿色
            'git_dirty': cls.YELLOW,         # Git脏状态 - 黄色
            'subscription': cls.BLUE,        # 订阅信息 - 蓝色
            'error': cls.RED,                # 错误 - 红色
            'warning': cls.YELLOW,           # 警告 - 黄色
        }

    @classmethod
    def get_usage_color(cls, usage_cost: float) -> str:
        """根据使用量返回对应的颜色代码

        Args:
            usage_cost: 使用量费用

        Returns:
            对应的颜色代码
        """
        if usage_cost >= 300:
            return cls.EXOTIC_RED    # 红色 - 不朽 (Exotic)
        elif usage_cost >= 200:
            return cls.ORANGE        # 橙色 - 传说 (Legendary)
        elif usage_cost >= 100:
            return cls.PURPLE        # 紫色 - 神器 (Artifact)
        elif usage_cost >= 50:
            return cls.PINK          # 品红 - 史诗 (Epic)
        elif usage_cost >= 20:
            return cls.DARK_BLUE     # 深蓝 - 稀有 (Rare)
        elif usage_cost >= 10:
            return cls.LIGHT_BLUE    # 浅蓝 - 卓越 (Exceptional)
        elif usage_cost >= 5:
            return cls.DARK_GREEN    # 深绿 - 精良 (Fine)
        elif usage_cost >= 2:
            return cls.LIGHT_GREEN   # 浅绿 - 优秀 (Uncommon)
        elif usage_cost >= 0.5:
            return cls.WHITE         # 白色 - 普通 (Common)
        else:
            return cls.GRAY          # 灰色 - 劣质 (Poor)

    @classmethod
    def get_balance_color(cls, balance: float, currency: str = "USD") -> str:
        """根据余额返回对应的颜色代码

        Args:
            balance: 余额数值
            currency: 货币类型

        Returns:
            对应的颜色代码
        """
        if balance < 0:
            return cls.BALANCE_NEGATIVE  # 负余额 - 红色
        elif currency.upper() in ["CNY", "RMB"]:
            # 人民币阈值
            if balance <= 10:
                return cls.BALANCE_LOW    # 低余额 - 黄色
            else:
                return cls.BALANCE_POSITIVE  # 正常余额 - 绿色
        elif currency.upper() == "POINTS":
            # KFC 点数系统阈值
            if balance <= 50:
                return cls.BALANCE_LOW    # 低点数 - 黄色
            else:
                return cls.BALANCE_POSITIVE  # 正常点数 - 绿色
        else:
            # 美元阈值
            if balance <= 5:
                return cls.BALANCE_LOW    # 低余额 - 黄色
            else:
                return cls.BALANCE_POSITIVE  # 正常余额 - 绿色

    @classmethod
    def format_colored_text(cls, text: str, color: str, reset_color: str = None) -> str:
        """格式化带颜色的文本

        Args:
            text: 文本内容
            color: 颜色代码
            reset_color: 重置颜色代码，默认为RESET

        Returns:
            格式化后的文本
        """
        if reset_color is None:
            reset_color = cls.RESET
        return f"{color}{text}{reset_color}"

    @classmethod
    def strip_ansi_codes(cls, text: str) -> str:
        """移除文本中的ANSI颜色代码

        Args:
            text: 包含颜色代码的文本

        Returns:
            移除颜色代码后的纯文本
        """
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    @classmethod
    def is_color_supported(cls) -> bool:
        """检查当前终端是否支持颜色

        Returns:
            是否支持颜色显示
        """
        import os
        import sys

        # 检查环境变量
        if os.environ.get('NO_COLOR'):
            return False
        if os.environ.get('FORCE_COLOR'):
            return True

        # Claude Code statusLine 环境特殊处理：强制启用颜色
        if os.environ.get('CLAUDE_CODE_STATUS_LINE'):
            return True

        # 检查是否是TTY
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            return True

        # 检查常见的支持颜色的环境变量
        term = os.environ.get('TERM', '').lower()
        if term in ['xterm', 'xterm-256color', 'screen', 'tmux', 'linux']:
            return True

        # 默认启用颜色（特别是在 Claude Code 环境中）
        return True