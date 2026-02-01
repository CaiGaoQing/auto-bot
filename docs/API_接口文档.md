# API 接口文档

**版本**: v1.0  
**日期**: 2024-01-16  
**基础URL**: `http://localhost:8000/api/v1`

---

## 1. 概述

### 1.1 接口规范

| 项目 | 规范 |
|------|------|
| 协议 | HTTPS (生产环境) |
| 格式 | JSON |
| 编码 | UTF-8 |
| 认证 | Bearer Token / API Key |
| 版本 | URL 路径版本化 `/api/v1` |

### 1.2 请求格式

```http
POST /api/v1/chat/completions HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer <token>

{
  "workspace_id": "123",
  "message": "你好"
}
```

### 1.3 响应格式

**成功响应:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    // 响应数据
  },
  "request_id": "req_abc123"
}
```

**错误响应:**
```json
{
  "code": 40001,
  "message": "Invalid request",
  "error": {
    "type": "validation_error",
    "details": [
      {"field": "workspace_id", "message": "required"}
    ]
  },
  "request_id": "req_abc123"
}
```

### 1.4 错误码定义

| 错误码范围 | 说明 |
|------------|------|
| 0 | 成功 |
| 40000-40099 | 请求错误 |
| 40100-40199 | 认证错误 |
| 40300-40399 | 权限错误 |
| 40400-40499 | 资源不存在 |
| 50000-50099 | 服务器错误 |

| 错误码 | 说明 |
|--------|------|
| 40001 | 参数验证失败 |
| 40002 | 参数格式错误 |
| 40101 | 未认证 |
| 40102 | Token 过期 |
| 40103 | Token 无效 |
| 40301 | 无权限 |
| 40401 | 资源不存在 |
| 50001 | 内部错误 |
| 50002 | AI 服务不可用 |

---

## 2. 认证

### 2.1 获取 Token

```http
POST /api/v1/auth/login
```

**请求体:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "refresh_token": "ref_abc123..."
  }
}
```

### 2.2 刷新 Token

```http
POST /api/v1/auth/refresh
```

**请求体:**
```json
{
  "refresh_token": "ref_abc123..."
}
```

### 2.3 API Key 认证

```http
GET /api/v1/workspaces
X-API-Key: sk_live_abc123...
```

---

## 3. 工作空间 API

### 3.1 列出工作空间

```http
GET /api/v1/workspaces
```

**查询参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20 |
| role | string | 否 | 按角色筛选 |
| is_active | bool | 否 | 是否激活 |

**响应:**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "ws_123",
        "name": "my-project",
        "slug": "my-project",
        "role": "developer",
        "description": "开发项目工作空间",
        "local_path": "/Users/user/projects/my-project",
        "is_active": true,
        "last_used_at": "2024-01-16T10:00:00Z",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

### 3.2 创建工作空间

```http
POST /api/v1/workspaces
```

**请求体:**
```json
{
  "name": "new-project",
  "role": "developer",
  "description": "新项目工作空间",
  "local_path": "/Users/user/projects/new-project",
  "settings": {
    "default_model": "gpt-4o",
    "skills": ["developer", "devops"]
  }
}
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "id": "ws_456",
    "name": "new-project",
    "slug": "new-project",
    "role": "developer",
    "local_path": "/Users/user/projects/new-project",
    "created_at": "2024-01-16T10:00:00Z"
  }
}
```

### 3.3 获取工作空间详情

```http
GET /api/v1/workspaces/{workspace_id}
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "id": "ws_123",
    "name": "my-project",
    "slug": "my-project",
    "role": "developer",
    "description": "开发项目工作空间",
    "local_path": "/Users/user/projects/my-project",
    "settings": {
      "default_model": "gpt-4o",
      "skills": ["developer", "devops"],
      "memory_enabled": true
    },
    "stats": {
      "conversation_count": 50,
      "message_count": 1200,
      "token_count": 500000,
      "memory_count": 15
    },
    "is_active": true,
    "last_used_at": "2024-01-16T10:00:00Z",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### 3.4 更新工作空间

```http
PATCH /api/v1/workspaces/{workspace_id}
```

**请求体:**
```json
{
  "name": "updated-name",
  "description": "更新后的描述",
  "settings": {
    "default_model": "claude-3-opus"
  }
}
```

### 3.5 删除工作空间

```http
DELETE /api/v1/workspaces/{workspace_id}
```

**响应:**
```json
{
  "code": 0,
  "message": "Workspace deleted successfully"
}
```

---

## 4. 对话 API

### 4.1 创建对话

```http
POST /api/v1/workspaces/{workspace_id}/conversations
```

**请求体:**
```json
{
  "title": "新对话",
  "role": "developer",
  "model": "gpt-4o"
}
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "id": "conv_789",
    "workspace_id": "ws_123",
    "title": "新对话",
    "role": "developer",
    "model": "gpt-4o",
    "status": "active",
    "created_at": "2024-01-16T10:00:00Z"
  }
}
```

### 4.2 发送消息

```http
POST /api/v1/conversations/{conversation_id}/messages
```

**请求体:**
```json
{
  "content": "帮我写一个 Python 爬虫",
  "attachments": [
    {
      "type": "file",
      "path": "/path/to/file.txt"
    }
  ]
}
```

**响应 (非流式):**
```json
{
  "code": 0,
  "data": {
    "id": "msg_abc",
    "conversation_id": "conv_789",
    "role": "assistant",
    "content": "好的，我来帮你写一个爬虫...\n\n```python\nimport requests\n...\n```",
    "model": "gpt-4o",
    "usage": {
      "prompt_tokens": 50,
      "completion_tokens": 200,
      "total_tokens": 250
    },
    "tool_calls": null,
    "created_at": "2024-01-16T10:00:05Z"
  }
}
```

### 4.3 发送消息 (流式)

```http
POST /api/v1/conversations/{conversation_id}/messages
Content-Type: application/json
Accept: text/event-stream

{
  "content": "帮我写一个 Python 爬虫",
  "stream": true
}
```

**响应 (SSE):**
```
event: message_start
data: {"id": "msg_abc", "role": "assistant"}

event: content_delta
data: {"delta": "好的"}

event: content_delta
data: {"delta": "，我来帮你写一个爬虫"}

event: tool_use
data: {"id": "call_123", "name": "write_file", "input": {"path": "crawler.py", "content": "..."}}

event: message_end
data: {"usage": {"prompt_tokens": 50, "completion_tokens": 200}}

event: done
data: [DONE]
```

### 4.4 列出对话

```http
GET /api/v1/workspaces/{workspace_id}/conversations
```

**查询参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| status | string | 否 | 状态筛选 |

### 4.5 获取对话详情

```http
GET /api/v1/conversations/{conversation_id}
```

### 4.6 获取对话消息

```http
GET /api/v1/conversations/{conversation_id}/messages
```

**查询参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| limit | int | 否 | 返回数量，默认 50 |
| before | string | 否 | 在此消息ID之前 |
| after | string | 否 | 在此消息ID之后 |

### 4.7 删除对话

```http
DELETE /api/v1/conversations/{conversation_id}
```

---

## 5. 记忆 API

### 5.1 列出记忆

```http
GET /api/v1/workspaces/{workspace_id}/memories
```

**查询参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| type | string | 否 | 记忆类型 |
| is_pinned | bool | 否 | 是否置顶 |
| search | string | 否 | 搜索关键词 |

**响应:**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "mem_123",
        "content": "项目使用 Python 3.11，代码风格遵循 PEP8",
        "memory_type": "preference",
        "source_type": "user",
        "importance": 80,
        "is_pinned": true,
        "access_count": 15,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 10
  }
}
```

### 5.2 添加记忆

```http
POST /api/v1/workspaces/{workspace_id}/memories
```

**请求体:**
```json
{
  "content": "新的记忆内容",
  "memory_type": "preference",
  "importance": 70,
  "is_pinned": false
}
```

### 5.3 更新记忆

```http
PATCH /api/v1/memories/{memory_id}
```

**请求体:**
```json
{
  "content": "更新后的内容",
  "importance": 90,
  "is_pinned": true
}
```

### 5.4 删除记忆

```http
DELETE /api/v1/memories/{memory_id}
```

### 5.5 搜索记忆 (语义)

```http
POST /api/v1/workspaces/{workspace_id}/memories/search
```

**请求体:**
```json
{
  "query": "Python 代码规范",
  "limit": 5,
  "types": ["preference", "rule"]
}
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "results": [
      {
        "memory": {
          "id": "mem_123",
          "content": "项目使用 Python 3.11，代码风格遵循 PEP8"
        },
        "score": 0.92
      }
    ]
  }
}
```

---

## 6. 技能 API

### 6.1 列出技能

```http
GET /api/v1/skills
```

**查询参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| category | string | 否 | 分类筛选 |
| installed | bool | 否 | 只显示已安装 |

**响应:**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "name": "developer",
        "display_name": "开发助手",
        "version": "1.0.0",
        "description": "代码生成、审查、调试",
        "category": "developer",
        "is_installed": true,
        "tools_count": 8
      }
    ]
  }
}
```

### 6.2 获取技能详情

```http
GET /api/v1/skills/{skill_name}
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "name": "developer",
    "display_name": "开发助手",
    "version": "1.0.0",
    "description": "代码生成、审查、调试",
    "category": "developer",
    "tools": [
      {
        "name": "write_code",
        "description": "生成代码",
        "dangerous": false,
        "parameters": [
          {
            "name": "language",
            "type": "string",
            "required": true
          }
        ]
      }
    ],
    "permissions": {
      "file_system": {"read": true, "write": true},
      "network": false
    }
  }
}
```

### 6.3 安装技能

```http
POST /api/v1/skills/{skill_name}/install
```

### 6.4 卸载技能

```http
POST /api/v1/skills/{skill_name}/uninstall
```

### 6.5 执行技能工具

```http
POST /api/v1/skills/{skill_name}/tools/{tool_name}/execute
```

**请求体:**
```json
{
  "workspace_id": "ws_123",
  "parameters": {
    "path": "~/Desktop",
    "recursive": false
  },
  "confirm_dangerous": false
}
```

**响应 (需确认):**
```json
{
  "code": 0,
  "data": {
    "status": "pending_confirmation",
    "confirmation_id": "conf_123",
    "message": "即将移动 35 个文件到 ~/Documents，确认执行？",
    "expires_at": "2024-01-16T10:05:00Z"
  }
}
```

**确认执行:**
```http
POST /api/v1/skills/confirmations/{confirmation_id}/confirm
```

---

## 7. AI 提供商 API

### 7.1 列出提供商

```http
GET /api/v1/ai-providers
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "prov_123",
        "name": "openai",
        "display_name": "OpenAI",
        "provider_type": "official",
        "base_url": "https://api.openai.com/v1",
        "health_status": "healthy",
        "is_default": true,
        "is_enabled": true,
        "available_models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
      }
    ]
  }
}
```

### 7.2 添加提供商

```http
POST /api/v1/ai-providers
```

**请求体:**
```json
{
  "name": "openai_proxy",
  "display_name": "OpenAI 代理",
  "provider_type": "proxy",
  "base_url": "https://proxy.example.com/v1",
  "api_key": "sk-xxx",
  "proxy_config": {
    "upstream_provider": "openai",
    "rate_limit": {
      "requests_per_minute": 100
    }
  }
}
```

### 7.3 更新提供商

```http
PATCH /api/v1/ai-providers/{provider_id}
```

### 7.4 删除提供商

```http
DELETE /api/v1/ai-providers/{provider_id}
```

### 7.5 测试提供商

```http
POST /api/v1/ai-providers/{provider_id}/test
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "status": "healthy",
    "latency_ms": 234,
    "models_available": ["gpt-4o", "gpt-4o-mini"]
  }
}
```

### 7.6 设为默认

```http
POST /api/v1/ai-providers/{provider_id}/set-default
```

---

## 8. 统计 API

### 8.1 获取使用统计

```http
GET /api/v1/stats/usage
```

**查询参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| start_date | date | 否 | 开始日期 |
| end_date | date | 否 | 结束日期 |
| workspace_id | string | 否 | 工作空间筛选 |
| group_by | string | 否 | 分组: day, model, workspace |

**响应:**
```json
{
  "code": 0,
  "data": {
    "summary": {
      "total_requests": 1234,
      "total_tokens": 2456789,
      "total_cost": 12.34,
      "avg_latency_ms": 456
    },
    "by_day": [
      {
        "date": "2024-01-16",
        "requests": 100,
        "tokens": 50000,
        "cost": 1.23
      }
    ],
    "by_model": [
      {
        "model": "gpt-4o",
        "requests": 800,
        "tokens": 1800000,
        "cost": 10.00
      }
    ]
  }
}
```

### 8.2 获取成本预估

```http
GET /api/v1/stats/cost-estimate
```

**查询参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| period | string | 否 | 预估周期: week, month |

**响应:**
```json
{
  "code": 0,
  "data": {
    "current_month": {
      "used": 12.34,
      "estimated": 45.00,
      "budget": 100.00,
      "usage_percent": 12.34
    },
    "daily_avg": 1.50,
    "trend": "increasing"
  }
}
```

---

## 9. 定时任务 API

### 9.1 列出任务

```http
GET /api/v1/schedules
```

### 9.2 创建任务

```http
POST /api/v1/schedules
```

**请求体:**
```json
{
  "name": "每日报告",
  "workspace_id": "ws_123",
  "schedule_type": "cron",
  "cron_expression": "0 9 * * *",
  "timezone": "Asia/Shanghai",
  "task_type": "chat",
  "task_config": {
    "prompt": "生成今日工作报告",
    "role": "developer",
    "output": {
      "type": "file",
      "path": "./reports/daily-{{date}}.md"
    }
  }
}
```

### 9.3 更新任务

```http
PATCH /api/v1/schedules/{schedule_id}
```

### 9.4 删除任务

```http
DELETE /api/v1/schedules/{schedule_id}
```

### 9.5 暂停/恢复任务

```http
POST /api/v1/schedules/{schedule_id}/pause
POST /api/v1/schedules/{schedule_id}/resume
```

### 9.6 立即执行

```http
POST /api/v1/schedules/{schedule_id}/run
```

### 9.7 获取执行日志

```http
GET /api/v1/schedules/{schedule_id}/logs
```

---

## 10. Webhook API

### 10.1 接收 Webhook

```http
POST /api/v1/webhooks/{platform}
X-Webhook-Secret: <secret>
```

**支持的平台:**
- `wecom` - 企业微信
- `dingtalk` - 钉钉
- `feishu` - 飞书
- `slack` - Slack
- `custom` - 自定义

### 10.2 配置 Webhook

```http
POST /api/v1/webhook-configs
```

**请求体:**
```json
{
  "name": "企业微信助手",
  "platform": "wecom",
  "workspace_id": "ws_123",
  "verify_token": "token123",
  "secret": "secret456",
  "handler_config": {
    "default_role": "general",
    "allowed_users": ["user1", "user2"]
  }
}
```

---

## 11. WebSocket API

### 11.1 连接

```
ws://localhost:8000/api/v1/ws
```

**连接参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| token | string | 是 | 认证 Token |

### 11.2 消息格式

**客户端发送:**
```json
{
  "type": "chat",
  "conversation_id": "conv_123",
  "content": "你好"
}
```

**服务端响应:**
```json
{
  "type": "message",
  "data": {
    "id": "msg_abc",
    "role": "assistant",
    "content": "你好！有什么我可以帮助你的吗？"
  }
}
```

### 11.3 消息类型

| 类型 | 方向 | 说明 |
|------|------|------|
| `chat` | C→S | 发送聊天消息 |
| `message` | S→C | 接收消息 |
| `typing` | S→C | AI 正在输入 |
| `tool_call` | S→C | 工具调用 |
| `error` | S→C | 错误 |
| `ping` | C→S | 心跳 |
| `pong` | S→C | 心跳响应 |

---

## 12. 健康检查

### 12.1 健康状态

```http
GET /api/v1/health
```

**响应:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "ai_providers": {
      "openai": "healthy",
      "azure": "degraded"
    }
  },
  "uptime_seconds": 86400
}
```

### 12.2 就绪检查

```http
GET /api/v1/ready
```

### 12.3 存活检查

```http
GET /api/v1/live
```

---

## 附录

### A. 速率限制

| 接口 | 限制 |
|------|------|
| 默认 | 1000 请求/分钟 |
| 对话 | 60 请求/分钟 |
| 文件上传 | 10 请求/分钟 |

速率限制响应头:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705401600
```

### B. 分页

所有列表接口支持分页:

```http
GET /api/v1/workspaces?page=1&page_size=20
```

响应包含分页信息:
```json
{
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

### C. 筛选与排序

```http
GET /api/v1/conversations?status=active&sort=-created_at
```

排序:
- `field` - 升序
- `-field` - 降序

### D. 字段选择

```http
GET /api/v1/workspaces?fields=id,name,role
```

### E. SDK 示例

**Python:**
```python
from auto_client import AutoClient

client = AutoClient(
    base_url="http://localhost:8000",
    api_key="sk_xxx"
)

# 创建工作空间
workspace = client.workspaces.create(
    name="my-project",
    role="developer"
)

# 对话
response = client.chat(
    workspace_id=workspace.id,
    message="帮我写一个爬虫"
)
print(response.content)

# 流式对话
for chunk in client.chat_stream(
    workspace_id=workspace.id,
    message="帮我写一个爬虫"
):
    print(chunk.delta, end="")
```

**CLI:**
```bash
# 配置
auto config set api.url http://localhost:8000
auto config set api.key sk_xxx

# 对话
auto chat "帮我写一个爬虫"
```
