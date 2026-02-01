"""AI 提供商路由"""

from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auto.shared.config import get_config_manager, AIProviderConfig

router = APIRouter()


class ProviderCreate(BaseModel):
    """创建提供商请求"""
    name: str
    provider_type: str = "official"
    base_url: Optional[str] = None
    api_key: str
    is_default: bool = False
    models: Optional[List[str]] = None


class ProviderUpdate(BaseModel):
    """更新提供商请求"""
    enabled: Optional[bool] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: Optional[List[str]] = None


class ProviderResponse(BaseModel):
    """提供商响应"""
    code: int = 0
    message: str = "success"
    data: dict = {}


# 默认模型列表
DEFAULT_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
    "deepseek": ["deepseek-chat", "deepseek-coder"],
    "openrouter": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet"],
}

# 默认 Base URL
DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "deepseek": "https://api.deepseek.com",
    "openrouter": "https://openrouter.ai/api/v1",
}


@router.get("/providers")
async def list_providers() -> ProviderResponse:
    """列出 AI 提供商"""
    config_manager = get_config_manager()
    providers = config_manager.config.providers
    
    items = [
        {
            "name": p.name,
            "display_name": p.name.upper() if p.name in ["openai", "anthropic"] else p.name.title(),
            "provider_type": p.provider_type,
            "base_url": p.base_url,
            "api_key_set": bool(p.api_key),
            "enabled": p.is_enabled,
            "is_default": p.is_default,
            "models": getattr(p, "models", None) or DEFAULT_MODELS.get(p.name, []),
        }
        for p in providers
    ]
    
    return ProviderResponse(
        data={
            "items": items,
            "total": len(items),
        }
    )


# 兼容旧路由
@router.get("/ai-providers")
async def list_providers_legacy() -> ProviderResponse:
    """列出 AI 提供商 (兼容)"""
    return await list_providers()


@router.post("/providers")
async def create_provider(request: ProviderCreate) -> ProviderResponse:
    """添加 AI 提供商"""
    config_manager = get_config_manager()
    
    # 检查是否已存在
    for p in config_manager.config.providers:
        if p.name == request.name:
            raise HTTPException(status_code=400, detail=f"提供商 {request.name} 已存在")
    
    # 使用默认 base_url
    base_url = request.base_url or DEFAULT_BASE_URLS.get(request.name, "")
    
    provider = AIProviderConfig(
        name=request.name,
        provider_type=request.provider_type,
        base_url=base_url,
        api_key=request.api_key,
        is_default=request.is_default,
        is_enabled=True,
    )
    
    config_manager.add_provider(provider)
    
    return ProviderResponse(
        message="添加成功",
        data={
            "name": provider.name,
            "provider_type": provider.provider_type,
        }
    )


# 兼容旧路由
@router.post("/ai-providers")
async def create_provider_legacy(request: ProviderCreate) -> ProviderResponse:
    """添加 AI 提供商 (兼容)"""
    return await create_provider(request)


@router.post("/providers/{provider_name}/test")
async def test_provider(provider_name: str) -> ProviderResponse:
    """测试 AI 提供商"""
    from auto.core.ai.router import get_router
    
    ai_router = get_router()
    results = await ai_router.health_check(provider_name)
    
    status = results.get(provider_name, False)
    
    return ProviderResponse(
        data={
            "name": provider_name,
            "status": "healthy" if status else "unhealthy",
        }
    )


@router.delete("/providers/{provider_name}")
async def delete_provider(provider_name: str) -> ProviderResponse:
    """删除 AI 提供商"""
    config_manager = get_config_manager()
    
    original_count = len(config_manager.config.providers)
    providers = [p for p in config_manager.config.providers if p.name != provider_name]
    
    if len(providers) == original_count:
        raise HTTPException(status_code=404, detail=f"提供商 {provider_name} 不存在")
    
    config_manager._config.providers = providers
    config_manager.save()
    
    return ProviderResponse(message="删除成功", data={})


@router.patch("/providers/{provider_name}")
async def update_provider(provider_name: str, request: ProviderUpdate) -> ProviderResponse:
    """更新 AI 提供商"""
    config_manager = get_config_manager()
    
    for p in config_manager.config.providers:
        if p.name == provider_name:
            if request.enabled is not None:
                p.is_enabled = request.enabled
            if request.api_key is not None:
                p.api_key = request.api_key
            if request.base_url is not None:
                p.base_url = request.base_url
            
            config_manager.save()
            
            return ProviderResponse(
                message="更新成功",
                data={"name": provider_name, "enabled": p.is_enabled}
            )
    
    raise HTTPException(status_code=404, detail=f"提供商 {provider_name} 不存在")


# 兼容旧路由
@router.post("/ai-providers/{provider_name}/test")
async def test_provider_legacy(provider_name: str) -> ProviderResponse:
    return await test_provider(provider_name)


@router.delete("/ai-providers/{provider_name}")
async def delete_provider_legacy(provider_name: str) -> ProviderResponse:
    return await delete_provider(provider_name)


# ===== 图像生成配置 =====

class ImageGenConfigUpdate(BaseModel):
    """图像生成配置更新"""
    enabled: Optional[bool] = None
    provider: Optional[str] = None  # openai, nano_banana, custom
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    default_size: Optional[str] = None


@router.get("/image-gen/config")
async def get_image_gen_config() -> ProviderResponse:
    """获取图像生成配置"""
    config_manager = get_config_manager()
    image_config = config_manager.config.image_gen
    
    return ProviderResponse(
        data={
            "enabled": image_config.enabled,
            "provider": image_config.provider,
            "base_url": image_config.base_url,
            "api_key_set": bool(image_config.api_key),
            "model": image_config.model,
            "default_size": image_config.default_size,
            "available_models": ["dall-e-3", "dall-e-2"],
            "available_sizes": ["1024x1024", "1792x1024", "1024x1792"],
        }
    )


@router.put("/image-gen/config")
async def update_image_gen_config(request: ImageGenConfigUpdate) -> ProviderResponse:
    """更新图像生成配置"""
    config_manager = get_config_manager()
    image_config = config_manager.config.image_gen
    
    if request.enabled is not None:
        image_config.enabled = request.enabled
    if request.provider is not None:
        image_config.provider = request.provider
    if request.base_url is not None:
        image_config.base_url = request.base_url
    if request.api_key is not None:
        image_config.api_key = request.api_key
    if request.model is not None:
        image_config.model = request.model
    if request.default_size is not None:
        image_config.default_size = request.default_size
    
    config_manager.save()
    
    return ProviderResponse(
        message="配置已更新",
        data={
            "enabled": image_config.enabled,
            "provider": image_config.provider,
            "model": image_config.model,
        }
    )


@router.post("/image-gen/test")
async def test_image_gen() -> ProviderResponse:
    """测试图像生成配置"""
    try:
        from auto.core.ai.image import get_image_generator
        
        generator = get_image_generator()
        
        if not generator.api_key:
            return ProviderResponse(
                code=400,
                message="未配置 API Key",
                data={"success": False}
            )
        
        # 生成测试图像
        urls = await generator.generate(
            prompt="A simple blue circle on white background, minimal design",
            size="1024x1024",
            n=1
        )
        
        return ProviderResponse(
            message="测试成功",
            data={
                "success": True,
                "image_url": urls[0] if urls else None,
            }
        )
    except Exception as e:
        return ProviderResponse(
            code=500,
            message=f"测试失败: {str(e)}",
            data={"success": False}
        )
