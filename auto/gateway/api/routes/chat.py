1`"""对话路由"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auto.core.ai.router import get_router
from auto.shared.models import Message, MessageRole

router = APIRouter()

# 工作空间根目录
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
WORKSPACES_ROOT = _PROJECT_ROOT / "data" / "workspaces"


class ChatRequest(BaseModel
    """聊天请求"""
    message: str
    model: Optional[str] = None
    workspace_id: Optional[str] = None
    role: Optional[str] = None
    stream: bool = False
    save_to_workspace: bool = True  # 是否保存到工作空间


class ChatResponse(BaseModel):
    """聊天响应"""
    code: int = 0
    message: str = "success"
    data: dict


def _detect_file_type(message: str) -> tuple[str, str]:
    """根据消息检测应该生成的文件类型"""
    message_lower = message.lower()
    
    # 检测关键词
    if any(kw in message_lower for kw in ['ppt', '演示', '幻灯片', 'slide']):
        return 'pptx', 'ppt'
    elif any(kw in message_lower for kw in ['excel', '表格', '工资', '财务', '数据表', 'xlsx']):
        return 'xlsx', 'data'
    elif any(kw in message_lower for kw in ['代码', 'python', 'code', '脚本', 'script']):
        if 'python' in message_lower:
            return 'py', 'code'
        elif 'javascript' in message_lower or 'js' in message_lower:
            return 'js', 'code'
        elif 'typescript' in message_lower or 'ts' in message_lower:
            return 'ts', 'code'
        return 'py', 'code'
    elif any(kw in message_lower for kw in ['json', '配置']):
        return 'json', 'data'
    else:
        return 'md', 'docs'


def _generate_filename(message: str, ext: str) -> str:
    """根据消息生成文件名"""
    clean = re.sub(r'^(帮我|请|生成|写|创建|制作|编写|做一个?|给我)', '', message)
    name = clean[:20].strip()
    name = re.sub(r'[\\/:*?"<>|\s]', '_', name)
    timestamp = datetime.now().strftime("%H%M%S")
    
    if not name:
        name = f"output_{timestamp}"
    else:
        name = f"{name}_{timestamp}"
    
    return f"{name}.{ext}"


def _save_markdown(workspace_id: str, content: str, folder: str, filename: str) -> str:
    """保存 Markdown/文本内容"""
    workspace_path = WORKSPACES_ROOT / workspace_id
    target_dir = workspace_path / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = target_dir / filename
    file_path.write_text(content, encoding='utf-8')
    
    return f"{folder}/{filename}"


async def _generate_slide_image(title: str, workspace_path: Path, slide_index: int) -> Optional[Path]:
    """为幻灯片生成配图"""
    try:
        from auto.core.ai.image import get_image_generator
        
        generator = get_image_generator()
        
        # 生成图像描述
        prompt = f"Professional business presentation slide background image for topic: {title}. Modern, clean, minimalist design with subtle gradient. No text. Corporate style."
        
        image_path = workspace_path / "images" / f"slide_{slide_index}.png"
        result = await generator.generate_and_download(prompt, image_path, size="1792x1024")
        
        return result
    except Exception as e:
        print(f"图像生成跳过: {e}")
        return None


def _generate_pptx_sync(workspace_id: str, content: str, filename: str, with_images: bool = False) -> str:
    """同步生成 PPTX 文件（不含图片）"""
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
        
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        
        # 解析内容生成幻灯片
        lines = content.split('\n')
        current_title = ""
        current_content = []
        slides_data = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                if current_title or current_content:
                    slides_data.append((current_title, current_content))
                current_title = line[2:]
                current_content = []
            elif line.startswith('## '):
                if current_title or current_content:
                    slides_data.append((current_title, current_content))
                current_title = line[3:]
                current_content = []
            elif line.startswith('### '):
                current_content.append(f"◆ {line[4:]}")
            elif line.startswith('- ') or line.startswith('* '):
                current_content.append(f"• {line[2:]}")
            elif line.startswith('|') or line.startswith('```'):
                continue
            elif line:
                current_content.append(line)
        
        if current_title or current_content:
            slides_data.append((current_title, current_content))
        
        # 颜色方案
        primary_color = RGBColor(0x1E, 0x3A, 0x8A)  # 深蓝色
        accent_color = RGBColor(0x3B, 0x82, 0xF6)   # 亮蓝色
        
        # 生成幻灯片
        for i, (title, content_lines) in enumerate(slides_data):
            slide_layout = prs.slide_layouts[6]  # 空白布局
            slide = prs.slides.add_slide(slide_layout)
            
            # 添加背景色块（左侧装饰条）
            left_bar = slide.shapes.add_shape(
                1,  # MSO_SHAPE.RECTANGLE
                Inches(0), Inches(0),
                Inches(0.3), Inches(7.5)
            )
            left_bar.fill.solid()
            left_bar.fill.fore_color.rgb = primary_color
            left_bar.line.fill.background()
            
            if i == 0:
                # 封面页
                title_box = slide.shapes.add_textbox(Inches(0.8), Inches(2.5), Inches(11.5), Inches(1.5))
                tf = title_box.text_frame
                p = tf.paragraphs[0]
                p.text = title
                p.font.size = Pt(48)
                p.font.bold = True
                p.font.color.rgb = primary_color
                p.alignment = PP_ALIGN.CENTER
                
                # 副标题
                if content_lines:
                    sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(4.2), Inches(11.5), Inches(1))
                    tf = sub_box.text_frame
                    p = tf.paragraphs[0]
                    p.text = content_lines[0] if content_lines else ""
                    p.font.size = Pt(24)
                    p.font.color.rgb = accent_color
                    p.alignment = PP_ALIGN.CENTER
            else:
                # 内容页标题
                title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.8))
                tf = title_box.text_frame
                p = tf.paragraphs[0]
                p.text = title
                p.font.size = Pt(32)
                p.font.bold = True
                p.font.color.rgb = primary_color
                
                # 分隔线
                line = slide.shapes.add_shape(
                    1, Inches(0.8), Inches(1.15), Inches(11.5), Inches(0.03)
                )
                line.fill.solid()
                line.fill.fore_color.rgb = accent_color
                line.line.fill.background()
                
                # 内容
                if content_lines:
                    content_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.4), Inches(11.5), Inches(5.5))
                    tf = content_box.text_frame
                    tf.word_wrap = True
                    
                    for j, line_text in enumerate(content_lines[:10]):
                        if j == 0:
                            p = tf.paragraphs[0]
                        else:
                            p = tf.add_paragraph()
                        p.text = line_text
                        p.font.size = Pt(20)
                        p.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
                        p.space_after = Pt(12)
        
        # 保存
        workspace_path = WORKSPACES_ROOT / workspace_id
        target_dir = workspace_path / "ppt"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = target_dir / filename
        prs.save(str(file_path))
        
        return f"ppt/{filename}"
    except Exception as e:
        import traceback
        print(f"PPT生成失败: {e}")
        traceback.print_exc()
        return _save_markdown(workspace_id, content, "docs", filename.replace('.pptx', '.md'))


def _generate_pptx(workspace_id: str, content: str, filename: str) -> str:
    """生成 PPTX 文件（同步版本）"""
    return _generate_pptx_sync(workspace_id, content, filename)


def _generate_xlsx(workspace_id: str, content: str, filename: str) -> str:
    """生成真正的 XLSX 文件"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        
        wb = Workbook()
        ws = wb.active
        ws.title = "数据"
        
        # 解析 Markdown 表格或内容
        lines = content.split('\n')
        row = 1
        
        # 样式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        for line in lines:
            line = line.strip()
            if line.startswith('|') and '|' in line[1:]:
                # Markdown 表格行
                if '---' in line:
                    continue
                cells = [c.strip() for c in line.split('|')[1:-1]]
                for col, value in enumerate(cells, 1):
                    cell = ws.cell(row=row, column=col, value=value)
                    cell.border = border
                    if row == 1:
                        cell.font = header_font
                        cell.fill = header_fill
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                row += 1
            elif line and not line.startswith('#') and not line.startswith('```'):
                # 普通内容
                ws.cell(row=row, column=1, value=line)
                row += 1
        
        # 调整列宽
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            ws.column_dimensions[column].width = min(max_length + 2, 50)
        
        # 保存
        workspace_path = WORKSPACES_ROOT / workspace_id
        target_dir = workspace_path / "data"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = target_dir / filename
        wb.save(str(file_path))
        
        return f"data/{filename}"
    except ImportError:
        return _save_markdown(workspace_id, content, "docs", filename.replace('.xlsx', '.md'))


@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """发送聊天消息"""
    try:
        router_instance = get_router()
        
        # 提取核心消息（去掉参考文件标记等）
        core_message = request.message
        if '[参考文件' in core_message:
            # 去掉参考文件标记，只保留实际请求
            import re
            core_message = re.sub(r'\[参考文件[^\]]*\]\s*', '', core_message).strip()
        
        # 检测文件类型
        ext, folder = _detect_file_type(core_message)
        
        # 根据文件类型调整 AI 提示
        if ext == 'pptx':
            prompt = f"""你是一个专业的PPT设计师。请为以下主题创建完整的PPT内容。

要求：
1. 严格使用以下Markdown格式输出
2. 用 # 表示PPT标题（封面）
3. 用 ## 表示每一页的标题
4. 用 - 表示每页的要点内容
5. 生成 8-12 页内容
6. 内容要专业、具体、有数据支撑

格式示例：
# 产品发布会

## 公司简介
- 成立于2020年
- 专注于xxx领域
- 服务超过100万用户

## 产品亮点
- 功能一：描述
- 功能二：描述

主题：{core_message}

请直接输出PPT内容，不要有任何解释性文字："""
        elif ext == 'xlsx':
            prompt = f"""请为以下需求创建完整的表格数据。使用 Markdown 表格格式，包含表头和至少10行数据：

| 列1 | 列2 | 列3 | 列4 |
|-----|-----|-----|-----|
| 数据 | 数据 | 数据 | 数据 |

需求：{core_message}

请直接输出表格，不要有任何解释性文字："""
        else:
            prompt = request.message
        
        messages = [Message(role=MessageRole.USER, content=prompt)]
        
        response = await router_instance.chat(
            messages=messages,
            model=request.model,
        )
        
        content = response.message.content
        saved_file = None
        
        # 如果有工作空间 ID 且需要保存
        if request.workspace_id and request.save_to_workspace:
            workspace_path = WORKSPACES_ROOT / request.workspace_id
            if workspace_path.exists():
                filename = _generate_filename(core_message, ext)
                
                # 根据类型生成不同格式的文件
                if ext == 'pptx':
                    saved_file = _generate_pptx(request.workspace_id, content, filename)
                elif ext == 'xlsx':
                    saved_file = _generate_xlsx(request.workspace_id, content, filename)
                else:
                    saved_file = _save_markdown(request.workspace_id, content, folder, filename)
        
        return ChatResponse(
            data={
                "id": response.id,
                "content": content,
                "model": response.model,
                "saved_file": saved_file,
                "file_type": ext,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    request: ChatRequest,
) -> ChatResponse:
    """在会话中发送消息"""
    # TODO: 实现会话管理
    return await chat(request)
