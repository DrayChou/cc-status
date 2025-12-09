# 平台接口 API 文档

本文档详细说明了 cc-status 支持的各个平台的 API 接口规范和认证方式。

## 📋 目录

- [Kimi 平台](#kimi-平台)
- [KFC (Kimi For Coding) 平台](#kfc-kimi-for-coding-平台)
- [Minimaxi 平台](#minimaxi-平台)
- [DeepSeek 平台](#deepseek-平台)
- [SiliconFlow 平台](#siliconflow-平台)
- [GLM 平台](#glm-平台)
- [GAC Code 平台](#gac-code-平台)

---

## Kimi 平台

### 认证方式

- **Token 类型**: `auth_token` (Bearer)
- **Token 格式**: `sk-` 开头的 API Key

### API 端点

#### 查询余额

```
GET https://api.moonshot.cn/v1/users/me/balance
```

**请求头**:

```http
Authorization: Bearer {auth_token}
Content-Type: application/json
```

**响应示例**:

```json
{
  "code": 0,
  "data": {
    "available_balance": 5.19,
    "voucher_balance": 0,
    "cash_balance": 5.19
  }
}
```

### 配置示例

```json
{
  "kimi": {
    "name": "Kimi",
    "api_base_url": "https://api.moonshot.cn/anthropic",
    "auth_token": "sk-your-kimi-api-key-here",
    "enabled": true
  }
}
```

---

## KFC (Kimi For Coding) 平台

### 认证方式

- **Token 类型**: `auth_token` (Kimi API Key)
- **Token 格式**: `sk-` 开头的 API Key

### API 端点

#### 查询使用量

```
POST https://www.kimi.com/coding/kimi.billing.v1.BillingService/GetUsage
```

**请求头**:

```http
Content-Type: application/json
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36
```

**请求体**:

```json
{
  "credential": {
    "key": "{auth_token}",
    "scope": "FEATURE_CODING"
  }
}
```

**响应示例**:

```json
{
  "usage": {
    "limit": "7168",
    "used": "1453",
    "remaining": "5715",
    "resetTime": "2025-11-22T03:21:23.580297585Z"
  }
}
```

### 配置示例

```json
{
  "kfc": {
    "name": "Kimi For Coding",
    "api_base_url": "https://api.kimi.com/coding/",
    "auth_token": "sk-your-kimi-api-key-here",
    "model": "kimi-for-coding",
    "enabled": true
  }
}
```

---

## Minimaxi 平台

### 认证方式

- **Token 类型**: `auth_token` (Bearer)
- **Token 格式**: JWT token (以 `eyJ` 开头)

### API 端点

#### 查询订阅信息

```
GET https://www.minimaxi.com/v1/api/openplatform/charge/combo/cycle_audio_resource_package
```

**请求头**:

```http
Authorization: Bearer {auth_token}
Content-Type: application/json
accept: application/json, text/plain, */*
origin: https://platform.minimaxi.com
referer: https://platform.minimaxi.com/
```

**响应示例**:

```json
{
  "current_subscribe": {
    "current_subscribe_title": "Pro Plan",
    "current_subscribe_end_time": "12/15/2025"
  }
}
```

#### 查询使用量

```
GET https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains
```

**请求头**:

```http
Authorization: Bearer {auth_token}
Content-Type: application/json
accept: application/json, text/plain, */*
origin: https://platform.minimaxi.com
referer: https://platform.minimaxi.com/
```

**响应示例**:

```json
{
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  },
  "model_remains": [
    {
      "model_name": "MiniMax-M2",
      "current_interval_total_count": 600,
      "current_interval_usage_count": 100,
      "end_time": 1732521600000,
      "remains_time": 86400
    }
  ]
}
```

### 配置示例

```json
{
  "minimaxi": {
    "name": "Minimaxi",
    "api_base_url": "https://api.minimaxi.com/anthropic",
    "auth_token": "eyJ...",
    "model": "MiniMax-M2",
    "enabled": true
  }
}
```

### 注意事项

- Minimaxi 使用 JWT token 作为 auth_token
- 不再需要 `login_token` 和 `group_id`
- 使用量数据包含重置时间和总量限制

---

## DeepSeek 平台

### 认证方式

- **Token 类型**: `api_key` (Bearer)
- **Token 格式**: `sk-` 开头的 API Key

### API 端点

#### 查询余额

```
GET https://api.deepseek.com/user/balance
```

**请求头**:

```http
Authorization: Bearer {api_key}
Content-Type: application/json
```

**响应示例**:

```json
{
  "is_available": true,
  "balance_infos": [
    {
      "currency": "CNY",
      "total_balance": "24.67"
    }
  ]
}
```

### 配置示例

```json
{
  "deepseek": {
    "name": "DeepSeek",
    "api_base_url": "https://api.deepseek.com/anthropic",
    "api_key": "sk-your-deepseek-key-here",
    "enabled": true
  }
}
```

---

## SiliconFlow 平台

### 认证方式

- **Token 类型**: `api_key` (Bearer)
- **Token 格式**: `sk-` 开头的 API Key

### API 端点

#### 查询余额

```
GET https://api.siliconflow.cn/v1/user/info
```

**请求头**:

```http
Authorization: Bearer {api_key}
Content-Type: application/json
```

**响应示例**:

```json
{
  "code": 20000,
  "data": {
    "balance": "24.671",
    "totalBalance": "32.1293"
  }
}
```

### 配置示例

```json
{
  "siliconflow": {
    "name": "SiliconFlow",
    "api_base_url": "https://api.siliconflow.cn/",
    "api_key": "sk-your-siliconflow-key-here",
    "enabled": true
  }
}
```

---

## GLM 平台

### 认证方式

- **Token 类型**: `auth_token` (API Key，优先) 或 `login_token` (JWT，兼容)
- **Token 格式**: API Key (以 `8ef0c8` 开头) 或 JWT token (以 `eyJ` 开头)

### API 端点

#### 查询余额

```
GET https://open.bigmodel.cn/api/biz/account/query-customer-account-report
```

**请求头**:

```http
Authorization: Bearer {auth_token}
Content-Type: application/json
```

**响应示例**:

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "balance": 17.28,
    "availableBalance": 17.28
  },
  "success": true
}
```

#### 查询订阅信息

```
GET https://open.bigmodel.cn/api/biz/subscription/list
```

**请求头**:

```http
Authorization: Bearer {auth_token}
Content-Type: application/json
```

**响应示例**:

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": [
    {
      "status": "VALID",
      "inCurrentPeriod": true,
      "nextRenewTime": "2026-01-09"
    }
  ],
  "success": true
}
```

### 配置示例

```json
{
  "glm": {
    "name": "GLM",
    "api_base_url": "https://open.bigmodel.cn/api/anthropic",
    "auth_token": "8ef0c8...", // 优先使用 API Key
    "model": "glm-4.6",
    "enabled": true
  }
}
```

### 注意事项

- GLM 使用 API Key (`auth_token`) 进行认证
- API Key 使用 Bearer 格式
- 需要同时查询余额和订阅信息

### 备用查询方式 (login_token)

如果使用 `login_token`（网页登录获取的 JWT token），可以使用以下端点：

#### 查询余额

```
GET https://bigmodel.cn/api/biz/account/query-customer-account-report
```

**请求头**:

```http
Authorization: {login_token}  // 不带 Bearer 前缀
Content-Type: application/json
bigmodel-organization: org-0157fc0012064f86B6261289788959ae
bigmodel-project: proj_CE4Eb8359E0842F19c5f497a8A5Dd7b5
```

**配置示例**:

```json
{
  "glm": {
    "name": "GLM",
    "api_base_url": "https://open.bigmodel.cn/api/anthropic",
    "login_token": "eyJ...", // 登录获取的 JWT token
    "model": "glm-4.6",
    "enabled": true
  }
}
```

**注意**: `login_token` 方式需要添加额外的组织 ID 和项目 ID 请求头，配置相对复杂。建议优先使用 `auth_token` (API Key) 方式。

---

## GAC Code 平台

### 认证方式

- **Token 类型**: `login_token` (Bearer)
- **Token 格式**: 平台特定格式

### API 端点

#### 查询余额

```
GET https://relay05.gaccode.com/claudecode/api/balance
```

**请求头**:

```http
Authorization: Bearer {login_token}
Content-Type: application/json
```

**响应示例**:

```json
{
  "balance": 100,
  "limit": 500
}
```

### 配置示例

```json
{
  "gaccode": {
    "name": "GAC Code",
    "api_base_url": "https://relay05.gaccode.com/claudecode",
    "login_token": "your-gac-token-here",
    "enabled": true
  }
}
```

---

## 📝 通用规范

### Token 验证规则

所有平台的 token 必须满足以下条件：

1. 存在且为字符串类型
2. 非空且包含有效内容
3. 去除首尾空格后长度 > 0

### 错误处理

当 API 调用失败时，平台会返回以下状态：

- `NoData` - 没有数据
- `API401` - Token 过期或无效
- `Unavail` - API 服务不可用
- `Error` - 其他错误

### 缓存策略

- **余额数据**: 5 分钟缓存
- **使用量数据**: 1 分钟缓存
- **订阅数据**: 5 分钟缓存

### 并发请求

所有平台的 API 请求使用 `ThreadPoolExecutor` 并发执行，提高响应速度。

---

## 🔄 版本更新记录

### v2.2 (当前版本)

- ✅ **Kimi**: 移除 login_token 支持，统一使用 auth_token
- ✅ **KFC**: 改用 KFC 专用 API，支持 auth_token 直接查询
- ✅ **Minimaxi**: 移除 login_token 和 group_id 依赖，统一使用 auth_token
- ✅ **GLM**: 支持使用 auth_token (API Key) 直接查询余额，同时保持 login_token 向后兼容

### v2.1

- 新增 KFC、Minimaxi、GLM 平台支持
- 优化 Token 验证逻辑

---

## 📞 技术支持

如有问题或建议，请访问：

- GitHub Issues: https://github.com/DrayChou/cc-status/issues
- 相关项目: [cc-launcher](https://github.com/DrayChou/cc-launcher)
