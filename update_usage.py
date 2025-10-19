#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usage updater - 自动更新使用量统计系统
异步获取和缓存今日使用量数据
"""

import json
import subprocess
import sys
import os
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from cc_status.core.cache import CacheManager
from cc_status.core.config import ConfigManager
from cc_status.utils.logger import get_logger

# 配置参数
CACHE_DIR = Path.home() / ".claude" / "cache"
LOCK_FILE = CACHE_DIR / "update_usage.lock"
COOLDOWN_MINUTES = 30
USAGE_TTL_SECONDS = 3600  # 1小时

# 确保目录存在
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class UsageUpdater:
    """使用量更新器"""

    def __init__(self):
        self.logger = get_logger("usage_updater")
        self.cache_manager = CacheManager()
        self.config_manager = ConfigManager()

    def is_lock_valid(self) -> bool:
        """检查锁文件是否有效"""
        if not LOCK_FILE.exists():
            return False

        try:
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                lock_time = datetime.fromisoformat(f.read().strip())

            # 如果锁文件超过冷却时间，则视为无效
            if datetime.now() - lock_time > timedelta(minutes=COOLDOWN_MINUTES):
                return False

            return True
        except Exception:
            # 锁文件损坏，视为无效
            return False

    def create_lock(self) -> bool:
        """创建锁文件"""
        try:
            with open(LOCK_FILE, "w", encoding="utf-8") as f:
                f.write(datetime.now().isoformat())
            self.logger.debug("Lock file created")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create lock file: {e}")
            return False

    def remove_lock(self) -> bool:
        """移除锁文件"""
        try:
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
                self.logger.debug("Lock file removed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove lock file: {e}")
            return False

    def is_cooldown_active(self) -> bool:
        """检查是否在冷却期内"""
        today_cache_key = f"usage_daily_{datetime.now().strftime('%Y%m%d')}"
        cached_usage = self.cache_manager.get(today_cache_key)

        if cached_usage:
            # 检查缓存时间戳
            cache_file = CACHE_DIR / f"cache_{today_cache_key}.json"
            if cache_file.exists():
                cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
                if cache_age < COOLDOWN_MINUTES * 60:  # 仍在冷却期内
                    self.logger.debug(f"Update skipped due to cooldown (age: {cache_age:.1f}s)")
                    return True

        return False

    def get_usage_from_ccusage(self) -> Optional[Dict[str, Any]]:
        """从ccusage获取使用量数据"""
        try:
            self.logger.info("Fetching usage data from ccusage...")

            # 尝试多种ccusage调用方式
            ccusage_commands = [
                ["ccusage"],
                ["npx", "ccusage"],
                ["python", "-m", "ccusage"]
            ]

            for cmd in ccusage_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=30
                    )

                    if result.returncode == 0:
                        usage_data = self.parse_ccusage_output(result.stdout)
                        if usage_data:
                            self.logger.info(f"Successfully fetched usage via: {' '.join(cmd)}")
                            return usage_data
                    else:
                        self.logger.debug(f"Command failed: {' '.join(cmd)} (code: {result.returncode})")

                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Timeout for command: {' '.join(cmd)}")
                    continue
                except FileNotFoundError:
                    self.logger.debug(f"Command not found: {cmd[0]}")
                    continue
                except Exception as e:
                    self.logger.debug(f"Error running command {' '.join(cmd)}: {e}")
                    continue

            self.logger.warning("All ccusage commands failed")
            return None

        except Exception as e:
            self.logger.error(f"Error getting usage from ccusage: {e}")
            return None

    def parse_ccusage_output(self, output: str) -> Optional[Dict[str, Any]]:
        """解析ccusage输出"""
        try:
            # 尝试解析JSON输出
            if output.strip().startswith('{'):
                return json.loads(output.strip())

            # 尝试从多行输出中提取JSON
            lines = output.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    return json.loads(line)

            # 尝试从关键信息中构建使用量数据
            return self.extract_usage_from_text(output)

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON output: {e}")
            # 尝试从文本中提取
            return self.extract_usage_from_text(output)
        except Exception as e:
            self.logger.error(f"Error parsing ccusage output: {e}")
            return None

    def extract_usage_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本输出中提取使用量信息"""
        try:
            import re

            usage_data = {
                "date": datetime.now().strftime("%Y%m%d"),
                "total_cost": 0.0,
                "requests": 0,
                "platforms": {}
            }

            # 查找成本信息
            cost_patterns = [
                r"total.*cost[:\s]*\$?(\d+\.?\d*)",
                r"cost[:\s]*\$?(\d+\.?\d*)",
                r"total[:\s]*\$?(\d+\.?\d*)",
                r"\$(\d+\.?\d*)"
            ]

            for pattern in cost_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    try:
                        usage_data["total_cost"] = float(matches[0])
                        break
                    except ValueError:
                        continue

            # 查找请求次数
            request_patterns = [
                r"requests?[:\s]*(\d+)",
                r"calls?[:\s]*(\d+)",
                r"api\s+calls?[:\s]*(\d+)"
            ]

            for pattern in request_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    try:
                        usage_data["requests"] = int(matches[0])
                        break
                    except ValueError:
                        continue

            # 查找平台特定信息
            platform_patterns = {
                "deepseek": r"deepseek.*\$?(\d+\.?\d*)",
                "kimi": r"kimi.*\$?(\d+\.?\d*)",
                "glm": r"glm.*\$?(\d+\.?\d*)",
                "siliconflow": r"siliconflow.*\$?(\d+\.?\d*)",
                "gaccode": r"gaccode.*\$?(\d+\.?\d*)"
            }

            for platform, pattern in platform_patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    try:
                        usage_data["platforms"][platform] = {
                            "cost": float(matches[0])
                        }
                    except ValueError:
                        continue

            # 如果提取到了一些信息，返回数据
            if usage_data["total_cost"] > 0 or usage_data["requests"] > 0:
                self.logger.info(f"Extracted usage from text: cost=${usage_data['total_cost']}, requests={usage_data['requests']}")
                return usage_data

            return None

        except Exception as e:
            self.logger.error(f"Error extracting usage from text: {e}")
            return None

    def update_usage_cache(self, usage_data: Dict[str, Any]) -> bool:
        """更新使用量缓存"""
        try:
            today = datetime.now().strftime("%Y%m%d")
            cache_key = f"usage_daily_{today}"

            # 添加时间戳
            usage_data["updated_at"] = datetime.now().isoformat()

            # 更新缓存
            success = self.cache_manager.set(cache_key, usage_data)

            if success:
                self.logger.info(f"Usage cache updated successfully: ${usage_data.get('total_cost', 0):.2f}")
                return True
            else:
                self.logger.error("Failed to update usage cache")
                return False

        except Exception as e:
            self.logger.error(f"Error updating usage cache: {e}")
            return False

    def update_usage(self, force: bool = False) -> bool:
        """主要的使用量更新函数"""
        try:
            self.logger.info("Starting usage update process...")

            # 检查锁文件
            if self.is_lock_valid():
                if not force:
                    self.logger.info("Another update process is running or in cooldown period")
                    return False
                else:
                    self.logger.info("Force update: ignoring lock file")

            # 检查冷却期
            if not force and self.is_cooldown_active():
                self.logger.info("Update skipped due to cooldown period")
                return True

            # 创建锁文件
            if not self.create_lock():
                self.logger.error("Failed to create lock file")
                return False

            try:
                # 获取使用量数据
                usage_data = self.get_usage_from_ccusage()

                if usage_data:
                    # 更新缓存
                    success = self.update_usage_cache(usage_data)

                    if success:
                        self.logger.info(f"Usage update completed: ${usage_data.get('total_cost', 0):.2f}")
                        return True
                    else:
                        self.logger.error("Failed to update usage cache")
                        return False
                else:
                    self.logger.warning("No usage data received from ccusage")
                    return False

            finally:
                # 移除锁文件
                self.remove_lock()

        except Exception as e:
            self.logger.error(f"Error in update_usage: {e}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
            self.remove_lock()
            return False

    def get_cached_usage(self) -> Optional[Dict[str, Any]]:
        """获取缓存的使用量数据"""
        try:
            today = datetime.now().strftime("%Y%m%d")
            cache_key = f"usage_daily_{today}"

            return self.cache_manager.get(cache_key)
        except Exception as e:
            self.logger.error(f"Error getting cached usage: {e}")
            return None


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Usage updater for cc-status")
    parser.add_argument("--force", action="store_true", help="Force update, ignore cooldown and locks")
    parser.add_argument("--get", action="store_true", help="Get cached usage data")
    parser.add_argument("--status", action="store_true", help="Show update status")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode (updates every hour)")

    args = parser.parse_args()

    updater = UsageUpdater()

    if args.get:
        # 获取缓存的使用量
        usage = updater.get_cached_usage()
        if usage:
            print(json.dumps(usage, indent=2, ensure_ascii=False))
        else:
            print("No cached usage data found")
            return 1

    elif args.status:
        # 显示状态
        lock_valid = updater.is_lock_valid()
        cooldown_active = updater.is_cooldown_active()
        cached_usage = updater.get_cached_usage()

        print("Usage Update Status:")
        print(f"  Lock file valid: {'Yes' if lock_valid else 'No'}")
        print(f"  Cooldown active: {'Yes' if cooldown_active else 'No'}")
        print(f"  Cached usage: {'Available' if cached_usage else 'Not available'}")

        if cached_usage:
            print(f"  Total cost: ${cached_usage.get('total_cost', 0):.2f}")
            print(f"  Requests: {cached_usage.get('requests', 0)}")
            print(f"  Updated: {cached_usage.get('updated_at', 'Unknown')}")

    elif args.daemon:
        # 守护进程模式
        print(f"Starting usage update daemon (updates every {COOLDOWN_MINUTES} minutes)...")

        try:
            import time
            while True:
                updater.update_usage()
                time.sleep(COOLDOWN_MINUTES * 60)
        except KeyboardInterrupt:
            print("\nDaemon stopped by user")

    else:
        # 默认：执行一次更新
        success = updater.update_usage(force=args.force)
        if success:
            print("Usage update completed successfully")
            return 0
        else:
            print("Usage update failed")
            return 1


if __name__ == "__main__":
    sys.exit(main())