"""
SkillHub - 技能市场

借鉴 OpenClaw 的 ClawHub 设计:
- 技能发布与版本管理
- 技能搜索（支持向量搜索）
- 技能安装与卸载
- 技能依赖管理
"""

from .registry import SkillRegistry, SkillInfo, SkillVersion
from .installer import SkillInstaller

__all__ = [
    "SkillRegistry",
    "SkillInfo",
    "SkillVersion",
    "SkillInstaller",
]
