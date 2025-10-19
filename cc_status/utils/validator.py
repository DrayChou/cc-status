#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Configuration Validator - 高级配置验证器
提供全面的配置验证、错误检测和修复建议
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
import requests
from pathlib import Path

from .logger import get_logger


class ValidationResult:
    """验证结果类"""

    def __init__(self, is_valid: bool, message: str = "", field: str = "",
                 severity: str = "error", suggestion: str = ""):
        self.is_valid = is_valid
        self.message = message
        self.field = field
        self.severity = severity  # error, warning, info
        self.suggestion = suggestion

    def __str__(self):
        return f"[{self.severity.upper()}] {self.field}: {self.message}"


class ConfigValidator:
    """高级配置验证器"""

    def __init__(self):
        self.logger = get_logger("config_validator")

        # API密钥格式模式
        self.api_key_patterns = {
            "anthropic": r"^sk-ant-api03-[A-Za-z0-9_-]{95}$",
            "openai": r"^sk-[A-Za-z0-9]{48}$",
            "deepseek": r"^sk-[a-zA-Z0-9]{48}$",
            "moonshot": r"^sk-[A-Za-z0-9]{48}$",
            "glm": r"^[a-fA-F0-9]{64}$",
            "siliconflow": r"^sk-[a-zA-Z0-9]{48}$",
            "generic": r"^sk-[A-Za-z0-9_-]{20,}$"
        }

        # URL格式模式
        self.url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        # 模型名称模式
        self.model_patterns = {
            "anthropic": r"^claude-3-[a-z]+-[\d-]+$",
            "openai": r"^gpt-[a-z\d-]+$|^o1-[a-z]+$",
            "deepseek": r"^deepseek-[a-z]+$",
            "moonshot": r"^moonshot-v1-[\d-]+",
            "glm": r"^glm-[a-z\d-]+$",
            "generic": r"^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$"
        }

    def validate_platform_config(self, platform_name: str, config: Dict[str, Any]) -> List[ValidationResult]:
        """验证平台配置"""
        results = []

        try:
            # 基本字段验证
            results.extend(self._validate_basic_fields(platform_name, config))

            # 认证信息验证
            results.extend(self._validate_auth_info(platform_name, config))

            # API端点验证
            results.extend(self._validate_api_endpoint(platform_name, config))

            # 模型配置验证
            results.extend(self._validate_model_config(platform_name, config))

            # 高级配置验证
            results.extend(self._validate_advanced_config(platform_name, config))

            # 连通性测试（可选）
            if config.get("test_connection", False):
                results.extend(self._test_connectivity(platform_name, config))

        except Exception as e:
            self.logger.error(f"Error validating platform config for {platform_name}: {e}")
            results.append(ValidationResult(
                False, f"Validation error: {e}", "general", "error"
            ))

        return results

    def _validate_basic_fields(self, platform_name: str, config: Dict[str, Any]) -> List[ValidationResult]:
        """验证基本字段"""
        results = []

        # 验证平台名称
        if not platform_name or not isinstance(platform_name, str):
            results.append(ValidationResult(
                False, "Platform name is required and must be a string", "platform_name", "error",
                "Set a valid platform name like 'deepseek', 'kimi', etc."
            ))

        # 验证display_name
        display_name = config.get("display_name") or config.get("name")
        if display_name and not isinstance(display_name, str):
            results.append(ValidationResult(
                False, "Display name must be a string", "display_name", "error",
                "Set a valid display name string"
            ))

        # 验证enabled字段
        enabled = config.get("enabled")
        if enabled is not None and not isinstance(enabled, bool):
            results.append(ValidationResult(
                False, "Enabled field must be a boolean", "enabled", "error",
                "Set enabled to true or false"
            ))

        return results

    def _validate_auth_info(self, platform_name: str, config: Dict[str, Any]) -> List[ValidationResult]:
        """验证认证信息"""
        results = []

        # 检查至少有一个认证字段
        auth_fields = ["api_key", "auth_token", "login_token"]
        has_auth = any(config.get(field) for field in auth_fields)

        if not has_auth:
            results.append(ValidationResult(
                False, "No authentication information found", "auth", "error",
                "Set one of: api_key, auth_token, or login_token"
            ))
            return results

        # 验证API密钥格式
        for field in auth_fields:
            value = config.get(field)
            if value:
                key_result = self._validate_api_key(value, platform_name, field)
                results.append(key_result)

        # 检查认证冲突（多个认证字段）
        auth_count = sum(1 for field in auth_fields if config.get(field))
        if auth_count > 1:
            results.append(ValidationResult(
                True, f"Multiple authentication methods found ({auth_count})", "auth", "warning",
                "Consider using only one authentication method to avoid conflicts"
            ))

        return results

    def _validate_api_key(self, api_key: str, platform_name: str, field_name: str) -> ValidationResult:
        """验证API密钥格式"""
        if not isinstance(api_key, str):
            return ValidationResult(
                False, "API key must be a string", field_name, "error",
                "Ensure the API key is a valid string"
            )

        if len(api_key) < 10:
            return ValidationResult(
                False, "API key is too short (minimum 10 characters)", field_name, "error",
                "Check if the API key is complete"
            )

        # 检查常见错误模式
        common_errors = [
            (r"^sk-$", "API key appears to be incomplete"),
            (r"^your-api-key-here$", "Using placeholder API key"),
            (r"^xxx+", "Using placeholder API key"),
            (r"\s+", "API key contains whitespace"),
        ]

        for pattern, message in common_errors:
            if re.search(pattern, api_key):
                return ValidationResult(
                    False, message, field_name, "error",
                    "Replace with a valid API key"
                )

        # 尝试匹配特定平台的API密钥格式
        platform_patterns = {
            "anthropic": "anthropic",
            "deepseek": "deepseek",
            "kimi": "moonshot",
            "moonshot": "moonshot",
            "glm": "glm",
            "siliconflow": "siliconflow"
        }

        pattern_key = platform_patterns.get(platform_name.lower(), "generic")
        if pattern_key in self.api_key_patterns:
            pattern = self.api_key_patterns[pattern_key]
            if not re.match(pattern, api_key):
                return ValidationResult(
                    True, f"API key format may not match expected pattern for {platform_name}",
                    field_name, "warning",
                    f"Verify the API key format for {platform_name}"
                )

        return ValidationResult(True, "API key format appears valid", field_name, "info")

    def _validate_api_endpoint(self, platform_name: str, config: Dict[str, Any]) -> List[ValidationResult]:
        """验证API端点"""
        results = []

        api_base_url = config.get("api_base_url")
        if not api_base_url:
            # API端点是可选的，某些平台使用默认端点
            return results

        if not isinstance(api_base_url, str):
            results.append(ValidationResult(
                False, "API base URL must be a string", "api_base_url", "error",
                "Set a valid URL string"
            ))
            return results

        # 验证URL格式
        if not self.url_pattern.match(api_base_url):
            results.append(ValidationResult(
                False, "Invalid URL format", "api_base_url", "error",
                "Use a valid URL like: https://api.example.com"
            ))
        else:
            # 检查URL协议
            parsed = urlparse(api_base_url)
            if parsed.scheme not in ["http", "https"]:
                results.append(ValidationResult(
                    False, "URL must use http or https protocol", "api_base_url", "error",
                    "Change to http:// or https://"
                ))
            elif parsed.scheme == "http":
                results.append(ValidationResult(
                    True, "Using HTTP instead of HTTPS (less secure)", "api_base_url", "warning",
                    "Consider using HTTPS for better security"
                ))

            # 检查常见的API端点问题
            if api_base_url.endswith("/"):
                results.append(ValidationResult(
                    True, "URL ends with trailing slash", "api_base_url", "info",
                    "Trailing slash is usually fine, but verify with API documentation"
                ))

        return results

    def _validate_model_config(self, platform_name: str, config: Dict[str, Any]) -> List[ValidationResult]:
        """验证模型配置"""
        results = []

        model = config.get("model")
        if model:
            if not isinstance(model, str):
                results.append(ValidationResult(
                    False, "Model name must be a string", "model", "error",
                    "Set a valid model name string"
                ))
            else:
                # 验证模型名称格式
                pattern_key = platform_name.lower()
                if pattern_key in self.model_patterns:
                    pattern = self.model_patterns[pattern_key]
                    if not re.match(pattern, model):
                        results.append(ValidationResult(
                            True, f"Model name format may not match expected pattern for {platform_name}",
                            "model", "warning",
                            f"Verify the model name for {platform_name} (e.g., 'claude-3-sonnet-20240229')"
                        ))

                # 检查常见模型名称错误
                if model.lower() in ["model", "test", "example", "your-model"]:
                    results.append(ValidationResult(
                        False, "Using placeholder model name", "model", "error",
                        "Replace with a valid model name"
                    ))

        # 验证small_model
        small_model = config.get("small_model")
        if small_model and not isinstance(small_model, str):
            results.append(ValidationResult(
                False, "Small model name must be a string", "small_model", "error",
                "Set a valid small model name string"
            ))

        return results

    def _validate_advanced_config(self, platform_name: str, config: Dict[str, Any]) -> List[ValidationResult]:
        """验证高级配置"""
        results = []

        # 验证超时设置
        timeout = config.get("timeout")
        if timeout is not None:
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                results.append(ValidationResult(
                    False, "Timeout must be a positive number", "timeout", "error",
                    "Set timeout to a positive number (e.g., 30)"
                ))
            elif timeout > 300:
                results.append(ValidationResult(
                    True, "Very long timeout may cause performance issues", "timeout", "warning",
                    "Consider reducing timeout to under 300 seconds"
                ))

        # 验证重试设置
        max_retries = config.get("max_retries")
        if max_retries is not None:
            if not isinstance(max_retries, int) or max_retries < 0:
                results.append(ValidationResult(
                    False, "Max retries must be a non-negative integer", "max_retries", "error",
                    "Set max_retries to a non-negative integer"
                ))
            elif max_retries > 5:
                results.append(ValidationResult(
                    True, "High retry count may cause performance issues", "max_retries", "warning",
                    "Consider reducing max_retries to 5 or less"
                ))

        # 验证Claude Code特定配置
        claude_config = config.get("claude_code_config", {})
        if claude_config:
            max_tokens = claude_config.get("max_output_tokens")
            if max_tokens is not None:
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    results.append(ValidationResult(
                        False, "Max output tokens must be a positive integer", "claude_code_config.max_output_tokens", "error",
                        "Set to a positive integer (e.g., 4096)"
                    ))
                elif max_tokens > 200000:
                    results.append(ValidationResult(
                        True, "Very high max tokens may be expensive", "claude_code_config.max_output_tokens", "warning",
                        "Consider reducing max_output_tokens for cost control"
                    ))

        return results

    def _test_connectivity(self, platform_name: str, config: Dict[str, Any]) -> List[ValidationResult]:
        """测试API连通性"""
        results = []

        api_base_url = config.get("api_base_url")
        if not api_base_url:
            results.append(ValidationResult(
                True, "No API base URL configured, skipping connectivity test", "connectivity", "info",
                "Set api_base_url to enable connectivity testing"
            ))
            return results

        # 尝试连接测试
        try:
            # 使用简单的HEAD请求测试连通性
            response = requests.head(
                api_base_url,
                timeout=10,
                allow_redirects=True
            )

            if response.status_code < 400:
                results.append(ValidationResult(
                    True, f"API endpoint is reachable (status: {response.status_code})", "connectivity", "info"
                ))
            else:
                results.append(ValidationResult(
                    False, f"API endpoint returned error status: {response.status_code}", "connectivity", "error",
                    "Check if the API URL is correct and the service is available"
                ))

        except requests.exceptions.Timeout:
            results.append(ValidationResult(
                False, "API endpoint timeout (10s)", "connectivity", "error",
                "Check network connection and API availability"
            ))
        except requests.exceptions.ConnectionError:
            results.append(ValidationResult(
                False, "Cannot connect to API endpoint", "connectivity", "error",
                "Check if the URL is correct and the service is available"
            ))
        except Exception as e:
            results.append(ValidationResult(
                False, f"Connection test failed: {e}", "connectivity", "error",
                "Check network configuration and API availability"
            ))

        return results

    def validate_full_config(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """验证完整配置"""
        all_results = []

        try:
            # 验证 platforms 配置
            platforms = config.get("platforms", {})
            if not isinstance(platforms, dict):
                all_results.append(ValidationResult(
                    False, "Platforms configuration must be a dictionary", "platforms", "error",
                    "Ensure platforms section is properly formatted"
                ))
                return all_results

            if not platforms:
                all_results.append(ValidationResult(
                    True, "No platforms configured", "platforms", "warning",
                    "Add at least one platform configuration"
                ))
                return all_results

            # 验证每个平台
            for platform_name, platform_config in platforms.items():
                if not isinstance(platform_config, dict):
                    all_results.append(ValidationResult(
                        False, f"Platform config for '{platform_name}' must be a dictionary", "platforms", "error"
                    ))
                    continue

                platform_results = self.validate_platform_config(platform_name, platform_config)
                all_results.extend(platform_results)

            # 验证全局配置
            all_results.extend(self._validate_global_config(config))

        except Exception as e:
            self.logger.error(f"Error validating full config: {e}")
            all_results.append(ValidationResult(
                False, f"Configuration validation error: {e}", "general", "error"
            ))

        return all_results

    def _validate_global_config(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """验证全局配置"""
        results = []

        # 验证版本信息
        version = config.get("version")
        if version and not isinstance(version, str):
            results.append(ValidationResult(
                False, "Version must be a string", "version", "error",
                "Set version as a string (e.g., '1.0.0')"
            ))

        return results

    def generate_report(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """生成验证报告"""
        report = {
            "summary": {
                "total": len(results),
                "errors": len([r for r in results if r.severity == "error"]),
                "warnings": len([r for r in results if r.severity == "warning"]),
                "info": len([r for r in results if r.severity == "info"])
            },
            "is_valid": all(r.is_valid for r in results if r.severity == "error"),
            "results": []
        }

        for result in results:
            report["results"].append({
                "field": result.field,
                "severity": result.severity,
                "is_valid": result.is_valid,
                "message": result.message,
                "suggestion": result.suggestion
            })

        return report