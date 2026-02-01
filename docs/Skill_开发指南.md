# 技能包开发指南

**版本**: v1.0  
**日期**: 2024-01-16

---

## 1. 概述

技能包（Skill）是 AI 个人助手的核心扩展机制，每个技能包包含一组相关的工具（Tools），用于完成特定领域的任务。

### 1.1 技能包结构

```
skills/
└── my_skill/                    # 技能包目录
    ├── skill.yaml              # 技能配置文件 (必须)
    ├── __init__.py             # Python 包初始化
    ├── tools/                  # 工具目录
    │   ├── __init__.py
    │   ├── tool_a.py           # 工具实现
    │   └── tool_b.py
    ├── prompts/                # 提示词模板 (可选)
    │   └── main.md
    ├── templates/              # 输出模板 (可选)
    │   └── report.xlsx
    └── tests/                  # 测试用例 (可选)
        └── test_tools.py
```

---

## 2. 技能配置文件 (skill.yaml)

### 2.1 完整配置示例

```yaml
# skill.yaml - 技能包配置文件

# 基本信息
name: file_manager                  # 技能标识 (唯一，英文下划线)
display_name: 文件管理              # 显示名称
version: "1.0.0"                    # 版本号
description: |
  文件和文件夹管理技能，支持文件整理、搜索、批量操作等功能。
  适用于桌面整理、文件归档等场景。

# 技能分类
category: productivity              # 分类: productivity, developer, finance, etc.
tags:                              # 标签 (用于搜索)
  - file
  - organize
  - desktop

# 适用角色 (可选，为空表示所有角色可用)
roles:
  - general
  - developer

# 依赖配置
dependencies:
  python:                          # Python 依赖
    - pathlib
    - shutil
  system:                          # 系统依赖
    - fd                           # 可选的系统命令
  skills:                          # 依赖其他技能
    - base_tools

# 工具列表
tools:
  - name: list_directory
    description: 列出目录内容
    module: tools.list_dir         # Python 模块路径
    function: list_directory       # 函数名
    dangerous: false               # 是否危险操作
    parameters:
      - name: path
        type: string
        description: 目录路径
        required: true
        default: "."
      - name: recursive
        type: boolean
        description: 是否递归列出
        required: false
        default: false
      - name: pattern
        type: string
        description: 文件名匹配模式
        required: false

  - name: move_files
    description: 批量移动文件
    module: tools.file_ops
    function: move_files
    dangerous: true                # 危险操作需要确认
    confirm_message: "即将移动 {count} 个文件，确认执行？"
    parameters:
      - name: files
        type: array
        items:
          type: string
        description: 文件路径列表
        required: true
      - name: destination
        type: string
        description: 目标目录
        required: true

  - name: organize_desktop
    description: 整理桌面文件
    module: tools.organize
    function: organize_desktop
    dangerous: true
    parameters:
      - name: rules
        type: object
        description: 整理规则
        properties:
          images:
            type: string
            description: 图片存放目录
          documents:
            type: string
            description: 文档存放目录
          downloads:
            type: string
            description: 下载文件存放目录

# 权限配置
permissions:
  file_system:
    read: true
    write: true
    delete: false                  # 不允许删除
  network: false
  shell: false

# 安全限制
security:
  allowed_paths:                   # 允许操作的路径
    - "~/Desktop"
    - "~/Documents"
    - "~/Downloads"
  blocked_paths:                   # 禁止操作的路径
    - "/"
    - "/etc"
    - "/usr"
    - "~/.ssh"

# 提示词配置
prompts:
  system: prompts/system.md        # 系统提示词
  user: prompts/user.md            # 用户提示词模板

# 输出配置
outputs:
  - type: text                     # 文本输出
  - type: table                    # 表格输出
  - type: file                     # 文件输出
    formats:
      - json
      - csv
```

### 2.2 参数类型定义

| 类型 | 说明 | 示例 |
|------|------|------|
| `string` | 字符串 | `"hello"` |
| `number` | 数字 | `42`, `3.14` |
| `integer` | 整数 | `42` |
| `boolean` | 布尔值 | `true`, `false` |
| `array` | 数组 | `["a", "b"]` |
| `object` | 对象 | `{"key": "value"}` |
| `file` | 文件路径 | `"/path/to/file.txt"` |
| `directory` | 目录路径 | `"/path/to/dir"` |

---

## 3. 工具函数实现

### 3.1 基础工具函数

```python
# tools/list_dir.py

from typing import Optional, List
from pathlib import Path
from dataclasses import dataclass

from auto.core.tool import Tool, ToolResult, ToolContext


@dataclass
class FileInfo:
    """文件信息"""
    name: str
    path: str
    size: int
    is_dir: bool
    modified: str


def list_directory(
    ctx: ToolContext,
    path: str = ".",
    recursive: bool = False,
    pattern: Optional[str] = None
) -> ToolResult:
    """
    列出目录内容
    
    Args:
        ctx: 工具上下文，包含工作空间信息、权限等
        path: 目录路径
        recursive: 是否递归
        pattern: 文件名匹配模式
    
    Returns:
        ToolResult: 包含文件列表的结果
    """
    target_path = Path(path).expanduser().resolve()
    
    # 安全检查
    if not ctx.security.is_allowed_path(target_path):
        return ToolResult.error(f"路径 {path} 不在允许范围内")
    
    if not target_path.exists():
        return ToolResult.error(f"路径 {path} 不存在")
    
    if not target_path.is_dir():
        return ToolResult.error(f"{path} 不是目录")
    
    # 获取文件列表
    files: List[FileInfo] = []
    
    if recursive:
        iterator = target_path.rglob(pattern or "*")
    else:
        iterator = target_path.glob(pattern or "*")
    
    for item in iterator:
        try:
            stat = item.stat()
            files.append(FileInfo(
                name=item.name,
                path=str(item),
                size=stat.st_size,
                is_dir=item.is_dir(),
                modified=stat.st_mtime
            ))
        except PermissionError:
            continue
    
    return ToolResult.success(
        data=files,
        message=f"找到 {len(files)} 个文件/文件夹"
    )
```

### 3.2 危险操作工具

```python
# tools/file_ops.py

from typing import List
from pathlib import Path
import shutil

from auto.core.tool import Tool, ToolResult, ToolContext, DangerousOperation


@DangerousOperation(
    message="即将移动 {count} 个文件到 {destination}",
    require_confirm=True
)
def move_files(
    ctx: ToolContext,
    files: List[str],
    destination: str
) -> ToolResult:
    """
    批量移动文件
    
    Args:
        ctx: 工具上下文
        files: 文件路径列表
        destination: 目标目录
    
    Returns:
        ToolResult: 操作结果
    """
    dest_path = Path(destination).expanduser().resolve()
    
    # 安全检查
    if not ctx.security.is_allowed_path(dest_path):
        return ToolResult.error(f"目标路径 {destination} 不在允许范围内")
    
    # 创建目标目录
    dest_path.mkdir(parents=True, exist_ok=True)
    
    moved = []
    errors = []
    
    for file_path in files:
        src = Path(file_path).expanduser().resolve()
        
        # 安全检查
        if not ctx.security.is_allowed_path(src):
            errors.append(f"{file_path}: 不在允许范围内")
            continue
        
        if not src.exists():
            errors.append(f"{file_path}: 文件不存在")
            continue
        
        try:
            dest_file = dest_path / src.name
            shutil.move(str(src), str(dest_file))
            moved.append({
                "from": str(src),
                "to": str(dest_file)
            })
        except Exception as e:
            errors.append(f"{file_path}: {str(e)}")
    
    return ToolResult.success(
        data={
            "moved": moved,
            "errors": errors
        },
        message=f"成功移动 {len(moved)} 个文件，{len(errors)} 个失败"
    )
```

### 3.3 异步工具

```python
# tools/async_tool.py

import asyncio
from auto.core.tool import ToolResult, ToolContext, async_tool


@async_tool
async def download_file(
    ctx: ToolContext,
    url: str,
    destination: str
) -> ToolResult:
    """
    异步下载文件
    """
    import aiohttp
    
    dest_path = Path(destination).expanduser().resolve()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return ToolResult.error(f"下载失败: HTTP {response.status}")
                
                content = await response.read()
                
                with open(dest_path, 'wb') as f:
                    f.write(content)
        
        return ToolResult.success(
            data={"path": str(dest_path), "size": len(content)},
            message=f"下载完成: {dest_path}"
        )
    except Exception as e:
        return ToolResult.error(f"下载失败: {str(e)}")
```

---

## 4. 工具上下文 (ToolContext)

### 4.1 上下文结构

```python
@dataclass
class ToolContext:
    """工具执行上下文"""
    
    # 工作空间信息
    workspace: Workspace
    workspace_path: Path
    
    # 用户信息
    user_id: str
    role: str
    
    # 会话信息
    conversation_id: str
    message_id: str
    
    # 安全检查器
    security: SecurityChecker
    
    # 配置
    config: Dict[str, Any]
    
    # 全局记忆 (只读)
    memory: List[Memory]
    
    # 日志记录器
    logger: Logger
    
    # 进度报告
    progress: ProgressReporter
    
    def report_progress(self, current: int, total: int, message: str = ""):
        """报告进度"""
        self.progress.update(current, total, message)
    
    def log(self, level: str, message: str, **kwargs):
        """记录日志"""
        self.logger.log(level, message, **kwargs)
```

### 4.2 安全检查器

```python
class SecurityChecker:
    """安全检查器"""
    
    def is_allowed_path(self, path: Path) -> bool:
        """检查路径是否在允许范围内"""
        ...
    
    def is_dangerous_operation(self, operation: str) -> bool:
        """检查是否是危险操作"""
        ...
    
    def check_permission(self, permission: str) -> bool:
        """检查权限"""
        ...
```

---

## 5. 返回结果 (ToolResult)

### 5.1 结果结构

```python
@dataclass
class ToolResult:
    """工具执行结果"""
    
    success: bool              # 是否成功
    data: Any = None          # 返回数据
    message: str = ""         # 消息
    error: str = None         # 错误信息
    
    # 输出建议
    output_type: str = "text" # text, table, file, chart
    output_format: str = None # json, csv, xlsx, etc.
    
    @classmethod
    def success(cls, data=None, message="", output_type="text"):
        return cls(success=True, data=data, message=message, output_type=output_type)
    
    @classmethod
    def error(cls, error: str):
        return cls(success=False, error=error)
    
    @classmethod
    def table(cls, data: List[Dict], message=""):
        """返回表格数据"""
        return cls(success=True, data=data, message=message, output_type="table")
    
    @classmethod
    def file(cls, path: str, message=""):
        """返回文件"""
        return cls(success=True, data={"path": path}, message=message, output_type="file")
```

### 5.2 输出类型

| 类型 | 说明 | 数据格式 |
|------|------|----------|
| `text` | 纯文本 | `str` |
| `table` | 表格 | `List[Dict]` |
| `file` | 文件 | `{"path": str}` |
| `chart` | 图表 | `{"type": str, "data": dict}` |
| `image` | 图片 | `{"path": str}` or `{"base64": str}` |
| `code` | 代码 | `{"language": str, "content": str}` |

---

## 6. 提示词模板

### 6.1 系统提示词

```markdown
<!-- prompts/system.md -->

你是一个文件管理助手，可以帮助用户整理和管理文件。

## 可用工具

{{#each tools}}
### {{name}}
{{description}}

参数:
{{#each parameters}}
- `{{name}}` ({{type}}{{#if required}}, 必需{{/if}}): {{description}}
{{/each}}

{{/each}}

## 安全规则

- 只能操作以下目录: {{allowed_paths}}
- 禁止操作: {{blocked_paths}}
- 删除操作需要用户确认

## 工作流程

1. 分析用户需求
2. 选择合适的工具
3. 执行操作前显示预览
4. 危险操作需要用户确认
5. 报告执行结果
```

### 6.2 用户提示词

```markdown
<!-- prompts/user.md -->

用户请求: {{user_input}}

当前工作空间: {{workspace.name}}
当前目录: {{workspace.path}}

{{#if memory}}
相关记忆:
{{#each memory}}
- {{this.content}}
{{/each}}
{{/if}}
```

---

## 7. 测试

### 7.1 单元测试

```python
# tests/test_tools.py

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from skills.file_manager.tools.list_dir import list_directory
from auto.core.tool import ToolContext, ToolResult


@pytest.fixture
def mock_context():
    """创建模拟上下文"""
    ctx = MagicMock(spec=ToolContext)
    ctx.security.is_allowed_path.return_value = True
    return ctx


class TestListDirectory:
    
    def test_list_current_directory(self, mock_context, tmp_path):
        """测试列出当前目录"""
        # 创建测试文件
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        (tmp_path / "subdir").mkdir()
        
        result = list_directory(mock_context, str(tmp_path))
        
        assert result.success
        assert len(result.data) == 3
    
    def test_list_with_pattern(self, mock_context, tmp_path):
        """测试模式匹配"""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.py").touch()
        
        result = list_directory(mock_context, str(tmp_path), pattern="*.txt")
        
        assert result.success
        assert len(result.data) == 1
        assert result.data[0].name == "file1.txt"
    
    def test_blocked_path(self, mock_context):
        """测试禁止路径"""
        mock_context.security.is_allowed_path.return_value = False
        
        result = list_directory(mock_context, "/etc")
        
        assert not result.success
        assert "不在允许范围内" in result.error
```

### 7.2 集成测试

```python
# tests/test_integration.py

import pytest
from auto.core.skill_engine import SkillEngine


class TestFileManagerSkill:
    
    @pytest.fixture
    def skill_engine(self):
        engine = SkillEngine()
        engine.load_skill("file_manager")
        return engine
    
    def test_organize_desktop_workflow(self, skill_engine, tmp_path):
        """测试桌面整理工作流"""
        # 创建测试文件
        desktop = tmp_path / "Desktop"
        desktop.mkdir()
        (desktop / "screenshot1.png").touch()
        (desktop / "document.pdf").touch()
        
        # 执行整理
        result = skill_engine.run_tool(
            "file_manager.organize_desktop",
            path=str(desktop),
            rules={
                "images": str(tmp_path / "Pictures"),
                "documents": str(tmp_path / "Documents")
            }
        )
        
        assert result.success
        assert (tmp_path / "Pictures" / "screenshot1.png").exists()
        assert (tmp_path / "Documents" / "document.pdf").exists()
```

---

## 8. 发布与分发

### 8.1 技能包打包

```bash
# 打包技能包
auto skill pack file_manager

# 输出: file_manager-1.0.0.zip
```

### 8.2 技能包结构

```
file_manager-1.0.0.zip
├── skill.yaml
├── tools/
├── prompts/
├── templates/
├── README.md
└── CHANGELOG.md
```

### 8.3 安装技能包

```bash
# 从本地安装
auto skill install ./file_manager-1.0.0.zip

# 从远程仓库安装 (未来支持)
auto skill install file_manager

# 卸载
auto skill uninstall file_manager
```

---

## 9. 最佳实践

### 9.1 设计原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个工具只做一件事 |
| **安全优先** | 危险操作必须确认 |
| **错误处理** | 提供清晰的错误信息 |
| **可测试性** | 工具函数应易于测试 |
| **文档完善** | 参数和返回值要有清晰说明 |

### 9.2 命名规范

```yaml
# 技能名: 小写下划线
name: file_manager

# 工具名: 小写下划线，动词开头
tools:
  - name: list_directory    # ✓ 
  - name: move_files        # ✓
  - name: FileList          # ✗ 不要用驼峰
  - name: files             # ✗ 不要用名词

# 参数名: 小写下划线
parameters:
  - name: file_path         # ✓
  - name: filePath          # ✗
```

### 9.3 安全规范

```python
# ✓ 正确: 使用上下文安全检查
def my_tool(ctx: ToolContext, path: str):
    if not ctx.security.is_allowed_path(path):
        return ToolResult.error("路径不允许")

# ✗ 错误: 不检查直接操作
def my_tool(ctx: ToolContext, path: str):
    os.remove(path)  # 危险!
```

### 9.4 错误处理

```python
# ✓ 正确: 返回清晰的错误信息
def my_tool(ctx: ToolContext, path: str):
    if not Path(path).exists():
        return ToolResult.error(f"文件不存在: {path}")
    
    try:
        # 操作
        ...
    except PermissionError:
        return ToolResult.error(f"没有权限访问: {path}")
    except Exception as e:
        ctx.log("error", f"操作失败: {e}")
        return ToolResult.error(f"操作失败: {str(e)}")

# ✗ 错误: 抛出异常或返回模糊信息
def my_tool(ctx: ToolContext, path: str):
    return open(path).read()  # 可能抛出异常
```

---

## 10. 示例技能包

### 10.1 DevOps 技能包

```yaml
# skills/devops/skill.yaml
name: devops
display_name: DevOps 运维
version: "1.0.0"
description: Docker、数据库、Redis 运维操作

tools:
  - name: docker_ps
    description: 列出 Docker 容器
    module: tools.docker
    function: list_containers
    dangerous: false
    
  - name: docker_restart
    description: 重启 Docker 容器
    module: tools.docker
    function: restart_container
    dangerous: true
    confirm_message: "确认重启容器 {container_name}？"
    parameters:
      - name: container_name
        type: string
        required: true

  - name: db_query
    description: 执行数据库查询
    module: tools.database
    function: execute_query
    dangerous: true
    parameters:
      - name: query
        type: string
        required: true
      - name: database
        type: string
        required: false

permissions:
  shell: true
  network: true

security:
  blocked_commands:
    - "rm -rf"
    - "DROP DATABASE"
    - "DELETE FROM"
```

### 10.2 财务技能包

```yaml
# skills/finance/skill.yaml
name: finance
display_name: 财务助手
version: "1.0.0"
description: Excel 处理、报表生成

tools:
  - name: read_excel
    description: 读取 Excel 文件
    module: tools.excel
    function: read_excel
    parameters:
      - name: file_path
        type: file
        required: true
      - name: sheet_name
        type: string
        required: false

  - name: create_report
    description: 生成财务报表
    module: tools.report
    function: create_report
    parameters:
      - name: data
        type: object
        required: true
      - name: template
        type: string
        required: false
        default: "default"
      - name: output_path
        type: string
        required: true
```

### 10.3 A股调研技能包

```yaml
# skills/stock_research/skill.yaml
name: stock_research
display_name: A股市场调研
version: "1.0.0"
description: |
  A股市场研究分析工具，支持：
  - 实时行情查询
  - 财报数据分析
  - 行业板块研究
  - 技术指标计算
  - 调研报告生成

category: finance
tags:
  - stock
  - A股
  - 投资
  - 财报
  - 调研

# 角色适用
roles:
  - finance
  - analyst
  - investor

# 依赖
dependencies:
  python:
    - akshare>=1.10     # A股数据接口
    - pandas>=2.0
    - matplotlib>=3.7
    - mplfinance>=0.12  # K线图
    - openpyxl>=3.0

# 工具列表
tools:
  # ═══════════════════════════════════════════════════════════════════════
  #                          行情数据
  # ═══════════════════════════════════════════════════════════════════════
  
  - name: get_stock_quote
    description: 获取股票实时行情 (价格、涨跌幅、成交量等)
    module: tools.quote
    function: get_realtime_quote
    parameters:
      - name: symbol
        type: string
        description: 股票代码 (如 600519, 000001)
        required: true
      - name: market
        type: string
        description: 市场 (sh=上海, sz=深圳)
        required: false
        default: auto  # 自动识别

  - name: get_stock_history
    description: 获取股票历史行情数据
    module: tools.quote
    function: get_history
    parameters:
      - name: symbol
        type: string
        required: true
      - name: start_date
        type: string
        description: 开始日期 (YYYY-MM-DD)
        required: false
      - name: end_date
        type: string
        description: 结束日期 (YYYY-MM-DD)
        required: false
      - name: period
        type: string
        description: 周期 (daily/weekly/monthly)
        default: daily

  - name: get_stock_kline
    description: 生成K线图
    module: tools.chart
    function: draw_kline
    parameters:
      - name: symbol
        type: string
        required: true
      - name: days
        type: integer
        default: 60
      - name: indicators
        type: array
        items:
          type: string
        description: 技术指标 (MA/MACD/KDJ/RSI/BOLL)
        default: ["MA", "MACD"]

  # ═══════════════════════════════════════════════════════════════════════
  #                          财务数据
  # ═══════════════════════════════════════════════════════════════════════
  
  - name: get_financial_report
    description: 获取财务报表数据 (资产负债表/利润表/现金流量表)
    module: tools.financial
    function: get_report
    parameters:
      - name: symbol
        type: string
        required: true
      - name: report_type
        type: string
        description: 报表类型 (balance=资产负债表, income=利润表, cashflow=现金流量表)
        required: true
      - name: period
        type: string
        description: 报告期 (如 2024Q3, 2024H1, 2024)
        required: false

  - name: get_financial_indicators
    description: 获取财务指标 (ROE/ROA/毛利率/净利率等)
    module: tools.financial
    function: get_indicators
    parameters:
      - name: symbol
        type: string
        required: true
      - name: indicators
        type: array
        items:
          type: string
        description: 指标列表
        default: ["ROE", "ROA", "gross_margin", "net_margin", "debt_ratio"]

  - name: analyze_financial_health
    description: 分析企业财务健康度 (综合评分)
    module: tools.financial
    function: analyze_health
    parameters:
      - name: symbol
        type: string
        required: true

  # ═══════════════════════════════════════════════════════════════════════
  #                          行业板块
  # ═══════════════════════════════════════════════════════════════════════
  
  - name: get_industry_stocks
    description: 获取行业板块成分股
    module: tools.industry
    function: get_stocks
    parameters:
      - name: industry
        type: string
        description: 行业名称 (如 白酒, 新能源, 芯片)
        required: true

  - name: get_industry_ranking
    description: 获取行业涨跌幅排行
    module: tools.industry
    function: get_ranking
    parameters:
      - name: top_n
        type: integer
        default: 10

  - name: compare_industry_peers
    description: 同行业公司对比分析
    module: tools.industry
    function: compare_peers
    parameters:
      - name: symbol
        type: string
        required: true
      - name: metrics
        type: array
        items:
          type: string
        default: ["PE", "PB", "ROE", "revenue_growth", "profit_growth"]

  # ═══════════════════════════════════════════════════════════════════════
  #                          研究报告
  # ═══════════════════════════════════════════════════════════════════════
  
  - name: search_research_reports
    description: 搜索券商研报
    module: tools.research
    function: search_reports
    parameters:
      - name: keyword
        type: string
        description: 关键词 (股票名称/代码/行业)
        required: true
      - name: limit
        type: integer
        default: 10

  - name: get_analyst_ratings
    description: 获取分析师评级
    module: tools.research
    function: get_ratings
    parameters:
      - name: symbol
        type: string
        required: true

  # ═══════════════════════════════════════════════════════════════════════
  #                          资金流向
  # ═══════════════════════════════════════════════════════════════════════
  
  - name: get_money_flow
    description: 获取资金流向数据 (主力/散户/北向资金)
    module: tools.moneyflow
    function: get_flow
    parameters:
      - name: symbol
        type: string
        required: true
      - name: days
        type: integer
        default: 10

  - name: get_north_flow
    description: 获取北向资金流入数据
    module: tools.moneyflow
    function: get_north_flow
    parameters:
      - name: days
        type: integer
        default: 30

  # ═══════════════════════════════════════════════════════════════════════
  #                          报告生成
  # ═══════════════════════════════════════════════════════════════════════
  
  - name: generate_stock_report
    description: 生成个股调研报告
    module: tools.report
    function: generate_stock_report
    parameters:
      - name: symbol
        type: string
        required: true
      - name: output_format
        type: string
        description: 输出格式 (md/pdf/xlsx)
        default: md
      - name: include_sections
        type: array
        items:
          type: string
        description: 包含章节
        default: ["基本信息", "行情走势", "财务分析", "行业对比", "资金流向", "投资建议"]

  - name: generate_industry_report
    description: 生成行业研究报告
    module: tools.report
    function: generate_industry_report
    parameters:
      - name: industry
        type: string
        required: true
      - name: output_format
        type: string
        default: md

  - name: generate_portfolio_report
    description: 生成投资组合分析报告
    module: tools.report
    function: generate_portfolio_report
    parameters:
      - name: symbols
        type: array
        items:
          type: string
        description: 股票代码列表
        required: true

# 权限配置
permissions:
  network: true   # 需要访问数据接口
  file_system:
    read: true
    write: true   # 生成报告

# 系统提示词
system_prompt: |
  你是一个专业的A股市场分析师，擅长：
  - 个股基本面分析
  - 财务报表解读
  - 行业趋势研究
  - 技术指标分析
  - 投资价值评估
  
  分析时请注意：
  1. 数据来源标注清楚
  2. 分析逻辑清晰
  3. 风险提示完整
  4. 不做具体买卖建议，只提供分析参考
  
  免责声明：所有分析仅供参考，不构成投资建议。

# 输出格式
output_formats:
  - md      # Markdown 报告
  - xlsx    # Excel 数据表
  - pdf     # PDF 报告
  - png     # 图表
```

**工具实现示例:**

```python
# tools/quote.py

import akshare as ak
from datetime import datetime, timedelta
from auto.core.tool import ToolResult, ToolContext


def get_realtime_quote(ctx: ToolContext, symbol: str, market: str = "auto") -> ToolResult:
    """获取股票实时行情"""
    try:
        # 自动识别市场
        if market == "auto":
            market = "sh" if symbol.startswith("6") else "sz"
        
        full_symbol = f"{market}{symbol}"
        
        # 获取实时行情
        df = ak.stock_zh_a_spot_em()
        stock_data = df[df['代码'] == symbol]
        
        if stock_data.empty:
            return ToolResult.error(f"未找到股票: {symbol}")
        
        data = stock_data.iloc[0].to_dict()
        
        return ToolResult.success(
            data={
                "symbol": symbol,
                "name": data.get("名称"),
                "price": data.get("最新价"),
                "change": data.get("涨跌额"),
                "change_pct": data.get("涨跌幅"),
                "volume": data.get("成交量"),
                "amount": data.get("成交额"),
                "high": data.get("最高"),
                "low": data.get("最低"),
                "open": data.get("今开"),
                "prev_close": data.get("昨收"),
                "pe": data.get("市盈率-动态"),
                "pb": data.get("市净率"),
                "market_cap": data.get("总市值"),
                "update_time": datetime.now().isoformat()
            },
            output_type="table"
        )
    except Exception as e:
        ctx.log("error", f"获取行情失败: {e}")
        return ToolResult.error(f"获取行情失败: {str(e)}")


def get_history(
    ctx: ToolContext,
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    period: str = "daily"
) -> ToolResult:
    """获取历史行情"""
    try:
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        
        # 转换日期格式
        start_date = start_date.replace("-", "")
        end_date = end_date.replace("-", "")
        
        # 获取历史数据
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"  # 前复权
        )
        
        if df.empty:
            return ToolResult.error(f"未获取到历史数据: {symbol}")
        
        # 转换为列表
        data = df.to_dict(orient="records")
        
        return ToolResult.success(
            data={
                "symbol": symbol,
                "period": period,
                "count": len(data),
                "records": data[-30:]  # 最近30条
            },
            message=f"获取 {symbol} 历史数据 {len(data)} 条"
        )
    except Exception as e:
        ctx.log("error", f"获取历史数据失败: {e}")
        return ToolResult.error(f"获取历史数据失败: {str(e)}")
```

```python
# tools/report.py

from datetime import datetime
from pathlib import Path
from auto.core.tool import ToolResult, ToolContext


async def generate_stock_report(
    ctx: ToolContext,
    symbol: str,
    output_format: str = "md",
    include_sections: list = None
) -> ToolResult:
    """生成个股调研报告"""
    
    if include_sections is None:
        include_sections = ["基本信息", "行情走势", "财务分析", "行业对比", "资金流向", "投资建议"]
    
    # 1. 收集数据
    ctx.report_progress(1, 6, "获取基本信息...")
    quote = await ctx.call_tool("stock_research.get_stock_quote", symbol=symbol)
    
    ctx.report_progress(2, 6, "获取财务数据...")
    financial = await ctx.call_tool("stock_research.get_financial_indicators", symbol=symbol)
    
    ctx.report_progress(3, 6, "获取行业对比...")
    peers = await ctx.call_tool("stock_research.compare_industry_peers", symbol=symbol)
    
    ctx.report_progress(4, 6, "获取资金流向...")
    money_flow = await ctx.call_tool("stock_research.get_money_flow", symbol=symbol)
    
    ctx.report_progress(5, 6, "生成K线图...")
    kline = await ctx.call_tool("stock_research.get_stock_kline", symbol=symbol, days=60)
    
    # 2. 生成报告
    ctx.report_progress(6, 6, "生成报告...")
    
    report_content = f"""# {quote.data['name']}({symbol}) 调研报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**数据来源**: A股公开数据

---

## 一、基本信息

| 指标 | 数值 |
|------|------|
| 股票代码 | {symbol} |
| 股票名称 | {quote.data['name']} |
| 最新价格 | {quote.data['price']} 元 |
| 涨跌幅 | {quote.data['change_pct']}% |
| 市盈率(PE) | {quote.data['pe']} |
| 市净率(PB) | {quote.data['pb']} |
| 总市值 | {quote.data['market_cap']} |

## 二、财务分析

{_format_financial_section(financial.data)}

## 三、行业对比

{_format_peers_section(peers.data)}

## 四、资金流向

{_format_money_flow_section(money_flow.data)}

## 五、技术分析

![K线图]({kline.data['chart_path']})

## 六、风险提示

1. 市场风险：股市有风险，投资需谨慎
2. 行业风险：需关注行业政策变化
3. 经营风险：需持续跟踪公司经营情况

---

*免责声明：本报告仅供参考，不构成任何投资建议。*
"""
    
    # 3. 保存报告
    output_dir = ctx.workspace_path / "outputs" / "reports" / "stock"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{symbol}_{datetime.now().strftime('%Y%m%d')}.{output_format}"
    output_path = output_dir / filename
    
    if output_format == "md":
        output_path.write_text(report_content, encoding="utf-8")
    elif output_format == "pdf":
        # 使用 markdown 转 PDF
        await _convert_to_pdf(report_content, output_path)
    
    return ToolResult.file(
        path=str(output_path),
        message=f"调研报告已生成: {output_path}"
    )
```

**CLI 交互示例:**

```bash
$ auto chat --skill stock_research

You> 分析一下贵州茅台

AI> 正在分析贵州茅台(600519)...

📊 获取实时行情...
📈 获取历史数据...
📋 获取财务指标...
🏭 获取行业对比...
💰 获取资金流向...

## 贵州茅台(600519) 快速分析

### 实时行情
| 指标 | 数值 |
|------|------|
| 最新价 | 1680.00 |
| 涨跌幅 | +1.25% |
| 成交额 | 45.6亿 |
| 市盈率 | 28.5 |
| 市净率 | 8.2 |

### 财务亮点
- ROE: 31.2% (优秀)
- 毛利率: 91.5% (极高)
- 净利率: 52.3% (优秀)
- 资产负债率: 18.5% (低)

### 行业对比
贵州茅台在白酒行业中:
- 市值排名: 第1
- ROE 排名: 第1
- 毛利率排名: 第1

### 资金流向 (近5日)
- 主力净流入: +12.5亿
- 北向资金: +8.3亿

是否需要生成完整的调研报告？

You> 是的，生成报告

AI> 📄 正在生成调研报告...

✅ 报告已生成: outputs/reports/stock/600519_20240116.md

You> 对比五粮液和茅台

AI> 正在对比分析...

## 贵州茅台 vs 五粮液 对比

| 指标 | 贵州茅台(600519) | 五粮液(000858) |
|------|------------------|----------------|
| 股价 | 1680.00 | 168.50 |
| 市值 | 2.1万亿 | 6500亿 |
| PE | 28.5 | 22.3 |
| PB | 8.2 | 4.5 |
| ROE | 31.2% | 25.8% |
| 毛利率 | 91.5% | 75.2% |
| 净利率 | 52.3% | 38.5% |
| 营收增速 | 15.2% | 12.8% |
| 净利增速 | 18.5% | 14.2% |

### 分析结论
1. 茅台盈利能力更强 (毛利率、净利率领先)
2. 茅台估值略高 (PE、PB 更高)
3. 五粮液估值更具吸引力
4. 两者都是白酒龙头，长期投资价值高

You> 看看今天白酒板块涨幅排行

AI> 📊 白酒板块今日涨幅排行

| 排名 | 股票 | 代码 | 涨跌幅 | 成交额 |
|------|------|------|--------|--------|
| 1 | 金种子酒 | 600199 | +5.82% | 8.2亿 |
| 2 | 老白干酒 | 600559 | +4.15% | 3.5亿 |
| 3 | 水井坊 | 600779 | +3.28% | 4.1亿 |
| 4 | 舍得酒业 | 600702 | +2.95% | 5.8亿 |
| 5 | 贵州茅台 | 600519 | +1.25% | 45.6亿 |
```

outputs:
  - type: file
    formats: [xlsx, pdf]
```

---

## 附录

### A. 完整类型定义

```python
# auto/core/tool.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum


class ToolStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    module: str
    function: str
    parameters: List[ToolParameter] = field(default_factory=list)
    dangerous: bool = False
    confirm_message: Optional[str] = None


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    output_type: str = "text"
    output_format: Optional[str] = None
    
    # ... 方法实现


class Tool(ABC):
    """工具基类"""
    
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """工具定义"""
        pass
    
    @abstractmethod
    def execute(self, ctx: ToolContext, **kwargs) -> ToolResult:
        """执行工具"""
        pass
```

### B. 配置验证 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "display_name", "version", "description", "tools"],
  "properties": {
    "name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$"
    },
    "display_name": {
      "type": "string"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "tools": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "description", "module", "function"],
        "properties": {
          "name": {"type": "string"},
          "description": {"type": "string"},
          "module": {"type": "string"},
          "function": {"type": "string"},
          "dangerous": {"type": "boolean"},
          "parameters": {
            "type": "array"
          }
        }
      }
    }
  }
}
```

---

## 11. 发布到 Skill 市场

### 11.1 发布流程

```bash
# 1. 验证技能包
auto skill validate ./my-skill

# 2. 打包
auto skill pack ./my-skill
# 输出: my-skill-1.0.0.zip

# 3. 登录 (首次)
auto skill login

# 4. 发布
auto skill publish ./my-skill-1.0.0.zip

# 或一步完成
auto skill publish ./my-skill --version 1.0.0
```

### 11.2 发布配置

```yaml
# skill.yaml 中添加发布信息

# 发布信息
publish:
  # 作者信息
  author: Your Name
  email: your@email.com
  homepage: https://github.com/your/skill
  
  # 许可证
  license: MIT
  
  # 仓库
  repository: https://github.com/your/skill
  
  # 关键词 (用于搜索)
  keywords:
    - excel
    - finance
    - report
  
  # 最低系统版本要求
  min_auto_version: "1.0.0"
  
  # 支持的平台
  platforms:
    - linux
    - darwin
    - win32
  
  # 截图/预览
  screenshots:
    - https://example.com/screenshot1.png
```

### 11.3 版本管理

```bash
# 更新版本
auto skill version patch  # 1.0.0 -> 1.0.1
auto skill version minor  # 1.0.0 -> 1.1.0
auto skill version major  # 1.0.0 -> 2.0.0

# 查看版本历史
auto skill versions my-skill

# 回滚到指定版本
auto skill install my-skill@1.0.0
```

### 11.4 私有仓库

```bash
# 添加私有仓库
auto skill source add company https://skills.mycompany.com/registry --token ${TOKEN}

# 从私有仓库安装
auto skill install company/internal-skill

# 发布到私有仓库
auto skill publish ./my-skill --registry company
```

---

## 12. MCP 服务器开发

除了开发 Skill，你也可以开发 MCP 服务器来扩展系统能力。

### 12.1 MCP vs Skill 选择

| 特性 | Skill | MCP Server |
|------|-------|------------|
| 运行位置 | 主进程内 | 独立进程 |
| 语言 | Python | 任意语言 |
| 通信方式 | 函数调用 | stdio/SSE |
| 隔离性 | 低 | 高 |
| 性能 | 高 | 中 |
| 复用性 | 本系统 | 跨系统 (Cursor, Claude Desktop 等) |

**选择建议:**
- 需要高性能、深度集成 → **Skill**
- 需要跨系统复用、语言无关 → **MCP Server**

### 12.2 创建 MCP 服务器 (Python)

```python
# my_mcp_server.py

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# 创建服务器
server = Server("my-mcp-server")


# 定义工具
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="hello",
            description="Say hello",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name to greet"}
                },
                "required": ["name"]
            }
        )
    ]


# 实现工具
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "hello":
        return [TextContent(
            type="text",
            text=f"Hello, {arguments['name']}!"
        )]
    raise ValueError(f"Unknown tool: {name}")


# 运行服务器
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
```

### 12.3 注册 MCP 服务器

```yaml
# ~/.auto/mcp_servers.yaml

servers:
  - name: my-server
    transport: stdio
    command: python
    args: ["/path/to/my_mcp_server.py"]
    enabled: true
```

```bash
# 或通过 CLI 添加
auto mcp add my-server --transport stdio --command "python /path/to/my_mcp_server.py"

# 测试
auto mcp test my-server

# 查看工具
auto mcp tools my-server
```

### 12.4 在 Skill 中使用 MCP 工具

技能包可以依赖 MCP 服务器提供的工具：

```yaml
# skill.yaml

name: enhanced_file_manager
display_name: 增强文件管理

# 声明依赖的 MCP 服务器
mcp_dependencies:
  - name: filesystem
    package: "@modelcontextprotocol/server-filesystem"
    optional: false

# 工具可以组合 MCP 工具
tools:
  - name: smart_organize
    description: 智能整理文件 (使用 MCP filesystem)
    module: tools.organize
    function: smart_organize
    # 这个工具内部会调用 MCP 的 filesystem 工具
```

```python
# tools/organize.py

async def smart_organize(ctx: ToolContext, path: str):
    """智能整理文件，内部使用 MCP filesystem 工具"""
    
    # 调用 MCP 工具
    files = await ctx.mcp.call_tool(
        server="filesystem",
        tool="list_directory",
        arguments={"path": path}
    )
    
    # 处理文件...
    for file in files:
        # 分析文件类型，移动到合适目录
        ...
    
    return ToolResult.success(message="整理完成")
```

---

## 13. 与外部工具生态集成

### 13.1 支持的外部 Skill 源

| 源 | 说明 | 示例 |
|---|------|------|
| 官方仓库 | auto 官方维护 | `auto skill install official/finance` |
| GitHub | 从 GitHub 仓库安装 | `auto skill install github:user/repo` |
| npm | 从 npm 安装 (Node.js) | `auto skill install npm:skill-name` |
| PyPI | 从 PyPI 安装 (Python) | `auto skill install pypi:skill-name` |
| URL | 从 URL 直接下载 | `auto skill install https://...` |
| 本地 | 从本地路径安装 | `auto skill install ./my-skill` |

### 13.2 支持的 MCP 服务器源

| 源 | 说明 | 示例 |
|---|------|------|
| 官方 | Anthropic 官方 MCP 服务器 | `auto mcp install @modelcontextprotocol/server-*` |
| npm | 从 npm 安装 | `auto mcp install npm:mcp-server-name` |
| 本地 | 本地 MCP 服务器 | `auto mcp add local --command "python server.py"` |
| 远程 | SSE 远程服务器 | `auto mcp add remote --url https://mcp.example.com/sse` |

### 13.3 工具优先级

当多个来源提供同名工具时，按以下优先级：

1. **用户明确指定** - `skill_name.tool_name`
2. **当前激活的 Skill** - 当前角色/会话激活的技能包
3. **内置 Skill** > **外部 Skill** > **MCP 工具**

```bash
# 明确指定来源
auto chat "使用 filesystem.read_file 读取 /etc/hosts"

# 自动选择
auto chat "读取 /etc/hosts"  # 系统自动选择合适的工具
```
