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

    def render(self, formatted_status: str, config: dict):
        """
        渲染状态输出

        Args:
            formatted_status: 格式化后的状态字符串
            config: 配置信息
        """
        try:
            if not formatted_status:
                return

            layout = config.get("layout", "single_line")
            auto_wrap = config.get("auto_wrap", True)

            if layout == "multi_line":
                # 多行显示 - 按分隔符分割
                import re
                parts = re.split(r' \| | ⮞ | • ', formatted_status)
                for part in parts:
                    if part.strip():
                        print(part.strip(), flush=True)
            else:
                # 单行显示 - 检查是否需要自动换行
                if auto_wrap:
                    self._render_with_auto_wrap(formatted_status)
                else:
                    self._safe_print(formatted_status, end="")

        except Exception as e:
            self.logger.error(f"Error rendering status: {e}")
            print("Status Error", end="")

    def _render_with_auto_wrap(self, text: str):
        """自动换行渲染

        Args:
            text: 要渲染的文本
        """
        try:
            import shutil
            import re

            # 获取终端宽度
            terminal_width = shutil.get_terminal_size().columns
            # 保留一些边距，避免完全填满
            max_width = min(terminal_width - 5, 200)

            # 检查文本长度
            if len(text) <= max_width:
                # 文本不长，直接显示
                self._safe_print(text, end="")
                return

            # 需要换行 - 按分隔符分割
            separator_pattern = r' \| | ⮞ | • '
            parts = re.split(separator_pattern, text)

            current_line = ""
            lines = []

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                # 如果加上这个部分会超出宽度，且当前行不为空，则换行
                if current_line and len(current_line) + len(part) + 3 > max_width:
                    lines.append(current_line)
                    current_line = part
                else:
                    # 添加到当前行
                    if current_line:
                        # 恢复分隔符
                        if ' ⮞ ' in text:
                            current_line += ' ⮞ ' + part
                        elif ' • ' in text:
                            current_line += ' • ' + part
                        else:
                            current_line += ' | ' + part
                    else:
                        current_line = part

            # 添加最后一行
            if current_line:
                lines.append(current_line)

            # 输出所有行
            for i, line in enumerate(lines):
                if i == len(lines) - 1:
                    # 最后一行不换行
                    self._safe_print(line, end="")
                else:
                    print(line, flush=True)

        except Exception as e:
            self.logger.warning(f"Auto-wrap failed: {e}, falling back to single line")
            self._safe_print(text, end="")

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