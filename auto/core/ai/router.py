"""AI 路由器 - 管理多个 AI 提供商，实现负载均衡和故障转移"""

from typing import AsyncIterator, Optional

from auto.core.ai.provider import AIProvider, create_provider
from auto.shared.config import get_config_manager, AIProviderConfig
from auto.shared.models import ChatResponse, Message


class AIRouter:
    """AI 路由器
    
    负责:
    - 管理多个 AI 提供商
    - 路由请求到合适的提供商
    - 负载均衡
    - 故障转移
    - 成本控制
    """
    
    def __init__(self):
        self._providers: dict[str, AIProvider] = {}
        self._config_manager = get_config_manager()
        self._initialized = False
    
    def _ensure_initialized(self) -> None:
        """确保已初始化"""
        if self._initialized:
            return
        
        config = self._config_manager.config
        
        # 从配置加载提供商
        for provider_config in config.providers:
            if provider_config.is_enabled:
                provider = create_provider(
                    name=provider_config.name,
                    provider_type=provider_config.provider_type,
                    base_url=provider_config.base_url,
                    api_key=provider_config.api_key,
                )
                self._providers[provider_config.name] = provider
        
        self._initialized = True
    
    def register_provider(self, name: str, provider: AIProvider) -> None:
        """注册提供商"""
        self._providers[name] = provider
    
    def get_provider(self, name: str) -> Optional[AIProvider]:
        """获取提供商"""
        self._ensure_initialized()
        return self._providers.get(name)
    
    def list_providers(self) -> list[str]:
        """列出所有提供商"""
        self._ensure_initialized()
        return list(self._providers.keys())
    
    async def chat(
        self,
        messages: list[Message],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> ChatResponse:
        """发送聊天请求
        
        Args:
            messages: 消息列表
            model: 模型名称
            provider: 指定提供商名称
            temperature: 温度
            max_tokens: 最大 Token 数
            tools: 工具列表
            **kwargs: 其他参数
        
        Returns:
            ChatResponse: 聊天响应
        """
        self._ensure_initialized()
        
        config = self._config_manager.config
        model = model or config.default_model
        
        # 选择提供商
        selected_provider = self._select_provider(provider, model)
        
        if selected_provider is None:
            raise ValueError("没有可用的 AI 提供商，请先配置: auto config provider add")
        
        # 发送请求
        try:
            response = await selected_provider.chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                **kwargs,
            )
            return response
        except Exception as e:
            # 尝试故障转移
            fallback = self._get_fallback_provider(selected_provider.name)
            if fallback:
                return await fallback.chat(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    **kwargs,
                )
            raise
    
    async def chat_stream(
        self,
        messages: list[Message],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式聊天"""
        self._ensure_initialized()
        
        config = self._config_manager.config
        model = model or config.default_model
        
        # 选择提供商
        selected_provider = self._select_provider(provider, model)
        
        if selected_provider is None:
            raise ValueError("没有可用的 AI 提供商，请先配置")
        
        # 发送请求
        async for chunk in selected_provider.chat_stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        ):
            yield chunk
    
    def _select_provider(
        self,
        provider_name: Optional[str],
        model: str,
    ) -> Optional[AIProvider]:
        """选择提供商
        
        Args:
            provider_name: 指定的提供商名称
            model: 模型名称
        
        Returns:
            AIProvider: 选择的提供商
        """
        # 如果指定了提供商
        if provider_name and provider_name in self._providers:
            return self._providers[provider_name]
        
        # 根据模型推断提供商
        if model.startswith("gpt-") or model.startswith("o1-"):
            # OpenAI 模型
            for name, provider in self._providers.items():
                if "openai" in name.lower():
                    return provider
        elif model.startswith("claude-"):
            # Anthropic 模型
            for name, provider in self._providers.items():
                if "anthropic" in name.lower() or "claude" in name.lower():
                    return provider
        
        # 返回默认提供商
        config = self._config_manager.config
        default_provider_config = self._config_manager.get_default_provider()
        if default_provider_config and default_provider_config.name in self._providers:
            return self._providers[default_provider_config.name]
        
        # 返回第一个可用的提供商
        if self._providers:
            return list(self._providers.values())[0]
        
        return None
    
    def _get_fallback_provider(self, exclude_name: str) -> Optional[AIProvider]:
        """获取备用提供商"""
        for name, provider in self._providers.items():
            if name != exclude_name:
                return provider
        return None
    
    async def health_check(self, provider_name: Optional[str] = None) -> dict[str, bool]:
        """健康检查
        
        Args:
            provider_name: 指定提供商名称，为空则检查所有
        
        Returns:
            dict: 提供商名称 -> 健康状态
        """
        self._ensure_initialized()
        
        results = {}
        
        providers_to_check = (
            {provider_name: self._providers[provider_name]}
            if provider_name and provider_name in self._providers
            else self._providers
        )
        
        for name, provider in providers_to_check.items():
            try:
                results[name] = await provider.health_check()
            except Exception:
                results[name] = False
        
        return results


# 全局路由器实例
_router: Optional[AIRouter] = None


def get_router() -> AIRouter:
    """获取全局 AI 路由器"""
    global _router
    if _router is None:
        _router = AIRouter()
    return _router
