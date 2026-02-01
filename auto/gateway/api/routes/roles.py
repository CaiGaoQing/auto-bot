"""角色管理 API 路由"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auto.core.role import get_role_manager, RoleConfig

router = APIRouter()


class RoleResponse(BaseModel):
    """角色响应"""
    code: int = 0
    message: str = "success"
    data: dict = {}


class CreateRoleRequest(BaseModel):
    """创建角色请求"""
    role_id: str
    name: str
    display_name: str
    description: str = ""
    system_prompt: str = ""
    icon: str = "👤"
    enabled_skills: list[str] = []
    permissions: list[str] = []


@router.get("/roles")
async def list_roles() -> RoleResponse:
    """列出所有角色"""
    manager = get_role_manager()
    roles = manager.list_roles()
    
    items = [
        {
            "id": r.id,
            "name": r.name,
            "display_name": r.display_name,
            "description": r.description,
            "icon": r.icon,
            "builtin": r.builtin,
            "enabled_skills": r.config.enabled_skills,
        }
        for r in roles
    ]
    
    return RoleResponse(
        data={
            "items": items,
            "count": len(items),
            "builtin_count": sum(1 for r in roles if r.builtin),
            "custom_count": sum(1 for r in roles if not r.builtin),
        }
    )


@router.get("/roles/{role_id}")
async def get_role(role_id: str) -> RoleResponse:
    """获取角色详情"""
    manager = get_role_manager()
    role = manager.get_role(role_id)
    
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    data = manager.export_role(role_id)
    
    return RoleResponse(data=data)


@router.post("/roles")
async def create_role(request: CreateRoleRequest) -> RoleResponse:
    """创建自定义角色"""
    manager = get_role_manager()
    
    # 检查是否已存在
    if manager.get_role(request.role_id):
        raise HTTPException(status_code=400, detail="角色 ID 已存在")
    
    role = manager.create_custom_role(
        role_id=request.role_id,
        name=request.name,
        display_name=request.display_name,
        description=request.description,
        system_prompt=request.system_prompt,
        enabled_skills=request.enabled_skills,
        permissions=request.permissions,
        icon=request.icon,
    )
    
    return RoleResponse(
        message="角色已创建",
        data={
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
        }
    )


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str) -> RoleResponse:
    """删除自定义角色"""
    manager = get_role_manager()
    
    role = manager.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role.builtin:
        raise HTTPException(status_code=400, detail="无法删除内置角色")
    
    if manager.remove_role(role_id):
        return RoleResponse(message="角色已删除")
    else:
        raise HTTPException(status_code=500, detail="删除失败")


@router.post("/roles/{role_id}/activate")
async def activate_role(role_id: str) -> RoleResponse:
    """激活角色"""
    manager = get_role_manager()
    
    if manager.set_current_role(role_id):
        role = manager.get_role(role_id)
        return RoleResponse(
            message=f"已切换到 {role.display_name}",
            data={
                "role_id": role_id,
                "display_name": role.display_name,
                "enabled_skills": role.config.enabled_skills,
            }
        )
    else:
        raise HTTPException(status_code=404, detail="角色不存在")


@router.get("/roles/current")
async def get_current_role() -> RoleResponse:
    """获取当前角色"""
    manager = get_role_manager()
    role = manager.get_current_role()
    
    if not role:
        return RoleResponse(
            data={"current": None},
            message="未设置当前角色",
        )
    
    return RoleResponse(
        data={
            "current": {
                "id": role.id,
                "display_name": role.display_name,
                "icon": role.icon,
            }
        }
    )


@router.get("/roles/{role_id}/prompt")
async def get_role_prompt(role_id: str) -> RoleResponse:
    """获取角色系统提示词"""
    manager = get_role_manager()
    
    prompt = manager.get_system_prompt(role_id)
    
    if not prompt:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return RoleResponse(
        data={
            "role_id": role_id,
            "system_prompt": prompt,
        }
    )
