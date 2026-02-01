"""
工作空间提示词管理

借鉴 OpenClaw 的 AGENTS.md / SOUL.md / TOOLS.md 设计
允许用户通过 Markdown 文件自定义 AI 行为

核心功能:
- 读取工作空间中的所有文件作为知识上下文
- 支持 AGENTS.md / SOUL.md / TOOLS.md 自定义行为
- 智能文件过滤和内容摘要
"""

import os
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple
import logging

logger = logging.getLogger(__name__)

# 支持读取的文件扩展名
READABLE_EXTENSIONS = {
    # 代码文件
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
    '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.cs',
    # 配置文件
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.env', '.env.example', '.env.local',
    # 文档文件
    '.md', '.txt', '.rst', '.adoc',
    # Web 文件
    '.html', '.htm', '.css', '.scss', '.sass', '.less',
    '.vue', '.svelte',
    # 脚本文件
    '.sh', '.bash', '.zsh', '.fish', '.bat', '.ps1',
    # 数据文件
    '.sql', '.graphql',
    # 其他
    '.xml', '.csv',
}

# 应该跳过的目录
SKIP_DIRECTORIES = {
    '.git', '.svn', '.hg',
    'node_modules', 'venv', '.venv', 'env', '__pycache__',
    '.idea', '.vscode', '.cursor',
    'dist', 'build', 'target', 'out',
    '.next', '.nuxt',
    'coverage', '.pytest_cache', '.mypy_cache',
}

# 应该跳过的文件模式
SKIP_FILES = {
    '.DS_Store', 'Thumbs.db',
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    '.gitignore', '.dockerignore',
}

# 单个文件最大读取大小 (字节)
MAX_FILE_SIZE = 100 * 1024  # 100KB

# 总上下文最大大小 (字符)
MAX_CONTEXT_SIZE = 200 * 1024  # 200K 字符


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
    
    def scan_workspace_files(
        self,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_files: int = 100,
    ) -> List[Dict]:
        """
        扫描工作空间中的所有文件
        
        Args:
            include_patterns: 要包含的文件模式（glob）
            exclude_patterns: 要排除的文件模式
            max_files: 最大文件数量
        
        Returns:
            文件信息列表 [{"path": "...", "size": 123, "type": "python"}, ...]
        """
        files = []
        
        for root, dirs, filenames in os.walk(self.workspace_path):
            # 跳过特定目录
            dirs[:] = [d for d in dirs if d not in SKIP_DIRECTORIES]
            
            for filename in filenames:
                if filename in SKIP_FILES:
                    continue
                
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(self.workspace_path)
                
                # 检查扩展名
                ext = file_path.suffix.lower()
                if ext not in READABLE_EXTENSIONS:
                    continue
                
                # 检查文件大小
                try:
                    size = file_path.stat().st_size
                    if size > MAX_FILE_SIZE:
                        continue
                    if size == 0:
                        continue
                except OSError:
                    continue
                
                # 确定文件类型
                file_type = self._get_file_type(ext)
                
                files.append({
                    "path": str(relative_path),
                    "absolute_path": str(file_path),
                    "size": size,
                    "type": file_type,
                    "extension": ext,
                })
                
                if len(files) >= max_files:
                    break
            
            if len(files) >= max_files:
                break
        
        # 按重要性排序：README > 配置文件 > 代码文件
        def sort_key(f):
            name = f["path"].lower()
            if "readme" in name:
                return (0, name)
            if f["type"] == "config":
                return (1, name)
            if f["type"] == "code":
                return (2, name)
            return (3, name)
        
        files.sort(key=sort_key)
        return files
    
    def _get_file_type(self, ext: str) -> str:
        """根据扩展名确定文件类型"""
        code_exts = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', 
                     '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.cs'}
        config_exts = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.env'}
        doc_exts = {'.md', '.txt', '.rst', '.adoc'}
        web_exts = {'.html', '.htm', '.css', '.scss', '.vue', '.svelte'}
        
        if ext in code_exts:
            return "code"
        elif ext in config_exts:
            return "config"
        elif ext in doc_exts:
            return "document"
        elif ext in web_exts:
            return "web"
        else:
            return "other"
    
    def read_workspace_files(
        self,
        max_files: int = 50,
        max_total_size: int = MAX_CONTEXT_SIZE,
    ) -> Tuple[List[Dict], int]:
        """
        读取工作空间中的所有文件内容
        
        Args:
            max_files: 最大读取文件数
            max_total_size: 最大总字符数
        
        Returns:
            (文件内容列表, 总字符数)
        """
        files = self.scan_workspace_files(max_files=max_files)
        results = []
        total_size = 0
        
        for file_info in files:
            if total_size >= max_total_size:
                break
            
            try:
                file_path = Path(file_info["absolute_path"])
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                
                # 截断过长的内容
                remaining = max_total_size - total_size
                if len(content) > remaining:
                    content = content[:remaining] + "\n... (内容已截断)"
                
                results.append({
                    "path": file_info["path"],
                    "type": file_info["type"],
                    "content": content,
                    "size": len(content),
                })
                
                total_size += len(content)
                
            except Exception as e:
                logger.warning(f"读取文件失败 {file_info['path']}: {e}")
                continue
        
        return results, total_size
    
    def build_knowledge_context(
        self,
        include_file_contents: bool = True,
        max_files: int = 30,
        summary_only: bool = False,
    ) -> str:
        """
        构建工作空间知识上下文
        
        将工作空间中的所有文件内容组织成 AI 可以理解的上下文
        
        Args:
            include_file_contents: 是否包含文件内容
            max_files: 最大文件数
            summary_only: 仅生成文件列表摘要，不包含内容
        
        Returns:
            知识上下文字符串
        """
        parts = []
        
        # 添加标题
        parts.append("# 工作空间知识库\n")
        parts.append(f"工作空间路径: `{self.workspace_path}`\n")
        
        if summary_only:
            # 仅生成文件结构
            files = self.scan_workspace_files(max_files=100)
            parts.append(f"\n## 文件结构 (共 {len(files)} 个文件)\n")
            
            # 按目录分组
            dirs = {}
            for f in files:
                path = Path(f["path"])
                parent = str(path.parent) if path.parent != Path(".") else "根目录"
                if parent not in dirs:
                    dirs[parent] = []
                dirs[parent].append(f)
            
            for dir_name, dir_files in sorted(dirs.items()):
                parts.append(f"\n### {dir_name}/\n")
                for f in dir_files:
                    parts.append(f"- `{Path(f['path']).name}` ({f['type']}, {f['size']} bytes)")
            
        elif include_file_contents:
            # 读取并包含文件内容
            files, total_size = self.read_workspace_files(max_files=max_files)
            
            parts.append(f"\n## 项目文件 (共 {len(files)} 个文件, {total_size:,} 字符)\n")
            parts.append("以下是工作空间中的文件内容，请学习并理解这些内容：\n")
            
            for f in files:
                parts.append(f"\n### 文件: `{f['path']}`\n")
                parts.append(f"类型: {f['type']} | 大小: {f['size']} 字符\n")
                
                # 根据文件类型添加代码块
                lang = self._get_language_for_file(f['path'])
                parts.append(f"\n```{lang}\n{f['content']}\n```\n")
        
        return "\n".join(parts)
    
    def _get_language_for_file(self, path: str) -> str:
        """获取文件对应的语言标识"""
        ext = Path(path).suffix.lower()
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.cs': 'csharp',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.md': 'markdown',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.vue': 'vue',
            '.sql': 'sql',
            '.sh': 'bash',
            '.xml': 'xml',
        }
        return lang_map.get(ext, '')


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
