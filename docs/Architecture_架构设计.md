# AI 个人助手 - 系统架构设计

**版本**: v1.0  
**日期**: 2024-01-16  
**设计原则**: 模块化、可扩展、松耦合

---

## 1. 设计原则

### 1.1 核心设计理念

| 原则 | 说明 |
|------|------|
| **模块化** | 每个功能模块独立，可单独开发、测试、部署 |
| **松耦合** | 模块间通过接口通信，降低依赖 |
| **可扩展** | 支持插件化扩展，新增功能无需修改核心代码 |
| **可配置** | 配置驱动，行为可通过配置调整 |
| **可观测** | 完善的日志、监控、追踪能力 |

### 1.2 扩展性设计目标

- **技能包可插拔**: 新增技能包只需添加配置和代码，无需修改核心
- **AI 提供商可扩展**: 新增 AI 服务只需实现适配器接口
- **接入方式可扩展**: 新增 Webhook/协议只需实现适配器
- **存储可扩展**: 支持切换不同的数据库/缓存/向量库
- **交付物可扩展**: 新增输出格式只需实现生成器接口

---

## 2. 部署模式

### 2.1 支持的部署模式

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          部署模式选择                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   模式 1: 纯 CLI 模式 (最轻量)                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  CLI ──► 核心引擎 ──► AI 接口                                       │   │
│   │   │                                                                  │   │
│   │   └──► 本地存储 (SQLite + 文件)                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   适用: 个人使用、开发调试                                                   │
│                                                                              │
│   模式 2: CLI + 后端服务                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  CLI ──► 后端API ──► 核心引擎 ──► AI 接口                           │   │
│   │           │                                                          │   │
│   │           └──► MySQL + Redis                                        │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   适用: 多设备同步、Webhook 接入                                             │
│                                                                              │
│   模式 3: 完整模式 (CLI + Web + 后端)                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  CLI ──┐                                                             │   │
│   │        ├──► 后端API ──► 核心引擎 ──► AI 接口                        │   │
│   │  Web ──┘       │                                                     │   │
│   │               └──► MySQL + Redis + 向量库                           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   适用: 团队使用、完整功能                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 CLI 优先设计原则

**CLI 是一等公民**，可以独立运行并完成所有功能：

| 原则 | 说明 |
|------|------|
| **独立运行** | CLI 可脱离后端服务运行（使用本地模式） |
| **功能完整** | 所有功能都可通过 CLI 完成 |
| **查询能力** | CLI 可查询所有功能、配置、状态 |
| **交互友好** | 支持交互式对话和命令两种模式 |

---

## 3. 系统分层架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                            接入层 (Gateway Layer)                            │
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │                        CLI (一等公民)                                  │ │
│   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │ │
│   │  │ 交互式对话  │ │ 命令模式    │ │ 管理命令    │ │ 查询命令    │     │ │
│   │  │ auto chat   │ │ auto <cmd>  │ │ auto config │ │ auto query  │     │ │
│   │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘     │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ (可选)     │
│   │  Web    │ │ Webhook │ │  MCP    │ │ Schedule│ │ Custom  │             │
│   │ (可选)  │ │ (可选)  │ │ (可选)  │ │ (可选)  │ │ (可选)  │             │
│   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘             │
│        │          │          │          │          │                      │
│        └──────────┴──────────┴──────────┼──────────┴──────────────────────│
│                                         │                                  │
│                                   ┌─────┴─────┐                           │
│                                   │  统一网关  │                           │
│                                   │ (Gateway)  │                           │
│                                   └─────┬─────┘                           │
└─────────────────────────────────────────┼─────────────────────────────────┘
                                          │
┌─────────────────────────────────────────┼─────────────────────────────────┐
│                                         │                                  │
│                          应用服务层 (Application Layer)                    │
│                                         │                                  │
│   ┌─────────────────────────────────────┼─────────────────────────────────┐│
│   │                              API Router                               ││
│   └─────────────────────────────────────┬─────────────────────────────────┘│
│                                         │                                  │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│   │Workspace│ │ Chat    │ │ Skill   │ │ Memory  │ │ Admin   │            │
│   │ Service │ │ Service │ │ Service │ │ Service │ │ Service │            │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────┼─────────────────────────────────┐
│                                         │                                  │
│                            核心层 (Core Layer)                             │
│                                         │                                  │
│   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐             │
│   │   AI Router     │ │  Skill Engine   │ │  Task Executor  │             │
│   │   (AI路由器)    │ │  (技能引擎)     │ │  (任务执行器)   │             │
│   └─────────────────┘ └─────────────────┘ └─────────────────┘             │
│                                                                            │
│   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐             │
│   │  Memory Engine  │ │ Output Generator│ │  Event Bus      │             │
│   │  (记忆引擎)     │ │  (输出生成器)   │ │  (事件总线)     │             │
│   └─────────────────┘ └─────────────────┘ └─────────────────┘             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────┼─────────────────────────────────┐
│                                         │                                  │
│                          集成层 (Integration Layer)                        │
│                                         │                                  │
│   ┌─────────────────────────────────────┼─────────────────────────────────┐│
│   │                          Adapter Manager                              ││
│   └─────────────────────────────────────┬─────────────────────────────────┘│
│                                         │                                  │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│   │   AI    │ │ Storage │ │ External│ │  Tool   │ │ Notify  │            │
│   │ Adapter │ │ Adapter │ │ Adapter │ │ Adapter │ │ Adapter │            │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────┼─────────────────────────────────┐
│                                         │                                  │
│                          基础设施层 (Infrastructure Layer)                 │
│                                         │                                  │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│   │  MySQL  │ │  Redis  │ │ Vector  │ │  File   │ │  Queue  │            │
│   │         │ │         │ │   DB    │ │ Storage │ │ (Celery)│            │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. CLI 完整设计

### 4.1 CLI 架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLI 架构                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         CLI 入口 (auto)                              │   │
│   └────────────────────────────────┬────────────────────────────────────┘   │
│                                    │                                        │
│   ┌────────────┬───────────────────┼───────────────────┬────────────────┐   │
│   │            │                   │                   │                │   │
│   ▼            ▼                   ▼                   ▼                ▼   │
│ ┌──────┐  ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────┐   │
│ │ chat │  │workspace │      │  skill   │      │  config  │      │query │   │
│ │ 对话 │  │ 工作空间 │      │  技能    │      │  配置    │      │ 查询 │   │
│ └──────┘  └──────────┘      └──────────┘      └──────────┘      └──────┘   │
│                                                                              │
│ ┌──────┐  ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────┐   │
│ │memory│  │  stats   │      │   rpa    │      │ schedule │      │ help │   │
│ │ 记忆 │  │  统计    │      │  自动化  │      │  定时    │      │ 帮助 │   │
│ └──────┘  └──────────┘      └──────────┘      └──────────┘      └──────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           运行模式选择                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────┐            ┌─────────────────────┐                │
│   │     本地模式        │            │     远程模式        │                │
│   │  (--local / 默认)   │            │   (--remote)        │                │
│   ├─────────────────────┤            ├─────────────────────┤                │
│   │ - SQLite 存储       │            │ - 连接后端 API      │                │
│   │ - 本地文件系统      │            │ - MySQL 存储        │                │
│   │ - 直接调用 AI 接口  │            │ - 多设备同步        │                │
│   │ - 无需启动服务      │            │ - 支持 Webhook      │                │
│   └─────────────────────┘            └─────────────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 CLI 命令完整列表

```bash
# ═══════════════════════════════════════════════════════════════════════════
#                              对话命令
# ═══════════════════════════════════════════════════════════════════════════

auto chat                          # 进入交互式对话
auto chat "你的问题"               # 单次对话
auto chat --file input.txt         # 从文件读取输入
auto chat --role developer         # 指定角色
auto chat --model gpt-4o           # 指定模型
auto chat --skill finance          # 使用特定技能

# 交互式对话中的命令
> /help                            # 显示帮助
> /role developer                  # 切换角色
> /skill finance                   # 切换技能
> /model gpt-4o                    # 切换模型
> /memory                          # 查看当前记忆
> /clear                           # 清除对话历史
> /save                            # 保存对话
> /exit                            # 退出

# ═══════════════════════════════════════════════════════════════════════════
#                            工作空间命令
# ═══════════════════════════════════════════════════════════════════════════

auto workspace create <name>       # 创建工作空间
auto workspace create <name> --role developer  # 创建并指定角色
auto workspace list                # 列出所有工作空间
auto workspace switch <name>       # 切换工作空间
auto workspace info                # 当前工作空间信息
auto workspace delete <name>       # 删除工作空间
auto workspace export <name>       # 导出工作空间

# ═══════════════════════════════════════════════════════════════════════════
#                              技能命令
# ═══════════════════════════════════════════════════════════════════════════

auto skill list                    # 列出所有技能
auto skill list --installed        # 列出已安装的技能
auto skill info <name>             # 查看技能详情
auto skill install <name>          # 安装技能
auto skill uninstall <name>        # 卸载技能
auto skill run <name> [args]       # 直接运行技能

# 技能快捷命令 (常用技能可直接调用)
auto excel read data.xlsx          # 读取 Excel
auto excel create report.xlsx      # 创建 Excel
auto docker ps                     # Docker 容器列表
auto db query "SELECT * FROM ..."  # 数据库查询
auto search "关键词"               # 网络搜索

# ═══════════════════════════════════════════════════════════════════════════
#                              记忆命令
# ═══════════════════════════════════════════════════════════════════════════

auto memory list                   # 列出所有记忆
auto memory list --type preference # 按类型筛选
auto memory add "记忆内容"         # 添加记忆
auto memory add "内容" --type rule # 添加指定类型
auto memory delete <id>            # 删除记忆
auto memory pin <id>               # 置顶记忆
auto memory unpin <id>             # 取消置顶
auto memory search "关键词"        # 搜索记忆
auto memory clear                  # 清空记忆 (需确认)

# ═══════════════════════════════════════════════════════════════════════════
#                              配置命令
# ═══════════════════════════════════════════════════════════════════════════

auto config list                   # 列出所有配置
auto config get <key>              # 获取配置
auto config set <key> <value>      # 设置配置

# AI 提供商配置
auto config provider list          # 列出 AI 提供商
auto config provider add           # 添加提供商 (交互式)
auto config provider add --name "proxy" --base-url "https://..." --api-key "sk-..."
auto config provider test <name>   # 测试提供商
auto config provider delete <name> # 删除提供商
auto config provider set-default <name>  # 设为默认

# 模型配置
auto config model list             # 列出所有模型
auto config model set-default <model>    # 设置默认模型

# ═══════════════════════════════════════════════════════════════════════════
#                              统计命令
# ═══════════════════════════════════════════════════════════════════════════

auto stats                         # 显示使用统计
auto stats --today                 # 今日统计
auto stats --month                 # 本月统计
auto stats --workspace <name>      # 按工作空间
auto stats --model                 # 按模型
auto stats --export                # 导出报告

# ═══════════════════════════════════════════════════════════════════════════
#                              定时任务命令
# ═══════════════════════════════════════════════════════════════════════════

auto schedule list                 # 列出定时任务
auto schedule add                  # 添加任务 (交互式)
auto schedule add --cron "0 9 * * *" --task "每日报告"
auto schedule delete <id>          # 删除任务
auto schedule pause <id>           # 暂停任务
auto schedule resume <id>          # 恢复任务
auto schedule run <id>             # 立即执行

# ═══════════════════════════════════════════════════════════════════════════
#                              RPA 命令
# ═══════════════════════════════════════════════════════════════════════════

auto rpa list                      # 列出流程
auto rpa record <name>             # 录制流程
auto rpa run <name>                # 运行流程
auto rpa run <name> --var "key=value"  # 带变量运行
auto rpa delete <name>             # 删除流程
auto rpa export <name>             # 导出流程

# ═══════════════════════════════════════════════════════════════════════════
#                              查询命令 (统一查询入口)
# ═══════════════════════════════════════════════════════════════════════════

auto query                         # 进入查询模式
auto query skills                  # 查询所有技能
auto query providers               # 查询 AI 提供商
auto query models                  # 查询可用模型
auto query roles                   # 查询可用角色
auto query workspaces              # 查询工作空间
auto query memories                # 查询记忆
auto query tasks                   # 查询定时任务
auto query stats                   # 查询统计
auto query all                     # 查询所有信息概览

# ═══════════════════════════════════════════════════════════════════════════
#                              帮助命令
# ═══════════════════════════════════════════════════════════════════════════

auto help                          # 显示帮助
auto help <command>                # 显示命令帮助
auto help skills                   # 显示技能使用帮助
auto version                       # 显示版本

# ═══════════════════════════════════════════════════════════════════════════
#                              服务命令 (可选)
# ═══════════════════════════════════════════════════════════════════════════

auto server start                  # 启动后端服务
auto server stop                   # 停止服务
auto server status                 # 服务状态
auto server logs                   # 查看日志
```

### 4.3 CLI 交互式对话示例

```
$ auto chat

╭─────────────────────────────────────────────────────────────╮
│           🤖 AI 个人助手 v1.0                               │
│                                                              │
│  工作空间: my-project                                        │
│  角色: developer                                             │
│  模型: gpt-4o                                                │
│                                                              │
│  输入 /help 查看命令, /exit 退出                            │
╰─────────────────────────────────────────────────────────────╯

You> 帮我写一个 Python 爬虫脚本

🧠 使用记忆: 项目使用 Python 3.11, 代码风格遵循 PEP8

AI> 好的，我来帮你写一个爬虫脚本。

```python
import requests
from bs4 import BeautifulSoup

def crawl(url: str) -> dict:
    """爬取网页内容"""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    return {
        'title': soup.title.string,
        'content': soup.get_text()
    }

if __name__ == '__main__':
    result = crawl('https://example.com')
    print(result)
```

💾 是否保存到文件? [y/N] y
📁 已保存: outputs/code/crawler.py

You> /skill

当前可用技能:
┌─────────────────┬───────────────────────────────┐
│ 技能            │ 描述                          │
├─────────────────┼───────────────────────────────┤
│ developer       │ 代码生成、审查、调试          │
│ devops          │ Docker、数据库、Redis         │
│ file_manager    │ 文件整理、桌面清理            │
│ testing         │ 自动化测试                    │
└─────────────────┴───────────────────────────────┘

输入 /skill <name> 切换技能

You> 帮我整理下桌面

AI> 🔍 正在分析桌面文件...

📊 桌面文件分析结果：
- 截图文件: 15个 (Screenshot_*.png)
- 文档文件: 8个 (.docx, .pdf)
- 下载文件: 12个

📋 整理建议：
┌─────────────────────────────────────────────────┐
│ 操作                          │ 文件数         │
├─────────────────────────────────────────────────┤
│ 移动截图到 ~/Pictures/Screenshots    │ 15个    │
│ 移动文档到 ~/Documents/Desktop归档    │ 8个     │
│ 移动下载到 ~/Downloads               │ 12个    │
└─────────────────────────────────────────────────┘

⚠️  是否执行以上操作? [y/N] y

✅ 整理完成！已移动 35 个文件

You> /exit

👋 再见！对话已保存。
```

### 4.4 CLI 查询功能

```bash
$ auto query all

╭─────────────────────────────────────────────────────────────╮
│                    🔍 系统概览                              │
╰─────────────────────────────────────────────────────────────╯

📁 工作空间 (3个)
┌──────────────┬────────────┬─────────────────────┐
│ 名称         │ 角色       │ 最后使用            │
├──────────────┼────────────┼─────────────────────┤
│ my-project   │ developer  │ 2分钟前 (当前)      │
│ finance-work │ finance    │ 1天前               │
│ daily-tasks  │ general    │ 3天前               │
└──────────────┴────────────┴─────────────────────┘

🤖 AI 提供商 (4个)
┌─────────────────┬──────────┬────────┐
│ 名称            │ 类型     │ 状态   │
├─────────────────┼──────────┼────────┤
│ openai          │ official │ 🟢正常 │
│ openai_proxy    │ proxy    │ 🟢正常 │
│ claude_proxy    │ proxy    │ 🟢正常 │
│ local_ollama    │ custom   │ 🔴离线 │
└─────────────────┴──────────┴────────┘

🎯 技能包 (18个)
  已安装: developer, finance, file_manager, devops
  可安装: testing, social_media, rpa, ...

🧠 记忆 (12条)
  置顶: 3条
  偏好: 4条
  规则: 5条

📊 本月统计
  Token: 2,456,789
  成本: $12.34
  请求: 1,234次

⏰ 定时任务 (2个)
  活跃: 2个
  下次执行: 每日报告 (明天 09:00)

输入 `auto query <类型>` 查看详情
```

### 4.5 本地模式 vs 远程模式

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         运行模式对比                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   特性              │ 本地模式 (默认)     │ 远程模式                        │
│   ─────────────────────────────────────────────────────────────────────────│
│   存储              │ SQLite + 本地文件   │ MySQL + 云存储                  │
│   启动方式          │ 直接运行 CLI        │ 需启动后端服务                  │
│   多设备同步        │ ❌ 不支持           │ ✅ 支持                         │
│   Webhook           │ ❌ 不支持           │ ✅ 支持                         │
│   定时任务          │ 简单支持 (cron)     │ 完整支持 (Celery)              │
│   Web 界面          │ ❌ 无               │ ✅ 可选                         │
│   适用场景          │ 个人单机            │ 团队/多设备                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

# 本地模式 (默认)
$ auto chat "你好"

# 远程模式
$ auto --remote chat "你好"
$ auto --remote --server http://localhost:8000 chat "你好"

# 配置默认模式
$ auto config set mode remote
$ auto config set server.url http://localhost:8000
```

---

## 5. 模块目录结构

### 3.1 模块概览

```
auto/
├── gateway/                 # 接入层
│   ├── api/                # REST API
│   ├── websocket/          # WebSocket
│   ├── adapters/           # 接入适配器
│   │   ├── webhook/        # Webhook (企微/钉钉/飞书)
│   │   ├── mcp/            # MCP 协议
│   │   └── scheduler/      # 定时调度
│   └── middleware/         # 中间件 (认证/限流/日志)
│
├── application/            # 应用服务层
│   ├── workspace/          # 工作空间服务
│   ├── chat/               # 对话服务
│   ├── skill/              # 技能服务
│   ├── memory/             # 记忆服务
│   └── admin/              # 管理服务
│
├── core/                   # 核心层
│   ├── ai/                 # AI 路由器
│   ├── skill/              # 技能引擎
│   ├── task/               # 任务执行器
│   ├── memory/             # 记忆引擎
│   ├── output/             # 输出生成器
│   └── event/              # 事件总线
│
├── integration/            # 集成层
│   ├── ai/                 # AI 提供商适配器
│   ├── mcp/                # MCP 客户端 (连接外部 MCP 服务器)
│   ├── storage/            # 存储适配器
│   ├── external/           # 外部服务适配器
│   ├── tools/              # 工具适配器
│   └── notify/             # 通知适配器
│
├── infrastructure/         # 基础设施层
│   ├── database/           # 数据库
│   ├── cache/              # 缓存
│   ├── queue/              # 消息队列
│   └── storage/            # 文件存储
│
├── skills/                 # 技能包 (插件)
│   ├── builtin/            # 内置技能包
│   ├── external/           # 外部安装的技能包
│   └── custom/             # 自定义技能包
│
├── mcp_servers/            # MCP 服务器配置
│   ├── installed/          # 已安装的 MCP 服务器
│   └── configs/            # MCP 服务器配置
│
└── shared/                 # 共享模块
    ├── models/             # 数据模型
    ├── schemas/            # 接口定义
    ├── utils/              # 工具函数
    └── config/             # 配置管理
```

---

## 6. 核心引擎设计

### 4.1 AI 路由器 (AI Router)

负责管理多个 AI 提供商，实现负载均衡、故障转移、成本控制。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            AI Router                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────┐                                                   │
│   │  Request Handler │◄─── 接收 AI 请求                                 │
│   └────────┬────────┘                                                   │
│            │                                                             │
│            ▼                                                             │
│   ┌─────────────────┐     ┌─────────────────┐                          │
│   │  Model Selector │────►│  Config Store   │ 读取模型配置              │
│   └────────┬────────┘     └─────────────────┘                          │
│            │                                                             │
│            ▼                                                             │
│   ┌─────────────────┐                                                   │
│   │ Provider Router │ 选择提供商 (负载均衡/故障转移)                     │
│   └────────┬────────┘                                                   │
│            │                                                             │
│            ▼                                                             │
│   ┌─────────────────┐                                                   │
│   │ Request Builder │ 构建请求 (适配不同 API 格式)                       │
│   └────────┬────────┘                                                   │
│            │                                                             │
│            ▼                                                             │
│   ┌─────────────────┐     ┌─────────────────┐                          │
│   │  Rate Limiter   │────►│  Token Counter  │ 限流 & Token 统计         │
│   └────────┬────────┘     └─────────────────┘                          │
│            │                                                             │
│            ▼                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Provider Adapters                          │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
│   │  │ OpenAI  │ │Anthropic│ │  Azure  │ │ Ollama  │ │ Custom  │  │   │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│            │                                                             │
│            ▼                                                             │
│   ┌─────────────────┐                                                   │
│   │Response Handler │ 统一响应格式 + 流式处理                            │
│   └─────────────────┘                                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**接口定义:**

```python
# core/ai/router.py

from abc import ABC, abstractmethod
from typing import AsyncIterator

class AIProvider(ABC):
    """AI 提供商抽象接口"""
    
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        model: str,
        **kwargs
    ) -> ChatResponse:
        """同步对话"""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        model: str,
        **kwargs
    ) -> AsyncIterator[ChatChunk]:
        """流式对话"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass

class AIRouter:
    """AI 路由器"""
    
    def __init__(self):
        self.providers: dict[str, AIProvider] = {}
        self.config: RouterConfig = None
    
    def register_provider(self, name: str, provider: AIProvider):
        """注册提供商"""
        self.providers[name] = provider
    
    async def route(self, request: ChatRequest) -> ChatResponse:
        """路由请求到合适的提供商"""
        provider = self._select_provider(request)
        return await provider.chat(request.messages, request.model)
    
    def _select_provider(self, request: ChatRequest) -> AIProvider:
        """选择提供商 (负载均衡 + 故障转移)"""
        pass
```

### 4.2 技能引擎 (Skill Engine)

负责加载、管理、执行技能包。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Skill Engine                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Skill Registry                              │   │
│   │                                                                  │   │
│   │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │   │
│   │   │ finance │ │developer│ │ devops  │ │  ...    │              │   │
│   │   └─────────┘ └─────────┘ └─────────┘ └─────────┘              │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────┐     ┌─────────────────┐                          │
│   │  Skill Loader   │────►│  Skill Config   │ 加载技能包配置            │
│   └─────────────────┘     └─────────────────┘                          │
│                                                                          │
│   ┌─────────────────┐                                                   │
│   │  Tool Registry  │ 注册技能包的工具                                   │
│   └─────────────────┘                                                   │
│                                                                          │
│   ┌─────────────────┐                                                   │
│   │ Prompt Builder  │ 构建技能专属提示词                                 │
│   └─────────────────┘                                                   │
│                                                                          │
│   ┌─────────────────┐                                                   │
│   │  Tool Executor  │ 执行工具 (安全沙箱)                               │
│   └─────────────────┘                                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**技能包接口定义:**

```python
# core/skill/base.py

from abc import ABC, abstractmethod

class Skill(ABC):
    """技能包抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述"""
        pass
    
    @property
    def tools(self) -> list[Tool]:
        """技能包含的工具列表"""
        return []
    
    @property
    def system_prompt(self) -> str:
        """系统提示词"""
        return ""
    
    def on_load(self):
        """技能加载时回调"""
        pass
    
    def on_unload(self):
        """技能卸载时回调"""
        pass

class Tool(ABC):
    """工具抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    def parameters(self) -> dict:
        """参数定义 (JSON Schema)"""
        return {}
    
    @property
    def requires_confirmation(self) -> bool:
        """是否需要用户确认"""
        return False
    
    @abstractmethod
    async def execute(self, **params) -> ToolResult:
        """执行工具"""
        pass
```

**技能包配置格式:**

```yaml
# skills/finance/skill.yaml
name: finance
display_name: 财务助手
version: 1.0.0
description: Excel处理、财务报表、数据分析

# 依赖
dependencies:
  python:
    - openpyxl>=3.0
    - pandas>=2.0

# 工具列表
tools:
  - name: read_excel
    description: 读取Excel文件
    module: tools.excel
    function: read_excel
    parameters:
      type: object
      properties:
        file_path:
          type: string
          description: 文件路径
      required: [file_path]

  - name: create_excel
    description: 创建Excel报表
    module: tools.excel
    function: create_excel
    requires_confirmation: true

# 系统提示词
system_prompt: |
  你是一个专业的财务助手，擅长：
  - Excel 数据处理
  - 财务报表生成
  - 数据分析和可视化

# 输出格式
output_formats:
  - xlsx
  - csv
  - pdf
```

### 4.3 统一工具层 (Unified Tool Layer)

系统支持三种工具来源：**内置 Skill**、**外部 Skill** 和 **MCP 服务器**，通过统一的工具层进行管理。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        统一工具层 (Unified Tool Layer)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                          ┌─────────────────────┐                            │
│                          │   Tool Dispatcher   │◄─── AI 调用工具             │
│                          └──────────┬──────────┘                            │
│                                     │                                        │
│          ┌──────────────────────────┼──────────────────────────┐            │
│          │                          │                          │            │
│          ▼                          ▼                          ▼            │
│   ┌─────────────┐          ┌─────────────┐          ┌─────────────┐        │
│   │   内置/外部  │          │    MCP      │          │   原生 API  │        │
│   │   Skill     │          │   Client    │          │   (HTTP)    │        │
│   └──────┬──────┘          └──────┬──────┘          └──────┬──────┘        │
│          │                        │                        │                │
│          ▼                        ▼                        ▼                │
│   ┌─────────────┐          ┌─────────────┐          ┌─────────────┐        │
│   │ Local Tools │          │ MCP Servers │          │ HTTP APIs   │        │
│   │             │          │             │          │             │        │
│   │ ・内置技能包 │          │ ・filesystem │          │ ・REST API  │        │
│   │ ・外部安装   │          │ ・browser    │          │ ・GraphQL   │        │
│   │ ・自定义开发 │          │ ・database   │          │ ・Webhook   │        │
│   │             │          │ ・自定义 MCP │          │             │        │
│   └─────────────┘          └─────────────┘          └─────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 MCP 客户端 (MCP Client)

支持连接外部 MCP 服务器，使用 MCP 协议标准的工具。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MCP Client                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     MCP Server Registry                              │   │
│   │                                                                      │   │
│   │   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐      │   │
│   │   │ filesystem │ │  browser   │ │  database  │ │   custom   │      │   │
│   │   │   (stdio)  │ │  (stdio)   │ │   (sse)    │ │   (sse)    │      │   │
│   │   └────────────┘ └────────────┘ └────────────┘ └────────────┘      │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────┐                                                       │
│   │ Connection Pool │  管理 MCP 服务器连接 (stdio / SSE)                    │
│   └─────────────────┘                                                       │
│                                                                              │
│   ┌─────────────────┐                                                       │
│   │ Tool Discovery  │  自动发现 MCP 服务器提供的 tools/resources/prompts   │
│   └─────────────────┘                                                       │
│                                                                              │
│   ┌─────────────────┐                                                       │
│   │ Request Handler │  处理 tool 调用，转换为 MCP 协议请求                   │
│   └─────────────────┘                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**MCP 配置格式:**

```yaml
# mcp_servers/configs/servers.yaml

servers:
  # stdio 方式连接
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/Users/user/Documents"]
    enabled: true
    
  # SSE 方式连接
  - name: database
    transport: sse
    url: http://localhost:3001/sse
    enabled: true
    
  # 从 MCP 市场安装
  - name: github
    source: mcp-registry/github
    version: "1.0.0"
    config:
      token: "${GITHUB_TOKEN}"
    enabled: true

  # 自定义 MCP 服务器
  - name: custom-erp
    transport: stdio
    command: python
    args: ["/path/to/custom_mcp_server.py"]
    env:
      API_KEY: "${ERP_API_KEY}"
    enabled: true
```

**MCP 客户端接口:**

```python
# integration/mcp/client.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MCPTool:
    """MCP 工具定义"""
    name: str
    description: str
    input_schema: dict
    server_name: str  # 来源服务器


@dataclass
class MCPResource:
    """MCP 资源定义"""
    uri: str
    name: str
    description: str
    mime_type: str


class MCPClient:
    """MCP 客户端"""
    
    def __init__(self, config_path: str):
        self.servers: Dict[str, MCPServerConnection] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
    
    async def connect_all(self):
        """连接所有启用的 MCP 服务器"""
        pass
    
    async def disconnect_all(self):
        """断开所有连接"""
        pass
    
    async def discover_tools(self) -> List[MCPTool]:
        """发现所有可用工具"""
        tools = []
        for server in self.servers.values():
            server_tools = await server.list_tools()
            tools.extend(server_tools)
        return tools
    
    async def call_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: dict
    ) -> Any:
        """调用 MCP 工具"""
        server = self.servers[server_name]
        return await server.call_tool(tool_name, arguments)
    
    async def read_resource(self, uri: str) -> str:
        """读取 MCP 资源"""
        pass
    
    async def get_prompt(
        self, 
        server_name: str, 
        prompt_name: str, 
        arguments: dict
    ) -> str:
        """获取 MCP 提示词"""
        pass


class MCPServerConnection(ABC):
    """MCP 服务器连接抽象"""
    
    @abstractmethod
    async def connect(self):
        pass
    
    @abstractmethod
    async def disconnect(self):
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[MCPTool]:
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, arguments: dict) -> Any:
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[MCPResource]:
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> str:
        pass
```

### 4.5 外部 Skill 市场 (Skill Marketplace)

支持从外部市场安装和管理技能包。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Skill Marketplace Integration                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      Skill Sources                                   │   │
│   │                                                                      │   │
│   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │   │
│   │   │ Official Repo │  │  Community    │  │   Private     │          │   │
│   │   │ (官方仓库)    │  │  (社区仓库)   │  │  (私有仓库)   │          │   │
│   │   └───────────────┘  └───────────────┘  └───────────────┘          │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────┐     ┌─────────────────┐                              │
│   │  Skill Fetcher  │────►│  Registry API   │  搜索/下载技能包             │
│   └─────────────────┘     └─────────────────┘                              │
│                                                                              │
│   ┌─────────────────┐                                                       │
│   │ Skill Installer │  安装/更新/卸载技能包                                 │
│   └─────────────────┘                                                       │
│                                                                              │
│   ┌─────────────────┐                                                       │
│   │ Version Manager │  版本管理/依赖解析                                    │
│   └─────────────────┘                                                       │
│                                                                              │
│   ┌─────────────────┐                                                       │
│   │ Security Scanner│  安全扫描/签名验证                                    │
│   └─────────────────┘                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**CLI 命令:**

```bash
# ═══════════════════════════════════════════════════════════════════════════
#                           MCP 服务器管理
# ═══════════════════════════════════════════════════════════════════════════

auto mcp list                      # 列出所有 MCP 服务器
auto mcp add <name> <config>       # 添加 MCP 服务器
auto mcp install <package>         # 从 MCP 市场安装
auto mcp remove <name>             # 移除 MCP 服务器
auto mcp enable <name>             # 启用
auto mcp disable <name>            # 禁用
auto mcp test <name>               # 测试连接
auto mcp tools <name>              # 列出服务器提供的工具

# 示例
auto mcp install @modelcontextprotocol/server-filesystem
auto mcp add my-db --transport sse --url http://localhost:3001
auto mcp tools filesystem

# ═══════════════════════════════════════════════════════════════════════════
#                           外部 Skill 管理
# ═══════════════════════════════════════════════════════════════════════════

auto skill search <keyword>        # 搜索技能包
auto skill install <name>          # 从市场安装
auto skill install <url>           # 从 URL 安装
auto skill install <path>          # 从本地路径安装
auto skill update <name>           # 更新技能包
auto skill uninstall <name>        # 卸载技能包
auto skill publish <path>          # 发布技能包 (需认证)

# 管理源
auto skill source list             # 列出所有源
auto skill source add <name> <url> # 添加源
auto skill source remove <name>    # 移除源

# 示例
auto skill search excel            # 搜索 Excel 相关技能
auto skill install official/finance
auto skill install https://github.com/user/my-skill/releases/download/v1.0/skill.zip
auto skill source add company https://skills.mycompany.com/registry
```

**工具统一注册:**

```python
# core/tool/registry.py

from typing import Dict, List, Union
from dataclasses import dataclass
from enum import Enum


class ToolSource(Enum):
    BUILTIN = "builtin"      # 内置技能包
    EXTERNAL = "external"    # 外部安装的技能包
    MCP = "mcp"              # MCP 服务器
    API = "api"              # HTTP API


@dataclass
class UnifiedTool:
    """统一工具定义"""
    name: str                    # 工具名称
    description: str             # 描述
    parameters: dict             # 参数 schema
    source: ToolSource           # 来源类型
    source_name: str             # 来源名称 (skill名 / MCP服务器名)
    requires_confirmation: bool = False
    
    @property
    def full_name(self) -> str:
        """完整名称: source_name.tool_name"""
        return f"{self.source_name}.{self.name}"


class UnifiedToolRegistry:
    """统一工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, UnifiedTool] = {}
        self.skill_engine = None
        self.mcp_client = None
    
    async def refresh(self):
        """刷新工具列表"""
        self.tools.clear()
        
        # 1. 加载内置和外部 Skill 的工具
        for skill in self.skill_engine.list_skills():
            for tool in skill.tools:
                unified = UnifiedTool(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.parameters,
                    source=ToolSource.BUILTIN if skill.is_builtin else ToolSource.EXTERNAL,
                    source_name=skill.name,
                    requires_confirmation=tool.requires_confirmation
                )
                self.tools[unified.full_name] = unified
        
        # 2. 加载 MCP 服务器的工具
        mcp_tools = await self.mcp_client.discover_tools()
        for tool in mcp_tools:
            unified = UnifiedTool(
                name=tool.name,
                description=tool.description,
                parameters=tool.input_schema,
                source=ToolSource.MCP,
                source_name=tool.server_name
            )
            self.tools[unified.full_name] = unified
    
    def get_tool(self, full_name: str) -> UnifiedTool:
        """获取工具"""
        return self.tools.get(full_name)
    
    def list_tools(self, source: ToolSource = None) -> List[UnifiedTool]:
        """列出工具"""
        if source:
            return [t for t in self.tools.values() if t.source == source]
        return list(self.tools.values())
    
    async def execute(self, full_name: str, arguments: dict) -> Any:
        """执行工具"""
        tool = self.get_tool(full_name)
        if not tool:
            raise ValueError(f"Tool not found: {full_name}")
        
        if tool.source == ToolSource.MCP:
            return await self.mcp_client.call_tool(
                tool.source_name, 
                tool.name, 
                arguments
            )
        else:
            return await self.skill_engine.execute_tool(
                tool.source_name,
                tool.name,
                arguments
            )
    
    def to_openai_tools(self) -> List[dict]:
        """转换为 OpenAI tools 格式"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.full_name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self.tools.values()
        ]
```

### 4.6 记忆引擎 (Memory Engine)

负责管理工作空间的全局记忆，支持语义检索。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Memory Engine                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Memory Store                                │   │
│   │                                                                  │   │
│   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │   │
│   │   │  Short-term   │  │   Long-term   │  │    Pinned     │      │   │
│   │   │  (会话记忆)   │  │   (持久记忆)  │  │   (置顶记忆)  │      │   │
│   │   └───────────────┘  └───────────────┘  └───────────────┘      │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────┐     ┌─────────────────┐                          │
│   │ Memory Extractor│────►│   AI (提取)     │ 从对话中提取记忆          │
│   └─────────────────┘     └─────────────────┘                          │
│                                                                          │
│   ┌─────────────────┐     ┌─────────────────┐                          │
│   │ Memory Retriever│────►│   Vector DB     │ 语义检索相关记忆          │
│   └─────────────────┘     └─────────────────┘                          │
│                                                                          │
│   ┌─────────────────┐                                                   │
│   │ Memory Injector │ 将记忆注入上下文                                   │
│   └─────────────────┘                                                   │
│                                                                          │
│   ┌─────────────────┐                                                   │
│   │Memory Lifecycle │ 记忆生命周期管理 (过期/合并/清理)                  │
│   └─────────────────┘                                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.4 任务执行器 (Task Executor)

负责异步任务的执行、监控、重试。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Task Executor                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────┐                                                   │
│   │  Task Scheduler │ 任务调度 (立即/延迟/定时)                          │
│   └────────┬────────┘                                                   │
│            │                                                             │
│            ▼                                                             │
│   ┌─────────────────┐     ┌─────────────────┐                          │
│   │   Task Queue    │────►│   Celery/Redis  │                          │
│   └────────┬────────┘     └─────────────────┘                          │
│            │                                                             │
│            ▼                                                             │
│   ┌─────────────────┐                                                   │
│   │  Task Worker    │ 任务执行 (多进程/多线程)                           │
│   └────────┬────────┘                                                   │
│            │                                                             │
│            ▼                                                             │
│   ┌─────────────────┐                                                   │
│   │  Task Monitor   │ 任务监控 (进度/状态/日志)                          │
│   └────────┬────────┘                                                   │
│            │                                                             │
│            ▼                                                             │
│   ┌─────────────────┐                                                   │
│   │ Callback Handler│ 回调处理 (通知/Webhook)                            │
│   └─────────────────┘                                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.5 输出生成器 (Output Generator)

负责生成各种格式的交付物。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Output Generator                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     Generator Registry                           │   │
│   │                                                                  │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│   │  │  Excel  │ │  PPT    │ │Markdown │ │  Code   │ │  Image  │   │   │
│   │  │Generator│ │Generator│ │Generator│ │Generator│ │Generator│   │   │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│   │                                                                  │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐                           │   │
│   │  │   PDF   │ │   CSV   │ │ Custom  │                           │   │
│   │  │Generator│ │Generator│ │Generator│                           │   │
│   │  └─────────┘ └─────────┘ └─────────┘                           │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────┐                                                   │
│   │Template Manager │ 模板管理                                           │
│   └─────────────────┘                                                   │
│                                                                          │
│   ┌─────────────────┐                                                   │
│   │  File Manager   │ 文件保存/导出                                      │
│   └─────────────────┘                                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**生成器接口:**

```python
# core/output/base.py

from abc import ABC, abstractmethod

class OutputGenerator(ABC):
    """输出生成器抽象基类"""
    
    @property
    @abstractmethod
    def format(self) -> str:
        """输出格式 (xlsx, pptx, md, etc.)"""
        pass
    
    @property
    @abstractmethod
    def mime_type(self) -> str:
        """MIME 类型"""
        pass
    
    @abstractmethod
    async def generate(
        self, 
        data: dict, 
        template: str = None,
        **options
    ) -> OutputResult:
        """生成输出"""
        pass

# 注册新的生成器
output_registry.register("xlsx", ExcelGenerator())
output_registry.register("pptx", PPTGenerator())
```

### 4.6 事件总线 (Event Bus)

负责模块间的事件通信，实现松耦合。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Event Bus                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   事件类型:                                                              │
│   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐             │
│   │ chat.message   │ │ task.started   │ │ skill.executed │             │
│   │ chat.completed │ │ task.completed │ │ memory.added   │             │
│   │ chat.error     │ │ task.failed    │ │ memory.updated │             │
│   └────────────────┘ └────────────────┘ └────────────────┘             │
│                                                                          │
│   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐             │
│   │ output.created │ │ webhook.received│ │ user.action   │             │
│   │ output.exported│ │ schedule.triggered│                │             │
│   └────────────────┘ └────────────────┘ └────────────────┘             │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                        Event Handlers                           │   │
│   │                                                                  │   │
│   │   on("chat.completed") → extract_memory()                       │   │
│   │   on("task.completed") → notify_user()                          │   │
│   │   on("output.created") → save_to_workspace()                    │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. 适配器设计 (Adapter Pattern)

### 5.1 适配器架构

所有外部依赖都通过适配器接入，便于替换和扩展。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Adapter Manager                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                       AI Adapters                                │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │   │
│   │  │ OpenAI  │ │Anthropic│ │  Azure  │ │ Ollama  │               │   │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐                           │   │
│   │  │ OneAPI  │ │  vLLM   │ │ Custom  │ ◄── 可扩展               │   │
│   │  └─────────┘ └─────────┘ └─────────┘                           │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     Storage Adapters                             │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │   │
│   │  │  MySQL  │ │PostgreSQL│ │ SQLite │ │ Custom  │               │   │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     Vector DB Adapters                           │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │   │
│   │  │ Chroma  │ │ Milvus  │ │Pinecone │ │ Custom  │               │   │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     Cache Adapters                               │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐                           │   │
│   │  │  Redis  │ │Memcached│ │ Memory  │                           │   │
│   │  └─────────┘ └─────────┘ └─────────┘                           │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     Notify Adapters                              │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │   │
│   │  │  WeCom  │ │DingTalk │ │ Feishu  │ │  Email  │               │   │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │   │
│   │  ┌─────────┐ ┌─────────┐                                       │   │
│   │  │ Webhook │ │ Custom  │                                       │   │
│   │  └─────────┘ └─────────┘                                       │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 适配器接口定义

```python
# integration/base.py

from abc import ABC, abstractmethod

class Adapter(ABC):
    """适配器基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        pass
    
    @abstractmethod
    async def disconnect(self):
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass


class StorageAdapter(Adapter):
    """存储适配器"""
    
    @abstractmethod
    async def get(self, key: str) -> Any:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = None):
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        pass


class VectorAdapter(Adapter):
    """向量数据库适配器"""
    
    @abstractmethod
    async def add(self, id: str, vector: list[float], metadata: dict):
        pass
    
    @abstractmethod
    async def search(
        self, 
        query_vector: list[float], 
        top_k: int = 10
    ) -> list[SearchResult]:
        pass
    
    @abstractmethod
    async def delete(self, id: str):
        pass


class NotifyAdapter(Adapter):
    """通知适配器"""
    
    @abstractmethod
    async def send(self, message: NotifyMessage) -> bool:
        pass
```

---

## 8. 数据流设计

### 6.1 对话请求流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          对话请求数据流                                  │
└─────────────────────────────────────────────────────────────────────────┘

用户请求
    │
    ▼
┌─────────────┐
│   Gateway   │ ◄── 认证、限流、日志
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Chat Service │ ◄── 创建对话上下文
└──────┬──────┘
       │
       ├──────────────────────────────────────────┐
       ▼                                          ▼
┌─────────────┐                          ┌─────────────┐
│Memory Engine│ ◄── 检索相关记忆         │Skill Engine │ ◄── 加载技能
└──────┬──────┘                          └──────┬──────┘
       │                                        │
       └──────────────────┬─────────────────────┘
                          ▼
                  ┌─────────────┐
                  │Prompt Builder│ ◄── 构建完整提示词
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  AI Router  │ ◄── 选择AI提供商
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │AI Provider  │ ◄── 调用AI接口
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │Response Handler│ ◄── 解析响应
                  └──────┬──────┘
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│Tool Executor│  │Memory Engine│  │Token Counter│
│(执行工具)   │  │(提取记忆)   │  │(统计Token) │
└──────┬──────┘  └─────────────┘  └─────────────┘
       │
       ▼
┌─────────────┐
│Output Generator│ ◄── 生成交付物
└──────┬──────┘
       │
       ▼
    返回响应
```

### 6.2 Webhook 请求流程

```
外部平台消息 (企微/钉钉/飞书)
    │
    ▼
┌─────────────┐
│Webhook Adapter│ ◄── 验证签名、解析消息
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Message Parser│ ◄── 统一消息格式
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Task Queue  │ ◄── 入队异步处理
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Task Worker │ ◄── 处理消息
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Chat Service │ ◄── 调用对话服务
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Reply Sender │ ◄── 发送回复
└─────────────┘
```

---

## 9. 扩展机制

### 7.1 技能包扩展

```
skills/
├── builtin/                 # 内置技能包
│   ├── finance/
│   ├── developer/
│   └── ...
│
└── custom/                  # 自定义技能包
    └── my_skill/
        ├── skill.yaml       # 技能配置
        ├── __init__.py      # 技能入口
        ├── tools/           # 工具实现
        │   └── my_tool.py
        └── prompts/         # 提示词模板
            └── system.txt
```

**添加新技能包步骤:**

1. 创建 `skill.yaml` 配置文件
2. 实现工具类 (继承 `Tool` 基类)
3. 编写系统提示词
4. 放入 `skills/custom/` 目录
5. 系统自动加载

### 7.2 AI 提供商扩展

```python
# integration/ai/custom_provider.py

from core.ai.router import AIProvider

class CustomProvider(AIProvider):
    """自定义 AI 提供商"""
    
    @property
    def name(self) -> str:
        return "custom_llm"
    
    async def chat(self, messages, model, **kwargs):
        # 实现具体的 API 调用
        pass
    
    async def chat_stream(self, messages, model, **kwargs):
        # 实现流式响应
        pass
    
    async def health_check(self) -> bool:
        # 健康检查
        pass

# 注册
ai_router.register_provider("custom_llm", CustomProvider())
```

### 7.3 输出格式扩展

```python
# integration/output/custom_generator.py

from core.output.base import OutputGenerator

class CustomGenerator(OutputGenerator):
    """自定义输出生成器"""
    
    @property
    def format(self) -> str:
        return "custom"
    
    @property
    def mime_type(self) -> str:
        return "application/x-custom"
    
    async def generate(self, data, template=None, **options):
        # 实现生成逻辑
        pass

# 注册
output_registry.register("custom", CustomGenerator())
```

### 7.4 Webhook 扩展

```python
# gateway/adapters/webhook/custom_webhook.py

from gateway.adapters.webhook.base import WebhookAdapter

class CustomWebhookAdapter(WebhookAdapter):
    """自定义 Webhook 适配器"""
    
    @property
    def platform(self) -> str:
        return "custom_platform"
    
    async def verify_signature(self, request) -> bool:
        # 验证签名
        pass
    
    async def parse_message(self, request) -> Message:
        # 解析消息
        pass
    
    async def send_reply(self, user_id, content):
        # 发送回复
        pass

# 注册
webhook_manager.register("custom", CustomWebhookAdapter())
```

---

## 10. 配置系统

### 8.1 配置层级

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           配置优先级 (低 → 高)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   1. 默认配置 (代码内置)                                                 │
│      └── config/defaults.yaml                                           │
│                                                                          │
│   2. 系统配置 (全局)                                                     │
│      └── config/system.yaml                                             │
│                                                                          │
│   3. 数据库配置                                                          │
│      └── MySQL: system_config 表                                        │
│                                                                          │
│   4. 环境变量                                                            │
│      └── AUTO_* 前缀                                                    │
│                                                                          │
│   5. 工作空间配置                                                        │
│      └── workspaces/<name>/.auto/config.yaml                            │
│                                                                          │
│   6. 命令行参数                                                          │
│      └── --config-xxx                                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 配置热更新

```python
# shared/config/manager.py

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config = {}
        self.watchers = []
    
    def get(self, key: str, default=None):
        """获取配置"""
        return self._get_nested(self.config, key, default)
    
    def set(self, key: str, value):
        """设置配置"""
        self._set_nested(self.config, key, value)
        self._notify_watchers(key, value)
    
    def watch(self, key: str, callback):
        """监听配置变化"""
        self.watchers.append((key, callback))
    
    def reload(self):
        """重新加载配置"""
        pass
```

---

## 11. 安全设计

### 9.1 安全架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           安全层级                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      接入安全                                    │   │
│   │  - API Key 认证                                                 │   │
│   │  - 请求签名验证 (Webhook)                                       │   │
│   │  - 限流保护                                                      │   │
│   │  - IP 白名单                                                     │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      数据安全                                    │   │
│   │  - API Key 加密存储 (AES-256)                                   │   │
│   │  - 敏感数据脱敏                                                  │   │
│   │  - 传输加密 (HTTPS)                                             │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      操作安全                                    │   │
│   │  - 危险操作确认机制                                              │   │
│   │  - 操作审计日志                                                  │   │
│   │  - 工具执行沙箱                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      权限控制                                    │   │
│   │  - API Key 权限范围                                             │   │
│   │  - 工作空间隔离                                                  │   │
│   │  - 技能包权限控制                                                │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 工具执行沙箱

```python
# core/task/sandbox.py

class ToolSandbox:
    """工具执行沙箱"""
    
    # 权限级别
    PERMISSION_LEVELS = {
        "read": ["list_files", "read_file", "db_query"],
        "write": ["create_file", "update_file", "db_insert"],
        "execute": ["run_command", "docker_exec"],
        "dangerous": ["delete_file", "db_drop", "system_command"]
    }
    
    async def execute(
        self, 
        tool: Tool, 
        params: dict,
        permissions: list[str]
    ) -> ToolResult:
        """在沙箱中执行工具"""
        
        # 检查权限
        if not self._check_permission(tool, permissions):
            raise PermissionDenied(f"Tool {tool.name} requires higher permission")
        
        # 危险操作需要确认
        if tool.requires_confirmation:
            if not params.get("confirmed"):
                return ToolResult(
                    status="pending_confirmation",
                    preview=tool.preview(params)
                )
        
        # 执行工具
        try:
            result = await tool.execute(**params)
            self._log_execution(tool, params, result)
            return result
        except Exception as e:
            self._log_error(tool, params, e)
            raise
```

---

## 12. 监控与可观测性

### 10.1 监控架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          可观测性设计                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐          │
│   │     Metrics     │ │      Logs       │ │     Traces      │          │
│   │     (指标)      │ │     (日志)      │ │     (追踪)      │          │
│   └────────┬────────┘ └────────┬────────┘ └────────┬────────┘          │
│            │                   │                   │                    │
│            ▼                   ▼                   ▼                    │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     Observability Layer                          │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│            │                   │                   │                    │
│            ▼                   ▼                   ▼                    │
│   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐          │
│   │   Prometheus    │ │   ELK / Loki    │ │     Jaeger      │          │
│   └─────────────────┘ └─────────────────┘ └─────────────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 关键指标

```yaml
# 系统指标
metrics:
  # API 指标
  - api_request_total           # 请求总数
  - api_request_duration        # 请求耗时
  - api_error_rate              # 错误率
  
  # AI 指标
  - ai_request_total            # AI 调用次数
  - ai_token_usage              # Token 使用量
  - ai_response_time            # AI 响应时间
  - ai_error_rate               # AI 错误率
  
  # 任务指标
  - task_queue_length           # 队列长度
  - task_processing_time        # 处理时间
  - task_success_rate           # 成功率
  
  # 资源指标
  - memory_usage                # 内存使用
  - cpu_usage                   # CPU 使用
  - db_connections              # 数据库连接数
```

---

## 13. 部署架构

### 11.1 单机部署

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          单机部署架构                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                        Docker Compose                            │   │
│   │                                                                  │   │
│   │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │   │
│   │   │ Backend │ │  Web    │ │  MySQL  │ │  Redis  │              │   │
│   │   │  :8000  │ │  :3000  │ │  :3306  │ │  :6379  │              │   │
│   │   └─────────┘ └─────────┘ └─────────┘ └─────────┘              │   │
│   │                                                                  │   │
│   │   ┌─────────┐ ┌─────────┐                                       │   │
│   │   │ Celery  │ │ Celery  │                                       │   │
│   │   │ Worker  │ │  Beat   │                                       │   │
│   │   └─────────┘ └─────────┘                                       │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.2 分布式部署

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         分布式部署架构                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                        Load Balancer                             │   │
│   │                         (Nginx/Traefik)                          │   │
│   └────────────────────────────┬────────────────────────────────────┘   │
│                                │                                        │
│   ┌────────────────────────────┼────────────────────────────────────┐   │
│   │                            │                                    │   │
│   │   ┌─────────┐ ┌─────────┐ ┌─────────┐                          │   │
│   │   │ Backend │ │ Backend │ │ Backend │  (可水平扩展)            │   │
│   │   │  Pod 1  │ │  Pod 2  │ │  Pod N  │                          │   │
│   │   └─────────┘ └─────────┘ └─────────┘                          │   │
│   │                                                                  │   │
│   │   ┌─────────────────────────────────────────────────────────┐   │   │
│   │   │                    Worker Pods                          │   │   │
│   │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐                   │   │   │
│   │   │  │ Worker 1│ │ Worker 2│ │ Worker N│  (可水平扩展)     │   │   │
│   │   │  └─────────┘ └─────────┘ └─────────┘                   │   │   │
│   │   └─────────────────────────────────────────────────────────┘   │   │
│   │                                                                  │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Managed Services                            │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │   │
│   │  │  RDS    │ │  Redis  │ │   OSS   │ │ Vector  │              │   │
│   │  │ (MySQL) │ │ Cluster │ │(Storage)│ │   DB    │              │   │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘              │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 14. 技术选型总结

| 模块 | 选型 | 备选 | 说明 |
|------|------|------|------|
| **后端框架** | FastAPI | Flask, Django | 异步支持好，自动文档 |
| **任务队列** | Celery + Redis | RQ, Dramatiq | 成熟稳定 |
| **数据库** | MySQL 8.0 | PostgreSQL | 通用性强 |
| **缓存** | Redis | Memcached | 功能丰富 |
| **向量数据库** | ChromaDB | Milvus, Pinecone | 轻量易用 |
| **AI 集成** | LiteLLM | 自实现 | 多提供商支持 |
| **前端框架** | Next.js 14 | Vue, Svelte | React 生态 |
| **CLI 框架** | Typer | Click, Argparse | 类型提示好 |
| **容器化** | Docker Compose | K8s | 简单部署 |

---

## 15. 后续扩展预留

### 13.1 未来可能的扩展方向

| 方向 | 说明 |
|------|------|
| **多租户** | 支持多用户/团队 |
| **插件市场** | 技能包分享和安装 |
| **工作流引擎** | 可视化编排复杂流程 |
| **数据分析** | 使用统计和洞察 |
| **移动端** | iOS/Android App |
| **语音交互** | 语音输入/输出 |
| **Agent 协作** | 多 Agent 协同工作 |

### 13.2 接口预留

所有核心模块都预留了扩展接口，遵循开闭原则。

---

**文档更新记录**

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2024-01-16 | 初版架构设计 |
