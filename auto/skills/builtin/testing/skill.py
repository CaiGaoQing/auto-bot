"""测试助手技能"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class TestingSkill(Skill):
    """测试助手技能
    
    提供 API 测试、UI 自动化测试等功能。
    """
    
    @property
    def name(self) -> str:
        return "testing"
    
    @property
    def display_name(self) -> str:
        return "测试助手"
    
    @property
    def description(self) -> str:
        return "API 测试、UI 自动化、测试用例生成"
    
    @property
    def category(self) -> str:
        return "devops"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="http_request",
                description="发送 HTTP 请求 (API 测试)",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "请求 URL",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                            "description": "HTTP 方法",
                            "default": "GET",
                        },
                        "headers": {
                            "type": "object",
                            "description": "请求头",
                        },
                        "body": {
                            "type": "object",
                            "description": "请求体 (JSON)",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "超时秒数",
                            "default": 30,
                        },
                    },
                    "required": ["url"],
                },
                handler=self.http_request,
            ),
            ToolDefinition(
                name="api_test_suite",
                description="运行 API 测试套件",
                parameters={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "API 基础 URL",
                        },
                        "tests": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "method": {"type": "string"},
                                    "path": {"type": "string"},
                                    "body": {"type": "object"},
                                    "expected_status": {"type": "integer"},
                                },
                            },
                            "description": "测试用例列表",
                        },
                    },
                    "required": ["base_url", "tests"],
                },
                handler=self.api_test_suite,
            ),
            ToolDefinition(
                name="generate_test_cases",
                description="根据 API 规格生成测试用例",
                parameters={
                    "type": "object",
                    "properties": {
                        "api_spec": {
                            "type": "string",
                            "description": "API 规格描述",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["api_spec"],
                },
                handler=self.generate_test_cases,
            ),
            ToolDefinition(
                name="performance_test",
                description="简单的性能测试",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "测试 URL",
                        },
                        "requests": {
                            "type": "integer",
                            "description": "请求次数",
                            "default": 100,
                        },
                        "concurrency": {
                            "type": "integer",
                            "description": "并发数",
                            "default": 10,
                        },
                    },
                    "required": ["url"],
                },
                handler=self.performance_test,
            ),
            ToolDefinition(
                name="generate_pytest_file",
                description="生成 pytest 测试文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "module_name": {
                            "type": "string",
                            "description": "被测模块名",
                        },
                        "functions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "要测试的函数列表",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["module_name", "output_path"],
                },
                handler=self.generate_pytest_file,
            ),
            ToolDefinition(
                name="run_pytest",
                description="运行 pytest 测试",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "测试文件或目录路径",
                        },
                        "verbose": {
                            "type": "boolean",
                            "description": "详细输出",
                            "default": True,
                        },
                        "coverage": {
                            "type": "boolean",
                            "description": "生成覆盖率报告",
                            "default": False,
                        },
                    },
                    "required": ["path"],
                },
                dangerous=True,
                handler=self.run_pytest,
            ),
            ToolDefinition(
                name="health_check",
                description="服务健康检查",
                parameters={
                    "type": "object",
                    "properties": {
                        "endpoints": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "健康检查端点列表",
                        },
                    },
                    "required": ["endpoints"],
                },
                handler=self.health_check,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个测试助手，帮助用户进行软件测试：
- API 接口测试
- 生成测试用例
- 性能测试
- 健康检查

测试原则：
1. 覆盖正常和异常场景
2. 验证边界条件
3. 检查返回状态和数据
4. 记录测试结果"""
    
    async def http_request(
        self,
        ctx: ToolContext,
        url: str,
        method: str = "GET",
        headers: Optional[dict] = None,
        body: Optional[dict] = None,
        timeout: int = 30,
    ) -> ToolResult:
        """发送 HTTP 请求"""
        try:
            import httpx
        except ImportError:
            return ToolResult.error_result("需要安装: pip install httpx")
        
        headers = headers or {}
        
        try:
            start_time = datetime.now()
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=body)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=body)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=body)
                else:
                    return ToolResult.error_result(f"不支持的方法: {method}")
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            
            # 解析响应
            try:
                response_body = response.json()
            except Exception:
                response_body = response.text[:1000]
            
            result = {
                "status_code": response.status_code,
                "elapsed_ms": round(elapsed, 2),
                "headers": dict(response.headers),
                "body": response_body,
            }
            
            success = 200 <= response.status_code < 400
            
            return ToolResult.success_result(
                data=result,
                message=f"{method} {url} -> {response.status_code} ({elapsed:.0f}ms)",
            ) if success else ToolResult.error_result(
                f"请求失败: {response.status_code}"
            )
        
        except httpx.TimeoutException:
            return ToolResult.error_result(f"请求超时 ({timeout}s)")
        except Exception as e:
            return ToolResult.error_result(f"请求失败: {str(e)}")
    
    async def api_test_suite(
        self,
        ctx: ToolContext,
        base_url: str,
        tests: list[dict],
    ) -> ToolResult:
        """运行 API 测试套件"""
        try:
            import httpx
        except ImportError:
            return ToolResult.error_result("需要安装: pip install httpx")
        
        results = []
        passed = 0
        failed = 0
        
        async with httpx.AsyncClient(timeout=30) as client:
            for test in tests:
                name = test.get("name", "Unnamed Test")
                method = test.get("method", "GET").upper()
                path = test.get("path", "/")
                body = test.get("body")
                expected_status = test.get("expected_status", 200)
                
                url = f"{base_url.rstrip('/')}{path}"
                
                try:
                    start = datetime.now()
                    
                    if method == "GET":
                        response = await client.get(url)
                    elif method == "POST":
                        response = await client.post(url, json=body)
                    elif method == "PUT":
                        response = await client.put(url, json=body)
                    elif method == "DELETE":
                        response = await client.delete(url)
                    else:
                        response = await client.get(url)
                    
                    elapsed = (datetime.now() - start).total_seconds() * 1000
                    
                    success = response.status_code == expected_status
                    
                    if success:
                        passed += 1
                    else:
                        failed += 1
                    
                    results.append({
                        "name": name,
                        "status": "✅" if success else "❌",
                        "expected": expected_status,
                        "actual": response.status_code,
                        "time_ms": round(elapsed),
                    })
                
                except Exception as e:
                    failed += 1
                    results.append({
                        "name": name,
                        "status": "❌",
                        "error": str(e),
                    })
        
        return ToolResult.table(
            data=results,
            message=f"测试完成: {passed} 通过, {failed} 失败",
        )
    
    async def generate_test_cases(
        self,
        ctx: ToolContext,
        api_spec: str,
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成测试用例"""
        # 基于 API 规格生成测试用例框架
        content = f"""# API 测试用例

## 测试对象

{api_spec}

---

## 测试用例

### TC-001: 正常请求

**前置条件**: 无

**测试步骤**:
1. 发送正常请求
2. 验证响应状态码为 200
3. 验证响应数据格式

**预期结果**: 返回成功响应

---

### TC-002: 缺少必填参数

**前置条件**: 无

**测试步骤**:
1. 发送缺少必填参数的请求
2. 验证响应状态码为 400

**预期结果**: 返回参数错误

---

### TC-003: 无效参数值

**前置条件**: 无

**测试步骤**:
1. 发送包含无效参数值的请求
2. 验证响应状态码为 400

**预期结果**: 返回验证错误

---

### TC-004: 未授权访问

**前置条件**: 未登录

**测试步骤**:
1. 发送请求但不带认证信息
2. 验证响应状态码为 401

**预期结果**: 返回未授权错误

---

### TC-005: 边界值测试

**前置条件**: 无

**测试步骤**:
1. 测试最小值
2. 测试最大值
3. 测试空值

**预期结果**: 正确处理边界情况

---

## 测试数据

| 场景 | 输入 | 预期输出 |
|------|------|----------|
| 正常 | 有效数据 | 成功 |
| 边界 | 最小/最大值 | 成功 |
| 异常 | 无效数据 | 错误提示 |

---

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}
"""
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message="测试用例已生成")
        
        return ToolResult.success_result(
            data={"content": content},
            message="测试用例已生成",
        )
    
    async def performance_test(
        self,
        ctx: ToolContext,
        url: str,
        requests: int = 100,
        concurrency: int = 10,
    ) -> ToolResult:
        """性能测试"""
        try:
            import httpx
        except ImportError:
            return ToolResult.error_result("需要安装: pip install httpx")
        
        if requests > 1000:
            return ToolResult.error_result("请求次数不能超过 1000")
        
        if concurrency > 50:
            return ToolResult.error_result("并发数不能超过 50")
        
        times = []
        errors = 0
        
        async def make_request(client):
            nonlocal errors
            try:
                start = datetime.now()
                await client.get(url)
                elapsed = (datetime.now() - start).total_seconds() * 1000
                times.append(elapsed)
            except Exception:
                errors += 1
        
        start_time = datetime.now()
        
        async with httpx.AsyncClient(timeout=30) as client:
            # 分批执行
            for i in range(0, requests, concurrency):
                batch_size = min(concurrency, requests - i)
                tasks = [make_request(client) for _ in range(batch_size)]
                await asyncio.gather(*tasks)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        if not times:
            return ToolResult.error_result("所有请求都失败了")
        
        # 计算统计
        times.sort()
        avg = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        p50 = times[int(len(times) * 0.5)]
        p95 = times[int(len(times) * 0.95)]
        p99 = times[int(len(times) * 0.99)] if len(times) >= 100 else times[-1]
        
        rps = len(times) / total_time if total_time > 0 else 0
        
        return ToolResult.success_result(
            data={
                "url": url,
                "total_requests": requests,
                "successful": len(times),
                "failed": errors,
                "total_time_s": round(total_time, 2),
                "rps": round(rps, 2),
                "latency_ms": {
                    "min": round(min_time, 2),
                    "max": round(max_time, 2),
                    "avg": round(avg, 2),
                    "p50": round(p50, 2),
                    "p95": round(p95, 2),
                    "p99": round(p99, 2),
                },
            },
            message=f"RPS: {rps:.1f}, P95: {p95:.0f}ms, 错误: {errors}",
        )
    
    async def generate_pytest_file(
        self,
        ctx: ToolContext,
        module_name: str,
        output_path: str,
        functions: Optional[list[str]] = None,
    ) -> ToolResult:
        """生成 pytest 测试文件"""
        path = Path(output_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {output_path}")
        
        functions = functions or ["example_function"]
        
        content = f'''"""Tests for {module_name}"""

import pytest
# from {module_name} import ...


class Test{module_name.replace(".", "_").title()}:
    """测试类"""
    
    @pytest.fixture
    def setup(self):
        """测试前置"""
        # 准备测试数据
        yield
        # 清理

'''
        
        for func in functions:
            content += f'''    def test_{func}_success(self, setup):
        """测试 {func} 正常情况"""
        # Arrange
        # 准备数据
        
        # Act
        # result = {func}(...)
        
        # Assert
        # assert result == expected
        pass
    
    def test_{func}_edge_case(self, setup):
        """测试 {func} 边界情况"""
        pass
    
    def test_{func}_error(self, setup):
        """测试 {func} 异常情况"""
        # with pytest.raises(ValueError):
        #     {func}(invalid_input)
        pass

'''
        
        content += '''
# 参数化测试示例
# @pytest.mark.parametrize("input,expected", [
#     (1, 1),
#     (2, 4),
#     (3, 9),
# ])
# def test_square(input, expected):
#     assert square(input) == expected
'''
        
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        
        return ToolResult.file(
            path=str(path),
            message=f"pytest 文件已生成 ({len(functions)} 个函数)",
        )
    
    async def run_pytest(
        self,
        ctx: ToolContext,
        path: str,
        verbose: bool = True,
        coverage: bool = False,
    ) -> ToolResult:
        """运行 pytest"""
        test_path = Path(path).expanduser()
        
        if not test_path.exists():
            return ToolResult.error_result(f"路径不存在: {path}")
        
        # 构建命令
        cmd = ["python", "-m", "pytest", str(test_path)]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend(["--cov", "--cov-report=term-missing"])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300,
            )
            
            output = stdout.decode("utf-8", errors="ignore")
            errors = stderr.decode("utf-8", errors="ignore")
            
            success = process.returncode == 0
            
            return ToolResult.success_result(
                data={
                    "exit_code": process.returncode,
                    "output": output[:5000],
                    "errors": errors[:1000] if errors else None,
                },
                message="测试通过" if success else "测试失败",
            )
        
        except asyncio.TimeoutError:
            return ToolResult.error_result("测试执行超时 (5分钟)")
        except Exception as e:
            return ToolResult.error_result(f"执行失败: {str(e)}")
    
    async def health_check(
        self,
        ctx: ToolContext,
        endpoints: list[str],
    ) -> ToolResult:
        """健康检查"""
        try:
            import httpx
        except ImportError:
            return ToolResult.error_result("需要安装: pip install httpx")
        
        results = []
        
        async with httpx.AsyncClient(timeout=10) as client:
            for endpoint in endpoints:
                try:
                    start = datetime.now()
                    response = await client.get(endpoint)
                    elapsed = (datetime.now() - start).total_seconds() * 1000
                    
                    results.append({
                        "endpoint": endpoint,
                        "status": "🟢" if response.status_code == 200 else "🟡",
                        "code": response.status_code,
                        "time_ms": round(elapsed),
                    })
                except Exception as e:
                    results.append({
                        "endpoint": endpoint,
                        "status": "🔴",
                        "error": str(e)[:50],
                    })
        
        healthy = sum(1 for r in results if r["status"] == "🟢")
        
        return ToolResult.table(
            data=results,
            message=f"健康检查: {healthy}/{len(results)} 正常",
        )
