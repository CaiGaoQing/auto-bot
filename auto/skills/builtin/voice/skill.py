"""语音交互技能"""

import asyncio
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class VoiceSkill(Skill):
    """语音交互技能
    
    提供语音识别 (STT)、语音合成 (TTS) 等功能。
    """
    
    @property
    def name(self) -> str:
        return "voice"
    
    @property
    def display_name(self) -> str:
        return "语音交互"
    
    @property
    def description(self) -> str:
        return "语音识别、语音合成、会议转录"
    
    @property
    def category(self) -> str:
        return "productivity"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="transcribe_audio",
                description="将音频转录为文字 (语音识别)",
                parameters={
                    "type": "object",
                    "properties": {
                        "audio_path": {
                            "type": "string",
                            "description": "音频文件路径 (支持 mp3, wav, m4a, webm)",
                        },
                        "language": {
                            "type": "string",
                            "description": "语言代码 (zh, en, auto)",
                            "default": "auto",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "转录结果输出路径",
                        },
                    },
                    "required": ["audio_path"],
                },
                handler=self.transcribe_audio,
            ),
            ToolDefinition(
                name="text_to_speech",
                description="将文字转换为语音 (语音合成)",
                parameters={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "要转换的文本",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出音频文件路径",
                        },
                        "voice": {
                            "type": "string",
                            "description": "语音类型 (alloy, echo, fable, onyx, nova, shimmer)",
                            "default": "alloy",
                        },
                        "speed": {
                            "type": "number",
                            "description": "语速 (0.25-4.0)",
                            "default": 1.0,
                        },
                    },
                    "required": ["text", "output_path"],
                },
                handler=self.text_to_speech,
            ),
            ToolDefinition(
                name="transcribe_meeting",
                description="转录会议录音并生成摘要",
                parameters={
                    "type": "object",
                    "properties": {
                        "audio_path": {
                            "type": "string",
                            "description": "会议录音文件路径",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                        "generate_summary": {
                            "type": "boolean",
                            "description": "是否生成摘要",
                            "default": True,
                        },
                    },
                    "required": ["audio_path"],
                },
                handler=self.transcribe_meeting,
            ),
            ToolDefinition(
                name="list_voices",
                description="列出可用的语音类型",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                handler=self.list_voices,
            ),
            ToolDefinition(
                name="audio_info",
                description="获取音频文件信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "audio_path": {
                            "type": "string",
                            "description": "音频文件路径",
                        },
                    },
                    "required": ["audio_path"],
                },
                handler=self.audio_info,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个语音交互助手，可以帮助用户：
- 将音频转录为文字
- 将文字合成为语音
- 转录会议录音并生成摘要

支持的功能：
1. 语音识别 (Whisper API)
2. 语音合成 (TTS API)
3. 多语言支持"""
    
    async def transcribe_audio(
        self,
        ctx: ToolContext,
        audio_path: str,
        language: str = "auto",
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """语音转文字"""
        path = Path(audio_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {audio_path}")
        
        if not path.exists():
            return ToolResult.error_result(f"文件不存在: {audio_path}")
        
        # 检查文件格式
        supported = {".mp3", ".wav", ".m4a", ".webm", ".ogg", ".flac"}
        if path.suffix.lower() not in supported:
            return ToolResult.error_result(f"不支持的格式: {path.suffix}")
        
        try:
            import openai
        except ImportError:
            return ToolResult.error_result("需要安装: pip install openai")
        
        # 获取 API Key
        api_key = ctx.config.get("openai_api_key", "")
        if not api_key:
            return ToolResult.error_result("未配置 OpenAI API Key")
        
        try:
            client = openai.OpenAI(api_key=api_key)
            
            with open(path, "rb") as audio_file:
                if language == "auto":
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text",
                    )
                else:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language,
                        response_format="text",
                    )
            
            transcript = response if isinstance(response, str) else response.text
            
            # 保存结果
            if output_path:
                out_path = Path(output_path).expanduser()
                if ctx.security.is_allowed_path(out_path):
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(transcript, encoding="utf-8")
                    return ToolResult.file(
                        path=str(out_path),
                        message=f"转录完成 ({len(transcript)} 字符)",
                    )
            
            return ToolResult.success_result(
                data={
                    "transcript": transcript,
                    "length": len(transcript),
                    "audio_file": str(path),
                },
                message=f"转录完成 ({len(transcript)} 字符)",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"转录失败: {str(e)}")
    
    async def text_to_speech(
        self,
        ctx: ToolContext,
        text: str,
        output_path: str,
        voice: str = "alloy",
        speed: float = 1.0,
    ) -> ToolResult:
        """文字转语音"""
        if not text.strip():
            return ToolResult.error_result("文本不能为空")
        
        if len(text) > 4096:
            return ToolResult.error_result("文本过长 (最大 4096 字符)")
        
        out_path = Path(output_path).expanduser()
        
        if not ctx.security.is_allowed_path(out_path):
            return ToolResult.error_result(f"路径不允许: {output_path}")
        
        try:
            import openai
        except ImportError:
            return ToolResult.error_result("需要安装: pip install openai")
        
        api_key = ctx.config.get("openai_api_key", "")
        if not api_key:
            return ToolResult.error_result("未配置 OpenAI API Key")
        
        # 验证语音类型
        valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if voice not in valid_voices:
            voice = "alloy"
        
        # 限制语速范围
        speed = max(0.25, min(4.0, speed))
        
        try:
            client = openai.OpenAI(api_key=api_key)
            
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                speed=speed,
            )
            
            out_path.parent.mkdir(parents=True, exist_ok=True)
            response.stream_to_file(str(out_path))
            
            return ToolResult.file(
                path=str(out_path),
                message=f"语音已生成 ({voice})",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"语音合成失败: {str(e)}")
    
    async def transcribe_meeting(
        self,
        ctx: ToolContext,
        audio_path: str,
        output_path: Optional[str] = None,
        generate_summary: bool = True,
    ) -> ToolResult:
        """转录会议录音"""
        # 先进行转录
        result = await self.transcribe_audio(ctx, audio_path)
        
        if not result.success:
            return result
        
        transcript = result.data.get("transcript", "")
        
        if not transcript:
            return ToolResult.error_result("转录结果为空")
        
        # 生成会议纪要格式
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        content = f"""# 会议转录

**转录时间**: {timestamp}  
**音频文件**: {audio_path}

---

## 转录内容

{transcript}

---

"""
        
        if generate_summary:
            content += """## 会议摘要

> 请 AI 根据上述转录内容生成摘要

**主要议题**:
- [待生成]

**决议事项**:
- [待生成]

**待办事项**:
- [待生成]
"""
        
        if output_path:
            out_path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(out_path):
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(content, encoding="utf-8")
                return ToolResult.file(
                    path=str(out_path),
                    message="会议转录已完成",
                )
        
        return ToolResult.success_result(
            data={
                "content": content,
                "transcript_length": len(transcript),
            },
            message="会议转录已完成，请生成摘要",
        )
    
    async def list_voices(self, ctx: ToolContext) -> ToolResult:
        """列出可用语音"""
        voices = [
            {"name": "alloy", "description": "中性、平衡", "gender": "中性"},
            {"name": "echo", "description": "温暖、清晰", "gender": "男性"},
            {"name": "fable", "description": "叙事风格", "gender": "男性"},
            {"name": "onyx", "description": "深沉、权威", "gender": "男性"},
            {"name": "nova", "description": "活泼、年轻", "gender": "女性"},
            {"name": "shimmer", "description": "柔和、温暖", "gender": "女性"},
        ]
        
        return ToolResult.table(
            data=voices,
            message="OpenAI TTS 可用语音",
        )
    
    async def audio_info(
        self,
        ctx: ToolContext,
        audio_path: str,
    ) -> ToolResult:
        """获取音频信息"""
        path = Path(audio_path).expanduser()
        
        if not path.exists():
            return ToolResult.error_result(f"文件不存在: {audio_path}")
        
        info = {
            "path": str(path),
            "name": path.name,
            "format": path.suffix,
            "size": path.stat().st_size,
            "size_human": f"{path.stat().st_size / 1024 / 1024:.2f} MB",
            "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }
        
        # 尝试获取更多信息
        try:
            import mutagen
            audio = mutagen.File(str(path))
            if audio:
                info["duration"] = round(audio.info.length, 2) if hasattr(audio.info, "length") else None
                info["duration_human"] = f"{int(audio.info.length // 60)}:{int(audio.info.length % 60):02d}" if info["duration"] else None
                info["bitrate"] = getattr(audio.info, "bitrate", None)
                info["sample_rate"] = getattr(audio.info, "sample_rate", None)
        except ImportError:
            pass
        except Exception:
            pass
        
        return ToolResult.success_result(
            data=info,
            message=f"音频: {path.name}",
        )
