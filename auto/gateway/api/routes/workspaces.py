"""工作空间路由 - 完整实现"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter()

# 工作空间根目录 - 使用项目目录下的 data 文件夹
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent  # auto/gateway/api/routes -> project root
WORKSPACES_ROOT = _PROJECT_ROOT / "data" / "workspaces"
WORKSPACES_ROOT.mkdir(parents=True, exist_ok=True)


class WorkspaceCreate(BaseModel):
    """创建工作空间请求"""
    name: str
    roles: List[str] = ["assistant"]  # 支持多角色
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    """更新工作空间请求"""
    name: Optional[str] = None
    roles: Optional[List[str]] = None  # 支持更新角色列表
    description: Optional[str] = None


class FolderCreate(BaseModel):
    """创建文件夹请求"""
    path: str  # 相对路径，如 "code/frontend"


class WorkspaceResponse(BaseModel):
    """工作空间响应"""
    code: int = 0
    message: str = "success"
    data: dict


class WorkspaceInfo:
    """工作空间信息管理"""
    
    @staticmethod
    def get_workspace_path(workspace_id: str) -> Path:
        return WORKSPACES_ROOT / workspace_id
    
    @staticmethod
    def get_meta_path(workspace_id: str) -> Path:
        return WORKSPACES_ROOT / workspace_id / ".workspace.json"
    
    @staticmethod
    def get_files_path(workspace_id: str) -> Path:
        path = WORKSPACES_ROOT / workspace_id / "files"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_outputs_path(workspace_id: str) -> Path:
        path = WORKSPACES_ROOT / workspace_id / "outputs"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_logs_path(workspace_id: str) -> Path:
        path = WORKSPACES_ROOT / workspace_id / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def load_meta(workspace_id: str) -> Optional[dict]:
        meta_path = WorkspaceInfo.get_meta_path(workspace_id)
        if meta_path.exists():
            return json.loads(meta_path.read_text(encoding="utf-8"))
        return None
    
    @staticmethod
    def save_meta(workspace_id: str, meta: dict):
        meta_path = WorkspaceInfo.get_meta_path(workspace_id)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_workspace_id() -> str:
    """生成工作空间 ID"""
    import hashlib
    import time
    return f"ws_{hashlib.md5(str(time.time()).encode()).hexdigest()[:12]}"


def slugify(text: str) -> str:
    """将文本转换为 URL 友好的 slug"""
    import re
    # 保留中文、字母、数字
    text = re.sub(r'[^\w\u4e00-\u9fff-]', '-', text.lower())
    text = re.sub(r'-+', '-', text).strip('-')
    return text or 'workspace'


@router.get("/workspaces")
async def list_workspaces() -> WorkspaceResponse:
    """列出所有工作空间"""
    workspaces = []
    
    if WORKSPACES_ROOT.exists():
        for ws_dir in WORKSPACES_ROOT.iterdir():
            if ws_dir.is_dir() and not ws_dir.name.startswith('.'):
                meta = WorkspaceInfo.load_meta(ws_dir.name)
                if meta:
                    # 统计文件数量
                    files_path = WorkspaceInfo.get_files_path(ws_dir.name)
                    outputs_path = WorkspaceInfo.get_outputs_path(ws_dir.name)
                    
                    meta["files_count"] = len(list(files_path.glob("*"))) if files_path.exists() else 0
                    meta["outputs_count"] = len(list(outputs_path.glob("*"))) if outputs_path.exists() else 0
                    
                    workspaces.append(meta)
    
    # 按创建时间排序
    workspaces.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return WorkspaceResponse(
        data={
            "items": workspaces,
            "total": len(workspaces),
        }
    )


@router.post("/workspaces")
async def create_workspace(request: WorkspaceCreate) -> WorkspaceResponse:
    """创建工作空间"""
    workspace_id = generate_workspace_id()
    workspace_path = WorkspaceInfo.get_workspace_path(workspace_id)
    
    # 创建目录结构
    workspace_path.mkdir(parents=True, exist_ok=True)
    WorkspaceInfo.get_files_path(workspace_id)
    WorkspaceInfo.get_outputs_path(workspace_id)
    WorkspaceInfo.get_logs_path(workspace_id)
    
    # 保存元数据
    now = datetime.now().isoformat()
    meta = {
        "id": workspace_id,
        "name": request.name,
        "slug": slugify(request.name),
        "roles": request.roles,  # 多角色支持
        "description": request.description or "",
        "created_at": now,
        "updated_at": now,
        "path": str(workspace_path),
    }
    
    WorkspaceInfo.save_meta(workspace_id, meta)
    
    return WorkspaceResponse(data=meta)


@router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str) -> WorkspaceResponse:
    """获取工作空间详情"""
    meta = WorkspaceInfo.load_meta(workspace_id)
    if not meta:
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    # 获取文件列表
    files_path = WorkspaceInfo.get_files_path(workspace_id)
    outputs_path = WorkspaceInfo.get_outputs_path(workspace_id)
    
    files = []
    for f in files_path.glob("*"):
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "type": "input",
                "created_at": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
            })
    
    outputs = []
    for f in outputs_path.glob("*"):
        if f.is_file():
            outputs.append({
                "name": f.name,
                "size": f.stat().st_size,
                "type": "output",
                "created_at": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
            })
    
    meta["files"] = files
    meta["outputs"] = outputs
    
    return WorkspaceResponse(data=meta)


@router.patch("/workspaces/{workspace_id}")
async def update_workspace(workspace_id: str, request: WorkspaceUpdate) -> WorkspaceResponse:
    """更新工作空间"""
    meta = WorkspaceInfo.load_meta(workspace_id)
    if not meta:
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    if request.name:
        meta["name"] = request.name
        meta["slug"] = slugify(request.name)
    if request.roles is not None:
        meta["roles"] = request.roles
    if request.description is not None:
        meta["description"] = request.description
    
    meta["updated_at"] = datetime.now().isoformat()
    WorkspaceInfo.save_meta(workspace_id, meta)
    
    return WorkspaceResponse(data=meta)


@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(workspace_id: str) -> WorkspaceResponse:
    """删除工作空间"""
    workspace_path = WorkspaceInfo.get_workspace_path(workspace_id)
    
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    # 删除整个目录
    shutil.rmtree(workspace_path)
    
    return WorkspaceResponse(message="删除成功", data={"id": workspace_id})


# ===== 文件管理 =====

@router.post("/workspaces/{workspace_id}/files")
async def upload_file(
    workspace_id: str,
    file: UploadFile = File(...),
) -> WorkspaceResponse:
    """上传文件到工作空间"""
    meta = WorkspaceInfo.load_meta(workspace_id)
    if not meta:
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    files_path = WorkspaceInfo.get_files_path(workspace_id)
    
    # 安全的文件名
    safe_filename = file.filename.replace("/", "_").replace("\\", "_")
    file_path = files_path / safe_filename
    
    # 如果文件已存在，添加时间戳
    if file_path.exists():
        stem = file_path.stem
        suffix = file_path.suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{stem}_{timestamp}{suffix}"
        file_path = files_path / safe_filename
    
    # 保存文件
    content = await file.read()
    file_path.write_bytes(content)
    
    return WorkspaceResponse(
        data={
            "filename": safe_filename,
            "size": len(content),
            "path": str(file_path),
            "type": "input",
        }
    )


@router.get("/workspaces/{workspace_id}/files")
async def list_files(workspace_id: str) -> WorkspaceResponse:
    """列出工作空间的所有文件"""
    meta = WorkspaceInfo.load_meta(workspace_id)
    if not meta:
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    files_path = WorkspaceInfo.get_files_path(workspace_id)
    outputs_path = WorkspaceInfo.get_outputs_path(workspace_id)
    
    files = []
    
    # 输入文件
    for f in files_path.glob("*"):
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "type": "input",
                "created_at": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
            })
    
    # 输出文件
    for f in outputs_path.glob("*"):
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "type": "output",
                "created_at": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
            })
    
    return WorkspaceResponse(
        data={
            "items": files,
            "total": len(files),
        }
    )


@router.get("/workspaces/{workspace_id}/files/{filename}")
async def download_file(workspace_id: str, filename: str, file_type: str = "input"):
    """下载文件"""
    meta = WorkspaceInfo.load_meta(workspace_id)
    if not meta:
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    if file_type == "output":
        file_path = WorkspaceInfo.get_outputs_path(workspace_id) / filename
    else:
        file_path = WorkspaceInfo.get_files_path(workspace_id) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.delete("/workspaces/{workspace_id}/files/{filename}")
async def delete_file(workspace_id: str, filename: str, file_type: str = "input") -> WorkspaceResponse:
    """删除文件"""
    meta = WorkspaceInfo.load_meta(workspace_id)
    if not meta:
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    if file_type == "output":
        file_path = WorkspaceInfo.get_outputs_path(workspace_id) / filename
    else:
        file_path = WorkspaceInfo.get_files_path(workspace_id) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_path.unlink()
    
    return WorkspaceResponse(message="删除成功", data={"filename": filename})


# ===== 文件系统 API =====

def _get_file_type(filename: str) -> str:
    """根据文件名判断类型"""
    ext = Path(filename).suffix.lower()
    
    code_exts = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.cs', '.php', '.rb', '.swift', '.kt', '.vue', '.svelte'}
    doc_exts = {'.md', '.txt', '.rst', '.doc', '.docx', '.pdf'}
    data_exts = {'.json', '.yaml', '.yml', '.xml', '.csv', '.xlsx', '.xls'}
    ppt_exts = {'.ppt', '.pptx', '.key'}
    image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'}
    
    if ext in code_exts:
        return 'code'
    elif ext in doc_exts:
        return 'document'
    elif ext in data_exts:
        return 'data'
    elif ext in ppt_exts:
        return 'presentation'
    elif ext in image_exts:
        return 'image'
    else:
        return 'file'


def _build_file_tree(base_path: Path, current_path: Path = None, prefix: str = "") -> List[dict]:
    """递归构建文件树"""
    if current_path is None:
        current_path = base_path
    
    items = []
    
    try:
        entries = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        return items
    
    for entry in entries:
        # 跳过隐藏文件和元数据
        if entry.name.startswith('.'):
            continue
        
        relative_path = str(entry.relative_to(base_path))
        
        if entry.is_dir():
            children = _build_file_tree(base_path, entry, relative_path)
            items.append({
                "name": entry.name,
                "path": relative_path,
                "type": "folder",
                "children": children,
                "children_count": len(children),
            })
        else:
            stat = entry.stat()
            items.append({
                "name": entry.name,
                "path": relative_path,
                "type": "file",
                "file_type": _get_file_type(entry.name),
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    
    return items


@router.get("/workspaces/{workspace_id}/tree")
async def get_file_tree(workspace_id: str) -> WorkspaceResponse:
    """获取工作空间的完整文件树"""
    workspace_path = WorkspaceInfo.get_workspace_path(workspace_id)
    
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    tree = _build_file_tree(workspace_path)
    
    # 统计信息
    def count_files(items):
        total = 0
        for item in items:
            if item["type"] == "folder":
                total += count_files(item.get("children", []))
            else:
                total += 1
        return total
    
    return WorkspaceResponse(
        data={
            "tree": tree,
            "total_files": count_files(tree),
        }
    )


@router.post("/workspaces/{workspace_id}/folders")
async def create_folder(workspace_id: str, request: FolderCreate) -> WorkspaceResponse:
    """创建文件夹"""
    workspace_path = WorkspaceInfo.get_workspace_path(workspace_id)
    
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    # 安全检查：防止路径穿越
    folder_path = (workspace_path / request.path).resolve()
    if not str(folder_path).startswith(str(workspace_path.resolve())):
        raise HTTPException(status_code=400, detail="非法路径")
    
    folder_path.mkdir(parents=True, exist_ok=True)
    
    return WorkspaceResponse(
        data={
            "path": request.path,
            "created": True,
        }
    )


@router.post("/workspaces/{workspace_id}/upload")
async def upload_to_path(
    workspace_id: str,
    file: UploadFile = File(...),
    path: str = Form(default="", description="目标文件夹路径"),
) -> WorkspaceResponse:
    """上传文件到指定路径"""
    workspace_path = WorkspaceInfo.get_workspace_path(workspace_id)
    
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    # 目标路径
    if path:
        target_dir = workspace_path / path
    else:
        # 根据文件类型自动选择文件夹
        file_type = _get_file_type(file.filename)
        folder_map = {
            'code': 'code',
            'document': 'docs',
            'data': 'data',
            'presentation': 'ppt',
            'image': 'images',
            'file': 'files',
        }
        target_dir = workspace_path / folder_map.get(file_type, 'files')
    
    # 安全检查
    target_dir = target_dir.resolve()
    if not str(target_dir).startswith(str(workspace_path.resolve())):
        raise HTTPException(status_code=400, detail="非法路径")
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存文件
    safe_filename = file.filename.replace("/", "_").replace("\\", "_")
    file_path = target_dir / safe_filename
    
    # 如果文件已存在，添加时间戳
    if file_path.exists():
        stem = file_path.stem
        suffix = file_path.suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{stem}_{timestamp}{suffix}"
        file_path = target_dir / safe_filename
    
    content = await file.read()
    file_path.write_bytes(content)
    
    relative_path = str(file_path.relative_to(workspace_path))
    
    return WorkspaceResponse(
        data={
            "name": safe_filename,
            "path": relative_path,
            "size": len(content),
            "file_type": _get_file_type(safe_filename),
        }
    )


@router.get("/workspaces/{workspace_id}/browse/{file_path:path}")
async def browse_path(workspace_id: str, file_path: str) -> WorkspaceResponse:
    """浏览指定路径（文件夹返回内容列表，文件返回元信息）"""
    workspace_path = WorkspaceInfo.get_workspace_path(workspace_id)
    
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    target_path = (workspace_path / file_path).resolve()
    
    # 安全检查
    if not str(target_path).startswith(str(workspace_path.resolve())):
        raise HTTPException(status_code=400, detail="非法路径")
    
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="路径不存在")
    
    if target_path.is_dir():
        # 返回文件夹内容
        items = []
        for entry in sorted(target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if entry.name.startswith('.'):
                continue
            
            relative = str(entry.relative_to(workspace_path))
            
            if entry.is_dir():
                items.append({
                    "name": entry.name,
                    "path": relative,
                    "type": "folder",
                })
            else:
                stat = entry.stat()
                items.append({
                    "name": entry.name,
                    "path": relative,
                    "type": "file",
                    "file_type": _get_file_type(entry.name),
                    "size": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        
        return WorkspaceResponse(
            data={
                "type": "folder",
                "path": file_path,
                "items": items,
            }
        )
    else:
        # 返回文件信息
        stat = target_path.stat()
        return WorkspaceResponse(
            data={
                "type": "file",
                "name": target_path.name,
                "path": file_path,
                "file_type": _get_file_type(target_path.name),
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )


@router.get("/workspaces/{workspace_id}/preview/{file_path:path}")
async def preview_file(workspace_id: str, file_path: str) -> WorkspaceResponse:
    """预览文件内容（支持代码和文本）"""
    workspace_path = WorkspaceInfo.get_workspace_path(workspace_id)
    
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    target_path = (workspace_path / file_path).resolve()
    
    # 安全检查
    if not str(target_path).startswith(str(workspace_path.resolve())):
        raise HTTPException(status_code=400, detail="非法路径")
    
    if not target_path.exists() or target_path.is_dir():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 检查文件大小（限制 1MB）
    if target_path.stat().st_size > 1024 * 1024:
        return WorkspaceResponse(
            data={
                "preview": False,
                "reason": "文件过大，请下载查看",
                "size": target_path.stat().st_size,
            }
        )
    
    # 可预览的文件类型
    ext = target_path.suffix.lower()
    text_exts = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.cs',
        '.php', '.rb', '.swift', '.kt', '.vue', '.svelte', '.html', '.css', '.scss', '.less',
        '.json', '.yaml', '.yml', '.xml', '.md', '.txt', '.rst', '.sh', '.bash', '.zsh',
        '.sql', '.graphql', '.dockerfile', '.gitignore', '.env', '.toml', '.ini', '.cfg',
        '.csv', '.log',
    }
    
    if ext not in text_exts and not target_path.name.lower() in {'dockerfile', 'makefile', 'readme', 'license'}:
        return WorkspaceResponse(
            data={
                "preview": False,
                "reason": "不支持预览此文件类型",
                "file_type": _get_file_type(target_path.name),
            }
        )
    
    try:
        content = target_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            content = target_path.read_text(encoding='gbk')
        except:
            return WorkspaceResponse(
                data={
                    "preview": False,
                    "reason": "无法解码文件内容",
                }
            )
    
    # 语言映射
    lang_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.tsx': 'tsx',
        '.jsx': 'jsx', '.java': 'java', '.go': 'go', '.rs': 'rust', '.c': 'c',
        '.cpp': 'cpp', '.h': 'c', '.cs': 'csharp', '.php': 'php', '.rb': 'ruby',
        '.swift': 'swift', '.kt': 'kotlin', '.vue': 'vue', '.svelte': 'svelte',
        '.html': 'html', '.css': 'css', '.scss': 'scss', '.less': 'less',
        '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.xml': 'xml',
        '.md': 'markdown', '.sql': 'sql', '.sh': 'bash', '.bash': 'bash',
        '.dockerfile': 'dockerfile', '.graphql': 'graphql',
    }
    
    return WorkspaceResponse(
        data={
            "preview": True,
            "content": content,
            "language": lang_map.get(ext, 'text'),
            "lines": len(content.splitlines()),
            "size": len(content.encode('utf-8')),
        }
    )


@router.get("/workspaces/{workspace_id}/download/{file_path:path}")
async def download_path(workspace_id: str, file_path: str):
    """下载指定路径的文件"""
    workspace_path = WorkspaceInfo.get_workspace_path(workspace_id)
    
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    target_path = (workspace_path / file_path).resolve()
    
    # 安全检查
    if not str(target_path).startswith(str(workspace_path.resolve())):
        raise HTTPException(status_code=400, detail="非法路径")
    
    if not target_path.exists() or target_path.is_dir():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 根据文件类型设置 Content-Type
    content_types = {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pdf": "application/pdf",
        ".json": "application/json",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".py": "text/x-python",
        ".js": "application/javascript",
        ".html": "text/html",
        ".css": "text/css",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }
    
    suffix = target_path.suffix.lower()
    media_type = content_types.get(suffix, "application/octet-stream")
    
    return FileResponse(
        path=target_path,
        filename=target_path.name,
        media_type=media_type,
    )


@router.delete("/workspaces/{workspace_id}/path/{file_path:path}")
async def delete_path(workspace_id: str, file_path: str) -> WorkspaceResponse:
    """删除指定路径（文件或文件夹）"""
    workspace_path = WorkspaceInfo.get_workspace_path(workspace_id)
    
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="工作空间不存在")
    
    target_path = (workspace_path / file_path).resolve()
    
    # 安全检查
    if not str(target_path).startswith(str(workspace_path.resolve())):
        raise HTTPException(status_code=400, detail="非法路径")
    
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="路径不存在")
    
    # 不允许删除根目录
    if target_path == workspace_path:
        raise HTTPException(status_code=400, detail="不能删除工作空间根目录")
    
    if target_path.is_dir():
        shutil.rmtree(target_path)
    else:
        target_path.unlink()
    
    return WorkspaceResponse(message="删除成功", data={"path": file_path})
