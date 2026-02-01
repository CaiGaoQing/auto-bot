和同事跑「
」｜
？ i# AI Auto - AI 个人助手

一个支持 CLI 和 Web 的智能工作平台，通过集成多种 AI 能力，为不同职业角色提供定制化的工作辅助。

## 特性

- **CLI 优先** - 命令行交互，支持本地和远程模式
- **多角色支持** - 开发、财务、产品、运营等多种角色
- **技能包系统** - 可扩展的技能包，支持外部安装
- **MCP 协议** - 原生支持 Model Context Protocol
- **统一工具层** - 内置技能、外部技能、MCP 工具统一管理

## 快速开始

### 安装

```bash
# 基础安装
pip install -e .

# 包含所有功能
pip install -e ".[all]"
```

### 初始化

```bash
# 初始化配置
auto init

# 配置 AI 提供商
auto config provider add --name openai --api-key "sk-xxx"
```

### 使用

```bash
# 交互式对话
auto chat

# 单次对话
auto chat "帮我写一个 Python 爬虫"

# 查看所有功能
auto query all
```

## 文档

- [产品需求文档](docs/PRD_AI个人助手.md)
- [架构设计](docs/Architecture_架构设计.md)
- [API 接口文档](docs/API_接口文档.md)
- [技能包开发指南](docs/Skill_开发指南.md)
- [数据库设计](docs/Database_数据库设计.md)
- [部署运维手册](docs/Deploy_部署运维手册.md)

## 项目结构

```
auto/
├── cli/                    # CLI 命令
├── core/                   # 核心引擎
│   ├── ai/                # AI 路由器
│   ├── skill/             # 技能引擎
│   ├── tool/              # 工具注册
│   └── memory/            # 记忆引擎
├── integration/           # 集成层
│   ├── mcp/               # MCP 客户端
│   └── ai/                # AI 提供商适配器
├── infrastructure/        # 基础设施
├── skills/                # 技能包
│   └── builtin/           # 内置技能包
└── shared/                # 共享模块
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check .
mypy auto
```

## 许可证

MIT License
