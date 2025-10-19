#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Validation Tool - 配置验证工具
验证和诊断配置问题
"""

import sys
import json
import argparse
from pathlib import Path

# 添加项目路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from cc_status.core.config import ConfigManager
from cc_status.utils.validator import ConfigValidator
from cc_status.utils.logger import get_logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Configuration validation tool")
    parser.add_argument("--platform", help="Validate specific platform")
    parser.add_argument("--test-connection", action="store_true", help="Test API connectivity")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix common issues")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    logger = get_logger("validate_config")

    try:
        # 加载配置
        config_manager = ConfigManager()
        validator = ConfigValidator()

        print("Loading configuration...")
        full_config = config_manager.get_platforms_config()

        if not full_config:
            print("No configuration found")
            return 1

        # 执行验证
        if args.platform:
            # 验证特定平台
            if args.platform not in full_config:
                print(f"Platform '{args.platform}' not found in configuration")
                return 1

            platform_config = full_config[args.platform]
            if args.test_connection:
                platform_config["test_connection"] = True

            results = validator.validate_platform_config(args.platform, platform_config)
        else:
            # 验证完整配置
            if args.test_connection:
                # 为所有启用的平台添加连接测试
                for platform, config in full_config.items():
                    if config.get("enabled", False):
                        config["test_connection"] = True

            results = validator.validate_full_config(full_config)

        # 生成报告
        report = validator.generate_report(results)

        # 输出结果
        if args.format == "json":
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print_text_report(report)

        # 尝试修复问题
        if args.fix:
            try:
                fixed = attempt_fixes(results, full_config)
                if fixed:
                    print(f"\nAttempted to fix {fixed} issues")
                    print("Please review the changes and run validation again")
            except Exception as e:
                print(f"Error during auto-fix: {e}")

        return 0 if report["is_valid"] else 1

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        print(f"Error: {e}")
        return 1


def print_text_report(report):
    """打印文本格式的报告"""
    summary = report["summary"]

    print(f"\n{'='*50}")
    print("CONFIGURATION VALIDATION REPORT")
    print(f"{'='*50}")

    # 摘要
    print(f"\nSummary:")
    print(f"  Total checks: {summary['total']}")
    if summary['errors'] > 0:
        print(f"  Errors: {summary['errors']}")
    if summary['warnings'] > 0:
        print(f"  Warnings: {summary['warnings']}")
    if summary['info'] > 0:
        print(f"  Info: {summary['info']}")

    # 整体状态
    if report["is_valid"]:
        print(f"\n[OK] Configuration is valid")
    else:
        print(f"\n[FAIL] Configuration has errors that need to be fixed")

    # 详细结果
    if report["results"]:
        print(f"\nDetails:")
        print("-" * 50)

        # 按严重程度分组
        errors = [r for r in report["results"] if r["severity"] == "error"]
        warnings = [r for r in report["results"] if r["severity"] == "warning"]
        info = [r for r in report["results"] if r["severity"] == "info"]

        if errors:
            print("\n[ERRORS]")
            for result in errors:
                print(f"  • {result['field']}: {result['message']}")
                if result.get('suggestion'):
                    print(f"    Suggestion: {result['suggestion']}")

        if warnings:
            print("\n[WARNINGS]")
            for result in warnings:
                print(f"  • {result['field']}: {result['message']}")
                if result.get('suggestion'):
                    print(f"    Suggestion: {result['suggestion']}")

        if info and not args.verbose:
            print(f"\n[INFO] ({len(info)} informational messages)")
            print("  Use --verbose to see details")
        elif info:
            print("\n[INFO]")
            for result in info:
                print(f"  • {result['field']}: {result['message']}")
                if result.get('suggestion'):
                    print(f"    Suggestion: {result['suggestion']}")

    print(f"\n{'='*50}")


def attempt_fixes(results, config):
    """尝试修复常见问题"""
    fixed_count = 0

    for result in results:
        if not result.is_valid and result.suggestion:
            # 这里可以实现一些自动修复逻辑
            # 例如：移除URL末尾的斜杠，标准化字段名等
            pass

    return fixed_count


if __name__ == "__main__":
    sys.exit(main())