"""运维助手技能"""

import asyncio
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class DevOpsSkill(Skill):
    """运维助手技能
    
    提供 Docker、MySQL、Redis 等运维操作能力。
    """
    
    @property
    def name(self) -> str:
        return "devops"
    
    @property
    def display_name(self) -> str:
        return "运维助手"
    
    @property
    def description(self) -> str:
        return "Docker 容器管理、MySQL 数据库操作、Redis 缓存管理"
    
    @property
    def category(self) -> str:
        return "devops"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            # Docker 工具
            ToolDefinition(
                name="docker_ps",
                description="列出 Docker 容器",
                parameters={
                    "type": "object",
                    "properties": {
                        "all": {
                            "type": "boolean",
                            "description": "显示所有容器（包括已停止的）",
                            "default": False,
                        },
                    },
                },
                handler=self.docker_ps,
            ),
            ToolDefinition(
                name="docker_images",
                description="列出 Docker 镜像",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                handler=self.docker_images,
            ),
            ToolDefinition(
                name="docker_logs",
                description="查看容器日志",
                parameters={
                    "type": "object",
                    "properties": {
                        "container": {
                            "type": "string",
                            "description": "容器名称或 ID",
                        },
                        "tail": {
                            "type": "integer",
                            "description": "显示最后 N 行",
                            "default": 100,
                        },
                    },
                    "required": ["container"],
                },
                handler=self.docker_logs,
            ),
            ToolDefinition(
                name="docker_exec",
                description="在容器中执行命令",
                parameters={
                    "type": "object",
                    "properties": {
                        "container": {
                            "type": "string",
                            "description": "容器名称或 ID",
                        },
                        "command": {
                            "type": "string",
                            "description": "要执行的命令",
                        },
                    },
                    "required": ["container", "command"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.docker_exec,
            ),
            ToolDefinition(
                name="docker_start",
                description="启动容器",
                parameters={
                    "type": "object",
                    "properties": {
                        "container": {
                            "type": "string",
                            "description": "容器名称或 ID",
                        },
                    },
                    "required": ["container"],
                },
                handler=self.docker_start,
            ),
            ToolDefinition(
                name="docker_stop",
                description="停止容器",
                parameters={
                    "type": "object",
                    "properties": {
                        "container": {
                            "type": "string",
                            "description": "容器名称或 ID",
                        },
                    },
                    "required": ["container"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.docker_stop,
            ),
            ToolDefinition(
                name="docker_restart",
                description="重启容器",
                parameters={
                    "type": "object",
                    "properties": {
                        "container": {
                            "type": "string",
                            "description": "容器名称或 ID",
                        },
                    },
                    "required": ["container"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.docker_restart,
            ),
            # MySQL 工具
            ToolDefinition(
                name="mysql_query",
                description="执行 MySQL 查询",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL 查询语句",
                        },
                        "database": {
                            "type": "string",
                            "description": "数据库名称",
                        },
                        "host": {
                            "type": "string",
                            "description": "数据库主机",
                            "default": "localhost",
                        },
                        "port": {
                            "type": "integer",
                            "description": "端口",
                            "default": 3306,
                        },
                    },
                    "required": ["query", "database"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.mysql_query,
            ),
            ToolDefinition(
                name="mysql_show_databases",
                description="显示 MySQL 数据库列表",
                parameters={
                    "type": "object",
                    "properties": {
                        "host": {
                            "type": "string",
                            "default": "localhost",
                        },
                        "port": {
                            "type": "integer",
                            "default": 3306,
                        },
                    },
                },
                handler=self.mysql_show_databases,
            ),
            ToolDefinition(
                name="mysql_show_tables",
                description="显示数据库中的表",
                parameters={
                    "type": "object",
                    "properties": {
                        "database": {
                            "type": "string",
                            "description": "数据库名称",
                        },
                        "host": {
                            "type": "string",
                            "default": "localhost",
                        },
                        "port": {
                            "type": "integer",
                            "default": 3306,
                        },
                    },
                    "required": ["database"],
                },
                handler=self.mysql_show_tables,
            ),
            # Redis 工具
            ToolDefinition(
                name="redis_get",
                description="获取 Redis 键值",
                parameters={
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "键名",
                        },
                        "host": {
                            "type": "string",
                            "default": "localhost",
                        },
                        "port": {
                            "type": "integer",
                            "default": 6379,
                        },
                    },
                    "required": ["key"],
                },
                handler=self.redis_get,
            ),
            ToolDefinition(
                name="redis_set",
                description="设置 Redis 键值",
                parameters={
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "键名",
                        },
                        "value": {
                            "type": "string",
                            "description": "值",
                        },
                        "ttl": {
                            "type": "integer",
                            "description": "过期时间（秒）",
                        },
                        "host": {
                            "type": "string",
                            "default": "localhost",
                        },
                        "port": {
                            "type": "integer",
                            "default": 6379,
                        },
                    },
                    "required": ["key", "value"],
                },
                handler=self.redis_set,
            ),
            ToolDefinition(
                name="redis_keys",
                description="列出 Redis 键（支持模式匹配）",
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "匹配模式",
                            "default": "*",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "限制返回数量",
                            "default": 100,
                        },
                        "host": {
                            "type": "string",
                            "default": "localhost",
                        },
                        "port": {
                            "type": "integer",
                            "default": 6379,
                        },
                    },
                },
                handler=self.redis_keys,
            ),
            ToolDefinition(
                name="redis_info",
                description="获取 Redis 服务器信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "description": "信息部分 (server, clients, memory, stats, etc.)",
                        },
                        "host": {
                            "type": "string",
                            "default": "localhost",
                        },
                        "port": {
                            "type": "integer",
                            "default": 6379,
                        },
                    },
                },
                handler=self.redis_info,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个专业的运维助手，擅长：
- Docker 容器管理和故障排查
- MySQL 数据库运维和查询优化
- Redis 缓存管理和性能调优
- 系统监控和日志分析

安全规则：
- 危险操作（停止容器、修改数据）需要用户确认
- 不执行破坏性命令（DROP、DELETE、TRUNCATE）除非明确授权
- 保护敏感信息（密码、密钥）"""
    
    async def _run_command(
        self,
        command: str,
        timeout: int = 30,
    ) -> tuple[int, str, str]:
        """执行系统命令"""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
            return (
                process.returncode or 0,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace"),
            )
        except asyncio.TimeoutError:
            process.kill()
            return -1, "", "命令执行超时"
    
    # Docker 工具实现
    async def docker_ps(
        self,
        ctx: ToolContext,
        all: bool = False,
    ) -> ToolResult:
        """列出 Docker 容器"""
        cmd = "docker ps --format '{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'"
        if all:
            cmd = "docker ps -a --format '{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'"
        
        code, stdout, stderr = await self._run_command(cmd)
        
        if code != 0:
            return ToolResult.error_result(f"Docker 命令失败: {stderr}")
        
        containers = []
        for line in stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) >= 4:
                    containers.append({
                        "id": parts[0],
                        "name": parts[1],
                        "image": parts[2],
                        "status": parts[3],
                        "ports": parts[4] if len(parts) > 4 else "",
                    })
        
        return ToolResult.table(
            data=containers,
            message=f"找到 {len(containers)} 个容器",
        )
    
    async def docker_images(self, ctx: ToolContext) -> ToolResult:
        """列出 Docker 镜像"""
        cmd = "docker images --format '{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}'"
        
        code, stdout, stderr = await self._run_command(cmd)
        
        if code != 0:
            return ToolResult.error_result(f"Docker 命令失败: {stderr}")
        
        images = []
        for line in stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) >= 4:
                    images.append({
                        "repository": parts[0],
                        "tag": parts[1],
                        "id": parts[2],
                        "size": parts[3],
                        "created": parts[4] if len(parts) > 4 else "",
                    })
        
        return ToolResult.table(
            data=images,
            message=f"找到 {len(images)} 个镜像",
        )
    
    async def docker_logs(
        self,
        ctx: ToolContext,
        container: str,
        tail: int = 100,
    ) -> ToolResult:
        """查看容器日志"""
        cmd = f"docker logs --tail {tail} {container}"
        
        code, stdout, stderr = await self._run_command(cmd, timeout=60)
        
        if code != 0:
            return ToolResult.error_result(f"获取日志失败: {stderr}")
        
        # 合并 stdout 和 stderr（日志可能在任一流中）
        logs = stdout + stderr
        
        return ToolResult.success_result(
            data={"logs": logs, "lines": len(logs.split("\n"))},
            message=f"获取到 {container} 的日志",
        )
    
    async def docker_exec(
        self,
        ctx: ToolContext,
        container: str,
        command: str,
    ) -> ToolResult:
        """在容器中执行命令"""
        # 安全检查
        if ctx.security.is_dangerous_operation(command):
            return ToolResult.error_result(f"检测到危险命令: {command}")
        
        cmd = f"docker exec {container} {command}"
        
        code, stdout, stderr = await self._run_command(cmd)
        
        return ToolResult.success_result(
            data={
                "exit_code": code,
                "stdout": stdout,
                "stderr": stderr,
            },
            message=f"命令执行完成，退出码: {code}",
        )
    
    async def docker_start(
        self,
        ctx: ToolContext,
        container: str,
    ) -> ToolResult:
        """启动容器"""
        cmd = f"docker start {container}"
        code, stdout, stderr = await self._run_command(cmd)
        
        if code != 0:
            return ToolResult.error_result(f"启动失败: {stderr}")
        
        return ToolResult.success_result(
            message=f"容器 {container} 已启动",
        )
    
    async def docker_stop(
        self,
        ctx: ToolContext,
        container: str,
    ) -> ToolResult:
        """停止容器"""
        cmd = f"docker stop {container}"
        code, stdout, stderr = await self._run_command(cmd)
        
        if code != 0:
            return ToolResult.error_result(f"停止失败: {stderr}")
        
        return ToolResult.success_result(
            message=f"容器 {container} 已停止",
        )
    
    async def docker_restart(
        self,
        ctx: ToolContext,
        container: str,
    ) -> ToolResult:
        """重启容器"""
        cmd = f"docker restart {container}"
        code, stdout, stderr = await self._run_command(cmd)
        
        if code != 0:
            return ToolResult.error_result(f"重启失败: {stderr}")
        
        return ToolResult.success_result(
            message=f"容器 {container} 已重启",
        )
    
    # MySQL 工具实现
    async def mysql_query(
        self,
        ctx: ToolContext,
        query: str,
        database: str,
        host: str = "localhost",
        port: int = 3306,
    ) -> ToolResult:
        """执行 MySQL 查询"""
        # 安全检查 - 禁止危险操作
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE"]
        query_upper = query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper and not query_upper.strip().startswith("SELECT"):
                return ToolResult.error_result(
                    f"检测到危险操作 {keyword}，需要明确授权"
                )
        
        try:
            import aiomysql
        except ImportError:
            return ToolResult.error_result("需要安装 aiomysql: pip install aiomysql")
        
        # 从配置获取凭证
        username = ctx.config.get("mysql_user", "root")
        password = ctx.config.get("mysql_password", "")
        
        try:
            conn = await aiomysql.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                db=database,
            )
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query)
                
                if query_upper.strip().startswith("SELECT"):
                    rows = await cursor.fetchall()
                    return ToolResult.table(
                        data=list(rows),
                        message=f"查询返回 {len(rows)} 行",
                    )
                else:
                    await conn.commit()
                    return ToolResult.success_result(
                        data={"affected_rows": cursor.rowcount},
                        message=f"执行成功，影响 {cursor.rowcount} 行",
                    )
            
            conn.close()
        except Exception as e:
            return ToolResult.error_result(f"MySQL 错误: {str(e)}")
    
    async def mysql_show_databases(
        self,
        ctx: ToolContext,
        host: str = "localhost",
        port: int = 3306,
    ) -> ToolResult:
        """显示数据库列表"""
        return await self.mysql_query(
            ctx,
            "SHOW DATABASES",
            "information_schema",
            host,
            port,
        )
    
    async def mysql_show_tables(
        self,
        ctx: ToolContext,
        database: str,
        host: str = "localhost",
        port: int = 3306,
    ) -> ToolResult:
        """显示表列表"""
        return await self.mysql_query(
            ctx,
            "SHOW TABLES",
            database,
            host,
            port,
        )
    
    # Redis 工具实现
    async def _get_redis(self, host: str, port: int):
        """获取 Redis 连接"""
        try:
            import redis.asyncio as redis
        except ImportError:
            raise ImportError("需要安装 redis: pip install redis")
        
        return redis.Redis(host=host, port=port, decode_responses=True)
    
    async def redis_get(
        self,
        ctx: ToolContext,
        key: str,
        host: str = "localhost",
        port: int = 6379,
    ) -> ToolResult:
        """获取 Redis 键值"""
        try:
            r = await self._get_redis(host, port)
            value = await r.get(key)
            key_type = await r.type(key)
            ttl = await r.ttl(key)
            await r.close()
            
            if value is None:
                return ToolResult.success_result(
                    data={"key": key, "exists": False},
                    message=f"键 {key} 不存在",
                )
            
            return ToolResult.success_result(
                data={
                    "key": key,
                    "value": value,
                    "type": key_type,
                    "ttl": ttl if ttl > 0 else None,
                },
                message=f"获取到键 {key} 的值",
            )
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"Redis 错误: {str(e)}")
    
    async def redis_set(
        self,
        ctx: ToolContext,
        key: str,
        value: str,
        ttl: Optional[int] = None,
        host: str = "localhost",
        port: int = 6379,
    ) -> ToolResult:
        """设置 Redis 键值"""
        try:
            r = await self._get_redis(host, port)
            
            if ttl:
                await r.setex(key, ttl, value)
            else:
                await r.set(key, value)
            
            await r.close()
            
            return ToolResult.success_result(
                data={"key": key, "ttl": ttl},
                message=f"键 {key} 已设置",
            )
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"Redis 错误: {str(e)}")
    
    async def redis_keys(
        self,
        ctx: ToolContext,
        pattern: str = "*",
        limit: int = 100,
        host: str = "localhost",
        port: int = 6379,
    ) -> ToolResult:
        """列出 Redis 键"""
        try:
            r = await self._get_redis(host, port)
            
            keys = []
            async for key in r.scan_iter(match=pattern, count=limit):
                keys.append(key)
                if len(keys) >= limit:
                    break
            
            await r.close()
            
            return ToolResult.success_result(
                data={"keys": keys, "pattern": pattern},
                message=f"找到 {len(keys)} 个键",
            )
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"Redis 错误: {str(e)}")
    
    async def redis_info(
        self,
        ctx: ToolContext,
        section: Optional[str] = None,
        host: str = "localhost",
        port: int = 6379,
    ) -> ToolResult:
        """获取 Redis 服务器信息"""
        try:
            r = await self._get_redis(host, port)
            
            if section:
                info = await r.info(section)
            else:
                info = await r.info()
            
            await r.close()
            
            return ToolResult.success_result(
                data=info,
                message="Redis 服务器信息",
            )
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"Redis 错误: {str(e)}")
