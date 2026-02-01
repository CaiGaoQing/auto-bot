"""工具函数"""

import hashlib
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def generate_id(prefix: str = "") -> str:
    """生成唯一 ID"""
    uid = uuid.uuid4().hex[:12]
    if prefix:
        return f"{prefix}_{uid}"
    return uid


def slugify(text: str) -> str:
    """将文本转换为 URL 友好的 slug"""
    # 转小写
    text = text.lower()
    # 替换空格和特殊字符
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def hash_string(text: str) -> str:
    """计算字符串的 SHA256 哈希"""
    return hashlib.sha256(text.encode()).hexdigest()


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断字符串"""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    return dt.strftime(format)


def relative_time(dt: datetime) -> str:
    """相对时间"""
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "刚刚"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}分钟前"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}小时前"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days}天前"
    else:
        return dt.strftime("%Y-%m-%d")


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def format_tokens(tokens: int) -> str:
    """格式化 Token 数量"""
    if tokens < 1000:
        return str(tokens)
    elif tokens < 1000000:
        return f"{tokens / 1000:.1f}K"
    else:
        return f"{tokens / 1000000:.2f}M"


def format_cost(cost: float) -> str:
    """格式化成本"""
    if cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def ensure_dir(path: Path) -> Path:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_extension(path: str) -> str:
    """获取文件扩展名"""
    return Path(path).suffix.lower().lstrip(".")


def is_safe_path(path: str, base_path: str) -> bool:
    """检查路径是否安全（防止路径遍历攻击）"""
    base = Path(base_path).resolve()
    target = Path(path).resolve()
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def deep_merge(base: dict, override: dict) -> dict:
    """深度合并字典"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def extract_code_blocks(text: str) -> list[tuple[str, str]]:
    """从文本中提取代码块"""
    pattern = r"```(\w*)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [(lang or "text", code.strip()) for lang, code in matches]


def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """遮蔽 API Key"""
    if len(api_key) <= visible_chars * 2:
        return "*" * len(api_key)
    prefix = api_key[:visible_chars]
    suffix = api_key[-visible_chars:]
    masked = "*" * (len(api_key) - visible_chars * 2)
    return f"{prefix}{masked}{suffix}"
