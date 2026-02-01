"""AI 提供商基类和实现"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional

from auto.shared.models import ChatRequest, ChatResponse, Message, MessageRole, TokenUsage


class AIProvider(ABC):
    """AI 提供商抽象基类"""
    
    def __init__(self, name: str, base_url: str, api_key: str):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
    
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> ChatResponse:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式聊天"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """转换消息格式为 API 格式"""
        result = []
        for msg in messages:
            item = {
                "role": msg.role.value,
                "content": msg.content,
            }
            if msg.name:
                item["name"] = msg.name
            if msg.tool_calls:
                item["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                item["tool_call_id"] = msg.tool_call_id
            result.append(item)
        return result


class OpenAIProvider(AIProvider):
    """OpenAI 提供商"""
    
    def __init__(
        self,
        name: str = "openai",
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
    ):
        super().__init__(name, base_url, api_key)
        self._client = None
    
    @property
    def client(self):
        """延迟初始化客户端"""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client
    
    async def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> ChatResponse:
        """发送聊天请求"""
        from auto.shared.utils import generate_id
        
        request_params = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
        }
        
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        if tools:
            request_params["tools"] = tools
        
        response = await self.client.chat.completions.create(**request_params)
        
        # 解析响应
        choice = response.choices[0]
        message = Message(
            role=MessageRole.ASSISTANT,
            content=choice.message.content or "",
            tool_calls=choice.message.tool_calls if hasattr(choice.message, 'tool_calls') else None,
        )
        
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )
        
        return ChatResponse(
            id=generate_id("msg"),
            message=message,
            model=model,
            usage=usage,
            finish_reason=choice.finish_reason or "stop",
        )
    
    async def chat_stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式聊天"""
        request_params = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        if tools:
            request_params["tools"] = tools
        
        stream = await self.client.chat.completions.create(**request_params)
        
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 发送一个简单的请求
            await self.client.models.list()
            return True
        except Exception:
            return False


class AnthropicProvider(AIProvider):
    """Anthropic 提供商"""
    
    def __init__(
        self,
        name: str = "anthropic",
        base_url: str = "https://api.anthropic.com",
        api_key: str = "",
    ):
        super().__init__(name, base_url, api_key)
        self._client = None
    
    @property
    def client(self):
        """延迟初始化客户端"""
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url != "https://api.anthropic.com" else None,
            )
        return self._client
    
    async def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> ChatResponse:
        """发送聊天请求"""
        from auto.shared.utils import generate_id
        
        # Anthropic 消息格式转换
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_message = msg.content
            else:
                anthropic_messages.append({
                    "role": "user" if msg.role == MessageRole.USER else "assistant",
                    "content": msg.content,
                })
        
        request_params = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or 4096,
        }
        
        if system_message:
            request_params["system"] = system_message
        
        if tools:
            # 转换为 Anthropic 工具格式
            request_params["tools"] = self._convert_tools(tools)
        
        response = await self.client.messages.create(**request_params)
        
        # 解析响应
        content = ""
        for block in response.content:
            if hasattr(block, 'text'):
                content += block.text
        
        message = Message(
            role=MessageRole.ASSISTANT,
            content=content,
        )
        
        usage = TokenUsage(
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
        )
        
        return ChatResponse(
            id=generate_id("msg"),
            message=message,
            model=model,
            usage=usage,
            finish_reason=response.stop_reason or "stop",
        )
    
    async def chat_stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式聊天"""
        # Anthropic 消息格式转换
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_message = msg.content
            else:
                anthropic_messages.append({
                    "role": "user" if msg.role == MessageRole.USER else "assistant",
                    "content": msg.content,
                })
        
        request_params = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }
        
        if system_message:
            request_params["system"] = system_message
        
        async with self.client.messages.stream(**request_params) as stream:
            async for text in stream.text_stream:
                yield text
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 发送一个简单的请求
            await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True
        except Exception:
            return False
    
    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """转换工具格式为 Anthropic 格式"""
        result = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                result.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {}),
                })
        return result


class LiteLLMProvider(AIProvider):
    """LiteLLM 统一接口提供商 (支持多种后端)"""
    
    def __init__(
        self,
        name: str = "litellm",
        base_url: str = "",
        api_key: str = "",
    ):
        super().__init__(name, base_url, api_key)
    
    async def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> ChatResponse:
        """发送聊天请求"""
        import litellm
        from auto.shared.utils import generate_id
        
        request_params = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
        }
        
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        if tools:
            request_params["tools"] = tools
        if self.api_key:
            request_params["api_key"] = self.api_key
        if self.base_url:
            request_params["api_base"] = self.base_url
        
        response = await litellm.acompletion(**request_params)
        
        # 解析响应
        choice = response.choices[0]
        message = Message(
            role=MessageRole.ASSISTANT,
            content=choice.message.content or "",
        )
        
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )
        
        return ChatResponse(
            id=generate_id("msg"),
            message=message,
            model=model,
            usage=usage,
            finish_reason=choice.finish_reason or "stop",
        )
    
    async def chat_stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式聊天"""
        import litellm
        
        request_params = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        if self.api_key:
            request_params["api_key"] = self.api_key
        if self.base_url:
            request_params["api_base"] = self.base_url
        
        response = await litellm.acompletion(**request_params)
        
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True  # LiteLLM 本身不需要检查


def create_provider(
    name: str,
    provider_type: str,
    base_url: str,
    api_key: str,
) -> AIProvider:
    """创建 AI 提供商实例"""
    if provider_type == "openai" or (provider_type == "official" and "openai" in name.lower()):
        return OpenAIProvider(name=name, base_url=base_url, api_key=api_key)
    elif provider_type == "anthropic" or (provider_type == "official" and "anthropic" in name.lower()):
        return AnthropicProvider(name=name, base_url=base_url, api_key=api_key)
    elif provider_type in ("proxy", "custom"):
        # 代理和自定义使用 OpenAI 兼容接口
        return OpenAIProvider(name=name, base_url=base_url, api_key=api_key)
    else:
        # 默认使用 LiteLLM
        return LiteLLMProvider(name=name, base_url=base_url, api_key=api_key)
