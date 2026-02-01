# AI 个人助手产品需求文档 (PRD)

**版本**: v1.0  
**日期**: 2024-01-16  
**作者**: AI Assistant  
**状态**: 设计阶段

---

## 1. 产品概述

### 1.1 产品定义

AI 个人助手是一个支持 Web 和 CLI 双端交互的智能工作平台，通过集成多种 AI 能力，为不同职业角色（开发、财务、产品、运营等）提供定制化的工作辅助和交付物生成服务。

### 1.2 产品愿景

**让 AI 成为每个人的专属工作助手，提升工作效率 10 倍。**

### 1.3 目标用户

| 用户角色 | 核心痛点 | 解决方案 |
|----------|----------|----------|
| 开发人员 | 写代码效率低、运维操作繁琐 | AI 编码、自动化部署、DevOps 助手 |
| 财务人员 | Excel 处理耗时、报表制作繁琐 | 智能表格处理、自动生成报表 |
| 产品经理 | 需求文档编写耗时 | PRD 生成、需求分析 |
| 项目经理 | 任务拆分、进度管理复杂 | WBS 自动拆分、风险评估 |
| 运营人员 | 多平台内容发布繁琐 | 自动发布、评论回复 |
| 测试人员 | 测试用例编写重复 | 自动化测试、用例生成 |

### 1.4 核心价值

1. **多角色适配** - 根据职业角色提供定制化 AI 能力
2. **统一入口** - Web + CLI 双端，一个平台解决所有需求
3. **知识积累** - 学习公司知识库，越用越懂业务
4. **交付物导向** - 直接输出可用的工作成果（代码、Excel、PPT、文档）
5. **安全可控** - 危险操作确认机制，完整操作日志

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              外部请求源                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │企业微信  │ │  钉钉   │ │  飞书   │ │第三方API│ │定时调度  │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
└───────┼──────────┼──────────┼──────────┼──────────┼──────────────────────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           统一网关层                                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐           │
│  │   API Key 认证   │ │     限流器      │ │    请求路由     │           │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            客户端层                                      │
│  ┌─────────────────────────┐     ┌─────────────────────────┐           │
│  │       Web 前端          │     │       CLI 工具          │           │
│  │   (Next.js + React)     │     │   (Python + Typer)      │           │
│  └─────────────────────────┘     └─────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           后端服务层                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │ FastAPI 服务 │ │ WebSocket   │ │ Celery 队列 │ │  适配器层   │       │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           核心业务层                                     │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ │
│  │工作空间管理│ │ 角色管理  │ │技能包管理 │ │ AI 路由器 │ │任务执行器 │ │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            AI 接口层                                     │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐               │
│  │  OpenAI   │ │ Anthropic │ │   Azure   │ │  Ollama   │               │
│  │  GPT-4o   │ │  Claude   │ │  OpenAI   │ │   本地    │               │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            存储层                                        │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐               │
│  │   MySQL   │ │   Redis   │ │ 向量数据库 │ │ 文件系统  │               │
│  │  配置/日志 │ │ 缓存/队列 │ │ 知识库检索 │ │ 工作空间  │               │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| Web 前端 | Next.js 14 + TailwindCSS | 现代 React 框架，美观 UI |
| CLI 工具 | Python + Typer | 与后端共享代码，类型提示 |
| 后端服务 | Python + FastAPI | AI 生态友好，异步支持 |
| 任务队列 | Celery + Redis | 异步任务处理 |
| 主数据库 | MySQL 8.0 | 配置、日志、用户数据 |
| 向量数据库 | ChromaDB / Milvus | 知识库语义检索 |
| AI 集成 | LiteLLM | 统一多 AI 接口 |
| 容器化 | Docker + Docker Compose | 一键部署 |

---

## 3. 功能模块

### 3.1 功能全景图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI 个人助手功能全景                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        基础平台能力                              │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │    │
│  │  │工作空间   │ │ 角色系统 │ │ AI配置   │ │ 统一网关 │           │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        技能包系统                                │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │                                                                  │    │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐       │    │
│  │  │      办公效率类         │  │       开发运维类        │       │    │
│  │  │  ┌─────┐ ┌─────┐       │  │  ┌─────┐ ┌─────┐       │       │    │
│  │  │  │财务 │ │PPT  │       │  │  │开发 │ │运维 │       │       │    │
│  │  │  └─────┘ └─────┘       │  │  └─────┘ └─────┘       │       │    │
│  │  │  ┌─────┐ ┌─────┐       │  │  ┌─────┐ ┌─────┐       │       │    │
│  │  │  │邮件 │ │日程 │       │  │  │部署 │ │测试 │       │       │    │
│  │  │  └─────┘ └─────┘       │  │  └─────┘ └─────┘       │       │    │
│  │  └─────────────────────────┘  └─────────────────────────┘       │    │
│  │                                                                  │    │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐       │    │
│  │  │      管理协作类         │  │       运营自动化        │       │    │
│  │  │  ┌─────┐ ┌─────┐       │  │  ┌─────┐ ┌─────┐       │       │    │
│  │  │  │产品 │ │项目 │       │  │  │社媒 │ │RPA  │       │       │    │
│  │  │  └─────┘ └─────┘       │  │  └─────┘ └─────┘       │       │    │
│  │  │  ┌─────┐ ┌─────┐       │  │  ┌─────┐ ┌─────┐       │       │    │
│  │  │  │知识库│ │翻译 │       │  │  │搜索 │ │语音 │       │       │    │
│  │  │  └─────┘ └─────┘       │  │  └─────┘ └─────┘       │       │    │
│  │  └─────────────────────────┘  └─────────────────────────┘       │    │
│  │                                                                  │    │
│  │  ┌─────────────────────────┐                                    │    │
│  │  │      通用工具类         │                                    │    │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐                                    │    │
│  │  │  │文件 │ │笔记 │ │提醒 │                                    │    │
│  │  │  └─────┘ └─────┘ └─────┘                                    │    │
│  │  └─────────────────────────┘                                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 技能包详细列表

| 序号 | 技能包 | 核心功能 | 典型场景 | 交付物 |
|------|--------|----------|----------|--------|
| 1 | 财务助手 | Excel处理、数据分析 | 整理工资表、生成报表 | .xlsx |
| 2 | 开发助手 | 代码生成、审查 | 写代码、调试 | .py/.js/... |
| 3 | 产品助手 | PRD生成、需求分析 | 写需求文档 | .md |
| 4 | 项目管理 | WBS拆分、风险评估 | 任务拆分、周报 | .md/.xlsx |
| 5 | 运维助手 | Docker/DB/Redis | 容器管理、数据库操作 | 命令执行 |
| 6 | 部署助手 | 自动部署开源项目 | 一键部署GitHub项目 | docker-compose |
| 7 | 测试助手 | UI/API自动化测试 | 接口测试、页面测试 | 测试报告 |
| 8 | 知识库 | RAG检索增强 | 学习公司文档 | 知识检索 |
| 9 | 社媒运营 | 小红书/抖音/微博 | 发布内容、回复评论 | 帖子发布 |
| 10 | RPA自动化 | 屏幕OCR、按钮识别 | 自动化客服回复 | 自动操作 |
| 11 | PPT制作 | AI生图、内容生成 | 年会总结PPT | .pptx |
| 12 | 邮件助手 | 读取、总结、回复 | 邮件摘要 | 邮件发送 |
| 13 | 网络搜索 | 搜索引擎、网页抓取 | 竞品调研 | 调研报告 |
| 14 | 日程管理 | 日历、提醒 | 会议安排 | 日程同步 |
| 15 | 翻译服务 | 多语言翻译 | 文档翻译 | 翻译结果 |
| 16 | 语音交互 | 语音识别/合成 | 会议转录 | 文字/音频 |
| 17 | 文件管理 | 整理桌面、归档 | 清理桌面 | 文件移动 |
| 18 | 笔记助手 | 快速记录、搜索 | 工作备忘 | .md |
| 19 | **A股调研** | 股票数据、财报分析、行业研究 | 个股分析、板块研究 | 调研报告/.xlsx |

---

## 4. 核心功能详细设计

### 4.1 工作空间管理

#### 4.1.1 功能描述

工作空间是用户工作的基本单元，每个工作空间包含独立的配置、技能包、对话历史和交付物。

#### 4.1.2 工作空间结构

```
workspaces/
└── my-project/
    ├── .auto/                    # 系统配置目录
    │   ├── config.yaml          # 工作空间配置
    │   ├── skills/              # 已安装的技能包
    │   ├── logs/                # 对话日志
    │   │   └── 2024-01-15.jsonl
    │   └── cache/               # 缓存
    ├── outputs/                  # 交付物输出
    │   ├── reports/             # 报告类
    │   ├── code/                # 代码类
    │   └── docs/                # 文档类
    └── files/                    # 用户文件
```

#### 4.1.3 用户故事

| 编号 | 用户故事 | 优先级 |
|------|----------|--------|
| US-1.1 | 作为用户，我可以创建工作空间并指定角色 | P0 |
| US-1.2 | 作为用户，我可以切换不同的工作空间 | P0 |
| US-1.3 | 作为用户，工作空间会自动初始化技能包 | P0 |
| US-1.4 | 作为用户，我的对话历史会按日期保存 | P1 |
| US-1.5 | 作为用户，我可以导出工作空间配置 | P2 |

### 4.2 角色系统

#### 4.2.1 内置角色

| 角色 | 系统提示词 | 默认技能包 | 默认交付物 |
|------|------------|------------|------------|
| developer | 你是一个资深开发工程师... | 开发、运维、测试、部署 | 代码文件 |
| finance | 你是一个专业财务人员... | 财务、Excel处理 | Excel报表 |
| product | 你是一个产品经理... | 产品、知识库 | Markdown文档 |
| project_manager | 你是一个项目经理... | 项目管理、日程 | 任务清单 |
| operations | 你是一个运营专家... | 社媒、RPA、PPT | 内容发布 |
| general | 你是一个通用助手... | 文件、邮件、搜索 | 多种格式 |

#### 4.2.2 用户故事

| 编号 | 用户故事 | 优先级 |
|------|----------|--------|
| US-2.1 | 作为用户，我可以选择预设角色 | P0 |
| US-2.2 | 作为用户，我可以自定义角色提示词 | P1 |
| US-2.3 | 作为用户，角色决定可用的技能包 | P0 |

### 4.3 Token 统计与成本管理

#### 4.3.1 功能描述

实时统计每次 AI 调用的 Token 使用量，计算成本，支持按工作空间、角色、时间维度分析。

#### 4.3.2 统计维度

| 维度 | 说明 |
|------|------|
| 工作空间 | 每个工作空间的独立统计 |
| 模型 | 按 AI 模型分类统计 |
| 技能包 | 按技能包分类统计 |
| 时间 | 日/周/月统计 |

#### 4.3.3 数据库表

```sql
-- Token 使用记录
CREATE TABLE token_usage (
    id INT PRIMARY KEY AUTO_INCREMENT,
    workspace_id INT,
    conversation_id INT,
    model_id INT,
    skill_name VARCHAR(100),
    
    -- Token 统计
    prompt_tokens INT DEFAULT 0,       -- 输入 Token
    completion_tokens INT DEFAULT 0,   -- 输出 Token
    total_tokens INT DEFAULT 0,        -- 总 Token
    
    -- 成本计算
    cost_usd DECIMAL(10, 6),           -- 成本（美元）
    
    -- 时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (model_id) REFERENCES ai_models(id)
);

-- 每日汇总统计
CREATE TABLE token_daily_stats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stat_date DATE NOT NULL,
    workspace_id INT,
    model_id INT,
    
    total_requests INT DEFAULT 0,
    total_prompt_tokens INT DEFAULT 0,
    total_completion_tokens INT DEFAULT 0,
    total_cost_usd DECIMAL(10, 4),
    
    UNIQUE KEY (stat_date, workspace_id, model_id)
);
```

#### 4.3.4 成本计算规则

| 模型 | 输入价格 ($/1K tokens) | 输出价格 ($/1K tokens) |
|------|------------------------|------------------------|
| GPT-4o | $0.005 | $0.015 |
| GPT-4o-mini | $0.00015 | $0.0006 |
| Claude 3.5 Sonnet | $0.003 | $0.015 |
| Claude 3 Opus | $0.015 | $0.075 |

#### 4.3.5 使用场景

```bash
$ auto stats

📊 Token 使用统计 (本月)

┌─────────────────────────────────────────────────────────────┐
│ 总览                                                        │
├─────────────────────────────────────────────────────────────┤
│ 总请求数: 1,234                                             │
│ 总 Token: 2,456,789                                         │
│ 总成本: $12.34                                              │
└─────────────────────────────────────────────────────────────┘

📈 按模型统计:
┌───────────────────┬──────────┬─────────────┬──────────┐
│ 模型              │ 请求数   │ Token       │ 成本     │
├───────────────────┼──────────┼─────────────┼──────────┤
│ GPT-4o            │ 456      │ 1,234,567   │ $8.50    │
│ Claude 3.5 Sonnet │ 678      │ 987,654     │ $3.20    │
│ GPT-4o-mini       │ 100      │ 234,568     │ $0.64    │
└───────────────────┴──────────┴─────────────┴──────────┘

📁 按工作空间统计:
┌───────────────────┬──────────┬──────────┐
│ 工作空间          │ Token    │ 成本     │
├───────────────────┼──────────┼──────────┤
│ my-project        │ 1,500,000│ $7.80    │
│ finance-work      │ 800,000  │ $3.50    │
│ daily-tasks       │ 156,789  │ $1.04    │
└───────────────────┴──────────┴──────────┘

💡 本月预算: $50.00，已使用: 24.7%
```

#### 4.3.6 预算告警

```yaml
# 预算配置
budget:
  monthly_limit_usd: 50.00
  alert_thresholds:
    - 50%   # 达到50%时提醒
    - 80%   # 达到80%时警告
    - 100%  # 达到100%时阻止
  
  # 工作空间独立预算
  workspace_limits:
    my-project: 30.00
    finance-work: 15.00
```

---

### 4.4 工作空间全局记忆

#### 4.4.1 功能描述

全局记忆让 AI 能够跨对话记住工作空间中的重要信息，包括用户偏好、项目背景、常用配置等，使 AI 助手越用越懂你。

#### 4.4.2 记忆类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **用户偏好** | 用户的习惯和偏好 | "用户喜欢简洁的回复风格" |
| **项目背景** | 项目相关的背景知识 | "这是一个电商项目，使用 React + Node.js" |
| **常用配置** | 频繁使用的配置 | "数据库地址是 db.example.com" |
| **业务规则** | 业务相关的规则 | "报表需要符合公司财务模板" |
| **历史总结** | 重要对话的总结 | "上周完成了用户系统重构" |

#### 4.4.3 记忆结构

```sql
-- 工作空间记忆表
CREATE TABLE workspace_memories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    workspace_id INT NOT NULL,
    
    -- 记忆内容
    memory_type ENUM('preference', 'context', 'config', 'rule', 'summary'),
    content TEXT NOT NULL,
    
    -- 元数据
    source VARCHAR(100),              -- 来源：user_input, ai_extract, manual
    importance INT DEFAULT 5,         -- 重要性 1-10
    tags JSON,                        -- 标签
    
    -- 时间管理
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,           -- 最近使用时间
    use_count INT DEFAULT 0,          -- 使用次数
    
    -- 过期管理
    expires_at TIMESTAMP,             -- 过期时间（可选）
    is_pinned BOOLEAN DEFAULT FALSE,  -- 是否置顶（永不过期）
    
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- 记忆向量索引（用于语义检索）
CREATE TABLE memory_embeddings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    memory_id INT NOT NULL,
    embedding BLOB,                    -- 向量数据
    FOREIGN KEY (memory_id) REFERENCES workspace_memories(id)
);
```

#### 4.4.4 记忆工作流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        记忆系统工作流程                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   用户对话                                                               │
│      │                                                                   │
│      ▼                                                                   │
│   ┌──────────────┐                                                      │
│   │  记忆检索    │◄──── 语义匹配相关记忆                                │
│   └──────┬───────┘                                                      │
│          │                                                               │
│          ▼                                                               │
│   ┌──────────────┐                                                      │
│   │  注入上下文  │◄──── 将相关记忆加入 System Prompt                    │
│   └──────┬───────┘                                                      │
│          │                                                               │
│          ▼                                                               │
│   ┌──────────────┐                                                      │
│   │   AI 回复    │                                                      │
│   └──────┬───────┘                                                      │
│          │                                                               │
│          ▼                                                               │
│   ┌──────────────┐                                                      │
│   │  记忆提取    │◄──── AI 自动提取值得记住的信息                       │
│   └──────┬───────┘                                                      │
│          │                                                               │
│          ▼                                                               │
│   ┌──────────────┐                                                      │
│   │  记忆存储    │◄──── 向量化存储，用于后续检索                        │
│   └──────────────┘                                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 4.4.5 使用场景

**场景1: 自动记忆项目背景**

```bash
$ auto chat "这个项目是用 React + TypeScript 开发的电商平台"

✅ 已记住：项目技术栈是 React + TypeScript，类型是电商平台

# 后续对话中，AI 会自动知道这些信息
$ auto chat "帮我写一个商品列表组件"

🧠 使用记忆: 项目使用 React + TypeScript

# AI 直接生成 TypeScript + React 代码，无需再次说明
```

**场景2: 记住用户偏好**

```bash
$ auto chat "以后代码注释用中文"

✅ 已记住：用户偏好中文代码注释

# 后续所有代码生成都会使用中文注释
```

**场景3: 记住业务规则**

```bash
$ auto chat "公司规定：所有 API 必须有日志记录"

✅ 已记住：业务规则 - API 必须有日志记录

# 后续生成 API 代码时会自动加入日志
```

**场景4: 管理记忆**

```bash
$ auto memory list

🧠 工作空间记忆 (my-project)

📌 置顶记忆:
┌────┬─────────────────────────────────────────┬──────────┐
│ ID │ 内容                                    │ 使用次数 │
├────┼─────────────────────────────────────────┼──────────┤
│ 1  │ 技术栈: React + TypeScript + Node.js    │ 45       │
│ 2  │ 数据库: PostgreSQL, 地址 db.example.com │ 23       │
└────┴─────────────────────────────────────────┴──────────┘

👤 用户偏好:
┌────┬─────────────────────────────────────────┬──────────┐
│ 3  │ 代码注释使用中文                        │ 67       │
│ 4  │ 回复风格：简洁专业                      │ 34       │
└────┴─────────────────────────────────────────┴──────────┘

📋 业务规则:
┌────┬─────────────────────────────────────────┬──────────┐
│ 5  │ 所有 API 必须有日志记录                 │ 12       │
│ 6  │ 敏感操作需要二次确认                    │ 8        │
└────┴─────────────────────────────────────────┴──────────┘

$ auto memory add "部署使用 Docker + K8s"
✅ 已添加记忆

$ auto memory delete 6
✅ 已删除记忆 #6

$ auto memory pin 1
✅ 已置顶记忆 #1
```

#### 4.4.6 记忆注入策略

```python
# 记忆注入到 System Prompt 的逻辑
def build_system_prompt(workspace_id: int, user_message: str) -> str:
    # 1. 基础角色提示词
    base_prompt = get_role_prompt(workspace_id)
    
    # 2. 检索相关记忆（语义匹配）
    relevant_memories = search_memories(
        workspace_id=workspace_id,
        query=user_message,
        top_k=10
    )
    
    # 3. 获取置顶记忆
    pinned_memories = get_pinned_memories(workspace_id)
    
    # 4. 构建记忆上下文
    memory_context = format_memories(pinned_memories + relevant_memories)
    
    # 5. 组合最终提示词
    return f"""
{base_prompt}

## 工作空间记忆

以下是关于当前工作空间的重要信息，请在回答时参考：

{memory_context}
"""
```

#### 4.4.7 记忆自动提取

```python
# AI 自动从对话中提取记忆
MEMORY_EXTRACTION_PROMPT = """
分析以下对话，提取值得长期记住的信息：

对话内容：
{conversation}

请提取以下类型的信息（如果有）：
1. 用户偏好（如代码风格、回复格式等）
2. 项目背景（如技术栈、项目类型等）
3. 配置信息（如服务器地址、账号等）
4. 业务规则（如公司规定、流程要求等）

返回 JSON 格式：
[
  {"type": "preference", "content": "...", "importance": 8},
  {"type": "context", "content": "...", "importance": 7}
]

如果没有值得记忆的信息，返回空数组 []
"""
```

#### 4.4.8 记忆生命周期管理

| 策略 | 说明 |
|------|------|
| **自动过期** | 长期未使用的记忆自动降低优先级 |
| **使用增强** | 频繁使用的记忆提高重要性 |
| **冲突处理** | 新记忆与旧记忆冲突时，提示用户确认 |
| **容量限制** | 每个工作空间最多保存 1000 条记忆 |
| **置顶保护** | 置顶记忆永不自动删除 |

---

### 4.5 AI 配置

#### 4.5.1 支持的 AI 提供商

| 提供商 | 类型 | 支持模型 | 用途 |
|--------|------|----------|------|
| OpenAI | 官方 | GPT-4o, GPT-4o-mini | 通用对话、代码生成 |
| Anthropic | 官方 | Claude 3.5 Sonnet, Claude 3 Opus | 长文本、复杂推理 |
| Azure OpenAI | 官方 | GPT-4, GPT-3.5 | 企业合规场景 |
| Ollama | 本地 | Llama3, CodeLlama | 本地部署、隐私场景 |
| DALL-E 3 | 官方 | 图片生成 | PPT配图、图标生成 |
| **中转站/代理** | 代理 | 任意兼容模型 | API代理、多源聚合 |
| **自定义接口** | 自定义 | 自定义模型 | vLLM/LocalAI等 |

#### 4.5.2 中转站配置

支持配置 API 中转站（代理服务），用于：
- 绕过网络限制访问国外 AI 服务
- 使用第三方 API 聚合服务（如 One API、New API）
- 多 API Key 负载均衡
- 自建 API 代理服务（vLLM、LocalAI）

**数据库表设计：**

```sql
-- AI 提供商配置（支持中转站）
CREATE TABLE ai_providers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    provider_type ENUM('official', 'proxy', 'custom') DEFAULT 'official',
    
    -- API 配置
    api_key VARCHAR(500),              -- 加密存储
    api_base_url VARCHAR(255),         -- 官方或中转站地址
    api_version VARCHAR(20),           -- API 版本（如 Azure）
    
    -- 中转站特有配置
    proxy_config JSON,
    /*
    {
      "original_provider": "openai",   -- 原始提供商
      "custom_headers": {},            -- 自定义请求头
      "request_format": "openai",      -- 请求格式兼容
      "timeout": 60,                   -- 超时时间
      "retry_times": 3                 -- 重试次数
    }
    */
    
    -- 负载均衡配置
    load_balance_config JSON,
    /*
    {
      "strategy": "round_robin",       -- round_robin / random / weighted
      "endpoints": [
        {"url": "https://api1.proxy.com", "api_key": "sk-1", "weight": 1},
        {"url": "https://api2.proxy.com", "api_key": "sk-2", "weight": 2}
      ]
    }
    */
    
    -- 故障转移
    failover_config JSON,
    /*
    {
      "enabled": true,
      "fallback_providers": ["claude_proxy", "local_ollama"],
      "failure_threshold": 3
    }
    */
    
    -- 状态
    is_enabled BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0,
    is_healthy BOOLEAN DEFAULT TRUE,
    last_health_check TIMESTAMP
);
```

**常见中转站配置示例：**

```yaml
# 1. OpenAI 中转站
- name: openai_proxy
  display_name: "OpenAI 中转站"
  provider_type: proxy
  api_base_url: "https://api.openai-proxy.com/v1"
  api_key: "sk-xxx"
  proxy_config:
    original_provider: openai

# 2. One API / New API 聚合服务
- name: one_api
  display_name: "One API"
  provider_type: proxy
  api_base_url: "https://your-oneapi.com/v1"
  api_key: "sk-oneapi-xxx"
  proxy_config:
    original_provider: openai

# 3. 多端点负载均衡
- name: openai_lb
  display_name: "OpenAI 负载均衡"
  provider_type: proxy
  load_balance_config:
    strategy: round_robin
    endpoints:
      - url: "https://api1.proxy.com/v1"
        api_key: "sk-key1"
        weight: 1
      - url: "https://api2.proxy.com/v1"
        api_key: "sk-key2"
        weight: 2

# 4. 自建 vLLM / LocalAI
- name: local_vllm
  display_name: "本地 vLLM"
  provider_type: custom
  api_base_url: "http://localhost:8000/v1"
  proxy_config:
    request_format: openai
    timeout: 120

# 5. Claude 中转站
- name: claude_proxy
  display_name: "Claude 中转站"
  provider_type: proxy
  api_base_url: "https://claude-proxy.com"
  api_key: "sk-ant-xxx"
  proxy_config:
    original_provider: anthropic
```

**CLI 配置命令：**

```bash
# 添加中转站
auto config provider add \
  --name "openai_proxy" \
  --type proxy \
  --base-url "https://api.proxy.com/v1" \
  --api-key "sk-xxx"

# 查看提供商列表
auto config provider list

📋 AI 提供商配置：
┌─────────────────┬──────────┬─────────────────────────────┬────────┐
│ 名称            │ 类型     │ API 地址                    │ 状态   │
├─────────────────┼──────────┼─────────────────────────────┼────────┤
│ openai          │ official │ https://api.openai.com      │ 🟢正常 │
│ openai_proxy    │ proxy    │ https://api.proxy.com/v1    │ 🟢正常 │
│ one_api         │ proxy    │ https://your-oneapi.com/v1  │ 🟢正常 │
│ local_vllm      │ custom   │ http://localhost:8000/v1    │ 🟢正常 │
└─────────────────┴──────────┴─────────────────────────────┴────────┘

# 测试连接
auto config provider test openai_proxy

🔍 测试连接: openai_proxy
   响应时间: 245ms
   ✅ 连接成功！

# 设置默认
auto config set ai.default_provider openai_proxy
```

**自动故障转移：**

当主提供商不可用时，自动切换到备用：

```
主提供商失败 → 检测连续失败次数 → 超过阈值 → 切换到备用提供商
                                    ↓
                              定期健康检查
                                    ↓
                              主提供商恢复 → 自动切回
```

#### 4.5.3 配置存储

所有 AI 配置存储在 MySQL 数据库中，API Key 使用 AES-256 加密存储。

### 4.6 统一网关

#### 4.6.1 功能描述

统一网关是所有外部请求的入口，负责认证、限流、路由分发。

#### 4.6.2 支持的接入方式

| 接入方式 | 端点 | 说明 |
|----------|------|------|
| Web 前端 | /api/* | 网页端请求 |
| CLI 工具 | /api/* | 命令行请求 |
| 企业微信 | /gateway/webhook/wecom | Webhook 回调 |
| 钉钉 | /gateway/webhook/dingtalk | Webhook 回调 |
| 飞书 | /gateway/webhook/feishu | Webhook 回调 |
| MCP 协议 | /gateway/mcp | AI 工具调用 |
| 定时任务 | 内部调度 | Cron 触发 |

#### 4.4.3 认证方式

- **API Key 认证**: 适用于 CLI、第三方调用
- **Session 认证**: 适用于 Web 前端

---

## 5. 数据库设计

### 5.1 核心表结构

```sql
-- AI提供商配置
CREATE TABLE ai_providers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    api_key VARCHAR(500),          -- 加密存储
    api_base_url VARCHAR(255),
    is_enabled BOOLEAN DEFAULT TRUE,
    config JSON
);

-- AI模型配置
CREATE TABLE ai_models (
    id INT PRIMARY KEY AUTO_INCREMENT,
    provider_id INT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    is_default BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (provider_id) REFERENCES ai_providers(id)
);

-- 角色定义
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    system_prompt TEXT,
    default_output_format VARCHAR(50),
    allowed_skills JSON
);

-- 工作空间
CREATE TABLE workspaces (
    id INT PRIMARY KEY AUTO_INCREMENT,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    local_path VARCHAR(500),
    role_id INT,
    default_model_id INT,
    config JSON,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- API Key
CREATE TABLE api_keys (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    permissions JSON,
    rate_limit INT DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE
);

-- 对话记录
CREATE TABLE conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    workspace_id INT NOT NULL,
    title VARCHAR(255),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- 消息记录
CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    role ENUM('user', 'assistant', 'system'),
    content TEXT,
    attachments JSON,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- 知识库文档
CREATE TABLE kb_documents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    source_path VARCHAR(500),
    summary TEXT,
    category VARCHAR(100),
    tags JSON,
    workspace_id INT
);

-- 定时任务
CREATE TABLE scheduled_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    cron_expression VARCHAR(100),
    task_type VARCHAR(50),
    task_config JSON,
    is_active BOOLEAN DEFAULT TRUE
);

-- Token 使用记录
CREATE TABLE token_usage (
    id INT PRIMARY KEY AUTO_INCREMENT,
    workspace_id INT,
    conversation_id INT,
    model_id INT,
    skill_name VARCHAR(100),
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    cost_usd DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- 工作空间记忆
CREATE TABLE workspace_memories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    workspace_id INT NOT NULL,
    memory_type ENUM('preference', 'context', 'config', 'rule', 'summary'),
    content TEXT NOT NULL,
    source VARCHAR(100),
    importance INT DEFAULT 5,
    tags JSON,
    is_pinned BOOLEAN DEFAULT FALSE,
    use_count INT DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);
```

---

## 6. 接口设计

### 6.1 RESTful API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/workspaces | 创建工作空间 |
| GET | /api/workspaces | 获取工作空间列表 |
| GET | /api/workspaces/{id} | 获取工作空间详情 |
| POST | /api/chat | 发送对话消息 |
| GET | /api/conversations | 获取对话历史 |
| POST | /api/skills/{name}/execute | 执行技能 |
| GET | /api/admin/ai-providers | 获取AI配置 |
| POST | /api/admin/api-keys | 创建API Key |

### 6.2 WebSocket

| 事件 | 说明 |
|------|------|
| chat:message | 发送消息 |
| chat:stream | 流式响应 |
| task:progress | 任务进度 |
| task:complete | 任务完成 |

---

## 7. CLI 命令设计

```bash
# 工作空间管理
auto workspace create <name> --role <role>
auto workspace list
auto workspace switch <name>

# 对话
auto chat "你的问题"
auto chat --file input.txt

# 配置管理
auto config set ai.provider anthropic
auto config set ai.model claude-3-5-sonnet
auto config list

# 技能包
auto skill list
auto skill install <name>
auto skill run <name> [options]

# API Key 管理
auto apikey create --name "my-key"
auto apikey list
auto apikey revoke <key-id>

# 定时任务
auto schedule list
auto schedule create --cron "0 9 * * *" --task "daily_report"

# RPA 流程
auto rpa record <flow-name>
auto rpa run <flow-name>

# Token 统计
auto stats                    # 查看使用统计
auto stats --workspace <name> # 按工作空间统计
auto stats --model            # 按模型统计
auto stats --export           # 导出统计报告

# 记忆管理
auto memory list              # 查看记忆列表
auto memory add "内容"        # 手动添加记忆
auto memory delete <id>       # 删除记忆
auto memory pin <id>          # 置顶记忆
auto memory search "关键词"   # 搜索记忆
```

---

## 8. 安全设计

### 8.1 危险操作确认机制

```python
DANGEROUS_OPERATIONS = [
    "move_files",      # 移动文件
    "delete_files",    # 删除文件
    "docker_exec",     # Docker执行命令
    "db_write",        # 数据库写操作
    "send_email",      # 发送邮件
    "publish_post",    # 发布社媒内容
    "redis_flush",     # 清空Redis
]
```

### 8.2 操作日志

所有操作记录到数据库，包含：
- 操作时间
- 操作类型
- 操作参数
- 执行结果
- 用户确认状态

### 8.3 API Key 权限

```json
{
  "permissions": ["chat", "read", "write", "admin"],
  "rate_limit": 100,
  "allowed_ips": ["*"],
  "expires_at": "2025-01-01"
}
```

---

## 9. 部署方案

### 9.1 Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - mysql
      - redis

  celery-worker:
    build: ./backend
    command: celery -A app.tasks worker

  celery-beat:
    build: ./backend
    command: celery -A app.tasks beat

  web:
    build: ./web
    ports:
      - "3000:3000"

  mysql:
    image: mysql:8.0
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7-alpine

volumes:
  mysql_data:
```

### 9.2 系统要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 磁盘 | 20GB | 100GB |
| Python | 3.10+ | 3.11+ |
| Node.js | 18+ | 20+ |
| MySQL | 8.0+ | 8.0+ |
| Redis | 7.0+ | 7.0+ |

---

## 10. 实施计划

### 10.1 里程碑

| 阶段 | 里程碑 | 交付物 |
|------|--------|--------|
| M1 | 基础框架 | 后端API、数据库、CLI基础 |
| M2 | 统一网关 | API认证、限流、Webhook |
| M3 | AI集成 | 多AI接口、流式对话 |
| M4 | 核心技能包 | 开发、财务、文件管理 |
| M5 | Web前端 | 对话界面、管理后台 |
| M6 | 高级技能包 | RPA、社媒、PPT、知识库 |
| M7 | 优化完善 | 性能优化、测试覆盖 |

### 10.2 任务清单

| ID | 任务 | 优先级 |
|----|------|--------|
| T-01 | MySQL数据库表结构设计 | P0 |
| T-02 | FastAPI后端框架搭建 | P0 |
| T-03 | 统一网关实现 | P0 |
| T-04 | Webhook适配器 | P1 |
| T-05 | MCP协议适配器 | P1 |
| T-06 | Celery任务队列 | P0 |
| T-07 | 定时任务调度 | P1 |
| T-08 | 工作空间管理 | P0 |
| T-09 | AI路由器 | P0 |
| T-10 | CLI工具开发 | P0 |
| T-11 | 角色系统 | P0 |
| T-12 | Web前端界面 | P1 |
| T-13 | 技能包系统 | P0 |
| T-14 | 知识库RAG | P1 |
| T-15 | 交付物生成器 | P1 |
| T-16 | Token统计系统 | P0 |
| T-17 | 成本预算告警 | P1 |
| T-18 | 工作空间全局记忆 | P0 |
| T-19 | 记忆自动提取 | P1 |
| T-20 | 记忆语义检索 | P1 |

---

## 11. 验收标准

### 11.1 功能验收

- [ ] 可通过 CLI 创建工作空间并进行对话
- [ ] 可通过 Web 界面进行完整操作
- [ ] 支持至少 4 种 AI 提供商切换
- [ ] 支持至少 10 种技能包
- [ ] 支持企业微信/钉钉/飞书 Webhook
- [ ] 支持定时任务调度
- [ ] 知识库检索准确率 > 85%

### 11.2 性能验收

- [ ] API 响应时间 < 200ms (非AI调用)
- [ ] 支持 100 并发用户
- [ ] 流式输出延迟 < 500ms

### 11.3 安全验收

- [ ] 危险操作 100% 需要确认
- [ ] API Key 加密存储
- [ ] 操作日志完整记录

---

## 12. 附录

### 12.1 术语表

| 术语 | 说明 |
|------|------|
| 工作空间 | 用户工作的独立环境，包含配置和文件 |
| 技能包 | 一组相关工具和提示词的集合 |
| 交付物 | AI 生成的可用工作成果 |
| RAG | 检索增强生成，知识库问答技术 |
| RPA | 机器人流程自动化 |
| MCP | Model Context Protocol，AI工具协议 |

### 12.2 参考资料

- FastAPI 文档: https://fastapi.tiangolo.com/
- LiteLLM 文档: https://docs.litellm.ai/
- Playwright 文档: https://playwright.dev/
- python-pptx 文档: https://python-pptx.readthedocs.io/

---

**文档更新记录**

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2024-01-16 | 初版 | AI Assistant |
