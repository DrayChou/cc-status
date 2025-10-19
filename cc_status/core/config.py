#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Manager - 共享配置管理器
管理 ~/.claude/config/ 下的配置文件
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ..utils.logger import get_logger


class ConfigManager:
    """配置管理器 - 处理共享配置文件"""

    def __init__(self):
        """初始化配置管理器"""
        self.home_dir = Path.home()
        self.claude_dir = self.home_dir / ".claude"
        self.config_dir = self.claude_dir / "config"
        self.cache_dir = self.claude_dir / "cache"
        self.logs_dir = self.claude_dir / "logs"

        # 确保目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self.logger = get_logger("config")

        # 配置文件路径
        self.platforms_file = self.config_dir / "platforms.json"
        self.status_file = self.config_dir / "status.json"
        self.launcher_file = self.config_dir / "launcher.json"

    def _load_json_file(self, file_path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
        """安全加载JSON文件"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 创建默认配置文件
                self._save_json_file(file_path, default)
                return default.copy()
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"Failed to load {file_path}: {e}")
            return default.copy()

    def _save_json_file(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """安全保存JSON文件"""
        try:
            # 备份现有文件
            if file_path.exists():
                backup_path = file_path.with_suffix('.json.backup')
                file_path.rename(backup_path)

            # 保存新数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"Saved configuration to {file_path}")
            return True
        except IOError as e:
            self.logger.error(f"Failed to save {file_path}: {e}")
            return False

    def get_platforms_config(self) -> Dict[str, Any]:
        """获取平台配置"""
        default_config = {
            "platforms": {
                "gaccode": {
                    "name": "GAC Code",
                    "api_base_url": "https://relay05.gaccode.com/claudecode",
                    "login_token": "",
                    "model": "claude-3-5-sonnet-20241022",
                    "enabled": True
                },
                "deepseek": {
                    "name": "DeepSeek",
                    "api_base_url": "https://api.deepseek.com/anthropic",
                    "api_key": "",
                    "model": "deepseek-chat",
                    "enabled": True
                },
                "kimi": {
                    "name": "Kimi",
                    "api_base_url": "https://api.moonshot.cn/anthropic",
                    "auth_token": "",
                    "model": "moonshot-v1-8k",
                    "enabled": True
                },
                "siliconflow": {
                    "name": "SiliconFlow",
                    "api_base_url": "https://api.siliconflow.cn/",
                    "api_key": "",
                    "model": "deepseek-ai/DeepSeek-V3",
                    "enabled": True
                }
            },
            "default_platform": "gaccode",
            "aliases": {
                "gc": "gaccode",
                "dp": "deepseek",
                "ds": "deepseek",
                "sc": "siliconflow",
                "sf": "siliconflow"
            }
        }

        return self._load_json_file(self.platforms_file, default_config)

    def get_status_config(self) -> Dict[str, Any]:
        """获取状态栏配置"""
        default_config = {
            "show_balance": True,
            "show_model": True,
            "show_git_branch": True,
            "show_time": True,
            "show_session_cost": True,
            "show_today_usage": True,
            "show_directory": True,
            "layout": "single_line",
            "multiplier_config": {
                "enabled": True,
                "periods": [
                    {
                        "name": "peak_hour",
                        "start_time": "16:30",
                        "end_time": "18:30",
                        "multiplier": 5.0,
                        "display_text": "5X",
                        "weekdays_only": True,
                        "color": "red"
                    },
                    {
                        "name": "off_peak",
                        "start_time": "01:00",
                        "end_time": "10:00",
                        "multiplier": 0.8,
                        "display_text": "0.8X",
                        "weekdays_only": False,
                        "color": "green"
                    }
                ]
            },
            "cache_timeout": {
                "balance": 300,  # 5分钟
                "subscription": 3600,  # 1小时
                "usage": 600  # 10分钟
            }
        }

        return self._load_json_file(self.status_file, default_config)

    def get_launcher_config(self) -> Dict[str, Any]:
        """获取启动器配置"""
        default_config = {
            "default_platform": "gaccode",
            "claude_executable": "claude",
            "git_bash_path": "",
            "auto_create_session": True,
            "continue_last_session": False,
            "environment": {
                "clear_existing": True,
                "timeout_seconds": 30
            }
        }

        return self._load_json_file(self.launcher_file, default_config)

    def save_platforms_config(self, config: Dict[str, Any]) -> bool:
        """保存平台配置"""
        return self._save_json_file(self.platforms_file, config)

    def save_status_config(self, config: Dict[str, Any]) -> bool:
        """保存状态栏配置"""
        return self._save_json_file(self.status_file, config)

    def save_launcher_config(self, config: Dict[str, Any]) -> bool:
        """保存启动器配置"""
        return self._save_json_file(self.launcher_file, config)

    def get_platform_config(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """获取特定平台配置"""
        platforms_config = self.get_platforms_config()
        return platforms_config.get("platforms", {}).get(platform_name)

    def update_platform_config(self, platform_name: str, updates: Dict[str, Any]) -> bool:
        """更新特定平台配置"""
        platforms_config = self.get_platforms_config()
        if platform_name in platforms_config.get("platforms", {}):
            platforms_config["platforms"][platform_name].update(updates)
            return self.save_platforms_config(platforms_config)
        return False

    def get_cache_dir(self) -> Path:
        """获取缓存目录"""
        return self.cache_dir

    def get_logs_dir(self) -> Path:
        """获取日志目录"""
        return self.logs_dir