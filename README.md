# cc-status

Claude Code 状态栏管理器 - 实时显示API余额、使用量等信息

## ✨ 特性

- 🎯 **多平台支持** - GAC Code、DeepSeek、Kimi、SiliconFlow等
- 📊 **实时监控** - 余额、订阅信息、使用量统计
- 🚀 **智能缓存** - 1秒UI刷新，5分钟余额缓存
- 🎨 **可配置显示** - 自定义布局和显示内容
- 🔧 **零配置启动** - 自动检测运行模式
- 📁 **共享配置** - 与 cc-launcher 共享平台配置

## 📦 安装

```bash
cd scripts/cc-status
pip install -e .
```

## ⚙️ 配置

配置文件位置：`~/.claude/config/platforms.json`

```json
{
  "platforms": {
    "gaccode": {
      "name": "GAC Code",
      "api_base_url": "https://relay05.gaccode.com/claudecode",
      "login_token": "your-token-here",
      "enabled": true
    },
    "deepseek": {
      "name": "DeepSeek",
      "api_base_url": "https://api.deepseek.com/anthropic",
      "api_key": "sk-your-key-here",
      "enabled": true
    },
    "kimi": {
      "name": "Kimi",
      "api_base_url": "https://api.moonshot.cn/anthropic",
      "auth_token": "your-token-here",
      "enabled": true
    },
    "siliconflow": {
      "name": "SiliconFlow",
      "api_base_url": "https://api.siliconflow.cn/",
      "api_key": "sk-your-key-here",
      "enabled": true
    }
  },
  "default_platform": "gaccode"
}
```

## 🚀 使用

### 基础使用

```bash
# 直接显示状态信息
python statusline.py

# 或者作为模块运行
python -m cc_status
```

### Claude Code 集成

在 `~/.claude/settings.json` 中配置：

```json
{
  "statusLine": {
    "type": "command",
    "command": "python ~/.claude/scripts/cc-status/statusline.py",
    "refreshInterval": 1000
  }
}
```

## 📋 显示内容

- **模型信息** - 当前使用的AI模型
- **余额信息** - API账户余额和订阅状态
- **使用量** - 今日使用成本统计
- **会话信息** - 当前会话ID和时长
- **Git信息** - 当前分支和状态
- **时间显示** - 当前时间

## 🎨 自定义配置

在 `~/.claude/config/status.json` 中配置显示选项：

```json
{
  "show_balance": true,
  "show_model": true,
  "show_git_branch": true,
  "show_time": true,
  "show_session_cost": true,
  "show_today_usage": true,
  "layout": "single_line",
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
  }
}
```

## 🔧 故障排除

### 状态栏不显示余额？
1. 检查 `~/.claude/config/platforms.json` 中的API密钥配置
2. 确认网络连接正常
3. 查看日志文件 `~/.claude/logs/cc-status.log`

### 与 cc-launcher 配置冲突？
两个项目共享以下配置文件：
- `~/.claude/config/platforms.json` - 平台配置（共享）
- `~/.claude/config/status.json` - 状态栏配置（仅cc-status使用）
- `~/.claude/config/launcher.json` - 启动器配置（仅cc-launcher使用）

## 🗂️ 项目结构

```
cc-status/
├── statusline.py              # 主入口文件
├── cc_status/                 # Python包
│   ├── __init__.py
│   ├── core/                  # 核心模块
│   │   ├── config.py         # 配置管理
│   │   ├── cache.py          # 缓存系统
│   │   └── detector.py       # 平台检测
│   ├── platforms/             # 平台实现
│   │   ├── __init__.py
│   │   ├── base.py           # 基础平台类
│   │   ├── gaccode.py        # GAC Code平台
│   │   ├── deepseek.py       # DeepSeek平台
│   │   ├── kimi.py           # Kimi平台
│   │   └── siliconflow.py    # SiliconFlow平台
│   ├── display/               # 显示相关
│   │   ├── __init__.py
│   │   ├── formatter.py      # 状态格式化
│   │   └── renderer.py       # 输出渲染
│   └── utils/                 # 工具模块
│       ├── __init__.py
│       ├── logger.py         # 日志工具
│       └── file_lock.py      # 文件锁工具
├── setup.py                   # 安装脚本
└── README.md                  # 说明文档
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License