"""健康检查路由"""

from fastapi import APIRouter

from auto import __version__

router = APIRouter()


@router.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "version": __version__,
    }


@router.get("/ready")
async def ready():
    """就绪检查"""
    return {"status": "ready"}


@router.get("/live")
async def live():
    """存活检查"""
    return {"status": "live"}
