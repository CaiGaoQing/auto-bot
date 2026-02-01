"""
技能注册表

管理本地和远程技能
"""

import json
import yaml
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class SkillVersion:
    """技能版本"""
    version: str
    changelog: str = ""
    published_at: datetime = field(default_factory=datetime.now)
    download_url: Optional[str] = None
    checksum: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "changelog": self.changelog,
            "published_at": self.published_at.isoformat(),
            "download_url": self.download_url,
            "checksum": self.checksum,
        }


@dataclass
class SkillInfo:
    """
    技能信息
    
    对应 SKILL.md 的元数据
    """
    name: str
    display_name: str
    description: str
    author: str
    
    # 版本信息
    version: str = "1.0.0"
    versions: List[SkillVersion] = field(default_factory=list)
    
    # 分类和标签
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    
    # 来源
    source: str = "local"  # local, builtin, remote
    source_url: Optional[str] = None
    
    # 文件路径
    path: Optional[Path] = None
    skill_md_path: Optional[Path] = None
    
    # 统计
    stars: int = 0
    downloads: int = 0
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 状态
    installed: bool = False
    enabled: bool = True
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_skill_md(cls, skill_md_path: Path) -> Optional["SkillInfo"]:
        """
        从 SKILL.md 文件解析技能信息
        
        SKILL.md 格式:
        ---
        name: my-skill
        display_name: 我的技能
        description: 技能描述
        author: 作者
        version: 1.0.0
        category: automation
        tags: [rpa, automation]
        ---
        
        # 技能内容...
        """
        try:
            content = skill_md_path.read_text(encoding="utf-8")
            
            # 解析 YAML frontmatter
            frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            
            if frontmatter_match:
                frontmatter = yaml.safe_load(frontmatter_match.group(1))
            else:
                # 尝试从内容推断
                frontmatter = {
                    "name": skill_md_path.parent.name,
                    "display_name": skill_md_path.parent.name,
                    "description": content[:200] if content else "",
                    "author": "unknown",
                }
            
            return cls(
                name=frontmatter.get("name", skill_md_path.parent.name),
                display_name=frontmatter.get("display_name", frontmatter.get("name", "")),
                description=frontmatter.get("description", ""),
                author=frontmatter.get("author", "unknown"),
                version=frontmatter.get("version", "1.0.0"),
                category=frontmatter.get("category", "general"),
                tags=frontmatter.get("tags", []),
                path=skill_md_path.parent,
                skill_md_path=skill_md_path,
                metadata=frontmatter.get("metadata", {}),
                installed=True,
                source="local",
            )
            
        except Exception as e:
            logger.error(f"解析 SKILL.md 失败 {skill_md_path}: {e}")
            return None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "category": self.category,
            "tags": self.tags,
            "source": self.source,
            "source_url": self.source_url,
            "path": str(self.path) if self.path else None,
            "stars": self.stars,
            "downloads": self.downloads,
            "installed": self.installed,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SkillRegistry:
    """
    技能注册表
    
    管理本地安装的技能和远程技能市场
    """
    
    def __init__(
        self,
        local_skills_path: Optional[Path] = None,
        builtin_skills_path: Optional[Path] = None,
        registry_url: Optional[str] = None,
    ):
        """
        初始化注册表
        
        Args:
            local_skills_path: 本地技能目录
            builtin_skills_path: 内置技能目录
            registry_url: 远程技能市场 URL
        """
        # 默认路径
        if local_skills_path is None:
            local_skills_path = Path.home() / ".ai-auto" / "skills"
        
        if builtin_skills_path is None:
            # 内置技能在项目中
            builtin_skills_path = Path(__file__).parent.parent.parent / "skills" / "builtin"
        
        self.local_skills_path = local_skills_path
        self.builtin_skills_path = builtin_skills_path
        self.registry_url = registry_url or "https://skillhub.autobot.ai"
        
        # 技能缓存
        self._skills: Dict[str, SkillInfo] = {}
        self._loaded = False
        
        # 确保目录存在
        self.local_skills_path.mkdir(parents=True, exist_ok=True)
    
    def load(self, force: bool = False):
        """加载所有技能"""
        if self._loaded and not force:
            return
        
        self._skills = {}
        
        # 加载内置技能
        self._load_skills_from_dir(self.builtin_skills_path, "builtin")
        
        # 加载本地技能
        self._load_skills_from_dir(self.local_skills_path, "local")
        
        self._loaded = True
        logger.info(f"加载了 {len(self._skills)} 个技能")
    
    def _load_skills_from_dir(self, dir_path: Path, source: str):
        """从目录加载技能"""
        if not dir_path.exists():
            return
        
        for skill_dir in dir_path.iterdir():
            if not skill_dir.is_dir():
                continue
            
            # 查找 SKILL.md 或 skill.py
            skill_md = skill_dir / "SKILL.md"
            skill_py = skill_dir / "skill.py"
            
            if skill_md.exists():
                skill_info = SkillInfo.from_skill_md(skill_md)
                if skill_info:
                    skill_info.source = source
                    self._skills[skill_info.name] = skill_info
            elif skill_py.exists():
                # 从 Python 文件推断
                skill_info = SkillInfo(
                    name=skill_dir.name,
                    display_name=skill_dir.name.replace("_", " ").title(),
                    description=f"技能: {skill_dir.name}",
                    author="unknown",
                    path=skill_dir,
                    source=source,
                    installed=True,
                )
                self._skills[skill_info.name] = skill_info
    
    def get_skill(self, name: str) -> Optional[SkillInfo]:
        """获取技能信息"""
        self.load()
        return self._skills.get(name)
    
    def list_skills(
        self,
        source: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        installed_only: bool = False,
        enabled_only: bool = False,
    ) -> List[SkillInfo]:
        """
        列出技能
        
        Args:
            source: 按来源过滤 (local, builtin, remote)
            category: 按分类过滤
            tags: 按标签过滤（任一匹配）
            installed_only: 仅已安装
            enabled_only: 仅已启用
        
        Returns:
            技能列表
        """
        self.load()
        
        skills = list(self._skills.values())
        
        if source:
            skills = [s for s in skills if s.source == source]
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        if tags:
            skills = [s for s in skills if any(t in s.tags for t in tags)]
        
        if installed_only:
            skills = [s for s in skills if s.installed]
        
        if enabled_only:
            skills = [s for s in skills if s.enabled]
        
        return skills
    
    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> List[SkillInfo]:
        """
        搜索技能
        
        支持名称、描述、标签的模糊匹配
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
        
        Returns:
            匹配的技能列表
        """
        self.load()
        
        query_lower = query.lower()
        results = []
        
        for skill in self._skills.values():
            score = 0
            
            # 名称匹配（权重最高）
            if query_lower in skill.name.lower():
                score += 10
            if skill.name.lower().startswith(query_lower):
                score += 5
            
            # 显示名匹配
            if query_lower in skill.display_name.lower():
                score += 8
            
            # 描述匹配
            if query_lower in skill.description.lower():
                score += 3
            
            # 标签匹配
            for tag in skill.tags:
                if query_lower in tag.lower():
                    score += 5
                    break
            
            # 分类匹配
            if query_lower in skill.category.lower():
                score += 2
            
            if score > 0:
                results.append((score, skill))
        
        # 按分数排序
        results.sort(key=lambda x: x[0], reverse=True)
        
        return [skill for _, skill in results[:limit]]
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        self.load()
        categories = set()
        for skill in self._skills.values():
            categories.add(skill.category)
        return sorted(categories)
    
    def get_tags(self) -> List[str]:
        """获取所有标签"""
        self.load()
        tags = set()
        for skill in self._skills.values():
            tags.update(skill.tags)
        return sorted(tags)
    
    def register_skill(self, skill_info: SkillInfo):
        """注册技能"""
        self._skills[skill_info.name] = skill_info
        logger.info(f"注册技能: {skill_info.name}")
    
    def unregister_skill(self, name: str):
        """取消注册技能"""
        if name in self._skills:
            del self._skills[name]
            logger.info(f"取消注册技能: {name}")
    
    def enable_skill(self, name: str) -> bool:
        """启用技能"""
        skill = self._skills.get(name)
        if skill:
            skill.enabled = True
            return True
        return False
    
    def disable_skill(self, name: str) -> bool:
        """禁用技能"""
        skill = self._skills.get(name)
        if skill:
            skill.enabled = False
            return True
        return False
    
    def get_skill_content(self, name: str) -> Optional[str]:
        """获取技能内容（SKILL.md 的内容）"""
        skill = self.get_skill(name)
        if not skill or not skill.skill_md_path:
            return None
        
        try:
            content = skill.skill_md_path.read_text(encoding="utf-8")
            # 去除 frontmatter
            content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
            return content.strip()
        except Exception as e:
            logger.error(f"读取技能内容失败: {e}")
            return None
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        self.load()
        
        skills = list(self._skills.values())
        
        return {
            "total": len(skills),
            "builtin": sum(1 for s in skills if s.source == "builtin"),
            "local": sum(1 for s in skills if s.source == "local"),
            "remote": sum(1 for s in skills if s.source == "remote"),
            "enabled": sum(1 for s in skills if s.enabled),
            "categories": len(self.get_categories()),
            "tags": len(self.get_tags()),
        }


# 全局实例
_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """获取全局技能注册表"""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
