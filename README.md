# cc-status

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

**Claude Code 多平台状态栏管理器** - 专为Claude Code设计的实时状态监控工具，支持同时显示所有已启用API平台的余额信息。

> **🎯 专用设计**: 从原gaccode.com项目分拆出来的独立状态栏组件，专注于提供最佳的多平台余额显示体验。

## ✨ 核心特性

### 🌐 多平台统一显示
- **全平台监控** - 同时显示所有启用平台的余额信息（GAC Code、DeepSeek、Kimi、SiliconFlow、Minimaxi、GLM、KFC）
- **实时更新** - 1秒刷新频率，5分钟余额缓存策略
- **智能检测** - 自动识别已配置的平台并显示相应信息
- **自动过滤** - 未配置有效token的平台自动隐藏，保持状态栏整洁
- **并发获取** - 使用ThreadPoolExecutor并发调用API，提高响应速度

### 📊 智能信息展示
- **余额可视化** - 颜色编码显示余额状态（充足/警告/不足）
- **使用量统计** - 今日使用成本和会话成本追踪
- **倍率显示** - 支持时段倍率配置（如高峰期5倍计费）
- **状态指示** - 订阅状态、API连接状态实时显示

### 🔧 配置共享系统
- **统一配置** - 与cc-launcher共享`~/.claude/config/platforms.json`
- **独立配置** - 状态栏专用配置`~/.claude/config/status.json`
- **自动初始化** - 首次运行时自动创建默认配置文件
- **灵活定制** - 支持显示内容、布局、颜色的全面定制

## 📦 安装与配置

### 前置要求
- Python 3.7+
- Claude Code
- 至少一个支持平台的API密钥

### 快速安装

1. **克隆项目**
```bash
git clone https://github.com/DrayChou/cc-status.git
cd cc-status
```

2. **初始化配置**
```bash
python statusline.py --init-config
```

3. **配置API密钥**
编辑 `~/.claude/config/platforms.json`，添加您的API密钥：
```json
{
  "platforms": {
    "gaccode": {
      "name": "GAC Code",
      "api_base_url": "https://relay05.gaccode.com/claudecode",
      "login_token": "your-gac-token-here",
      "enabled": true
    },
    "deepseek": {
      "name": "DeepSeek",
      "api_base_url": "https://api.deepseek.com/anthropic",
      "api_key": "sk-your-deepseek-key-here",
      "enabled": true
    },
    "kimi": {
      "name": "Kimi",
      "api_base_url": "https://api.moonshot.cn/anthropic",
      "auth_token": "your-kimi-token-here",
      "enabled": true
    },
    "siliconflow": {
      "name": "SiliconFlow",
      "api_base_url": "https://api.siliconflow.cn/",
      "api_key": "sk-your-siliconflow-key-here",
      "enabled": true
    }
  },
  "default_platform": "gaccode"
}
```

### Claude Code 集成

编辑Claude Code配置文件 `~/.claude/settings.json`:
```json
{
  "statusLine": {
    "type": "command",
    "command": "python ~/.claude/scripts/cc-status/statusline.py",
    "refreshInterval": 1000
  }
}
```

### 多平台配置示例

支持的平台类型：
- **GAC Code**: `login_token` (Bearer)
- **DeepSeek**: `api_key` (Bearer)
- **Kimi**: `auth_token` (Bearer)
- **SiliconFlow**: `api_key` (Bearer)
- **Minimaxi**: `login_token` + `group_id` (Bearer + URL参数)
- **GLM**: `login_token` (完整JWT，非Bearer)
- **KFC**: `login_token` 或 `balance_token` (Bearer)

配置示例：
```json
{
  "platforms": {
    "minimaxi": {
      "name": "Minimaxi",
      "api_base_url": "https://api.minimaxi.com/anthropic",
      "login_token": "your-jwt-token-here",
      "group_id": "your-group-id-here",
      "model": "MiniMax-M2",
      "enabled": true
    },
    "glm": {
      "name": "GLM",
      "api_base_url": "https://open.bigmodel.cn/api/anthropic",
      "login_token": "your-jwt-token-here",
      "model": "glm-4.6",
      "enabled": true
    },
    "kfc": {
      "name": "Kimi For Coding",
      "api_base_url": "https://api.kimi.com/coding/",
      "login_token": "your-token-here",
      "model": "kimi-for-coding",
      "enabled": true
    }
  }
}
```

## 🚀 使用方法

### 基础使用

```bash
# 直接运行（测试状态栏显示）
python statusline.py

# 初始化配置文件
python statusline.py --init-config

# 检查配置
python statusline.py --check-config
```

### Claude Code 集成使用

配置完成后，直接启动Claude Code即可在状态栏看到所有平台信息：
```bash
claude
```

状态栏将显示类似信息：
```
Model:Unknown Time:16:33:02 | SiliconFlow:24.67CNY | DeepSeek:-0.32CNY | Kimi:5.19CNY | KFC:4173/7168[11-22 03:21] | Minimaxi:12-15 | GLM:-0.000439CNY Sub:01-09 | Git:main*
```

显示格式说明：
- **余额显示**: `平台名:余额单位`
- **订阅到期**: `平台名:MM-DD`（月-日）
- **使用量显示**: `平台名:剩余/限制[重置时间]`
- **颜色编码**: 🟢 充足 | 🟡 警告 | 🔴 危险 | ⚫ 错误/无数据

未配置有效token的平台会自动隐藏，保持状态栏整洁。

## 🎨 高级配置

### 状态栏显示配置

编辑 `~/.claude/config/status.json` 自定义显示选项：

```json
{
  "display": {
    "show_balance": true,
    "show_model": true,
    "show_git_branch": true,
    "show_time": true,
    "show_session_cost": true,
    "show_today_usage": true,
    "layout": "single_line"
  },
  "multiplier_config": {
    "enabled": true,
    "periods": [
      {
        "name": "peak_hour",
        "start_time": "16:30",
        "end_time": "18:30",
        "multiplier": 5.0,
        "display_text": "5X",
        "weekdays_only": true,
        "color": "red"
      }
    ]
  },
  "cache": {
    "balance_ttl": 300,
    "usage_ttl": 60
  }
}
```

### 显示选项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `show_balance` | 显示账户余额 | `true` |
| `show_model` | 显示AI模型名称 | `true` |
| `show_git_branch` | 显示Git分支 | `true` |
| `show_time` | 显示当前时间 | `true` |
| `show_session_cost` | 显示会话成本 | `true` |
| `show_today_usage` | 显示今日使用量 | `true` |
| `layout` | 布局方式 | `"single_line"` |

### Token 自动过滤

v2.1+ 版本增强：

状态栏会自动跳过未配置有效token的平台，**无需手动禁用平台**，保持界面整洁。

验证规则：
- 检查token字段是否存在
- 验证为字符串类型
- 非空且包含有效内容
- 支持多token类型：`login_token`、`auth_token`、`api_key`、`balance_token`

示例（此配置不会显示minimaxi）：
```json
{
  "minimaxi": {
    "login_token": "",     // 空值，自动隐藏
    "enabled": true       // 仍为true，但因为没有有效token而不显示
  }
}
```

日志中可查看被跳过的平台（DEBUG级别）：
```
Minimaxi login_token not configured, skipping balance query
```

## 🔧 故障排除

### 常见问题

**Q: 状态栏不显示余额信息？**
A: 检查以下几点：
1. 确认 `~/.claude/config/platforms.json` 中的API密钥已正确配置
2. 验证网络连接和API服务可用性
3. 查看日志文件 `~/.claude/logs/cc-status.log` 获取详细错误信息
4. 确认平台 `enabled` 设置为 `true`

**Q: 只显示部分平台信息？**
A: 可能的原因：
1. 部分平台未配置API密钥或 `enabled` 设置为 `false`
2. 网络超时导致某些平台API调用失败
3. 平台API服务暂时不可用

**Q: 配置文件不存在怎么办？**
A: 运行以下命令自动创建默认配置：
```bash
python statusline.py --init-config
```

**Q: 与cc-launcher如何协同工作？**
A: 两个项目配置文件分工：
- `~/.claude/config/platforms.json` - 平台配置（共享）
- `~/.claude/config/status.json` - 状态栏配置（仅cc-status使用）
- `~/.claude/config/launcher.json` - 启动器配置（仅cc-launcher使用）

### 调试模式

启用详细日志输出：
```bash
export CC_STATUS_DEBUG=1
python statusline.py
```

## 🗂️ 项目架构

```
cc-status/
├── statusline.py                  # 主入口文件，CLI接口
├── cc_status/                     # Python包
│   ├── __init__.py
│   ├── core/                      # 核心模块
│   │   ├── config.py             # 配置管理器
│   │   ├── cache.py              # 缓存系统
│   │   └── detector.py           # 平台检测器
│   ├── platforms/                 # 平台实现（支持7+平台）
│   │   ├── __init__.py
│   │   ├── manager.py            # 平台管理器
│   │   ├── base.py               # 基础平台类
│   │   ├── gaccode.py            # GAC Code平台
│   │   ├── deepseek.py           # DeepSeek平台
│   │   ├── kimi.py               # Kimi平台
│   │   ├── siliconflow.py        # SiliconFlow平台
│   │   ├── minimaxi.py           # Minimaxi平台（v2.1新增）
│   │   ├── glm.py                # GLM平台（v2.1新增）
│   │   └── kfc.py                # KFC平台（v2.1新增）
│   ├── display/                   # 显示相关
│   │   ├── __init__.py
│   │   ├── formatter.py          # 状态格式化器
│   │   └── renderer.py           # 输出渲染器
│   └── utils/                     # 工具模块
│       ├── __init__.py
│       ├── logger.py             # 日志工具
│       └── file_lock.py          # 文件锁工具（Windows兼容）
├── tests/                         # 测试文件
├── docs/                          # 文档目录
└── README.md                      # 说明文档
```

## 🔒 安全特性

- **配置保护**: 敏感配置文件自动添加到 `.gitignore`
- **密钥掩码**: 日志输出中自动掩码API密钥（仅显示token长度或前10字符）
- **权限控制**: 配置目录设置为用户可读写
- **输入验证**: 所有配置项经过严格验证（类型、非空、格式检查）
- **Token验证**: v2.1+ 增强token有效性检查，防止无效请求
- **空值过滤**: 未配置有效token的平台自动跳过，不发送API请求

## 🚀 性能优化

- **并发API调用**: 使用 `ThreadPoolExecutor` 同时获取多平台数据
- **智能缓存**: 分层缓存策略（余额5分钟，使用量1分钟）
- **增量更新**: 只更新变化的平台信息
- **异步处理**: 网络请求异步化，避免阻塞UI

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关项目

- **[cc-launcher](https://github.com/DrayChou/cc-launcher)** - Claude Code 多平台启动器
- **[gaccode.com](https://github.com/DrayChou/gaccode-statusline)** - 原始项目（已分拆）

---

> **💡 提示**: cc-status 专注于提供最佳的状态栏体验，如需启动Claude Code的完整解决方案，请配合使用 [cc-launcher](https://github.com/DrayChou/cc-launcher)。