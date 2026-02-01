"""
工作空间提示词管理

借鉴 OpenClaw 的 AGENTS.md / SOUL.md / TOOLS.md 设计
允许用户通过 Markdown 文件自定义 AI 行为
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class WorkspacePrompts:
    """
    工作空间提示词
    
    用于注入到 AI 对话中的自定义内容
    """
    workspace_path: Path
    
    # 核心提示词文件
    agents_content: str = ""  # AGENTS.md - Agent 行为定义
    soul_content: str = ""    # SOUL.md - AI 人格设定
    tools_content: str = ""   # TOOLS.md - 工具使用说明
    
    # 额外的自定义文件
    custom_prompts: Dict[str, str] = field(default_factory=dict)
    
    # 技能提示词
    skill_prompts: List[str] = field(default_factory=list)
    
    @classmethod
    def from_workspace(cls, workspace_path: Path) -> "WorkspacePrompts":
        """
        从工作空间目录加载提示词
        
        Args:
            workspace_path: 工作空间路径
        
        Returns:
            WorkspacePrompts 实例
        """
        instance = cls(workspace_path=workspace_path)
        instance.reload()
        return instance
    
    def reload(self):
        """重新加载所有提示词文件"""
        # 加载核心文件
        self.agents_content = self._read_file("AGENTS.md")
        self.soul_content = self._read_file("SOUL.md")
        self.tools_content = self._read_file("TOOLS.md")
        
        # 加载自定义提示词目录
        prompts_dir = self.workspace_path / "prompts"
        if prompts_dir.exists():
            for file_path in prompts_dir.glob("*.md"):
                name = file_path.stem
                self.custom_prompts[name] = self._read_file(f"prompts/{file_path.name}")
        
        # 加载技能提示词
        self._load_skill_prompts()
    
    def _read_file(self, relative_path: str) -> str:
        """读取工作空间中的文件"""
        file_path = self.workspace_path / relative_path
        if file_path.exists():
            try:
                return file_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"读取文件失败 {file_path}: {e}")
        return ""
    
    def _load_skill_prompts(self):
        """加载技能目录中的 SKILL.md"""
        skills_dir = self.workspace_path / "skills"
        if not skills_dir.exists():
            return
        
        self.skill_prompts = []
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        content = skill_file.read_text(encoding="utf-8")
                        self.skill_prompts.append(content)
                    except Exception as e:
                        logger.warning(f"读取技能文件失败 {skill_file}: {e}")
    
    def build_system_prompt(
        self,
        include_agents: bool = True,
        include_soul: bool = True,
        include_tools: bool = True,
        include_skills: bool = True,
        include_custom: Optional[List[str]] = None,
    ) -> str:
        """
        构建系统提示词
        
        Args:
            include_agents: 是否包含 AGENTS.md
            include_soul: 是否包含 SOUL.md
            include_tools: 是否包含 TOOLS.md
            include_skills: 是否包含技能提示词
            include_custom: 要包含的自定义提示词名称列表
        
        Returns:
            组合后的系统提示词
        """
        parts = []
        
        # SOUL.md 放在最前面（定义人格）
        if include_soul and self.soul_content:
            parts.append(f"# 人格设定\n\n{self.soul_content}")
        
        # AGENTS.md（定义行为）
        if include_agents and self.agents_content:
            parts.append(f"# 行为准则\n\n{self.agents_content}")
        
        # TOOLS.md（工具说明）
        if include_tools and self.tools_content:
            parts.append(f"# 工具使用\n\n{self.tools_content}")
        
        # 技能提示词
        if include_skills and self.skill_prompts:
            skills_section = "# 可用技能\n\n"
            for i, skill_prompt in enumerate(self.skill_prompts, 1):
                skills_section += f"## 技能 {i}\n\n{skill_prompt}\n\n"
            parts.append(skills_section)
        
        # 自定义提示词
        if include_custom:
            for name in include_custom:
                if name in self.custom_prompts:
                    parts.append(f"# {name}\n\n{self.custom_prompts[name]}")
        
        return "\n\n---\n\n".join(parts) if parts else ""
    
    def has_prompts(self) -> bool:
        """检查是否有任何提示词"""
        return bool(
            self.agents_content or 
            self.soul_content or 
            self.tools_content or 
            self.skill_prompts or 
            self.custom_prompts
        )
    
    def get_summary(self) -> dict:
        """获取提示词摘要"""
        return {
            "workspace_path": str(self.workspace_path),
            "has_agents": bool(self.agents_content),
            "has_soul": bool(self.soul_content),
            "has_tools": bool(self.tools_content),
            "skill_count": len(self.skill_prompts),
            "custom_prompts": list(self.custom_prompts.keys()),
            "agents_length": len(self.agents_content),
            "soul_length": len(self.soul_content),
            "tools_length": len(self.tools_content),
        }


# 默认模板
DEFAULT_AGENTS_MD = """# AGENTS.md

## 角色定义

你是一个智能助手，可以帮助用户完成各种任务。

## 行为准则

1. 始终保持礼貌和专业
2. 如果不确定，请先确认
3. 注重效率和准确性
4. 保护用户隐私

## 能力范围

- 代码开发与调试
- 文档编写
- 数据分析
- 任务规划

## 限制

- 不执行可能造成系统损害的操作
- 不泄露敏感信息
- 在执行重要操作前确认
"""

DEFAULT_SOUL_MD = """# SOUL.md

## 人格设定

我是 Auto Bot，一个友好、高效的 AI 助手。

## 沟通风格

- 简洁明了：避免冗长的解释
- 适度幽默：在合适的时候轻松一下
- 专业可靠：提供准确的信息
- 有耐心：不厌其烦地帮助用户

## 价值观

- 帮助用户解决问题是第一优先级
- 诚实面对自己的局限性
- 持续学习和改进
- 尊重用户的时间

## 语言风格

- 使用用户的语言（中文/英文）
- 技术术语配合通俗解释
- 代码注释清晰
"""

DEFAULT_TOOLS_MD = """# TOOLS.md

## 可用工具

### 文件操作

- 读取文件：可以读取工作空间中的文件
- 创建文件：可以创建新文件
- 修改文件：可以修改现有文件

### 代码执行

- Python：可以执行 Python 代码
- Shell：可以执行 Shell 命令（需要确认）

### 网络操作

- 网页搜索：可以搜索网络信息
- API 调用：可以调用配置的 API

## 使用原则

1. 优先使用最简单的工具
2. 执行前说明将要做什么
3. 提供操作结果的反馈
"""


def get_workspace_prompts(workspace_id: str) -> Optional[WorkspacePrompts]:
    """
    获取工作空间的提示词
    
    Args:
        workspace_id: 工作空间 ID
    
    Returns:
        WorkspacePrompts 实例，如果工作空间不存在则返回 None
    """
    from pathlib import Path
    
    # 获取工作空间根目录
    project_root = Path(__file__).parent.parent.parent.parent
    workspaces_root = project_root / "data" / "workspaces"
    
    workspace_path = workspaces_root / workspace_id
    
    if not workspace_path.exists():
        return None
    
    return WorkspacePrompts.from_workspace(workspace_path)


def init_workspace_prompts(workspace_path: Path, force: bool = False):
    """
    初始化工作空间提示词文件
    
    Args:
        workspace_path: 工作空间路径
        force: 是否覆盖现有文件
    """
    files = {
        "AGENTS.md": DEFAULT_AGENTS_MD,
        "SOUL.md": DEFAULT_SOUL_MD,
        "TOOLS.md": DEFAULT_TOOLS_MD,
    }
    
    for filename, content in files.items():
        file_path = workspace_path / filename
        if force or not file_path.exists():
            file_path.write_text(content, encoding="utf-8")
            logger.info(f"创建提示词文件: {file_path}")
    
    # 创建 skills 和 prompts 目录
    (workspace_path / "skills").mkdir(exist_ok=True)
    (workspace_path / "prompts").mkdir(exist_ok=True)
