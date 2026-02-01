"""部署助手技能"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class DeploySkill(Skill):
    """部署助手技能
    
    提供项目部署、Docker 配置生成、一键部署等功能。
    """
    
    @property
    def name(self) -> str:
        return "deploy"
    
    @property
    def display_name(self) -> str:
        return "部署助手"
    
    @property
    def description(self) -> str:
        return "自动部署开源项目、生成 Docker 配置、环境检测"
    
    @property
    def category(self) -> str:
        return "devops"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="clone_and_deploy",
                description="克隆 GitHub 项目并部署",
                parameters={
                    "type": "object",
                    "properties": {
                        "repo_url": {
                            "type": "string",
                            "description": "GitHub 仓库 URL",
                        },
                        "deploy_path": {
                            "type": "string",
                            "description": "部署目录路径",
                        },
                        "branch": {
                            "type": "string",
                            "description": "分支名称",
                            "default": "main",
                        },
                    },
                    "required": ["repo_url", "deploy_path"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.clone_and_deploy,
            ),
            ToolDefinition(
                name="generate_dockerfile",
                description="为项目生成 Dockerfile",
                parameters={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "项目路径",
                        },
                        "project_type": {
                            "type": "string",
                            "enum": ["python", "node", "go", "java", "rust", "auto"],
                            "description": "项目类型 (auto 自动检测)",
                            "default": "auto",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Dockerfile 输出路径",
                        },
                    },
                    "required": ["project_path"],
                },
                handler=self.generate_dockerfile,
            ),
            ToolDefinition(
                name="generate_docker_compose",
                description="生成 docker-compose.yml",
                parameters={
                    "type": "object",
                    "properties": {
                        "services": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "image": {"type": "string"},
                                    "ports": {"type": "array", "items": {"type": "string"}},
                                    "environment": {"type": "object"},
                                },
                            },
                            "description": "服务配置列表",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出路径",
                        },
                    },
                    "required": ["services"],
                },
                handler=self.generate_docker_compose,
            ),
            ToolDefinition(
                name="detect_project_type",
                description="检测项目类型和技术栈",
                parameters={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "项目路径",
                        },
                    },
                    "required": ["project_path"],
                },
                handler=self.detect_project_type,
            ),
            ToolDefinition(
                name="check_deploy_env",
                description="检查部署环境",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                handler=self.check_deploy_env,
            ),
            ToolDefinition(
                name="generate_nginx_config",
                description="生成 Nginx 配置",
                parameters={
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "域名",
                        },
                        "upstream_port": {
                            "type": "integer",
                            "description": "上游服务端口",
                            "default": 8000,
                        },
                        "ssl": {
                            "type": "boolean",
                            "description": "是否启用 SSL",
                            "default": False,
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出路径",
                        },
                    },
                    "required": ["domain"],
                },
                handler=self.generate_nginx_config,
            ),
            ToolDefinition(
                name="generate_systemd_service",
                description="生成 systemd 服务文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "服务名称",
                        },
                        "exec_start": {
                            "type": "string",
                            "description": "启动命令",
                        },
                        "working_dir": {
                            "type": "string",
                            "description": "工作目录",
                        },
                        "user": {
                            "type": "string",
                            "description": "运行用户",
                            "default": "root",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出路径",
                        },
                    },
                    "required": ["name", "exec_start", "working_dir"],
                },
                handler=self.generate_systemd_service,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个专业的 DevOps 部署助手，擅长：
- 分析项目结构和依赖
- 生成 Docker/Docker Compose 配置
- 配置 Nginx 反向代理
- 设置 systemd 服务
- 一键部署开源项目

部署原则：
1. 安全第一，最小权限
2. 容器化优先
3. 环境隔离
4. 日志完整
5. 便于回滚"""
    
    async def _run_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 300,
    ) -> tuple[int, str, str]:
        """执行命令"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
            
            return (
                process.returncode or 0,
                stdout.decode("utf-8", errors="ignore"),
                stderr.decode("utf-8", errors="ignore"),
            )
        except asyncio.TimeoutError:
            return (-1, "", "命令执行超时")
        except Exception as e:
            return (-1, "", str(e))
    
    async def clone_and_deploy(
        self,
        ctx: ToolContext,
        repo_url: str,
        deploy_path: str,
        branch: str = "main",
    ) -> ToolResult:
        """克隆并部署项目"""
        path = Path(deploy_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {deploy_path}")
        
        # 验证 URL
        if not re.match(r"https?://github\.com/[\w-]+/[\w.-]+", repo_url):
            return ToolResult.error_result("仅支持 GitHub 仓库 URL")
        
        steps = []
        
        # 1. 创建目录
        path.mkdir(parents=True, exist_ok=True)
        steps.append({"step": "创建目录", "status": "success"})
        
        # 2. 克隆仓库
        clone_cmd = f"git clone --depth 1 --branch {branch} {repo_url} {path}"
        code, stdout, stderr = await self._run_command(clone_cmd)
        
        if code != 0:
            steps.append({"step": "克隆仓库", "status": "failed", "error": stderr})
            return ToolResult.error_result(f"克隆失败: {stderr}")
        
        steps.append({"step": "克隆仓库", "status": "success"})
        
        # 3. 检测项目类型
        detect_result = await self.detect_project_type(ctx, str(path))
        project_info = detect_result.data if detect_result.success else {}
        
        steps.append({
            "step": "检测项目",
            "status": "success",
            "info": project_info,
        })
        
        # 4. 根据项目类型执行部署
        project_type = project_info.get("type", "unknown")
        
        if project_type == "python":
            # Python 项目
            if (path / "requirements.txt").exists():
                code, _, stderr = await self._run_command(
                    "pip install -r requirements.txt",
                    cwd=str(path),
                )
                if code == 0:
                    steps.append({"step": "安装依赖", "status": "success"})
                else:
                    steps.append({"step": "安装依赖", "status": "warning", "error": stderr})
        
        elif project_type == "node":
            # Node.js 项目
            if (path / "package.json").exists():
                code, _, stderr = await self._run_command(
                    "npm install",
                    cwd=str(path),
                )
                if code == 0:
                    steps.append({"step": "安装依赖", "status": "success"})
                else:
                    steps.append({"step": "安装依赖", "status": "warning", "error": stderr})
        
        # 5. 检查是否有 docker-compose
        if (path / "docker-compose.yml").exists() or (path / "docker-compose.yaml").exists():
            steps.append({
                "step": "发现 Docker Compose",
                "status": "info",
                "hint": "运行: docker-compose up -d",
            })
        
        return ToolResult.success_result(
            data={
                "repo_url": repo_url,
                "deploy_path": str(path),
                "branch": branch,
                "project_type": project_type,
                "steps": steps,
            },
            message=f"项目已克隆到 {path}",
        )
    
    async def generate_dockerfile(
        self,
        ctx: ToolContext,
        project_path: str,
        project_type: str = "auto",
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成 Dockerfile"""
        path = Path(project_path).expanduser()
        
        if not path.exists():
            return ToolResult.error_result(f"项目路径不存在: {project_path}")
        
        # 自动检测项目类型
        if project_type == "auto":
            detect_result = await self.detect_project_type(ctx, project_path)
            if detect_result.success:
                project_type = detect_result.data.get("type", "unknown")
        
        # 生成 Dockerfile
        dockerfile_content = self._generate_dockerfile_content(path, project_type)
        
        # 输出路径
        if output_path:
            out_path = Path(output_path).expanduser()
        else:
            out_path = path / "Dockerfile"
        
        if ctx.security.is_allowed_path(out_path):
            out_path.write_text(dockerfile_content, encoding="utf-8")
            return ToolResult.file(
                path=str(out_path),
                message=f"Dockerfile 已生成 ({project_type})",
            )
        
        return ToolResult.success_result(
            data={"content": dockerfile_content, "project_type": project_type},
            message="Dockerfile 内容已生成",
        )
    
    def _generate_dockerfile_content(self, path: Path, project_type: str) -> str:
        """生成 Dockerfile 内容"""
        if project_type == "python":
            return f"""# Python 应用 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        elif project_type == "node":
            return """# Node.js 应用 Dockerfile
FROM node:18-alpine

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm ci --only=production

# 复制代码
COPY . .

# 构建 (如果需要)
# RUN npm run build

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["npm", "start"]
"""
        
        elif project_type == "go":
            return """# Go 应用 Dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app

# 下载依赖
COPY go.mod go.sum ./
RUN go mod download

# 构建
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

# 运行镜像
FROM alpine:latest

WORKDIR /app
COPY --from=builder /app/main .

EXPOSE 8080

CMD ["./main"]
"""
        
        elif project_type == "java":
            return """# Java 应用 Dockerfile
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline

COPY src ./src
RUN mvn package -DskipTests

# 运行镜像
FROM eclipse-temurin:17-jre

WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]
"""
        
        else:
            return """# 通用 Dockerfile
FROM ubuntu:22.04

WORKDIR /app

# 安装基础工具
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

COPY . .

# 请根据项目类型修改以下配置
EXPOSE 8000

CMD ["./start.sh"]
"""
    
    async def generate_docker_compose(
        self,
        ctx: ToolContext,
        services: list[dict],
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成 docker-compose.yml"""
        if not services:
            return ToolResult.error_result("服务列表不能为空")
        
        # 构建 YAML 内容
        content = """version: '3.8'

services:
"""
        
        for service in services:
            name = service.get("name", "app")
            image = service.get("image", "")
            ports = service.get("ports", [])
            environment = service.get("environment", {})
            volumes = service.get("volumes", [])
            depends_on = service.get("depends_on", [])
            
            content += f"""  {name}:
"""
            if image:
                content += f"    image: {image}\n"
            else:
                content += f"    build: .\n"
            
            if ports:
                content += "    ports:\n"
                for port in ports:
                    content += f"      - \"{port}\"\n"
            
            if environment:
                content += "    environment:\n"
                for key, value in environment.items():
                    content += f"      {key}: {value}\n"
            
            if volumes:
                content += "    volumes:\n"
                for vol in volumes:
                    content += f"      - {vol}\n"
            
            if depends_on:
                content += "    depends_on:\n"
                for dep in depends_on:
                    content += f"      - {dep}\n"
            
            content += "    restart: unless-stopped\n\n"
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message="docker-compose.yml 已生成")
        
        return ToolResult.success_result(
            data={"content": content},
            message=f"docker-compose 已生成，包含 {len(services)} 个服务",
        )
    
    async def detect_project_type(
        self,
        ctx: ToolContext,
        project_path: str,
    ) -> ToolResult:
        """检测项目类型"""
        path = Path(project_path).expanduser()
        
        if not path.exists():
            return ToolResult.error_result(f"路径不存在: {project_path}")
        
        project_type = "unknown"
        framework = ""
        files_found = []
        
        # Python
        if (path / "requirements.txt").exists():
            project_type = "python"
            files_found.append("requirements.txt")
        if (path / "pyproject.toml").exists():
            project_type = "python"
            files_found.append("pyproject.toml")
        if (path / "setup.py").exists():
            project_type = "python"
            files_found.append("setup.py")
        
        # Node.js
        if (path / "package.json").exists():
            project_type = "node"
            files_found.append("package.json")
            
            # 检测框架
            try:
                import json
                pkg = json.loads((path / "package.json").read_text())
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                
                if "next" in deps:
                    framework = "Next.js"
                elif "nuxt" in deps:
                    framework = "Nuxt.js"
                elif "react" in deps:
                    framework = "React"
                elif "vue" in deps:
                    framework = "Vue"
                elif "express" in deps:
                    framework = "Express"
            except Exception:
                pass
        
        # Go
        if (path / "go.mod").exists():
            project_type = "go"
            files_found.append("go.mod")
        
        # Java
        if (path / "pom.xml").exists():
            project_type = "java"
            framework = "Maven"
            files_found.append("pom.xml")
        if (path / "build.gradle").exists():
            project_type = "java"
            framework = "Gradle"
            files_found.append("build.gradle")
        
        # Rust
        if (path / "Cargo.toml").exists():
            project_type = "rust"
            files_found.append("Cargo.toml")
        
        # Docker
        has_docker = (path / "Dockerfile").exists()
        has_compose = (path / "docker-compose.yml").exists() or (path / "docker-compose.yaml").exists()
        
        return ToolResult.success_result(
            data={
                "type": project_type,
                "framework": framework,
                "files_found": files_found,
                "has_dockerfile": has_docker,
                "has_docker_compose": has_compose,
            },
            message=f"项目类型: {project_type}" + (f" ({framework})" if framework else ""),
        )
    
    async def check_deploy_env(self, ctx: ToolContext) -> ToolResult:
        """检查部署环境"""
        checks = []
        
        # 检查 Docker
        code, stdout, _ = await self._run_command("docker --version")
        if code == 0:
            checks.append({"name": "Docker", "status": "ok", "version": stdout.strip()})
        else:
            checks.append({"name": "Docker", "status": "missing"})
        
        # 检查 Docker Compose
        code, stdout, _ = await self._run_command("docker-compose --version")
        if code == 0:
            checks.append({"name": "Docker Compose", "status": "ok", "version": stdout.strip()})
        else:
            # 尝试新版本
            code, stdout, _ = await self._run_command("docker compose version")
            if code == 0:
                checks.append({"name": "Docker Compose", "status": "ok", "version": stdout.strip()})
            else:
                checks.append({"name": "Docker Compose", "status": "missing"})
        
        # 检查 Git
        code, stdout, _ = await self._run_command("git --version")
        if code == 0:
            checks.append({"name": "Git", "status": "ok", "version": stdout.strip()})
        else:
            checks.append({"name": "Git", "status": "missing"})
        
        # 检查 Python
        code, stdout, _ = await self._run_command("python3 --version")
        if code == 0:
            checks.append({"name": "Python", "status": "ok", "version": stdout.strip()})
        else:
            checks.append({"name": "Python", "status": "missing"})
        
        # 检查 Node
        code, stdout, _ = await self._run_command("node --version")
        if code == 0:
            checks.append({"name": "Node.js", "status": "ok", "version": stdout.strip()})
        else:
            checks.append({"name": "Node.js", "status": "not installed"})
        
        all_ok = all(c["status"] == "ok" for c in checks if c["name"] in ["Docker", "Git"])
        
        return ToolResult.table(
            data=checks,
            message="环境检查完成" + ("" if all_ok else " (部分组件缺失)"),
        )
    
    async def generate_nginx_config(
        self,
        ctx: ToolContext,
        domain: str,
        upstream_port: int = 8000,
        ssl: bool = False,
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成 Nginx 配置"""
        if ssl:
            content = f"""server {{
    listen 80;
    server_name {domain};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {domain};

    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    location / {{
        proxy_pass http://127.0.0.1:{upstream_port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}
}}
"""
        else:
            content = f"""server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://127.0.0.1:{upstream_port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}
}}
"""
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message="Nginx 配置已生成")
        
        return ToolResult.success_result(
            data={"content": content, "domain": domain, "ssl": ssl},
            message=f"Nginx 配置已生成 (域名: {domain})",
        )
    
    async def generate_systemd_service(
        self,
        ctx: ToolContext,
        name: str,
        exec_start: str,
        working_dir: str,
        user: str = "root",
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成 systemd 服务文件"""
        content = f"""[Unit]
Description={name} Service
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={working_dir}
ExecStart={exec_start}
Restart=always
RestartSec=5

# 日志
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier={name}

# 环境变量
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
"""
        
        if output_path:
            path = Path(output_path).expanduser()
        else:
            path = Path(f"/etc/systemd/system/{name}.service")
        
        # 只返回内容，不实际写入系统目录
        return ToolResult.success_result(
            data={
                "content": content,
                "service_name": name,
                "commands": [
                    f"sudo cp {name}.service /etc/systemd/system/",
                    "sudo systemctl daemon-reload",
                    f"sudo systemctl enable {name}",
                    f"sudo systemctl start {name}",
                ],
            },
            message=f"systemd 服务文件已生成: {name}.service",
        )
