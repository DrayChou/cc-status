#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Status renderer - 渲染状态输出
"""

import os
import sys
from typing import List
from ..utils.logger import get_logger


class StatusRenderer:
    """状态渲染器"""

    def __init__(self):
        self.logger = get_logger("renderer")

    def render(self, formatted_parts: List[str], config: dict):
        """
        渲染状态输出

        Args:
            formatted_parts: 格式化后的状态部分
            config: 配置信息
        """
        try:
            if not formatted_parts:
                return

            layout = config.get("layout", "single_line")

            if layout == "multi_line":
                # 多行显示
                for part in formatted_parts:
                    print(part, flush=True)
            else:
                # 单行显示
                output = " ".join(formatted_parts)
                self._safe_print(output, end="")

        except Exception as e:
            self.logger.error(f"Error rendering status: {e}")
            print("Status Error", end="")

    def _safe_print(self, text: str, end: str = "\n"):
        """安全打印，处理编码问题"""
        try:
            print(text, end=end, flush=True)
        except UnicodeEncodeError:
            # 处理Windows控制台的编码问题
            try:
                # 移除非ASCII字符
                clean_text = text.encode('ascii', 'ignore').decode('ascii')
                print(clean_text, end=end, flush=True)
            except Exception:
                # 最后的兜底方案
                print("Status Display Error", end=end, flush=True)
        except Exception as e:
            self.logger.error(f"Print error: {e}")
            print("Status Error", end=end)