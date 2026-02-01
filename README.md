<div align="center">

# 🤖 Auto Bot

**AI 驱动的智能工作助手平台**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[功能特性](#-功能特性) •
[快速开始](#-快速开始) •
[使用指南](#-使用指南) •
[API 文档](#-api-文档) •
[技能开发](#-技能开发)

</div>

---

## 📖 项目简介

**Auto Bot** 是一个支持 CLI 和 Web 双端的智能工作平台，通过集成多种 AI 能力，为不同职业角色（开发者、财务、产品经理、运营等）提供定制化的工作辅助。

### 核心理念

- **角色驱动**：不同角色有不同的工作流程和交付物
- **技能可扩展**：通过技能包系统支持无限扩展
- **工作空间隔离**：每个项目独立管理，支持多人协作
- **多端协同**：CLI 适合开发者，Web 适合普通用户

---

## ✨ 功能特性

### 🎭 多角色 AI 助手

| 角色 | 职责 | 交付物 |
|------|------|--------|
| 💻 开发工程师 | 代码编写、调试、优化 | `.py` `.js` `.ts` 等代码文件 |
| 📊 财务人员 | 报表分析、数据处理 | Excel 表格、财务报告 |
| 📋 产品经理 | 需求文档、原型设计 | PRD 文档、流程图 |
| 📈 项目经理 | 任务拆分、风险管理 | 项目计划、甘特图 |
| 🎨 运营人员 | 内容创作、数据分析 | PPT、营销文案 |
| 🔬 金融分析师 | 股票研究、市场调研 | 研究报告、数据分析 |

### 🛠 核心能力

- **智能对话** - 基于上下文的多轮对话，支持流式输出
- **文件生成** - 自动生成 PPT、Excel、PDF、代码等文件
- **图像生成** - 集成 DALL-E / Nano Banana 等生图 API
- **工作空间** - 项目级文件管理，支持上传、预览、下载
- **定时任务** - 支持 Cron 表达式的自动化任务调度
- **知识库** - RAG 检索增强，学习企业私有文档
- **MCP 协议** - 原生支持 Model Context Protocol
- **Webhook** - 对接企业微信、钉钉、飞书等平台
- **Token 统计** - 用量追踪与预算控制

### 📦 内置技能包

```
skills/builtin/
├── developer/      # 代码开发、调试、重构
├── finance/        # 财务分析、报表生成
├── product/        # PRD 编写、需求分析
├── project/        # 项目管理、任务拆分
├── ppt/            # PPT 生成与美化
├── deploy/         # 自动部署开源项目
├── devops/         # Docker/K8s 运维
├── testing/        # 自动化测试
├── stock_research/ # A股市场调研
├── email/          # 邮件读取与发送
├── social/         # 小红书等社交平台
├── web_search/     # 网络搜索
├── knowledge/      # 知识库管理
├── rpa/            # RPA 自动化
├── calendar/       # 日程管理
├── notes/          # 笔记管理
├── translate/      # 多语言翻译
├── voice/          # 语音识别与合成
└── file_manager/   # 文件整理
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+ (Web 端)
- SQLite / MySQL (可选)

### 安装

```bash
# 克隆项目
git clone https://github.com/CaiGaoQing/auto-bot.git
cd auto-bot

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装后端依赖
pip install -e ".[all]"

# 安装前端依赖
cd web && npm install && cd ..
```

### 配置 AI 提供商

```bash
# 初始化配置
auto init

# 添加 AI 提供商（支持 OpenAI / Claude / 中转站）
auto config provider add --name openai --base-url "https://api.openai.com/v1" --api-key "sk-xxx"

# 或使用中转站
auto config provider add --name proxy --base-url "https://your-proxy.com/v1" --api-key "your-key"
```

### 启动服务

```bash
# 启动后端 API（端口 8000）
python -m uvicorn auto.gateway.api.app:app --reload --port 8000

# 启动前端（端口 3000）
cd web && npm run dev
```

访问 http://localhost:3000 打开 Web 界面。

---

## 📖 使用指南

### CLI 命令

```bash
# 交互式对话
auto chat

# 单次对话
auto chat "帮我写一个 Python 爬虫"

# 指定角色对话
auto chat --role developer "优化这段代码的性能"

# 查看所有功能
auto query all

# 工作空间管理
auto workspace list
auto workspace create "我的项目"
auto workspace open <id>

# 角色管理
auto role list
auto role switch developer

# 技能管理
auto skill list
auto skill install <skill-name>

# 定时任务
auto schedule list
auto schedule add --cron "0 9 * * *" --task "发送日报"

# MCP 工具
auto mcp list
auto mcp call <tool-name> --args '{...}'
```

### Web 界面功能

| 功能 | 说明 |
|------|------|
| **首页对话** | 直接与 AI 对话，无需选择角色 |
| **工作空间** | 创建项目，管理文件，支持代码预览 |
| **角色切换** | 根据任务切换不同 AI 角色 |
| **设置** | 配置 AI 提供商、图像生成等 |

### 工作空间使用

1. **创建工作空间** - 点击侧边栏 "新建工作空间"
2. **文件管理** - 上传文件、创建文件夹、预览代码
3. **AI 对话** - 在工作空间内对话，自动保存生成的文件
4. **下载交付物** - 生成的 PPT/Excel 等可直接下载

---

## 📡 API 文档

### 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (可选)

### 核心接口

#### 对话

```bash
POST /chat
Content-Type: application/json

{
  "message": "帮我生成一个租房小程序 PPT",
  "role_id": "product",
  "workspace_id": "ws_xxx",
  "save_to_workspace": true
}
```

#### 工作空间

```bash
# 列表
GET /workspaces

# 创建
POST /workspaces
{ "name": "我的项目", "description": "项目描述" }

# 文件树
GET /workspaces/{id}/tree

# 上传文件
POST /workspaces/{id}/upload
Content-Type: multipart/form-data

# 预览文件
GET /workspaces/{id}/preview/{path}

# 下载文件
GET /workspaces/{id}/download/{path}
```

#### AI 配置

```bash
# 获取提供商列表
GET /providers

# 添加提供商
POST /providers
{
  "name": "openai",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-xxx",
  "model": "gpt-4"
}

# 图像生成配置
PUT /image-gen/config
{
  "enabled": true,
  "base_url": "https://your-proxy.com/v1",
  "api_key": "your-key",
  "model": "dall-e-3"
}
```

完整 API 文档见 [docs/API_接口文档.md](docs/API_接口文档.md)

---

## 🔧 技能开发

### 创建自定义技能

```python
# auto/skills/custom/my_skill/skill.py
from auto.core.skill.base import BaseSkill, SkillMetadata

class MySkill(BaseSkill):
    """自定义技能示例"""
    
    metadata = SkillMetadata(
        name="my_skill",
        display_name="我的技能",
        description="这是一个自定义技能",
        version="1.0.0",
        author="Your Name",
        tags=["custom", "example"]
    )
    
    async def execute(self, context: dict) -> dict:
        # 实现技能逻辑
        result = await self.do_something(context["input"])
        return {"output": result, "status": "success"}
    
    async def do_something(self, input_data: str) -> str:
        # 具体处理逻辑
        return f"处理结果: {input_data}"
```

### 注册技能

```python
# auto/skills/custom/__init__.py
from .my_skill.skill import MySkill

__all__ = ["MySkill"]
```

详细开发指南见 [docs/Skill_开发指南.md](docs/Skill_开发指南.md)

---

## 🏗 项目架构

```
auto-bot/
├── auto/                       # Python 后端
│   ├── cli/                    # CLI 命令行工具
│   │   ├── commands/           # 各命令实现
│   │   └── main.py             # 入口
│   ├── core/                   # 核心引擎
│   │   ├── ai/                 # AI 路由器、图像生成
│   │   ├── skill/              # 技能引擎
│   │   ├── tool/               # 工具注册与执行
│   │   ├── memory/             # 对话记忆
│   │   ├── knowledge/          # 知识库 RAG
│   │   ├── scheduler/          # 定时任务
│   │   ├── role/               # 角色管理
│   │   ├── output/             # 输出生成器
│   │   ├── usage/              # Token 统计
│   │   ├── budget/             # 预算控制
│   │   ├── audit/              # 审计日志
│   │   └── task/               # 任务执行器
│   ├── gateway/                # API 网关
│   │   ├── api/                # FastAPI 路由
│   │   ├── middleware/         # 中间件
│   │   ├── webhook/            # Webhook 处理
│   │   └── websocket/          # WebSocket
│   ├── infrastructure/         # 基础设施
│   │   ├── database/           # 数据库
│   │   └── storage/            # 文件存储
│   ├── integration/            # 外部集成
│   │   ├── mcp/                # MCP 协议
│   │   └── ai/                 # AI 适配器
│   ├── skills/                 # 技能包
│   │   └── builtin/            # 内置技能
│   └── shared/                 # 共享模块
│       ├── config.py           # 配置管理
│       ├── models.py           # 数据模型
│       └── utils.py            # 工具函数
├── web/                        # Next.js 前端
│   ├── app/                    # 页面
│   │   ├── page.tsx            # 首页
│   │   ├── settings/           # 设置页
│   │   └── workspace/          # 工作空间页
│   └── components/             # 组件
├── docs/                       # 文档
├── scripts/                    # 脚本
├── tests/                      # 测试
├── docker-compose.yml          # Docker 编排
└── pyproject.toml              # Python 项目配置
```

---

## 🛡 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | Python 3.10+, FastAPI, Pydantic |
| **前端框架** | Next.js 14, React 18, TailwindCSS |
| **数据库** | SQLite (默认) / MySQL / PostgreSQL |
| **AI 集成** | OpenAI API, Claude API, 自定义中转站 |
| **文件生成** | python-pptx, openpyxl, WeasyPrint |
| **图像生成** | DALL-E, Nano Banana, Stable Diffusion |
| **协议支持** | MCP (Model Context Protocol) |
| **消息推送** | WebSocket, Webhook |
| **容器化** | Docker, Docker Compose |

---

## 📋 配置说明

### 环境变量

```bash
# .env 文件示例
AUTO_ENV=development
AUTO_DEBUG=true

# 数据库
AUTO_DB_URL=sqlite:///./data/auto.db

# AI 配置
AUTO_DEFAULT_PROVIDER=openai
AUTO_OPENAI_API_KEY=sk-xxx
AUTO_OPENAI_BASE_URL=https://api.openai.com/v1

# 图像生成
AUTO_IMAGE_GEN_ENABLED=true
AUTO_IMAGE_GEN_API_KEY=your-key
AUTO_IMAGE_GEN_BASE_URL=https://your-proxy.com/v1

# 服务端口
AUTO_API_PORT=8000
AUTO_WEB_PORT=3000
```

### 配置文件

配置文件位于 `~/.ai-auto/config.yaml`：

```yaml
providers:
  - name: openai
    base_url: https://api.openai.com/v1
    api_key: sk-xxx
    model: gpt-4
    is_default: true

image_gen:
  enabled: true
  provider: nano-banana
  base_url: https://api.nanobanana.com/v1
  api_key: your-key
  model: dall-e-3

workspaces:
  root: ./data/workspaces

memory:
  enabled: true
  max_history: 50
```

---

## 🧪 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check .
mypy auto

# 格式化代码
ruff format .
```

---

## 🗺 路线图

- [x] CLI 基础功能
- [x] Web 界面
- [x] 多角色系统
- [x] 工作空间管理
- [x] 文件生成 (PPT/Excel)
- [x] 图像生成配置
- [ ] 真实 PPT 插图
- [ ] 移动端适配
- [ ] 企业微信/钉钉集成
- [ ] 多用户权限系统
- [ ] 插件市场
- [ ] 私有化部署文档

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！**

Made with ❤️ by [CaiGaoQing](https://github.com/CaiGaoQing)

</div>
