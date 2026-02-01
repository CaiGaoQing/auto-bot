"""图像生成模块 - 支持多种图像生成 API"""

import base64
import os
from pathlib import Path
from typing import Optional
import httpx

from auto.shared.config import get_config_manager


class ImageGenerator:
    """图像生成器
    
    支持:
    - OpenAI DALL-E
    - Nano Banana 中转站
    - 其他兼容 OpenAI 格式的 API
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        config = get_config_manager().config
        image_config = config.image_gen
        
        # 优先使用图像生成专用配置
        self.base_url = (base_url or image_config.base_url or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or image_config.api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or image_config.model or "dall-e-3"
        self.enabled = image_config.enabled
        
        # 如果图像配置没有 API key，尝试从 providers 获取
        if not self.api_key:
            for provider in config.providers:
                if provider.is_enabled and provider.api_key:
                    if not base_url:
                        self.base_url = provider.base_url.rstrip("/")
                    self.api_key = provider.api_key
                    break
    
    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1,
    ) -> list[str]:
        """生成图像
        
        Args:
            prompt: 图像描述
            size: 图像尺寸 (1024x1024, 1792x1024, 1024x1792)
            quality: 质量 (standard, hd)
            n: 生成数量
            
        Returns:
            图像 URL 列表
        """
        url = f"{self.base_url}/images/generations"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n,
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        
        # 返回图像 URL
        return [item.get("url", "") for item in data.get("data", [])]
    
    async def generate_and_download(
        self,
        prompt: str,
        save_path: Path,
        size: str = "1024x1024",
    ) -> Optional[Path]:
        """生成图像并下载保存
        
        Args:
            prompt: 图像描述
            save_path: 保存路径
            size: 图像尺寸
            
        Returns:
            保存的文件路径，失败返回 None
        """
        try:
            urls = await self.generate(prompt, size=size)
            if not urls or not urls[0]:
                return None
            
            # 下载图像
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(urls[0])
                response.raise_for_status()
                
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_bytes(response.content)
                
            return save_path
        except Exception as e:
            print(f"图像生成失败: {e}")
            return None


# 全局实例
_image_generator: Optional[ImageGenerator] = None


def get_image_generator() -> ImageGenerator:
    """获取图像生成器实例"""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator
