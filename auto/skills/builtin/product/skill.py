"""产品助手技能"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class ProductSkill(Skill):
    """产品助手技能
    
    提供 PRD 生成、需求分析、用户故事等功能。
    """
    
    @property
    def name(self) -> str:
        return "product"
    
    @property
    def display_name(self) -> str:
        return "产品助手"
    
    @property
    def description(self) -> str:
        return "PRD 生成、需求分析、用户故事、竞品分析"
    
    @property
    def category(self) -> str:
        return "management"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="generate_prd",
                description="生成产品需求文档 (PRD)",
                parameters={
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "产品名称",
                        },
                        "description": {
                            "type": "string",
                            "description": "产品描述和背景",
                        },
                        "features": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "主要功能列表",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径 (.md)",
                        },
                        "template": {
                            "type": "string",
                            "enum": ["standard", "simple", "detailed"],
                            "description": "模板类型",
                            "default": "standard",
                        },
                    },
                    "required": ["product_name", "description", "output_path"],
                },
                handler=self.generate_prd,
            ),
            ToolDefinition(
                name="generate_user_stories",
                description="生成用户故事",
                parameters={
                    "type": "object",
                    "properties": {
                        "feature": {
                            "type": "string",
                            "description": "功能描述",
                        },
                        "user_roles": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "用户角色列表",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["feature"],
                },
                handler=self.generate_user_stories,
            ),
            ToolDefinition(
                name="analyze_requirement",
                description="分析需求，提取关键信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "requirement": {
                            "type": "string",
                            "description": "原始需求描述",
                        },
                    },
                    "required": ["requirement"],
                },
                handler=self.analyze_requirement,
            ),
            ToolDefinition(
                name="generate_api_spec",
                description="根据需求生成 API 规格",
                parameters={
                    "type": "object",
                    "properties": {
                        "feature": {
                            "type": "string",
                            "description": "功能描述",
                        },
                        "entities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "涉及的实体",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["feature"],
                },
                handler=self.generate_api_spec,
            ),
            ToolDefinition(
                name="generate_prototype_spec",
                description="生成原型设计规格",
                parameters={
                    "type": "object",
                    "properties": {
                        "feature": {
                            "type": "string",
                            "description": "功能描述",
                        },
                        "platform": {
                            "type": "string",
                            "enum": ["web", "mobile", "desktop"],
                            "description": "目标平台",
                            "default": "web",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["feature"],
                },
                handler=self.generate_prototype_spec,
            ),
            ToolDefinition(
                name="compare_products",
                description="竞品分析",
                parameters={
                    "type": "object",
                    "properties": {
                        "our_product": {
                            "type": "string",
                            "description": "我们的产品",
                        },
                        "competitors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "竞品列表",
                        },
                        "dimensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "比较维度",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["our_product", "competitors"],
                },
                handler=self.compare_products,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个专业的产品经理助手，擅长：
- 撰写清晰、完整的产品需求文档 (PRD)
- 将模糊需求转化为具体的用户故事
- 进行竞品分析和市场调研
- 设计 API 规格和数据模型
- 创建原型设计规格

文档撰写原则：
1. 结构清晰，层次分明
2. 使用 SMART 原则定义目标
3. 考虑边界条件和异常情况
4. 提供验收标准
5. 使用 Markdown 格式"""
    
    async def generate_prd(
        self,
        ctx: ToolContext,
        product_name: str,
        description: str,
        output_path: str,
        features: Optional[list[str]] = None,
        template: str = "standard",
    ) -> ToolResult:
        """生成 PRD 文档"""
        path = Path(output_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {output_path}")
        
        features = features or []
        
        # 根据模板生成内容
        if template == "simple":
            content = self._generate_simple_prd(product_name, description, features)
        elif template == "detailed":
            content = self._generate_detailed_prd(product_name, description, features)
        else:
            content = self._generate_standard_prd(product_name, description, features)
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            
            return ToolResult.file(
                path=str(path),
                message=f"PRD 已生成: {path.name}",
            )
        except Exception as e:
            return ToolResult.error_result(f"生成 PRD 失败: {str(e)}")
    
    def _generate_standard_prd(
        self,
        product_name: str,
        description: str,
        features: list[str],
    ) -> str:
        """生成标准 PRD"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        features_section = ""
        if features:
            features_list = "\n".join(f"- {f}" for f in features)
            features_section = f"""
## 3. 功能需求

### 3.1 功能列表

{features_list}

### 3.2 功能详情

"""
            for i, feature in enumerate(features, 1):
                features_section += f"""#### 3.2.{i} {feature}

**描述**: [待补充]

**用户故事**:
- 作为 [用户角色]，我想要 [功能]，以便 [价值]

**验收标准**:
- [ ] 条件1
- [ ] 条件2

---

"""
        
        return f"""# {product_name} 产品需求文档 (PRD)

**版本**: v1.0  
**日期**: {today}  
**状态**: 草稿

---

## 1. 产品概述

### 1.1 背景

{description}

### 1.2 目标

- 主要目标: [待补充]
- 次要目标: [待补充]

### 1.3 目标用户

| 用户角色 | 特征描述 | 核心需求 |
|----------|----------|----------|
| 角色1 | [描述] | [需求] |
| 角色2 | [描述] | [需求] |

---

## 2. 业务流程

### 2.1 核心流程

```
[开始] -> [步骤1] -> [步骤2] -> [结束]
```

### 2.2 状态流转

```
状态A -> 状态B -> 状态C
```

---
{features_section}
## 4. 非功能需求

### 4.1 性能要求

- 响应时间: < 500ms
- 并发支持: 1000 QPS

### 4.2 安全要求

- 数据加密
- 权限控制

---

## 5. 排期计划

| 阶段 | 内容 | 交付物 |
|------|------|--------|
| P0 | MVP | 核心功能 |
| P1 | 优化 | 完善功能 |
| P2 | 扩展 | 增值功能 |

---

## 6. 附录

### 6.1 术语表

| 术语 | 定义 |
|------|------|
| 术语1 | 定义1 |

### 6.2 参考文档

- [文档1](链接)
"""
    
    def _generate_simple_prd(
        self,
        product_name: str,
        description: str,
        features: list[str],
    ) -> str:
        """生成简版 PRD"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        features_text = "\n".join(f"- {f}" for f in features) if features else "- [待补充]"
        
        return f"""# {product_name}

**日期**: {today}

## 背景

{description}

## 目标

- [主要目标]

## 功能

{features_text}

## 验收标准

- [ ] 功能可用
- [ ] 性能达标
"""
    
    def _generate_detailed_prd(
        self,
        product_name: str,
        description: str,
        features: list[str],
    ) -> str:
        """生成详细 PRD"""
        base = self._generate_standard_prd(product_name, description, features)
        
        additional = """
---

## 7. 数据模型

### 7.1 实体关系

```
Entity1 --< Entity2 >-- Entity3
```

### 7.2 字段定义

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | bigint | 主键 | ✓ |

---

## 8. 接口设计

### 8.1 接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/v1/resource | POST | 创建资源 |

---

## 9. 埋点设计

| 事件 | 触发时机 | 参数 |
|------|----------|------|
| page_view | 页面加载 | page_id |

---

## 10. 灰度策略

- 第1周: 1% 用户
- 第2周: 10% 用户
- 第3周: 全量
"""
        return base + additional
    
    async def generate_user_stories(
        self,
        ctx: ToolContext,
        feature: str,
        user_roles: Optional[list[str]] = None,
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成用户故事"""
        user_roles = user_roles or ["用户", "管理员"]
        
        stories = []
        for role in user_roles:
            stories.append({
                "role": role,
                "story": f"作为{role}，我想要{feature}",
                "acceptance": [
                    "功能正常可用",
                    "界面清晰易懂",
                    "操作响应及时",
                ],
            })
        
        content = f"""# 用户故事: {feature}

**创建日期**: {datetime.now().strftime("%Y-%m-%d")}

---

"""
        for i, story in enumerate(stories, 1):
            criteria = "\n".join(f"- [ ] {c}" for c in story["acceptance"])
            content += f"""## Story {i}: {story["role"]}

**故事**: {story["story"]}

**验收标准**:
{criteria}

---

"""
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message="用户故事已生成")
        
        return ToolResult.success_result(
            data={"stories": stories, "content": content},
            message=f"生成了 {len(stories)} 个用户故事",
        )
    
    async def analyze_requirement(
        self,
        ctx: ToolContext,
        requirement: str,
    ) -> ToolResult:
        """分析需求"""
        # 基础分析结构
        analysis = {
            "original": requirement,
            "summary": f"需求摘要: {requirement[:100]}...",
            "entities": [],
            "actions": [],
            "constraints": [],
            "questions": [
                "目标用户是谁？",
                "预期交付时间？",
                "有无技术限制？",
            ],
            "risks": [
                "需求边界不清晰",
                "可能存在隐性需求",
            ],
        }
        
        return ToolResult.success_result(
            data=analysis,
            message="需求分析完成，请 AI 进一步细化",
        )
    
    async def generate_api_spec(
        self,
        ctx: ToolContext,
        feature: str,
        entities: Optional[list[str]] = None,
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成 API 规格"""
        entities = entities or ["Resource"]
        
        content = f"""# API 规格: {feature}

**版本**: v1  
**基础路径**: /api/v1

---

"""
        for entity in entities:
            entity_lower = entity.lower()
            content += f"""## {entity} API

### 创建 {entity}

```
POST /{entity_lower}s

Request:
{{
    "name": "string",
    "description": "string"
}}

Response: 201
{{
    "id": 1,
    "name": "string",
    "created_at": "2024-01-01T00:00:00Z"
}}
```

### 获取 {entity} 列表

```
GET /{entity_lower}s?page=1&size=20

Response: 200
{{
    "items": [...],
    "total": 100,
    "page": 1,
    "size": 20
}}
```

### 获取 {entity} 详情

```
GET /{entity_lower}s/{{id}}

Response: 200
{{
    "id": 1,
    "name": "string",
    ...
}}
```

### 更新 {entity}

```
PUT /{entity_lower}s/{{id}}

Request:
{{
    "name": "new name"
}}

Response: 200
```

### 删除 {entity}

```
DELETE /{entity_lower}s/{{id}}

Response: 204
```

---

"""
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message="API 规格已生成")
        
        return ToolResult.success_result(
            data={"content": content},
            message=f"为 {len(entities)} 个实体生成了 API 规格",
        )
    
    async def generate_prototype_spec(
        self,
        ctx: ToolContext,
        feature: str,
        platform: str = "web",
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成原型设计规格"""
        content = f"""# 原型设计规格: {feature}

**平台**: {platform}  
**日期**: {datetime.now().strftime("%Y-%m-%d")}

---

## 1. 页面结构

### 1.1 页面列表

| 页面 | 路径 | 说明 |
|------|------|------|
| 首页 | / | 入口页面 |
| 详情页 | /detail/:id | 详情展示 |

### 1.2 页面流程

```
首页 -> 列表页 -> 详情页
         ↓
      操作页 -> 结果页
```

---

## 2. 组件设计

### 2.1 头部导航

- Logo
- 导航菜单
- 用户头像

### 2.2 主内容区

- 筛选条件
- 数据列表/卡片
- 分页器

### 2.3 侧边栏

- 快捷操作
- 辅助信息

---

## 3. 交互说明

### 3.1 核心交互

| 操作 | 触发 | 反馈 |
|------|------|------|
| 点击按钮 | 鼠标点击 | 加载动画 |
| 提交表单 | 点击提交 | Toast 提示 |

### 3.2 手势支持 (移动端)

- 下拉刷新
- 左滑删除
- 长按菜单

---

## 4. 响应式适配

| 断点 | 宽度 | 布局 |
|------|------|------|
| Mobile | < 768px | 单列 |
| Tablet | 768-1024px | 双列 |
| Desktop | > 1024px | 多列 |

---

## 5. 设计规范

### 5.1 颜色

- 主色: #1890FF
- 成功: #52C41A
- 警告: #FAAD14
- 错误: #FF4D4F

### 5.2 字体

- 标题: 20px Bold
- 正文: 14px Regular
- 辅助: 12px Regular
"""
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message="原型规格已生成")
        
        return ToolResult.success_result(
            data={"content": content, "platform": platform},
            message="原型设计规格已生成",
        )
    
    async def compare_products(
        self,
        ctx: ToolContext,
        our_product: str,
        competitors: list[str],
        dimensions: Optional[list[str]] = None,
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """竞品分析"""
        dimensions = dimensions or ["功能完整性", "用户体验", "价格", "技术架构", "市场份额"]
        
        # 构建比较表格
        products = [our_product] + competitors
        header = "| 维度 | " + " | ".join(products) + " |"
        separator = "|------|" + "|".join(["------"] * len(products)) + "|"
        
        rows = []
        for dim in dimensions:
            row = f"| {dim} | " + " | ".join(["[待评估]"] * len(products)) + " |"
            rows.append(row)
        
        table = "\n".join([header, separator] + rows)
        
        content = f"""# 竞品分析报告

**日期**: {datetime.now().strftime("%Y-%m-%d")}  
**我方产品**: {our_product}  
**竞品**: {", ".join(competitors)}

---

## 1. 竞品概览

{table}

---

## 2. 竞品详情

"""
        for comp in competitors:
            content += f"""### {comp}

**简介**: [待补充]

**优势**:
- 优势1
- 优势2

**劣势**:
- 劣势1
- 劣势2

**定位**: [待补充]

---

"""
        
        content += """## 3. SWOT 分析

### 优势 (Strengths)
- S1

### 劣势 (Weaknesses)
- W1

### 机会 (Opportunities)
- O1

### 威胁 (Threats)
- T1

---

## 4. 策略建议

1. 建议1
2. 建议2
3. 建议3
"""
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message="竞品分析报告已生成")
        
        return ToolResult.success_result(
            data={"content": content, "competitors": competitors},
            message=f"竞品分析完成，比较了 {len(competitors)} 个竞品",
        )
