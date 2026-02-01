"""配置管理模块"""

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# 默认配置目录
DEFAULT_CONFIG_DIR = Path.home() / ".auto"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"


class AIProviderConfig(BaseModel):
    """AI 提供商配置"""
    name: str
    provider_type: str = "official"  # official, proxy, custom
    base_url: str
    api_key: str = ""
    is_enabled: bool = True
    is_default: bool = False
    models: list[str] = Field(default_factory=list)
    supports_image: bool = False  # 是否支持图像生成


class ImageGenConfig(BaseModel):
    """图像生成配置"""
    enabled: bool = True
    provider: str = "openai"  # openai, nano_banana, custom
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "dall-e-3"
    default_size: str = "1024x1024"


class StorageConfig(BaseModel):
    """存储配置"""
    type: str = "sqlite"  # sqlite, mysql
    path: str = str(DEFAULT_CONFIG_DIR / "data.db")
    # MySQL 配置
    host: str = "localhost"
    port: int = 3306
    database: str = "ai_assistant"
    user: str = "auto"
    password: str = ""


class WorkspaceConfig(BaseModel):
    """工作空间配置"""
    default_path: str = str(Path.home() / "auto-workspaces")
    current: Optional[str] = None


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    file: str = str(DEFAULT_CONFIG_DIR / "logs" / "auto.log")


class AppConfig(BaseModel):
    """应用配置"""
    mode: str = "local"  # local, remote
    debug: bool = False
    
    # AI 配置
    default_provider: str = "openai"
    default_model: str = "gpt-4o"
    providers: list[AIProviderConfig] = Field(default_factory=list)
    
    # 图像生成配置
    image_gen: ImageGenConfig = Field(default_factory=ImageGenConfig)
    
    # 存储配置
    storage: StorageConfig = Field(default_factory=StorageConfig)
    
    # 工作空间配置
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    
    # 日志配置
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # 远程服务器配置
    server_url: str = "http://localhost:8000"
    api_key: str = ""


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_CONFIG_FILE
        self._config: Optional[AppConfig] = None
    
    @property
    def config(self) -> AppConfig:
        """获取配置"""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def load(self) -> AppConfig:
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return AppConfig(**data)
        return AppConfig()
    
    def save(self) -> None:
        """保存配置"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                self.config.model_dump(exclude_none=True),
                f,
                allow_unicode=True,
                default_flow_style=False,
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        parts = key.split(".")
        value = self.config.model_dump()
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        parts = key.split(".")
        config_dict = self.config.model_dump()
        
        # 导航到目标位置
        target = config_dict
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
        
        # 设置值
        target[parts[-1]] = value
        
        # 重新创建配置对象
        self._config = AppConfig(**config_dict)
        self.save()
    
    def add_provider(self, provider: AIProviderConfig) -> None:
        """添加 AI 提供商"""
        # 检查是否已存在
        existing = [p for p in self.config.providers if p.name != provider.name]
        existing.append(provider)
        self._config.providers = existing
        self.save()
    
    def get_provider(self, name: str) -> Optional[AIProviderConfig]:
        """获取 AI 提供商配置"""
        for provider in self.config.providers:
            if provider.name == name:
                return provider
        return None
    
    def get_default_provider(self) -> Optional[AIProviderConfig]:
        """获取默认 AI 提供商"""
        # 先找标记为默认的
        for provider in self.config.providers:
            if provider.is_default and provider.is_enabled:
                return provider
        
        # 否则返回第一个启用的
        for provider in self.config.providers:
            if provider.is_enabled:
                return provider
        
        return None


# 全局配置实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """获取配置"""
    return get_config_manager().config
