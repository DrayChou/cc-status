#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test API Lock functionality - 测试API锁功能
"""

import sys
import time
import threading
from pathlib import Path

# 添加项目路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from cc_status.utils.api_lock import get_api_lock, LockKeys


def test_basic_lock():
    """测试基本的锁功能"""
    print("Testing basic API lock functionality...")

    api_lock = get_api_lock()
    test_key = "test_lock"

    # 测试获取锁
    if api_lock.acquire_lock(test_key, timeout=5):
        print(f"[OK] Acquired lock: {test_key}")

        # 测试锁状态
        if api_lock.is_locked(test_key):
            print(f"[OK] Lock is active: {test_key}")

        # 测试释放锁
        if api_lock.release_lock(test_key):
            print(f"[OK] Released lock: {test_key}")

        # 测试锁是否已释放
        if not api_lock.is_locked(test_key):
            print(f"[OK] Lock is released: {test_key}")

        return True
    else:
        print(f"[FAIL] Failed to acquire lock: {test_key}")
        return False


def test_concurrent_access():
    """测试并发访问"""
    print("\nTesting concurrent access...")

    api_lock = get_api_lock()
    test_key = "concurrent_test"
    results = []

    def worker(worker_id):
        """工作线程"""
        try:
            start_time = time.time()
            if api_lock.acquire_lock(test_key, timeout=3):
                # 持有锁2秒
                time.sleep(2)
                api_lock.release_lock(test_key)
                end_time = time.time()
                results.append(f"Worker {worker_id}: SUCCESS ({end_time - start_time:.1f}s)")
            else:
                end_time = time.time()
                results.append(f"Worker {worker_id}: TIMEOUT ({end_time - start_time:.1f}s)")
        except Exception as e:
            results.append(f"Worker {worker_id}: ERROR - {e}")

    # 启动3个并发工作线程
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 显示结果
    for result in results:
        print(f"  {result}")

    return len([r for r in results if "SUCCESS" in r]) > 0


def test_context_manager():
    """测试上下文管理器"""
    print("\nTesting context manager...")

    api_lock = get_api_lock()
    test_key = "context_test"

    try:
        with api_lock.lock(test_key, timeout=5):
            if api_lock.is_locked(test_key):
                print(f"[OK] Context manager acquired lock: {test_key}")
                time.sleep(1)  # 模拟工作
                print("[OK] Work completed within lock")
                return True

    except TimeoutError:
        print(f"[FAIL] Context manager timeout: {test_key}")
        return False
    except Exception as e:
        print(f"[FAIL] Context manager error: {e}")
        return False


def test_lock_cleanup():
    """测试锁清理功能"""
    print("\nTesting lock cleanup...")

    api_lock = get_api_lock()

    # 创建一些测试锁
    test_keys = ["cleanup_test_1", "cleanup_test_2"]
    for key in test_keys:
        if api_lock.acquire_lock(key, timeout=1):
            print(f"[OK] Created test lock: {key}")

    # 获取活跃锁数量
    active_locks = api_lock.get_active_locks()
    print(f"[INFO] Active locks before cleanup: {len(active_locks)}")

    # 清理过期锁（这些锁应该很快过期）
    time.sleep(2)  # 等待锁过期
    cleaned_count = api_lock.cleanup_expired_locks()
    print(f"[OK] Cleaned up {cleaned_count} expired locks")

    # 再次检查活跃锁
    active_locks_after = api_lock.get_active_locks()
    print(f"[INFO] Active locks after cleanup: {len(active_locks_after)}")

    return cleaned_count > 0


def main():
    """主函数"""
    print("API Lock Test Suite")
    print("=" * 50)

    tests = [
        ("Basic Lock", test_basic_lock),
        ("Concurrent Access", test_concurrent_access),
        ("Context Manager", test_context_manager),
        ("Lock Cleanup", test_lock_cleanup)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)

        try:
            if test_func():
                passed += 1
                print(f"[PASS] {test_name}")
            else:
                print(f"[FAIL] {test_name}")
        except Exception as e:
            print(f"[ERROR] {test_name}: {e}")

    print(f"\n{'=' * 50}")
    print(f"Test Results: {passed}/{total} passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())