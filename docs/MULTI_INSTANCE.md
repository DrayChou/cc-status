# 多实例平台配置指南

cc-status 现在支持为同一平台配置多个实例，每个实例可以有不同的名称、API 密钥和设置。

## 📋 功能特性

- ✅ 支持同一平台的多个实例
- ✅ 每个实例有独立的名称和配置
- ✅ 智能平台类型推断
- ✅ 向后兼容现有配置
- ✅ 支持多种命名模式

## 🔧 配置方式

### 方式 1: 使用 platform_type 字段（推荐）

```json
{
  "platforms": {
    "minimaxi": {
      "name": "Minimaxi",
      "platform_type": "minimaxi",
      "auth_token": "token_for_minimaxi",
      "model": "MiniMax-M2",
      "enabled": true
    },
    "minimaxi-user1": {
      "name": "Minimaxi From User1",
      "platform_type": "minimaxi",
      "auth_token": "token_for_user1",
      "model": "MiniMax-M2",
      "enabled": true
    },
    "gaccode": {
      "name": "GAC Code",
      "platform_type": "gaccode",
      "api_key": "key1",
      "enabled": true
    },
    "gaccodeuser1": {
      "name": "GACCode From user1",
      "platform_type": "gaccode",
      "api_key": "key2",
      "enabled": true
    }
  }
}
```

### 方式 2: 智能推断（向后兼容）

如果配置中没有 `platform_type` 字段，cc-status 会自动从实例 ID 推断平台类型：

```json
{
  "platforms": {
    "minimaxi": {
      "name": "Minimaxi",
      "auth_token": "token1",
      "enabled": true
    },
    "minimaxi-user1": {
      "name": "Minimaxi From User1",
      "auth_token": "token2",
      "enabled": true
    }
  }
}
```

支持的命名模式：
- 精确匹配: `minimaxi` → `minimaxi`
- 后缀模式: `minimaxi-user1` → `minimaxi`
- 前缀模式: `gaccodeuser1` → `gaccode`
- 下划线模式: `minimaxi_user1` → `minimaxi`

## 📝 配置示例

### 示例 1: 多个 Minimaxi 实例

```json
{
  "platforms": {
    "minimaxi": {
      "name": "Minimaxi Main",
      "platform_type": "minimaxi",
      "auth_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
      "model": "MiniMax-M2",
      "enabled": true
    },
    "minimaxi-work": {
      "name": "Minimaxi Work Account",
      "platform_type": "minimaxi",
      "auth_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
      "model": "MiniMax-M2",
      "enabled": true
    },
    "minimaxi-personal": {
      "name": "Minimaxi Personal",
      "platform_type": "minimaxi",
      "auth_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
      "model": "MiniMax-M2",
      "enabled": true
    }
  }
}
```

### 示例 2: 多个 GACCode 实例

```json
{
  "platforms": {
    "gaccode": {
      "name": "GAC Code Main",
      "platform_type": "gaccode",
      "api_key": "sk-ant-oat01-...",
      "model": "claude-sonnet-4-5-20250929",
      "enabled": true
    },
    "gaccodeuser1": {
      "name": "GACCode From user1",
      "platform_type": "gaccode",
      "api_key": "sk-ant-oat01-...",
      "model": "claude-sonnet-4-5-20250929",
      "enabled": true
    }
  }
}
```

## 🔍 平台类型列表

支持的平台类型：
- `deepseek` - DeepSeek
- `kimi` - Kimi
- `glm` - GLM (智谱)
- `siliconflow` - SiliconFlow
- `kfc` - Kimi For Coding
- `minimaxi` - Minimaxi
- `gaccode` - GAC Code
- `doubao` - 豆包
- `vanchin` - Vanchin

## 📊 显示效果

配置多个实例后，cc-status 会显示所有启用的平台实例：

```
GLM: 17.28CNY [01-09] | Minimaxi: 600/600 | GAC Code: 100/500 | Minimaxi-work: 300/600
```

每个实例都会独立显示其余额和状态。

## ⚙️ 高级配置

### 别名配置

可以在 `aliases` 中为每个实例添加简短的别名：

```json
{
  "platforms": { ... },
  "aliases": {
    "mm": "minimaxi",
    "mw": "minimaxi-work",
    "mp": "minimaxi-personal",
    "gc": "gaccode",
    "gt": "gaccodeuser1"
  }
}
```

### 默认平台

指定默认使用的平台：

```json
{
  "default_platform": "minimaxi",
  ...
}
```

## 🔄 更新现有配置

如果现有配置没有 `platform_type` 字段，cc-status 会自动推断，无需修改。

如果想要明确指定，可以手动添加 `platform_type` 字段。

## ❓ 常见问题

**Q: 可以配置多少个实例？**
A: 没有限制，可以配置任意数量的实例。

**Q: 不同实例会相互影响吗？**
A: 不会，每个实例都是独立的，有自己的 API 密钥和配置。

**Q: 如何删除某个实例？**
A: 在配置文件中删除对应的条目或将 `enabled` 设为 `false`。

**Q: 实例名称有什么要求？**
A: 必须唯一，推荐使用简短描述性的名称。

**Q: 旧配置还能用吗？**
A: 是的，完全向后兼容。cc-status 会自动推断平台类型。

---

更多帮助请访问：[GitHub Issues](https://github.com/DrayChou/cc-status/issues)
