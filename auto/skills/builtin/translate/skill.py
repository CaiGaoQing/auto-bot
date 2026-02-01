"""翻译服务技能"""

from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


# 语言代码映射
LANGUAGE_MAP = {
    "zh": "中文",
    "en": "英语",
    "ja": "日语",
    "ko": "韩语",
    "fr": "法语",
    "de": "德语",
    "es": "西班牙语",
    "pt": "葡萄牙语",
    "ru": "俄语",
    "ar": "阿拉伯语",
    "it": "意大利语",
    "nl": "荷兰语",
    "pl": "波兰语",
    "th": "泰语",
    "vi": "越南语",
    "id": "印尼语",
    "ms": "马来语",
    "tr": "土耳其语",
    "hi": "印地语",
}


class TranslateSkill(Skill):
    """翻译服务技能
    
    提供多语言翻译功能。
    """
    
    @property
    def name(self) -> str:
        return "translate"
    
    @property
    def display_name(self) -> str:
        return "翻译服务"
    
    @property
    def description(self) -> str:
        return "多语言翻译、文档翻译、术语翻译"
    
    @property
    def category(self) -> str:
        return "productivity"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="translate_text",
                description="翻译文本",
                parameters={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "要翻译的文本",
                        },
                        "target_language": {
                            "type": "string",
                            "description": "目标语言 (zh/en/ja/ko/fr/de/es/...)",
                            "default": "zh",
                        },
                        "source_language": {
                            "type": "string",
                            "description": "源语言 (auto 自动检测)",
                            "default": "auto",
                        },
                    },
                    "required": ["text"],
                },
                handler=self.translate_text,
            ),
            ToolDefinition(
                name="translate_file",
                description="翻译文档文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径 (支持 .txt, .md)",
                        },
                        "target_language": {
                            "type": "string",
                            "description": "目标语言",
                            "default": "zh",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["file_path"],
                },
                handler=self.translate_file,
            ),
            ToolDefinition(
                name="translate_terms",
                description="专业术语翻译",
                parameters={
                    "type": "object",
                    "properties": {
                        "terms": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "术语列表",
                        },
                        "domain": {
                            "type": "string",
                            "description": "专业领域 (tech/medical/legal/finance)",
                            "default": "tech",
                        },
                        "target_language": {
                            "type": "string",
                            "description": "目标语言",
                            "default": "zh",
                        },
                    },
                    "required": ["terms"],
                },
                handler=self.translate_terms,
            ),
            ToolDefinition(
                name="detect_language",
                description="检测文本语言",
                parameters={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "要检测的文本",
                        },
                    },
                    "required": ["text"],
                },
                handler=self.detect_language,
            ),
            ToolDefinition(
                name="list_languages",
                description="列出支持的语言",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                handler=self.list_languages,
            ),
            ToolDefinition(
                name="batch_translate",
                description="批量翻译",
                parameters={
                    "type": "object",
                    "properties": {
                        "texts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "文本列表",
                        },
                        "target_language": {
                            "type": "string",
                            "description": "目标语言",
                            "default": "zh",
                        },
                    },
                    "required": ["texts"],
                },
                handler=self.batch_translate,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个专业的翻译助手，擅长：
- 多语言互译 (中、英、日、韩、法、德、西等)
- 专业术语翻译 (技术、医学、法律、金融)
- 保持原文格式和语气
- 本地化适配

翻译原则：
1. 信 - 准确传达原意
2. 达 - 通顺自然
3. 雅 - 文采兼备
4. 保持专业术语的准确性
5. 适当本地化"""
    
    async def translate_text(
        self,
        ctx: ToolContext,
        text: str,
        target_language: str = "zh",
        source_language: str = "auto",
    ) -> ToolResult:
        """翻译文本
        
        使用 AI 进行翻译。
        """
        if not text.strip():
            return ToolResult.error_result("文本不能为空")
        
        target_name = LANGUAGE_MAP.get(target_language, target_language)
        source_name = LANGUAGE_MAP.get(source_language, source_language) if source_language != "auto" else "自动检测"
        
        # 构建翻译提示
        if source_language == "auto":
            prompt = f"请将以下文本翻译成{target_name}：\n\n{text}"
        else:
            prompt = f"请将以下{source_name}文本翻译成{target_name}：\n\n{text}"
        
        # 这里返回翻译请求，让 AI 进行实际翻译
        return ToolResult.success_result(
            data={
                "original": text,
                "source_language": source_language,
                "target_language": target_language,
                "target_language_name": target_name,
                "prompt": prompt,
                "instruction": "请基于上述提示进行翻译",
            },
            message=f"请翻译成{target_name}",
        )
    
    async def translate_file(
        self,
        ctx: ToolContext,
        file_path: str,
        target_language: str = "zh",
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """翻译文档"""
        path = Path(file_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {file_path}")
        
        if not path.exists():
            return ToolResult.error_result(f"文件不存在: {file_path}")
        
        # 支持的文件类型
        supported = {".txt", ".md", ".rst", ".json"}
        if path.suffix.lower() not in supported:
            return ToolResult.error_result(f"不支持的文件类型: {path.suffix}")
        
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return ToolResult.error_result(f"读取文件失败: {str(e)}")
        
        if len(content) > 50000:
            return ToolResult.error_result("文件过大 (>50000字符)，请分段翻译")
        
        target_name = LANGUAGE_MAP.get(target_language, target_language)
        
        # 确定输出路径
        if output_path:
            out_path = Path(output_path).expanduser()
        else:
            out_path = path.with_stem(f"{path.stem}_{target_language}")
        
        return ToolResult.success_result(
            data={
                "file": str(path),
                "content": content[:5000],  # 限制显示
                "content_length": len(content),
                "target_language": target_language,
                "output_path": str(out_path),
                "instruction": f"请将文件内容翻译成{target_name}，保持原有格式",
            },
            message=f"请翻译文件 {path.name} (共 {len(content)} 字符)",
        )
    
    async def translate_terms(
        self,
        ctx: ToolContext,
        terms: list[str],
        domain: str = "tech",
        target_language: str = "zh",
    ) -> ToolResult:
        """专业术语翻译"""
        if not terms:
            return ToolResult.error_result("术语列表不能为空")
        
        domain_names = {
            "tech": "技术/IT",
            "medical": "医学",
            "legal": "法律",
            "finance": "金融",
            "academic": "学术",
            "marketing": "营销",
        }
        
        domain_name = domain_names.get(domain, domain)
        target_name = LANGUAGE_MAP.get(target_language, target_language)
        
        # 构建术语表
        terms_list = "\n".join(f"- {term}" for term in terms)
        
        return ToolResult.success_result(
            data={
                "terms": terms,
                "domain": domain,
                "domain_name": domain_name,
                "target_language": target_language,
                "instruction": f"请将以下{domain_name}领域术语翻译成{target_name}：\n\n{terms_list}",
            },
            message=f"请翻译 {len(terms)} 个{domain_name}术语",
        )
    
    async def detect_language(
        self,
        ctx: ToolContext,
        text: str,
    ) -> ToolResult:
        """检测文本语言"""
        if not text.strip():
            return ToolResult.error_result("文本不能为空")
        
        # 简单的语言检测 (基于字符特征)
        detected = "unknown"
        confidence = 0.0
        
        # 中文检测
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        chinese_ratio = chinese_chars / len(text) if text else 0
        
        # 日文检测 (平假名、片假名)
        japanese_chars = sum(1 for c in text if '\u3040' <= c <= '\u30ff')
        japanese_ratio = japanese_chars / len(text) if text else 0
        
        # 韩文检测
        korean_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7af')
        korean_ratio = korean_chars / len(text) if text else 0
        
        # 西里尔字母 (俄语等)
        cyrillic_chars = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
        cyrillic_ratio = cyrillic_chars / len(text) if text else 0
        
        # 阿拉伯语
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06ff')
        arabic_ratio = arabic_chars / len(text) if text else 0
        
        # 判断
        if chinese_ratio > 0.3:
            detected = "zh"
            confidence = min(0.95, chinese_ratio + 0.3)
        elif japanese_ratio > 0.1:
            detected = "ja"
            confidence = min(0.95, japanese_ratio + 0.5)
        elif korean_ratio > 0.3:
            detected = "ko"
            confidence = min(0.95, korean_ratio + 0.3)
        elif cyrillic_ratio > 0.3:
            detected = "ru"
            confidence = min(0.95, cyrillic_ratio + 0.3)
        elif arabic_ratio > 0.3:
            detected = "ar"
            confidence = min(0.95, arabic_ratio + 0.3)
        else:
            # 默认英语
            detected = "en"
            confidence = 0.7
        
        return ToolResult.success_result(
            data={
                "language": detected,
                "language_name": LANGUAGE_MAP.get(detected, detected),
                "confidence": round(confidence, 2),
                "text_preview": text[:100],
            },
            message=f"检测到语言: {LANGUAGE_MAP.get(detected, detected)}",
        )
    
    async def list_languages(self, ctx: ToolContext) -> ToolResult:
        """列出支持的语言"""
        languages = [
            {"code": code, "name": name}
            for code, name in LANGUAGE_MAP.items()
        ]
        
        return ToolResult.table(
            data=languages,
            message=f"支持 {len(languages)} 种语言",
        )
    
    async def batch_translate(
        self,
        ctx: ToolContext,
        texts: list[str],
        target_language: str = "zh",
    ) -> ToolResult:
        """批量翻译"""
        if not texts:
            return ToolResult.error_result("文本列表不能为空")
        
        if len(texts) > 50:
            return ToolResult.error_result("一次最多翻译 50 条文本")
        
        target_name = LANGUAGE_MAP.get(target_language, target_language)
        
        # 构建批量翻译请求
        numbered_texts = "\n".join(f"{i+1}. {text}" for i, text in enumerate(texts))
        
        return ToolResult.success_result(
            data={
                "texts": texts,
                "count": len(texts),
                "target_language": target_language,
                "instruction": f"请将以下 {len(texts)} 条文本翻译成{target_name}：\n\n{numbered_texts}",
            },
            message=f"请批量翻译 {len(texts)} 条文本",
        )
