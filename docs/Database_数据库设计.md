# 数据库详细设计

**版本**: v1.0  
**日期**: 2024-01-16  
**数据库**: MySQL 8.0+

---

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| **规范化** | 遵循第三范式，减少数据冗余 |
| **可扩展** | 使用 JSON 字段存储可变结构数据 |
| **性能优先** | 合理设计索引，支持分区 |
| **安全存储** | 敏感数据加密存储 |
| **软删除** | 重要数据使用软删除 |

---

## 2. ER 图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ER 关系图                                       │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │    users     │
                              │──────────────│
                              │ id (PK)      │
                              │ username     │
                              │ email        │
                              └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │  workspaces  │ │  api_keys    │ │  ai_providers│
            │──────────────│ │──────────────│ │──────────────│
            │ id (PK)      │ │ id (PK)      │ │ id (PK)      │
            │ user_id (FK) │ │ user_id (FK) │ │ user_id (FK) │
            │ name         │ │ key_hash     │ │ name         │
            └──────┬───────┘ └──────────────┘ └──────────────┘
                   │
      ┌────────────┼────────────┬────────────┐
      │            │            │            │
      ▼            ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ convers- │ │ memories │ │ schedules│ │ token_usage  │
│ ations   │ │          │ │          │ │              │
│──────────│ │──────────│ │──────────│ │──────────────│
│ id (PK)  │ │ id (PK)  │ │ id (PK)  │ │ id (PK)      │
│ ws_id    │ │ ws_id    │ │ ws_id    │ │ ws_id (FK)   │
└────┬─────┘ └──────────┘ └──────────┘ └──────────────┘
     │
     ▼
┌──────────┐
│ messages │
│──────────│
│ id (PK)  │
│ conv_id  │
└──────────┘
```

---

## 3. 表结构详细设计

### 3.1 用户表 (users)

```sql
CREATE TABLE users (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email           VARCHAR(255) UNIQUE COMMENT '邮箱',
    password_hash   VARCHAR(255) COMMENT '密码哈希',
    display_name    VARCHAR(100) COMMENT '显示名称',
    avatar_url      VARCHAR(500) COMMENT '头像URL',
    status          ENUM('active', 'inactive', 'suspended') DEFAULT 'active' COMMENT '状态',
    settings        JSON COMMENT '用户设置',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP NULL COMMENT '软删除时间',
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_status (status),
    INDEX idx_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
```

**settings JSON 结构:**
```json
{
  "theme": "dark",
  "language": "zh-CN",
  "default_model": "gpt-4o",
  "default_role": "general",
  "notifications": {
    "email": true,
    "webhook": false
  }
}
```

---

### 3.2 工作空间表 (workspaces)

```sql
CREATE TABLE workspaces (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '所属用户',
    name            VARCHAR(100) NOT NULL COMMENT '工作空间名称',
    slug            VARCHAR(100) NOT NULL COMMENT 'URL友好标识',
    description     TEXT COMMENT '描述',
    role            VARCHAR(50) DEFAULT 'general' COMMENT '角色',
    local_path      VARCHAR(500) COMMENT '本地路径',
    settings        JSON COMMENT '工作空间设置',
    is_active       BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    last_used_at    TIMESTAMP NULL COMMENT '最后使用时间',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP NULL,
    
    UNIQUE KEY uk_user_slug (user_id, slug),
    INDEX idx_user_id (user_id),
    INDEX idx_role (role),
    INDEX idx_is_active (is_active),
    INDEX idx_last_used_at (last_used_at),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作空间表';
```

**settings JSON 结构:**
```json
{
  "default_model": "gpt-4o",
  "skills": ["developer", "devops"],
  "ai_provider": "openai_proxy",
  "output_dir": "./outputs",
  "memory_enabled": true,
  "auto_save": true
}
```

---

### 3.3 会话表 (conversations)

```sql
CREATE TABLE conversations (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    workspace_id    BIGINT UNSIGNED NOT NULL COMMENT '所属工作空间',
    title           VARCHAR(200) COMMENT '会话标题',
    summary         TEXT COMMENT '会话摘要',
    role            VARCHAR(50) COMMENT '使用的角色',
    model           VARCHAR(100) COMMENT '使用的模型',
    status          ENUM('active', 'archived', 'deleted') DEFAULT 'active',
    message_count   INT UNSIGNED DEFAULT 0 COMMENT '消息数量',
    token_count     INT UNSIGNED DEFAULT 0 COMMENT 'Token总数',
    metadata        JSON COMMENT '元数据',
    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at        TIMESTAMP NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_workspace_id (workspace_id),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at),
    INDEX idx_workspace_status (workspace_id, status),
    
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表';
```

---

### 3.4 消息表 (messages)

```sql
CREATE TABLE messages (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversation_id BIGINT UNSIGNED NOT NULL COMMENT '所属会话',
    role            ENUM('system', 'user', 'assistant', 'tool') NOT NULL COMMENT '角色',
    content         LONGTEXT NOT NULL COMMENT '消息内容',
    content_type    ENUM('text', 'image', 'file', 'mixed') DEFAULT 'text' COMMENT '内容类型',
    
    -- Token 统计
    prompt_tokens   INT UNSIGNED DEFAULT 0 COMMENT '输入Token',
    completion_tokens INT UNSIGNED DEFAULT 0 COMMENT '输出Token',
    
    -- 工具调用
    tool_calls      JSON COMMENT '工具调用列表',
    tool_call_id    VARCHAR(100) COMMENT '工具调用ID (tool角色)',
    
    -- 附件
    attachments     JSON COMMENT '附件列表',
    
    -- 元数据
    model           VARCHAR(100) COMMENT '使用的模型',
    finish_reason   VARCHAR(50) COMMENT '结束原因',
    latency_ms      INT UNSIGNED COMMENT '响应延迟(毫秒)',
    metadata        JSON COMMENT '其他元数据',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_role (role),
    INDEX idx_created_at (created_at),
    INDEX idx_conv_created (conversation_id, created_at),
    
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息表';
```

**tool_calls JSON 结构:**
```json
[
  {
    "id": "call_abc123",
    "type": "function",
    "function": {
      "name": "list_directory",
      "arguments": "{\"path\": \"~/Desktop\"}"
    }
  }
]
```

---

### 3.5 AI 提供商表 (ai_providers)

```sql
CREATE TABLE ai_providers (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED COMMENT '所属用户 (NULL=系统级)',
    name            VARCHAR(100) NOT NULL COMMENT '提供商名称',
    display_name    VARCHAR(100) COMMENT '显示名称',
    provider_type   ENUM('official', 'proxy', 'custom') NOT NULL COMMENT '类型',
    
    -- 连接配置
    base_url        VARCHAR(500) NOT NULL COMMENT 'API基础URL',
    api_key_encrypted VARBINARY(512) COMMENT '加密的API Key',
    
    -- 代理/中转站配置
    proxy_config    JSON COMMENT '代理配置',
    
    -- 负载均衡配置
    load_balance_config JSON COMMENT '负载均衡配置',
    
    -- 故障转移配置
    failover_config JSON COMMENT '故障转移配置',
    
    -- 可用模型
    available_models JSON COMMENT '可用模型列表',
    
    -- 健康检查
    health_status   ENUM('healthy', 'degraded', 'unhealthy', 'unknown') DEFAULT 'unknown',
    last_health_check TIMESTAMP NULL,
    health_check_config JSON COMMENT '健康检查配置',
    
    -- 状态
    is_default      BOOLEAN DEFAULT FALSE COMMENT '是否默认',
    is_enabled      BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    priority        INT DEFAULT 100 COMMENT '优先级 (越小越高)',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_user_name (user_id, name),
    INDEX idx_user_id (user_id),
    INDEX idx_provider_type (provider_type),
    INDEX idx_is_enabled (is_enabled),
    INDEX idx_health_status (health_status),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI提供商表';
```

**proxy_config JSON 结构:**
```json
{
  "upstream_provider": "openai",
  "rate_limit": {
    "requests_per_minute": 100,
    "tokens_per_minute": 100000
  },
  "timeout_seconds": 60,
  "retry": {
    "max_attempts": 3,
    "backoff_multiplier": 2
  }
}
```

**load_balance_config JSON 结构:**
```json
{
  "strategy": "round_robin",
  "endpoints": [
    {"url": "https://api1.example.com", "weight": 2},
    {"url": "https://api2.example.com", "weight": 1}
  ]
}
```

**failover_config JSON 结构:**
```json
{
  "enabled": true,
  "fallback_providers": ["openai_backup", "azure_openai"],
  "trigger_conditions": {
    "error_rate_threshold": 0.5,
    "latency_threshold_ms": 5000
  }
}
```

---

### 3.6 工作空间记忆表 (workspace_memories)

```sql
CREATE TABLE workspace_memories (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    workspace_id    BIGINT UNSIGNED NOT NULL COMMENT '所属工作空间',
    
    -- 记忆内容
    content         TEXT NOT NULL COMMENT '记忆内容',
    memory_type     ENUM('preference', 'rule', 'knowledge', 'context', 'summary') NOT NULL COMMENT '记忆类型',
    
    -- 来源
    source_type     ENUM('user', 'auto', 'conversation') DEFAULT 'user' COMMENT '来源类型',
    source_id       BIGINT UNSIGNED COMMENT '来源ID (如会话ID)',
    
    -- 重要性
    importance      TINYINT UNSIGNED DEFAULT 50 COMMENT '重要性 (0-100)',
    is_pinned       BOOLEAN DEFAULT FALSE COMMENT '是否置顶',
    
    -- 向量嵌入
    embedding_id    VARCHAR(100) COMMENT '向量数据库中的ID',
    
    -- 生命周期
    access_count    INT UNSIGNED DEFAULT 0 COMMENT '访问次数',
    last_accessed_at TIMESTAMP NULL COMMENT '最后访问时间',
    expires_at      TIMESTAMP NULL COMMENT '过期时间',
    
    -- 元数据
    metadata        JSON COMMENT '元数据',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP NULL,
    
    INDEX idx_workspace_id (workspace_id),
    INDEX idx_memory_type (memory_type),
    INDEX idx_is_pinned (is_pinned),
    INDEX idx_importance (importance),
    INDEX idx_expires_at (expires_at),
    INDEX idx_workspace_type (workspace_id, memory_type),
    
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作空间记忆表';
```

---

### 3.7 Token 使用统计表 (token_usage)

```sql
CREATE TABLE token_usage (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    workspace_id    BIGINT UNSIGNED COMMENT '工作空间ID',
    conversation_id BIGINT UNSIGNED COMMENT '会话ID',
    message_id      BIGINT UNSIGNED COMMENT '消息ID',
    
    -- 模型信息
    provider_id     BIGINT UNSIGNED COMMENT 'AI提供商ID',
    model           VARCHAR(100) NOT NULL COMMENT '模型名称',
    
    -- Token 统计
    prompt_tokens   INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '输入Token',
    completion_tokens INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '输出Token',
    total_tokens    INT UNSIGNED GENERATED ALWAYS AS (prompt_tokens + completion_tokens) STORED,
    
    -- 成本计算
    prompt_cost     DECIMAL(10, 6) DEFAULT 0 COMMENT '输入成本 (USD)',
    completion_cost DECIMAL(10, 6) DEFAULT 0 COMMENT '输出成本 (USD)',
    total_cost      DECIMAL(10, 6) GENERATED ALWAYS AS (prompt_cost + completion_cost) STORED,
    
    -- 请求信息
    request_type    ENUM('chat', 'completion', 'embedding', 'image') DEFAULT 'chat',
    latency_ms      INT UNSIGNED COMMENT '响应延迟',
    status          ENUM('success', 'error', 'timeout') DEFAULT 'success',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_workspace_id (workspace_id),
    INDEX idx_provider_id (provider_id),
    INDEX idx_model (model),
    INDEX idx_created_at (created_at),
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_workspace_created (workspace_id, created_at),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL,
    FOREIGN KEY (provider_id) REFERENCES ai_providers(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Token使用统计表';
```

---

### 3.8 Token 日统计表 (token_daily_stats)

```sql
CREATE TABLE token_daily_stats (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    workspace_id    BIGINT UNSIGNED COMMENT '工作空间ID',
    stat_date       DATE NOT NULL COMMENT '统计日期',
    
    -- 模型维度
    model           VARCHAR(100) COMMENT '模型 (NULL=汇总)',
    provider_id     BIGINT UNSIGNED COMMENT '提供商ID (NULL=汇总)',
    
    -- 统计数据
    request_count   INT UNSIGNED DEFAULT 0 COMMENT '请求次数',
    success_count   INT UNSIGNED DEFAULT 0 COMMENT '成功次数',
    error_count     INT UNSIGNED DEFAULT 0 COMMENT '错误次数',
    
    prompt_tokens   BIGINT UNSIGNED DEFAULT 0 COMMENT '输入Token总数',
    completion_tokens BIGINT UNSIGNED DEFAULT 0 COMMENT '输出Token总数',
    total_tokens    BIGINT UNSIGNED DEFAULT 0 COMMENT 'Token总数',
    
    total_cost      DECIMAL(12, 6) DEFAULT 0 COMMENT '总成本 (USD)',
    
    avg_latency_ms  INT UNSIGNED COMMENT '平均延迟',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_daily_stat (user_id, workspace_id, stat_date, model, provider_id),
    INDEX idx_user_date (user_id, stat_date),
    INDEX idx_workspace_date (workspace_id, stat_date),
    INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Token日统计表';
```

---

### 3.9 定时任务表 (scheduled_tasks)

```sql
CREATE TABLE scheduled_tasks (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '所属用户',
    workspace_id    BIGINT UNSIGNED COMMENT '关联工作空间',
    
    name            VARCHAR(100) NOT NULL COMMENT '任务名称',
    description     TEXT COMMENT '任务描述',
    
    -- 调度配置
    schedule_type   ENUM('cron', 'interval', 'once') NOT NULL COMMENT '调度类型',
    cron_expression VARCHAR(100) COMMENT 'Cron表达式',
    interval_seconds INT UNSIGNED COMMENT '间隔秒数',
    scheduled_at    TIMESTAMP COMMENT '一次性执行时间',
    timezone        VARCHAR(50) DEFAULT 'Asia/Shanghai' COMMENT '时区',
    
    -- 任务内容
    task_type       ENUM('chat', 'skill', 'webhook', 'script') NOT NULL COMMENT '任务类型',
    task_config     JSON NOT NULL COMMENT '任务配置',
    
    -- 状态
    status          ENUM('active', 'paused', 'completed', 'failed') DEFAULT 'active',
    
    -- 执行统计
    last_run_at     TIMESTAMP NULL COMMENT '最后执行时间',
    next_run_at     TIMESTAMP NULL COMMENT '下次执行时间',
    run_count       INT UNSIGNED DEFAULT 0 COMMENT '执行次数',
    success_count   INT UNSIGNED DEFAULT 0 COMMENT '成功次数',
    fail_count      INT UNSIGNED DEFAULT 0 COMMENT '失败次数',
    
    -- 重试配置
    max_retries     TINYINT UNSIGNED DEFAULT 3 COMMENT '最大重试次数',
    retry_delay_seconds INT UNSIGNED DEFAULT 60 COMMENT '重试延迟',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP NULL,
    
    INDEX idx_user_id (user_id),
    INDEX idx_workspace_id (workspace_id),
    INDEX idx_status (status),
    INDEX idx_next_run_at (next_run_at),
    INDEX idx_schedule_type (schedule_type),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时任务表';
```

**task_config JSON 结构:**
```json
{
  "type": "chat",
  "prompt": "生成今日工作报告",
  "role": "developer",
  "model": "gpt-4o",
  "output": {
    "type": "file",
    "path": "./reports/daily-{{date}}.md"
  },
  "notify": {
    "email": true,
    "webhook": "https://..."
  }
}
```

---

### 3.10 任务执行日志表 (task_logs)

```sql
CREATE TABLE task_logs (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    task_id         BIGINT UNSIGNED NOT NULL COMMENT '任务ID',
    
    -- 执行信息
    status          ENUM('running', 'success', 'failed', 'cancelled') NOT NULL,
    started_at      TIMESTAMP NOT NULL COMMENT '开始时间',
    ended_at        TIMESTAMP NULL COMMENT '结束时间',
    duration_ms     INT UNSIGNED COMMENT '执行时长(毫秒)',
    
    -- 结果
    result          LONGTEXT COMMENT '执行结果',
    error_message   TEXT COMMENT '错误信息',
    
    -- Token 使用
    tokens_used     INT UNSIGNED DEFAULT 0 COMMENT 'Token使用量',
    cost            DECIMAL(10, 6) DEFAULT 0 COMMENT '成本',
    
    -- 重试信息
    attempt_number  TINYINT UNSIGNED DEFAULT 1 COMMENT '尝试次数',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at),
    INDEX idx_task_status (task_id, status),
    
    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务执行日志表';
```

---

### 3.11 API Key 表 (api_keys)

```sql
CREATE TABLE api_keys (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '所属用户',
    
    name            VARCHAR(100) NOT NULL COMMENT 'Key名称',
    key_prefix      VARCHAR(10) NOT NULL COMMENT 'Key前缀 (用于显示)',
    key_hash        VARCHAR(64) NOT NULL COMMENT 'Key哈希 (SHA-256)',
    
    -- 权限
    permissions     JSON COMMENT '权限列表',
    allowed_ips     JSON COMMENT '允许的IP列表',
    
    -- 限制
    rate_limit      INT UNSIGNED DEFAULT 1000 COMMENT '每分钟请求限制',
    
    -- 状态
    is_active       BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    
    -- 统计
    last_used_at    TIMESTAMP NULL COMMENT '最后使用时间',
    usage_count     BIGINT UNSIGNED DEFAULT 0 COMMENT '使用次数',
    
    -- 有效期
    expires_at      TIMESTAMP NULL COMMENT '过期时间',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_key_hash (key_hash),
    INDEX idx_user_id (user_id),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API Key表';
```

---

### 3.12 知识库表 (knowledge_bases)

```sql
CREATE TABLE knowledge_bases (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '所属用户',
    workspace_id    BIGINT UNSIGNED COMMENT '关联工作空间',
    
    name            VARCHAR(100) NOT NULL COMMENT '知识库名称',
    description     TEXT COMMENT '描述',
    
    -- 来源配置
    source_type     ENUM('file', 'url', 'database', 'api') NOT NULL COMMENT '来源类型',
    source_config   JSON COMMENT '来源配置',
    
    -- 向量配置
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small' COMMENT '嵌入模型',
    chunk_size      INT UNSIGNED DEFAULT 500 COMMENT '分块大小',
    chunk_overlap   INT UNSIGNED DEFAULT 50 COMMENT '分块重叠',
    
    -- 统计
    document_count  INT UNSIGNED DEFAULT 0 COMMENT '文档数量',
    chunk_count     INT UNSIGNED DEFAULT 0 COMMENT '分块数量',
    total_tokens    BIGINT UNSIGNED DEFAULT 0 COMMENT 'Token总数',
    
    -- 同步状态
    sync_status     ENUM('pending', 'syncing', 'synced', 'failed') DEFAULT 'pending',
    last_synced_at  TIMESTAMP NULL COMMENT '最后同步时间',
    
    -- 状态
    is_enabled      BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP NULL,
    
    INDEX idx_user_id (user_id),
    INDEX idx_workspace_id (workspace_id),
    INDEX idx_source_type (source_type),
    INDEX idx_is_enabled (is_enabled),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库表';
```

---

### 3.13 知识文档表 (knowledge_documents)

```sql
CREATE TABLE knowledge_documents (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    knowledge_base_id BIGINT UNSIGNED NOT NULL COMMENT '所属知识库',
    
    title           VARCHAR(255) NOT NULL COMMENT '文档标题',
    source_url      VARCHAR(1000) COMMENT '来源URL',
    file_path       VARCHAR(500) COMMENT '文件路径',
    file_type       VARCHAR(50) COMMENT '文件类型',
    file_size       BIGINT UNSIGNED COMMENT '文件大小(字节)',
    
    -- 内容
    content         LONGTEXT COMMENT '文档内容',
    content_hash    VARCHAR(64) COMMENT '内容哈希 (用于去重)',
    
    -- 处理状态
    process_status  ENUM('pending', 'processing', 'processed', 'failed') DEFAULT 'pending',
    error_message   TEXT COMMENT '错误信息',
    
    -- 分块信息
    chunk_count     INT UNSIGNED DEFAULT 0 COMMENT '分块数量',
    token_count     INT UNSIGNED DEFAULT 0 COMMENT 'Token数量',
    
    -- 元数据
    metadata        JSON COMMENT '元数据',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_knowledge_base_id (knowledge_base_id),
    INDEX idx_process_status (process_status),
    INDEX idx_content_hash (content_hash),
    
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识文档表';
```

---

### 3.14 Webhook 配置表 (webhook_configs)

```sql
CREATE TABLE webhook_configs (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '所属用户',
    workspace_id    BIGINT UNSIGNED COMMENT '关联工作空间',
    
    name            VARCHAR(100) NOT NULL COMMENT '配置名称',
    platform        ENUM('wecom', 'dingtalk', 'feishu', 'slack', 'custom') NOT NULL COMMENT '平台',
    
    -- Webhook 配置
    webhook_url     VARCHAR(500) COMMENT '回调URL (出站)',
    verify_token    VARCHAR(100) COMMENT '验证Token',
    secret          VARBINARY(256) COMMENT '加密密钥',
    
    -- 处理配置
    handler_config  JSON COMMENT '处理器配置',
    
    -- 状态
    is_enabled      BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    
    -- 统计
    last_received_at TIMESTAMP NULL COMMENT '最后接收时间',
    receive_count   BIGINT UNSIGNED DEFAULT 0 COMMENT '接收次数',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_platform (platform),
    INDEX idx_is_enabled (is_enabled),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Webhook配置表';
```

---

### 3.15 MCP 服务器配置表 (mcp_servers)

```sql
CREATE TABLE mcp_servers (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED COMMENT '所属用户 (NULL=系统级)',
    
    name            VARCHAR(100) NOT NULL COMMENT '服务器名称',
    display_name    VARCHAR(100) COMMENT '显示名称',
    description     TEXT COMMENT '描述',
    
    -- 连接配置
    transport       ENUM('stdio', 'sse') NOT NULL COMMENT '传输方式',
    command         VARCHAR(500) COMMENT 'stdio 命令',
    args            JSON COMMENT '命令参数',
    url             VARCHAR(500) COMMENT 'SSE URL',
    env             JSON COMMENT '环境变量 (加密存储)',
    
    -- 来源
    source          ENUM('local', 'npm', 'custom') DEFAULT 'local' COMMENT '安装来源',
    package_name    VARCHAR(200) COMMENT '包名 (如 npm 包)',
    package_version VARCHAR(50) COMMENT '版本',
    
    -- 发现的能力
    tools           JSON COMMENT '提供的工具列表',
    resources       JSON COMMENT '提供的资源列表',
    prompts         JSON COMMENT '提供的提示词列表',
    
    -- 状态
    is_enabled      BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    connection_status ENUM('connected', 'disconnected', 'error', 'unknown') DEFAULT 'unknown',
    last_connected_at TIMESTAMP NULL COMMENT '最后连接时间',
    last_error      TEXT COMMENT '最后错误信息',
    
    -- 统计
    call_count      BIGINT UNSIGNED DEFAULT 0 COMMENT '调用次数',
    error_count     BIGINT UNSIGNED DEFAULT 0 COMMENT '错误次数',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_user_name (user_id, name),
    INDEX idx_user_id (user_id),
    INDEX idx_is_enabled (is_enabled),
    INDEX idx_source (source),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='MCP服务器配置表';
```

**tools JSON 结构:**
```json
[
  {
    "name": "read_file",
    "description": "Read file contents",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": {"type": "string"}
      },
      "required": ["path"]
    }
  }
]
```

---

### 3.16 已安装技能包表 (installed_skills)

```sql
CREATE TABLE installed_skills (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED COMMENT '所属用户 (NULL=系统级)',
    
    name            VARCHAR(100) NOT NULL COMMENT '技能名称',
    display_name    VARCHAR(100) COMMENT '显示名称',
    version         VARCHAR(50) NOT NULL COMMENT '版本',
    description     TEXT COMMENT '描述',
    
    -- 来源
    source          ENUM('builtin', 'official', 'github', 'npm', 'pypi', 'url', 'local') NOT NULL COMMENT '安装来源',
    source_url      VARCHAR(500) COMMENT '来源 URL',
    
    -- 安装信息
    install_path    VARCHAR(500) COMMENT '安装路径',
    
    -- 技能配置
    config          JSON COMMENT '技能配置 (skill.yaml 内容)',
    
    -- 权限
    permissions     JSON COMMENT '授予的权限',
    
    -- 依赖的 MCP 服务器
    mcp_dependencies JSON COMMENT 'MCP 依赖列表',
    
    -- 状态
    is_enabled      BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    is_verified     BOOLEAN DEFAULT FALSE COMMENT '是否经过验证',
    
    -- 统计
    use_count       BIGINT UNSIGNED DEFAULT 0 COMMENT '使用次数',
    last_used_at    TIMESTAMP NULL COMMENT '最后使用时间',
    
    -- 更新
    latest_version  VARCHAR(50) COMMENT '最新可用版本',
    update_available BOOLEAN DEFAULT FALSE COMMENT '是否有更新',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_user_name (user_id, name),
    INDEX idx_user_id (user_id),
    INDEX idx_source (source),
    INDEX idx_is_enabled (is_enabled),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='已安装技能包表';
```

---

### 3.17 技能包仓库源表 (skill_sources)

```sql
CREATE TABLE skill_sources (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED COMMENT '所属用户 (NULL=系统级)',
    
    name            VARCHAR(100) NOT NULL COMMENT '源名称',
    display_name    VARCHAR(100) COMMENT '显示名称',
    url             VARCHAR(500) NOT NULL COMMENT '仓库 URL',
    
    -- 认证
    auth_type       ENUM('none', 'token', 'basic') DEFAULT 'none' COMMENT '认证类型',
    auth_token      VARBINARY(512) COMMENT '加密的认证信息',
    
    -- 状态
    is_enabled      BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    priority        INT DEFAULT 100 COMMENT '优先级 (越小越高)',
    
    -- 健康检查
    last_check_at   TIMESTAMP NULL COMMENT '最后检查时间',
    is_available    BOOLEAN DEFAULT TRUE COMMENT '是否可用',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_user_name (user_id, name),
    INDEX idx_user_id (user_id),
    INDEX idx_is_enabled (is_enabled),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='技能包仓库源表';
```

---

### 3.18 操作审计日志表 (audit_logs)

```sql
CREATE TABLE audit_logs (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED COMMENT '操作用户',
    workspace_id    BIGINT UNSIGNED COMMENT '工作空间',
    
    -- 操作信息
    action          VARCHAR(100) NOT NULL COMMENT '操作类型',
    resource_type   VARCHAR(50) NOT NULL COMMENT '资源类型',
    resource_id     BIGINT UNSIGNED COMMENT '资源ID',
    
    -- 详情
    details         JSON COMMENT '操作详情',
    
    -- 请求信息
    ip_address      VARCHAR(45) COMMENT 'IP地址',
    user_agent      VARCHAR(500) COMMENT 'User Agent',
    request_id      VARCHAR(36) COMMENT '请求ID',
    
    -- 结果
    status          ENUM('success', 'failed') NOT NULL,
    error_message   TEXT COMMENT '错误信息',
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_created_at (created_at),
    INDEX idx_user_action (user_id, action, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作审计日志表'
PARTITION BY RANGE (UNIX_TIMESTAMP(created_at)) (
    PARTITION p202401 VALUES LESS THAN (UNIX_TIMESTAMP('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (UNIX_TIMESTAMP('2024-03-01')),
    PARTITION p202403 VALUES LESS THAN (UNIX_TIMESTAMP('2024-04-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

---

## 4. 索引设计

### 4.1 索引策略

| 场景 | 索引类型 | 说明 |
|------|----------|------|
| 主键查询 | PRIMARY KEY | 自增ID |
| 唯一约束 | UNIQUE KEY | 如 username, email |
| 外键关联 | INDEX | 所有外键字段 |
| 范围查询 | INDEX | 时间字段 |
| 组合查询 | COMPOSITE INDEX | 高频组合查询 |
| 全文搜索 | FULLTEXT | 内容搜索 (可选) |

### 4.2 常用查询优化

```sql
-- 查询用户最近的会话
-- 使用索引: idx_workspace_status, idx_started_at
SELECT * FROM conversations 
WHERE workspace_id = ? AND status = 'active'
ORDER BY started_at DESC 
LIMIT 20;

-- 查询 Token 使用统计
-- 使用索引: idx_user_created
SELECT DATE(created_at) as date, SUM(total_tokens), SUM(total_cost)
FROM token_usage
WHERE user_id = ? AND created_at >= ?
GROUP BY DATE(created_at);

-- 搜索记忆
-- 使用索引: idx_workspace_type
SELECT * FROM workspace_memories
WHERE workspace_id = ? AND memory_type IN ('preference', 'rule')
AND deleted_at IS NULL
ORDER BY is_pinned DESC, importance DESC;
```

---

## 5. 分区策略

### 5.1 按时间分区的表

适用于日志类、统计类数据：

```sql
-- 审计日志表按月分区
ALTER TABLE audit_logs PARTITION BY RANGE (UNIX_TIMESTAMP(created_at)) (
    PARTITION p202401 VALUES LESS THAN (UNIX_TIMESTAMP('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (UNIX_TIMESTAMP('2024-03-01')),
    -- ...
);

-- Token 使用记录按月分区
ALTER TABLE token_usage PARTITION BY RANGE (UNIX_TIMESTAMP(created_at)) (
    PARTITION p202401 VALUES LESS THAN (UNIX_TIMESTAMP('2024-02-01')),
    -- ...
);

-- 消息表按月分区
ALTER TABLE messages PARTITION BY RANGE (UNIX_TIMESTAMP(created_at)) (
    PARTITION p202401 VALUES LESS THAN (UNIX_TIMESTAMP('2024-02-01')),
    -- ...
);
```

### 5.2 分区维护脚本

```sql
-- 创建下个月分区的存储过程
DELIMITER //
CREATE PROCEDURE create_next_month_partition(IN table_name VARCHAR(64))
BEGIN
    DECLARE next_month DATE;
    DECLARE partition_name VARCHAR(20);
    DECLARE boundary_value BIGINT;
    
    SET next_month = DATE_ADD(LAST_DAY(CURDATE()), INTERVAL 1 DAY);
    SET partition_name = CONCAT('p', DATE_FORMAT(next_month, '%Y%m'));
    SET boundary_value = UNIX_TIMESTAMP(DATE_ADD(next_month, INTERVAL 1 MONTH));
    
    SET @sql = CONCAT(
        'ALTER TABLE ', table_name, 
        ' REORGANIZE PARTITION p_future INTO (',
        'PARTITION ', partition_name, ' VALUES LESS THAN (', boundary_value, '),',
        'PARTITION p_future VALUES LESS THAN MAXVALUE)'
    );
    
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //
DELIMITER ;
```

---

## 6. 数据迁移

### 6.1 初始化脚本

```sql
-- 初始化系统用户
INSERT INTO users (id, username, display_name, status) VALUES
(1, 'system', '系统', 'active');

-- 初始化默认 AI 提供商
INSERT INTO ai_providers (user_id, name, display_name, provider_type, base_url, is_default) VALUES
(NULL, 'openai', 'OpenAI', 'official', 'https://api.openai.com/v1', TRUE);

-- 初始化角色配置 (存储在配置表或文件中)
```

### 6.2 版本迁移

使用 Alembic 管理数据库迁移：

```bash
# 创建迁移
alembic revision --autogenerate -m "add_new_table"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

---

## 7. 备份策略

### 7.1 备份计划

| 备份类型 | 频率 | 保留时间 | 说明 |
|----------|------|----------|------|
| 全量备份 | 每天 | 30天 | mysqldump 或 xtrabackup |
| 增量备份 | 每小时 | 7天 | binlog |
| 实时同步 | 实时 | - | 主从复制 |

### 7.2 备份脚本

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/mysql"
DB_NAME="ai_assistant"

# 全量备份
mysqldump --single-transaction --routines --triggers \
    -u backup -p"$MYSQL_BACKUP_PASSWORD" \
    $DB_NAME | gzip > "$BACKUP_DIR/${DB_NAME}_${DATE}.sql.gz"

# 保留最近30天
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

---

## 附录

### A. 常用 SQL 示例

```sql
-- 获取工作空间统计
SELECT 
    w.id,
    w.name,
    COUNT(DISTINCT c.id) as conversation_count,
    COUNT(DISTINCT m.id) as message_count,
    COALESCE(SUM(tu.total_tokens), 0) as total_tokens,
    COALESCE(SUM(tu.total_cost), 0) as total_cost
FROM workspaces w
LEFT JOIN conversations c ON c.workspace_id = w.id
LEFT JOIN messages m ON m.conversation_id = c.id
LEFT JOIN token_usage tu ON tu.workspace_id = w.id
WHERE w.user_id = ?
GROUP BY w.id;

-- 获取模型使用排行
SELECT 
    model,
    COUNT(*) as request_count,
    SUM(total_tokens) as total_tokens,
    SUM(total_cost) as total_cost,
    AVG(latency_ms) as avg_latency
FROM token_usage
WHERE user_id = ? AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY model
ORDER BY total_tokens DESC;
```

### B. 字符集与排序规则

```sql
-- 数据库字符集
CREATE DATABASE ai_assistant
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 表字符集
CREATE TABLE ... 
    ENGINE=InnoDB 
    DEFAULT CHARSET=utf8mb4 
    COLLATE=utf8mb4_unicode_ci;
```

### C. 存储引擎选择

| 表类型 | 存储引擎 | 原因 |
|--------|----------|------|
| 业务表 | InnoDB | 事务支持、行级锁 |
| 日志表 | InnoDB | 支持分区 |
| 缓存表 | MEMORY | 高性能读写 (可选) |
