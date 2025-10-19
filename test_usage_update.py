#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test usage update system - 测试使用量更新系统
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from cc_status.core.cache import CacheManager
from cc_status.utils.logger import get_logger

def test_usage_update():
    """测试使用量更新系统"""
    logger = get_logger("test_usage")
    cache_manager = CacheManager()

    # 创建测试使用量数据
    today = datetime.now().strftime("%Y%m%d")
    test_usage_data = {
        "date": today,
        "total_cost": 3.67,
        "requests": 23,
        "platforms": {
            "deepseek": {"cost": 2.10, "requests": 14},
            "kimi": {"cost": 1.57, "requests": 9}
        },
        "updated_at": datetime.now().isoformat()
    }

    # 保存到缓存
    cache_key = f"usage_daily_{today}"
    success = cache_manager.set(cache_key, test_usage_data)

    if success:
        print(f"[OK] Test usage data saved: ${test_usage_data['total_cost']:.2f}")

        # 验证数据可以被读取
        cached_data = cache_manager.get(cache_key)
        if cached_data:
            print(f"[OK] Data verified: ${cached_data['total_cost']:.2f}")
            print(f"   Requests: {cached_data['requests']}")
            print(f"   Platforms: {list(cached_data['platforms'].keys())}")
            return True
        else:
            print("[FAIL] Failed to retrieve cached data")
            return False
    else:
        print("[FAIL] Failed to save test data")
        return False

if __name__ == "__main__":
    success = test_usage_update()
    sys.exit(0 if success else 1)