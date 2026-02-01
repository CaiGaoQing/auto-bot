"""FastAPI 应用"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auto import __version__


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """应用生命周期管理"""
    # 启动时初始化
    from auto.core.skill.engine import get_skill_engine
    from auto.integration.mcp.client import get_mcp_client
    from auto.core.scheduler import get_scheduler
    
    # 加载技能包
    skill_engine = get_skill_engine()
    skill_engine.load_builtin_skills()
    
    # 连接 MCP 服务器
    mcp_client = get_mcp_client()
    configs = mcp_client.load_config()
    for config in configs:
        mcp_client.add_server(config)
    await mcp_client.connect_all()
    
    # 启动调度器
    scheduler = get_scheduler()
    await scheduler.start()
    
    yield
    
    # 关闭时清理
    await scheduler.stop()
    await mcp_client.disconnect_all()


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="AI Auto API",
        description="AI 个人助手后端 API",
        version=__version__,
        lifespan=lifespan,
    )
    
    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    from auto.gateway.api.routes import (
        health,
        chat,
        workspaces,
        skills,
        providers,
        webhook,
        scheduler,
        usage,
        ws,
        audit,
        roles,
        budget,
        tasks,
        channels,
    )
    
    app.include_router(health.router, tags=["Health"])
    app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
    app.include_router(workspaces.router, prefix="/api/v1", tags=["Workspaces"])
    app.include_router(skills.router, prefix="/api/v1", tags=["Skills"])
    app.include_router(providers.router, prefix="/api/v1", tags=["Providers"])
    app.include_router(webhook.router, prefix="/api/v1", tags=["Webhook"])
    app.include_router(scheduler.router, prefix="/api/v1", tags=["Scheduler"])
    app.include_router(usage.router, prefix="/api/v1", tags=["Usage"])
    app.include_router(audit.router, prefix="/api/v1", tags=["Audit"])
    app.include_router(roles.router, prefix="/api/v1", tags=["Roles"])
    app.include_router(budget.router, prefix="/api/v1", tags=["Budget"])
    app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])  # 移动端友好任务接口
    app.include_router(channels.router, prefix="/api/v1", tags=["Channels"])  # 多渠道管理
    app.include_router(ws.router, tags=["WebSocket"])
    
    return app


# 创建默认应用实例
app = create_app()
