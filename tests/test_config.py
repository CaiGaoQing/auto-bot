"""配置模块测试"""

import pytest
from pathlib import Path
import tempfile

from auto.shared.config import ConfigManager, AppConfig, AIProviderConfig


class TestConfigManager:
    """测试配置管理器"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = AppConfig()
        
        assert config.mode == "local"
        assert config.debug is False
        assert config.default_model == "gpt-4o"
        assert config.storage.type == "sqlite"
    
    def test_load_save_config(self):
        """测试配置加载和保存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            manager = ConfigManager(config_path)
            
            # 修改配置
            manager.set("mode", "remote")
            manager.set("default_model", "gpt-4o-mini")
            
            # 重新加载
            manager2 = ConfigManager(config_path)
            config = manager2.load()
            
            assert config.mode == "remote"
            assert config.default_model == "gpt-4o-mini"
    
    def test_add_provider(self):
        """测试添加提供商"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            manager = ConfigManager(config_path)
            
            provider = AIProviderConfig(
                name="test_openai",
                provider_type="official",
                base_url="https://api.openai.com/v1",
                api_key="sk-test",
            )
            
            manager.add_provider(provider)
            
            # 验证
            saved_provider = manager.get_provider("test_openai")
            assert saved_provider is not None
            assert saved_provider.name == "test_openai"
            assert saved_provider.api_key == "sk-test"
    
    def test_get_default_provider(self):
        """测试获取默认提供商"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            manager = ConfigManager(config_path)
            
            # 添加两个提供商
            manager.add_provider(AIProviderConfig(
                name="provider1",
                provider_type="official",
                base_url="https://api1.com",
                api_key="key1",
                is_default=False,
            ))
            manager.add_provider(AIProviderConfig(
                name="provider2",
                provider_type="official",
                base_url="https://api2.com",
                api_key="key2",
                is_default=True,
            ))
            
            default = manager.get_default_provider()
            assert default is not None
            assert default.name == "provider2"
