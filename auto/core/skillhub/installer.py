"""
技能安装器

从远程仓库安装技能
"""

import asyncio
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import logging

import httpx

from .registry import SkillInfo, SkillVersion, get_skill_registry

logger = logging.getLogger(__name__)


class SkillInstaller:
    """
    技能安装器
    
    支持从多种来源安装技能:
    - GitHub 仓库
    - ZIP 文件
    - 远程技能市场
    """
    
    def __init__(
        self,
        install_path: Optional[Path] = None,
        registry_url: Optional[str] = None,
    ):
        if install_path is None:
            install_path = Path.home() / ".ai-auto" / "skills"
        
        self.install_path = install_path
        self.registry_url = registry_url or "https://skillhub.autobot.ai"
        self.install_path.mkdir(parents=True, exist_ok=True)
    
    async def install_from_github(
        self,
        repo_url: str,
        branch: str = "main",
        subdirectory: Optional[str] = None,
    ) -> Optional[SkillInfo]:
        """
        从 GitHub 安装技能
        
        Args:
            repo_url: GitHub 仓库 URL
            branch: 分支名
            subdirectory: 子目录（如果技能在子目录中）
        
        Returns:
            安装的技能信息
        """
        try:
            # 解析仓库信息
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip("/").split("/")
            
            if len(path_parts) < 2:
                logger.error(f"无效的 GitHub URL: {repo_url}")
                return None
            
            owner, repo = path_parts[0], path_parts[1]
            
            # 下载 ZIP
            zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(zip_url, follow_redirects=True)
                
                if response.status_code != 200:
                    logger.error(f"下载失败: {response.status_code}")
                    return None
                
                # 保存并解压
                with tempfile.TemporaryDirectory() as tmp_dir:
                    zip_path = Path(tmp_dir) / "skill.zip"
                    zip_path.write_bytes(response.content)
                    
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(tmp_dir)
                    
                    # 找到技能目录
                    extracted_dir = Path(tmp_dir) / f"{repo}-{branch}"
                    
                    if subdirectory:
                        skill_dir = extracted_dir / subdirectory
                    else:
                        skill_dir = extracted_dir
                    
                    if not skill_dir.exists():
                        logger.error(f"技能目录不存在: {skill_dir}")
                        return None
                    
                    # 安装
                    return await self._install_from_dir(skill_dir, f"github:{owner}/{repo}")
            
        except Exception as e:
            logger.error(f"从 GitHub 安装失败: {e}")
            return None
    
    async def install_from_zip(
        self,
        zip_path: Path,
        skill_name: Optional[str] = None,
    ) -> Optional[SkillInfo]:
        """
        从 ZIP 文件安装技能
        
        Args:
            zip_path: ZIP 文件路径
            skill_name: 技能名称（如果不提供则从内容推断）
        
        Returns:
            安装的技能信息
        """
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # 解压
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(tmp_dir)
                
                # 找到技能目录（包含 SKILL.md 或 skill.py）
                tmp_path = Path(tmp_dir)
                skill_dir = None
                
                # 先检查根目录
                if (tmp_path / "SKILL.md").exists() or (tmp_path / "skill.py").exists():
                    skill_dir = tmp_path
                else:
                    # 检查子目录
                    for subdir in tmp_path.iterdir():
                        if subdir.is_dir():
                            if (subdir / "SKILL.md").exists() or (subdir / "skill.py").exists():
                                skill_dir = subdir
                                break
                
                if not skill_dir:
                    logger.error("ZIP 中未找到有效的技能目录")
                    return None
                
                return await self._install_from_dir(skill_dir, f"zip:{zip_path.name}")
                
        except Exception as e:
            logger.error(f"从 ZIP 安装失败: {e}")
            return None
    
    async def install_from_registry(
        self,
        skill_name: str,
        version: Optional[str] = None,
    ) -> Optional[SkillInfo]:
        """
        从技能市场安装技能
        
        Args:
            skill_name: 技能名称
            version: 版本号（默认 latest）
        
        Returns:
            安装的技能信息
        """
        try:
            # 获取技能信息
            async with httpx.AsyncClient() as client:
                url = f"{self.registry_url}/api/skills/{skill_name}"
                if version:
                    url += f"/versions/{version}"
                
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.error(f"获取技能信息失败: {response.status_code}")
                    return None
                
                data = response.json()
                download_url = data.get("download_url")
                
                if not download_url:
                    logger.error("未找到下载链接")
                    return None
                
                # 下载
                download_response = await client.get(download_url, follow_redirects=True)
                
                if download_response.status_code != 200:
                    logger.error(f"下载失败: {download_response.status_code}")
                    return None
                
                # 验证校验和
                expected_checksum = data.get("checksum")
                if expected_checksum:
                    actual_checksum = hashlib.sha256(download_response.content).hexdigest()
                    if actual_checksum != expected_checksum:
                        logger.error("校验和不匹配")
                        return None
                
                # 保存并安装
                with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
                    f.write(download_response.content)
                    tmp_zip = Path(f.name)
                
                try:
                    result = await self.install_from_zip(tmp_zip, skill_name)
                    return result
                finally:
                    tmp_zip.unlink()
                    
        except Exception as e:
            logger.error(f"从技能市场安装失败: {e}")
            return None
    
    async def _install_from_dir(
        self,
        source_dir: Path,
        source_url: str,
    ) -> Optional[SkillInfo]:
        """从目录安装技能"""
        # 解析技能信息
        skill_md = source_dir / "SKILL.md"
        
        if skill_md.exists():
            skill_info = SkillInfo.from_skill_md(skill_md)
            if not skill_info:
                logger.error("解析 SKILL.md 失败")
                return None
        else:
            skill_info = SkillInfo(
                name=source_dir.name,
                display_name=source_dir.name.replace("_", " ").title(),
                description=f"技能: {source_dir.name}",
                author="unknown",
            )
        
        # 目标目录
        target_dir = self.install_path / skill_info.name
        
        # 如果已存在，先备份
        if target_dir.exists():
            backup_dir = self.install_path / f"{skill_info.name}.backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            target_dir.rename(backup_dir)
        
        # 复制文件
        shutil.copytree(source_dir, target_dir)
        
        # 更新技能信息
        skill_info.path = target_dir
        skill_info.skill_md_path = target_dir / "SKILL.md"
        skill_info.source = "local"
        skill_info.source_url = source_url
        skill_info.installed = True
        
        # 注册到注册表
        registry = get_skill_registry()
        registry.register_skill(skill_info)
        
        logger.info(f"技能安装成功: {skill_info.name}")
        return skill_info
    
    async def uninstall(self, skill_name: str) -> bool:
        """
        卸载技能
        
        Args:
            skill_name: 技能名称
        
        Returns:
            是否成功
        """
        try:
            skill_dir = self.install_path / skill_name
            
            if not skill_dir.exists():
                logger.warning(f"技能不存在: {skill_name}")
                return False
            
            # 删除目录
            shutil.rmtree(skill_dir)
            
            # 从注册表移除
            registry = get_skill_registry()
            registry.unregister_skill(skill_name)
            
            logger.info(f"技能卸载成功: {skill_name}")
            return True
            
        except Exception as e:
            logger.error(f"卸载技能失败: {e}")
            return False
    
    async def update(self, skill_name: str) -> Optional[SkillInfo]:
        """
        更新技能
        
        Args:
            skill_name: 技能名称
        
        Returns:
            更新后的技能信息
        """
        registry = get_skill_registry()
        skill = registry.get_skill(skill_name)
        
        if not skill:
            logger.error(f"技能不存在: {skill_name}")
            return None
        
        # 根据来源更新
        if skill.source_url and skill.source_url.startswith("github:"):
            # 从 GitHub 更新
            repo_path = skill.source_url.replace("github:", "")
            return await self.install_from_github(f"https://github.com/{repo_path}")
        elif skill.source == "remote":
            # 从技能市场更新
            return await self.install_from_registry(skill_name)
        else:
            logger.warning(f"无法更新本地技能: {skill_name}")
            return None
    
    def list_installed(self) -> List[SkillInfo]:
        """列出已安装的技能"""
        registry = get_skill_registry()
        return registry.list_skills(source="local", installed_only=True)
    
    async def search_registry(
        self,
        query: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        搜索技能市场
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
        
        Returns:
            技能信息列表
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.registry_url}/api/skills/search",
                    params={"q": query, "limit": limit},
                )
                
                if response.status_code != 200:
                    logger.error(f"搜索失败: {response.status_code}")
                    return []
                
                return response.json().get("skills", [])
                
        except Exception as e:
            logger.error(f"搜索技能市场失败: {e}")
            return []
