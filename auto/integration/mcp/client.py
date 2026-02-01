"""MCP 客户端"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import asyncio
import json
import yaml


@dataclass
class MCPTool:
    """MCP 工具定义"""
    name: str
    description: str
    input_schema: dict
    server_name: str


@dataclass
class MCPResource:
    """MCP 资源定义"""
    uri: str
    name: str
    description: str
    mime_type: str


@dataclass
class MCPServerConfig:
    """MCP 服务器配置"""
    name: str
    transport: str  # stdio, sse
    command: Optional[str] = None
    args: list[str] = field(default_factory=list)
    url: Optional[str] = None
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


class MCPServerConnection(ABC):
    """MCP 服务器连接抽象"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> None:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def list_tools(self) -> list[MCPTool]:
        """列出可用工具"""
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, arguments: dict) -> Any:
        """调用工具"""
        pass
    
    @abstractmethod
    async def list_resources(self) -> list[MCPResource]:
        """列出可用资源"""
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> str:
        """读取资源"""
        pass


class StdioMCPConnection(MCPServerConnection):
    """stdio 方式的 MCP 连接"""
    
    def __init__(self, config: MCPServerConfig):
        super().__init__(config)
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._request_id = 0
        self._pending_requests: dict[int, asyncio.Future] = {}
        self._read_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> None:
        """建立连接"""
        if self.is_connected:
            return
        
        if not self.config.command:
            raise ValueError("stdio 连接需要 command")
        
        # 准备环境变量
        import os
        env = os.environ.copy()
        env.update(self.config.env)
        
        # 启动进程
        self._process = await asyncio.create_subprocess_exec(
            self.config.command,
            *self.config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        
        self._reader = self._process.stdout
        self._writer = self._process.stdin
        
        # 启动读取任务
        self._read_task = asyncio.create_task(self._read_loop())
        
        # 初始化连接
        await self._send_initialize()
        
        self.is_connected = True
    
    async def disconnect(self) -> None:
        """断开连接"""
        if not self.is_connected:
            return
        
        # 取消读取任务
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        # 关闭进程
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
        
        self.is_connected = False
    
    async def _send_initialize(self) -> None:
        """发送初始化请求"""
        await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "ai-auto",
                "version": "0.1.0",
            },
        })
        
        # 发送 initialized 通知
        await self._send_notification("initialized", {})
    
    async def _send_request(self, method: str, params: dict) -> Any:
        """发送请求并等待响应"""
        self._request_id += 1
        request_id = self._request_id
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        
        # 创建 future 等待响应
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future
        
        # 发送请求
        await self._write_message(request)
        
        # 等待响应
        try:
            response = await asyncio.wait_for(future, timeout=30)
            return response
        except asyncio.TimeoutError:
            del self._pending_requests[request_id]
            raise
    
    async def _send_notification(self, method: str, params: dict) -> None:
        """发送通知 (无响应)"""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        await self._write_message(notification)
    
    async def _write_message(self, message: dict) -> None:
        """写入消息"""
        if not self._writer:
            raise RuntimeError("未连接")
        
        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        
        self._writer.write(header.encode())
        self._writer.write(content.encode())
        await self._writer.drain()
    
    async def _read_loop(self) -> None:
        """读取响应循环"""
        while True:
            try:
                message = await self._read_message()
                if message is None:
                    break
                
                # 处理响应
                if "id" in message:
                    request_id = message["id"]
                    if request_id in self._pending_requests:
                        future = self._pending_requests.pop(request_id)
                        if "error" in message:
                            future.set_exception(Exception(message["error"].get("message", "Unknown error")))
                        else:
                            future.set_result(message.get("result"))
            except asyncio.CancelledError:
                break
            except Exception:
                break
    
    async def _read_message(self) -> Optional[dict]:
        """读取消息"""
        if not self._reader:
            return None
        
        # 读取 header
        headers = {}
        while True:
            line = await self._reader.readline()
            if not line:
                return None
            
            line = line.decode().strip()
            if not line:
                break
            
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        
        # 读取 content
        content_length = int(headers.get("Content-Length", 0))
        if content_length > 0:
            content = await self._reader.read(content_length)
            return json.loads(content.decode())
        
        return None
    
    async def list_tools(self) -> list[MCPTool]:
        """列出可用工具"""
        result = await self._send_request("tools/list", {})
        
        tools = []
        for tool_data in result.get("tools", []):
            tools.append(MCPTool(
                name=tool_data["name"],
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {}),
                server_name=self.config.name,
            ))
        
        return tools
    
    async def call_tool(self, name: str, arguments: dict) -> Any:
        """调用工具"""
        result = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments,
        })
        
        # 解析结果
        content = result.get("content", [])
        if content:
            first = content[0]
            if first.get("type") == "text":
                return first.get("text", "")
        
        return result
    
    async def list_resources(self) -> list[MCPResource]:
        """列出可用资源"""
        result = await self._send_request("resources/list", {})
        
        resources = []
        for res_data in result.get("resources", []):
            resources.append(MCPResource(
                uri=res_data["uri"],
                name=res_data.get("name", ""),
                description=res_data.get("description", ""),
                mime_type=res_data.get("mimeType", "text/plain"),
            ))
        
        return resources
    
    async def read_resource(self, uri: str) -> str:
        """读取资源"""
        result = await self._send_request("resources/read", {"uri": uri})
        
        contents = result.get("contents", [])
        if contents:
            first = contents[0]
            if "text" in first:
                return first["text"]
        
        return ""


class MCPClient:
    """MCP 客户端
    
    管理多个 MCP 服务器连接。
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self._servers: dict[str, MCPServerConnection] = {}
        self._tools: dict[str, MCPTool] = {}  # tool_name -> tool
        self._config_path = config_path
    
    def load_config(self, config_path: Optional[Path] = None) -> list[MCPServerConfig]:
        """加载配置"""
        path = config_path or self._config_path
        if not path or not path.exists():
            return []
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        configs = []
        for server_data in data.get("servers", []):
            config = MCPServerConfig(
                name=server_data["name"],
                transport=server_data.get("transport", "stdio"),
                command=server_data.get("command"),
                args=server_data.get("args", []),
                url=server_data.get("url"),
                env=server_data.get("env", {}),
                enabled=server_data.get("enabled", True),
            )
            configs.append(config)
        
        return configs
    
    def add_server(self, config: MCPServerConfig) -> None:
        """添加服务器"""
        if config.transport == "stdio":
            connection = StdioMCPConnection(config)
        else:
            raise ValueError(f"不支持的传输方式: {config.transport}")
        
        self._servers[config.name] = connection
    
    async def connect_all(self) -> None:
        """连接所有启用的服务器"""
        for server in self._servers.values():
            if server.config.enabled:
                try:
                    await server.connect()
                except Exception as e:
                    print(f"连接 MCP 服务器 {server.config.name} 失败: {e}")
    
    async def disconnect_all(self) -> None:
        """断开所有连接"""
        for server in self._servers.values():
            try:
                await server.disconnect()
            except Exception:
                pass
    
    async def discover_tools(self) -> list[MCPTool]:
        """发现所有可用工具"""
        self._tools.clear()
        all_tools = []
        
        for server in self._servers.values():
            if server.is_connected:
                try:
                    tools = await server.list_tools()
                    for tool in tools:
                        self._tools[f"{server.config.name}.{tool.name}"] = tool
                        all_tools.append(tool)
                except Exception:
                    pass
        
        return all_tools
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict,
    ) -> Any:
        """调用 MCP 工具"""
        if server_name not in self._servers:
            raise ValueError(f"服务器未找到: {server_name}")
        
        server = self._servers[server_name]
        if not server.is_connected:
            raise RuntimeError(f"服务器未连接: {server_name}")
        
        return await server.call_tool(tool_name, arguments)
    
    async def read_resource(self, server_name: str, uri: str) -> str:
        """读取 MCP 资源"""
        if server_name not in self._servers:
            raise ValueError(f"服务器未找到: {server_name}")
        
        server = self._servers[server_name]
        if not server.is_connected:
            raise RuntimeError(f"服务器未连接: {server_name}")
        
        return await server.read_resource(uri)
    
    def list_servers(self) -> list[dict]:
        """列出所有服务器"""
        return [
            {
                "name": server.config.name,
                "transport": server.config.transport,
                "enabled": server.config.enabled,
                "connected": server.is_connected,
            }
            for server in self._servers.values()
        ]
    
    def get_tools(self) -> list[MCPTool]:
        """获取已发现的工具"""
        return list(self._tools.values())


# 全局客户端实例
_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """获取全局 MCP 客户端"""
    global _client
    if _client is None:
        from auto.shared.config import DEFAULT_CONFIG_DIR
        config_path = DEFAULT_CONFIG_DIR / "mcp_servers.yaml"
        _client = MCPClient(config_path)
    return _client
