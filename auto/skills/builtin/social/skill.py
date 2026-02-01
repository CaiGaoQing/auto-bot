"""社媒运营技能"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class SocialSkill(Skill):
    """社媒运营技能
    
    提供社交媒体内容生成、发布、评论管理等功能。
    注意：实际发布功能需要各平台 API 权限。
    """
    
    @property
    def name(self) -> str:
        return "social"
    
    @property
    def display_name(self) -> str:
        return "社媒运营"
    
    @property
    def description(self) -> str:
        return "社交媒体内容生成、发布规划、评论管理"
    
    @property
    def category(self) -> str:
        return "marketing"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="generate_post",
                description="生成社媒帖子内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "主题/话题",
                        },
                        "platform": {
                            "type": "string",
                            "enum": ["xiaohongshu", "weibo", "douyin", "wechat", "twitter"],
                            "description": "目标平台",
                            "default": "xiaohongshu",
                        },
                        "style": {
                            "type": "string",
                            "enum": ["informative", "emotional", "humorous", "professional"],
                            "description": "内容风格",
                            "default": "informative",
                        },
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "关键词/标签",
                        },
                    },
                    "required": ["topic"],
                },
                handler=self.generate_post,
            ),
            ToolDefinition(
                name="generate_hashtags",
                description="生成话题标签",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "内容描述",
                        },
                        "platform": {
                            "type": "string",
                            "description": "目标平台",
                            "default": "xiaohongshu",
                        },
                        "count": {
                            "type": "integer",
                            "description": "标签数量",
                            "default": 10,
                        },
                    },
                    "required": ["content"],
                },
                handler=self.generate_hashtags,
            ),
            ToolDefinition(
                name="create_content_calendar",
                description="创建内容发布日历",
                parameters={
                    "type": "object",
                    "properties": {
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "内容主题列表",
                        },
                        "platform": {
                            "type": "string",
                            "description": "目标平台",
                        },
                        "days": {
                            "type": "integer",
                            "description": "规划天数",
                            "default": 7,
                        },
                        "posts_per_day": {
                            "type": "integer",
                            "description": "每日发布数",
                            "default": 1,
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["topics"],
                },
                handler=self.create_content_calendar,
            ),
            ToolDefinition(
                name="generate_reply",
                description="生成评论回复",
                parameters={
                    "type": "object",
                    "properties": {
                        "comment": {
                            "type": "string",
                            "description": "原评论内容",
                        },
                        "tone": {
                            "type": "string",
                            "enum": ["friendly", "professional", "humorous", "grateful"],
                            "description": "回复语气",
                            "default": "friendly",
                        },
                        "brand_name": {
                            "type": "string",
                            "description": "品牌名称",
                        },
                    },
                    "required": ["comment"],
                },
                handler=self.generate_reply,
            ),
            ToolDefinition(
                name="analyze_post_performance",
                description="分析帖子表现 (模拟)",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "帖子内容",
                        },
                        "platform": {
                            "type": "string",
                            "description": "目标平台",
                        },
                    },
                    "required": ["content"],
                },
                handler=self.analyze_post_performance,
            ),
            ToolDefinition(
                name="generate_image_prompt",
                description="为帖子生成配图提示词",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "帖子内容",
                        },
                        "style": {
                            "type": "string",
                            "description": "图片风格",
                            "default": "modern",
                        },
                    },
                    "required": ["content"],
                },
                handler=self.generate_image_prompt,
            ),
            ToolDefinition(
                name="batch_generate_posts",
                description="批量生成帖子",
                parameters={
                    "type": "object",
                    "properties": {
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "主题列表",
                        },
                        "platform": {
                            "type": "string",
                            "description": "目标平台",
                            "default": "xiaohongshu",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["topics"],
                },
                handler=self.batch_generate_posts,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个社交媒体运营专家，擅长：
- 创作吸引人的社媒内容
- 根据平台特点调整风格
- 生成热门话题标签
- 规划内容发布日历
- 处理用户评论互动

平台特点：
- 小红书：分享、种草、攻略风格，多用emoji
- 微博：简洁、话题标签、@互动
- 抖音：口语化、节奏感、热点
- 微信公众号：深度、图文并茂
- Twitter/X：英文、简洁、话题标签"""
    
    async def generate_post(
        self,
        ctx: ToolContext,
        topic: str,
        platform: str = "xiaohongshu",
        style: str = "informative",
        keywords: Optional[list[str]] = None,
    ) -> ToolResult:
        """生成社媒帖子"""
        platform_names = {
            "xiaohongshu": "小红书",
            "weibo": "微博",
            "douyin": "抖音",
            "wechat": "微信公众号",
            "twitter": "Twitter/X",
        }
        
        style_names = {
            "informative": "干货分享型",
            "emotional": "情感共鸣型",
            "humorous": "幽默搞笑型",
            "professional": "专业权威型",
        }
        
        platform_name = platform_names.get(platform, platform)
        style_name = style_names.get(style, style)
        
        # 生成帖子模板
        template = self._get_post_template(platform, topic, style)
        
        keywords_str = ", ".join(keywords) if keywords else ""
        
        return ToolResult.success_result(
            data={
                "topic": topic,
                "platform": platform_name,
                "style": style_name,
                "keywords": keywords,
                "template": template,
                "instruction": f"请根据以下信息生成{platform_name}帖子：\n"
                               f"- 主题: {topic}\n"
                               f"- 风格: {style_name}\n"
                               f"- 关键词: {keywords_str}\n\n"
                               f"参考模板：\n{template}",
            },
            message=f"请生成{platform_name}帖子",
        )
    
    def _get_post_template(self, platform: str, topic: str, style: str) -> str:
        """获取平台帖子模板"""
        if platform == "xiaohongshu":
            return f"""📌 {topic}

大家好！今天来分享一下关于{topic}的内容～

💡 核心要点：
1️⃣ [要点1]
2️⃣ [要点2]
3️⃣ [要点3]

✨ 个人心得：
[分享个人经验]

💬 互动话题：
你们对{topic}有什么看法呢？评论区见～

#小红书 #{topic} #[相关标签]"""
        
        elif platform == "weibo":
            return f"""【{topic}】

[内容简述]

[配图说明]

#{topic}# #热门话题#"""
        
        elif platform == "douyin":
            return f"""🔥 {topic}

开头Hook：[吸引眼球的开场]

正文：
- [要点1]
- [要点2]
- [要点3]

结尾CTA：关注我，了解更多～

#{topic} #抖音热门"""
        
        else:
            return f"""【{topic}】

[正文内容]

#[标签]"""
    
    async def generate_hashtags(
        self,
        ctx: ToolContext,
        content: str,
        platform: str = "xiaohongshu",
        count: int = 10,
    ) -> ToolResult:
        """生成话题标签"""
        # 返回生成提示
        return ToolResult.success_result(
            data={
                "content": content[:200],
                "platform": platform,
                "requested_count": count,
                "instruction": f"请为以下内容生成 {count} 个适合 {platform} 平台的话题标签：\n\n{content}",
            },
            message=f"请生成 {count} 个标签",
        )
    
    async def create_content_calendar(
        self,
        ctx: ToolContext,
        topics: list[str],
        platform: str = "xiaohongshu",
        days: int = 7,
        posts_per_day: int = 1,
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """创建内容日历"""
        from datetime import timedelta
        
        today = datetime.now()
        
        content = f"""# 内容发布日历

**平台**: {platform}  
**周期**: {today.strftime("%Y-%m-%d")} ~ {(today + timedelta(days=days-1)).strftime("%Y-%m-%d")}  
**频率**: 每日 {posts_per_day} 条

---

"""
        
        topic_index = 0
        for i in range(days):
            date = today + timedelta(days=i)
            content += f"""## {date.strftime("%Y-%m-%d")} ({["周一","周二","周三","周四","周五","周六","周日"][date.weekday()]})

"""
            for j in range(posts_per_day):
                topic = topics[topic_index % len(topics)]
                topic_index += 1
                
                # 推荐发布时间
                if platform == "xiaohongshu":
                    time_slots = ["12:00", "18:30", "21:00"]
                elif platform == "weibo":
                    time_slots = ["08:00", "12:00", "22:00"]
                else:
                    time_slots = ["12:00", "20:00"]
                
                time_slot = time_slots[j % len(time_slots)]
                
                content += f"""### 帖子 {j + 1}

- **发布时间**: {time_slot}
- **主题**: {topic}
- **内容类型**: [图文/视频]
- **状态**: ⏳ 待创作

---

"""
        
        content += """## 内容创作清单

| 日期 | 主题 | 状态 |
|------|------|------|
"""
        
        topic_index = 0
        for i in range(days):
            date = today + timedelta(days=i)
            for j in range(posts_per_day):
                topic = topics[topic_index % len(topics)]
                topic_index += 1
                content += f"| {date.strftime('%m-%d')} | {topic} | ⏳ |\n"
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message=f"内容日历已生成 ({days} 天)")
        
        return ToolResult.success_result(
            data={
                "content": content,
                "days": days,
                "total_posts": days * posts_per_day,
            },
            message=f"内容日历已生成 ({days} 天, {days * posts_per_day} 条)",
        )
    
    async def generate_reply(
        self,
        ctx: ToolContext,
        comment: str,
        tone: str = "friendly",
        brand_name: Optional[str] = None,
    ) -> ToolResult:
        """生成评论回复"""
        tone_names = {
            "friendly": "友好亲切",
            "professional": "专业正式",
            "humorous": "幽默风趣",
            "grateful": "感谢致谢",
        }
        
        tone_name = tone_names.get(tone, tone)
        
        return ToolResult.success_result(
            data={
                "comment": comment,
                "tone": tone_name,
                "brand_name": brand_name,
                "instruction": f"请以{tone_name}的语气回复以下评论"
                               f"{f'（品牌: {brand_name}）' if brand_name else ''}：\n\n"
                               f"评论: {comment}",
            },
            message="请生成回复",
        )
    
    async def analyze_post_performance(
        self,
        ctx: ToolContext,
        content: str,
        platform: str = "xiaohongshu",
    ) -> ToolResult:
        """分析帖子表现 (预测)"""
        # 简单的内容分析
        analysis = {
            "length": len(content),
            "has_emoji": any(ord(c) > 0x1F600 for c in content),
            "has_hashtags": "#" in content,
            "has_call_to_action": any(word in content for word in ["关注", "点赞", "收藏", "评论"]),
            "has_numbers": any(c.isdigit() for c in content),
        }
        
        # 评分
        score = 50
        if analysis["has_emoji"]:
            score += 10
        if analysis["has_hashtags"]:
            score += 15
        if analysis["has_call_to_action"]:
            score += 10
        if 200 <= analysis["length"] <= 1000:
            score += 15
        
        suggestions = []
        if not analysis["has_emoji"]:
            suggestions.append("建议添加 emoji 增加亲和力")
        if not analysis["has_hashtags"]:
            suggestions.append("建议添加话题标签增加曝光")
        if not analysis["has_call_to_action"]:
            suggestions.append("建议添加互动引导提升互动率")
        if analysis["length"] < 200:
            suggestions.append("内容偏短，建议丰富内容")
        
        return ToolResult.success_result(
            data={
                "score": min(100, score),
                "analysis": analysis,
                "suggestions": suggestions,
            },
            message=f"内容评分: {min(100, score)}/100",
        )
    
    async def generate_image_prompt(
        self,
        ctx: ToolContext,
        content: str,
        style: str = "modern",
    ) -> ToolResult:
        """生成配图提示词"""
        return ToolResult.success_result(
            data={
                "content_summary": content[:200],
                "style": style,
                "instruction": f"请为以下社媒内容生成 AI 配图提示词（{style}风格）：\n\n{content}",
            },
            message="请生成配图提示词",
        )
    
    async def batch_generate_posts(
        self,
        ctx: ToolContext,
        topics: list[str],
        platform: str = "xiaohongshu",
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """批量生成帖子"""
        if not topics:
            return ToolResult.error_result("主题列表不能为空")
        
        content = f"""# 批量帖子内容

**平台**: {platform}  
**数量**: {len(topics)} 条

---

"""
        
        for i, topic in enumerate(topics, 1):
            template = self._get_post_template(platform, topic, "informative")
            content += f"""## 帖子 {i}: {topic}

{template}

---

"""
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message=f"已生成 {len(topics)} 条帖子模板")
        
        return ToolResult.success_result(
            data={
                "content": content,
                "count": len(topics),
                "topics": topics,
            },
            message=f"已生成 {len(topics)} 条帖子模板",
        )
