"""项目管理技能"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class ProjectSkill(Skill):
    """项目管理技能
    
    提供 WBS 拆分、任务管理、周报生成、风险评估等功能。
    """
    
    @property
    def name(self) -> str:
        return "project"
    
    @property
    def display_name(self) -> str:
        return "项目管理"
    
    @property
    def description(self) -> str:
        return "WBS 拆分、任务管理、周报日报、风险评估、会议纪要"
    
    @property
    def category(self) -> str:
        return "management"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="generate_wbs",
                description="生成工作分解结构 (WBS)",
                parameters={
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                            "description": "项目名称",
                        },
                        "description": {
                            "type": "string",
                            "description": "项目描述",
                        },
                        "milestones": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "主要里程碑",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                        "format": {
                            "type": "string",
                            "enum": ["markdown", "excel"],
                            "description": "输出格式",
                            "default": "markdown",
                        },
                    },
                    "required": ["project_name", "description", "output_path"],
                },
                handler=self.generate_wbs,
            ),
            ToolDefinition(
                name="generate_weekly_report",
                description="生成周报",
                parameters={
                    "type": "object",
                    "properties": {
                        "completed": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "本周完成的工作",
                        },
                        "in_progress": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "进行中的工作",
                        },
                        "planned": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "下周计划",
                        },
                        "issues": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "遇到的问题",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["completed", "planned"],
                },
                handler=self.generate_weekly_report,
            ),
            ToolDefinition(
                name="generate_daily_report",
                description="生成日报",
                parameters={
                    "type": "object",
                    "properties": {
                        "completed": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "今日完成",
                        },
                        "planned": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "明日计划",
                        },
                        "blockers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "阻塞问题",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["completed"],
                },
                handler=self.generate_daily_report,
            ),
            ToolDefinition(
                name="risk_assessment",
                description="项目风险评估",
                parameters={
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                            "description": "项目名称",
                        },
                        "risks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "probability": {"type": "string"},
                                    "impact": {"type": "string"},
                                },
                            },
                            "description": "风险列表",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["project_name"],
                },
                handler=self.risk_assessment,
            ),
            ToolDefinition(
                name="generate_meeting_notes",
                description="生成会议纪要",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "会议主题",
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "参会人员",
                        },
                        "content": {
                            "type": "string",
                            "description": "会议内容记录",
                        },
                        "action_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "task": {"type": "string"},
                                    "owner": {"type": "string"},
                                    "deadline": {"type": "string"},
                                },
                            },
                            "description": "待办事项",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["title", "content"],
                },
                handler=self.generate_meeting_notes,
            ),
            ToolDefinition(
                name="generate_gantt_data",
                description="生成甘特图数据",
                parameters={
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                            "description": "项目名称",
                        },
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "start": {"type": "string"},
                                    "duration": {"type": "integer"},
                                    "dependencies": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                            "description": "任务列表",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["project_name", "tasks"],
                },
                handler=self.generate_gantt_data,
            ),
            ToolDefinition(
                name="estimate_effort",
                description="工作量估算",
                parameters={
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "任务列表",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["story_points", "hours", "days"],
                            "description": "估算方法",
                            "default": "story_points",
                        },
                    },
                    "required": ["tasks"],
                },
                handler=self.estimate_effort,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个专业的项目管理助手，熟悉 PMP 规范，擅长：
- 工作分解结构 (WBS) 设计
- 进度计划和甘特图
- 风险识别和管理
- 周报日报撰写
- 会议纪要整理

项目管理原则：
1. 任务粒度适中 (2-8小时)
2. 明确责任人和截止时间
3. 识别关键路径
4. 预留缓冲时间 (10-20%)
5. 持续跟踪和调整"""
    
    async def generate_wbs(
        self,
        ctx: ToolContext,
        project_name: str,
        description: str,
        output_path: str,
        milestones: Optional[list[str]] = None,
        format: str = "markdown",
    ) -> ToolResult:
        """生成 WBS"""
        path = Path(output_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {output_path}")
        
        milestones = milestones or ["需求分析", "设计开发", "测试上线"]
        today = datetime.now()
        
        if format == "excel":
            return await self._generate_wbs_excel(path, project_name, description, milestones)
        
        # Markdown 格式
        content = f"""# {project_name} - 工作分解结构 (WBS)

**项目描述**: {description}  
**创建日期**: {today.strftime("%Y-%m-%d")}  
**预计周期**: [待确定]

---

## 1. 项目概览

```
{project_name}
├── 1. 项目启动
│   ├── 1.1 需求确认
│   ├── 1.2 团队组建
│   └── 1.3 启动会议
"""
        
        for i, milestone in enumerate(milestones, 2):
            content += f"""├── {i}. {milestone}
│   ├── {i}.1 [子任务1]
│   ├── {i}.2 [子任务2]
│   └── {i}.3 [子任务3]
"""
        
        content += f"""└── {len(milestones) + 2}. 项目收尾
    ├── {len(milestones) + 2}.1 验收测试
    ├── {len(milestones) + 2}.2 文档归档
    └── {len(milestones) + 2}.3 复盘总结
```

---

## 2. 任务分解

"""
        
        # 生成任务表格
        content += """| WBS编号 | 任务名称 | 负责人 | 预计工时 | 开始日期 | 结束日期 | 状态 |
|---------|----------|--------|----------|----------|----------|------|
| 1.0 | 项目启动 | PM | - | - | - | - |
| 1.1 | 需求确认 | PM | 8h | - | - | 待开始 |
| 1.2 | 团队组建 | PM | 4h | - | - | 待开始 |
| 1.3 | 启动会议 | PM | 2h | - | - | 待开始 |
"""
        
        for i, milestone in enumerate(milestones, 2):
            content += f"""| {i}.0 | {milestone} | [待分配] | - | - | - | - |
| {i}.1 | [子任务1] | [待分配] | 16h | - | - | 待开始 |
| {i}.2 | [子任务2] | [待分配] | 16h | - | - | 待开始 |
| {i}.3 | [子任务3] | [待分配] | 8h | - | - | 待开始 |
"""
        
        content += f"""
---

## 3. 里程碑

| 里程碑 | 目标日期 | 交付物 | 验收标准 |
|--------|----------|--------|----------|
| M1 - 项目启动 | {(today + timedelta(days=7)).strftime("%Y-%m-%d")} | 项目计划 | 计划评审通过 |
"""
        
        for i, milestone in enumerate(milestones):
            days = (i + 2) * 14
            content += f"""| M{i+2} - {milestone} | {(today + timedelta(days=days)).strftime("%Y-%m-%d")} | [交付物] | [验收标准] |
"""
        
        content += """
---

## 4. 依赖关系

```
1.0 项目启动 → 2.0 [阶段1] → 3.0 [阶段2] → 4.0 项目收尾
```

---

## 5. 资源需求

| 角色 | 人数 | 投入比例 | 技能要求 |
|------|------|----------|----------|
| 项目经理 | 1 | 50% | PMP认证 |
| 开发工程师 | 2 | 100% | [技术栈] |
| 测试工程师 | 1 | 50% | 自动化测试 |

---

## 6. 风险预警

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 需求变更 | 高 | 中 | 变更控制流程 |
| 资源不足 | 中 | 高 | 提前储备 |
"""
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            
            return ToolResult.file(
                path=str(path),
                message=f"WBS 已生成: {path.name}",
            )
        except Exception as e:
            return ToolResult.error_result(f"生成 WBS 失败: {str(e)}")
    
    async def _generate_wbs_excel(
        self,
        path: Path,
        project_name: str,
        description: str,
        milestones: list[str],
    ) -> ToolResult:
        """生成 Excel 格式的 WBS"""
        try:
            import pandas as pd
        except ImportError:
            return ToolResult.error_result("需要安装 pandas: pip install pandas openpyxl")
        
        # 构建任务数据
        tasks = [
            {"WBS编号": "1.0", "任务名称": "项目启动", "负责人": "PM", "预计工时": "", "状态": ""},
            {"WBS编号": "1.1", "任务名称": "需求确认", "负责人": "PM", "预计工时": "8h", "状态": "待开始"},
            {"WBS编号": "1.2", "任务名称": "团队组建", "负责人": "PM", "预计工时": "4h", "状态": "待开始"},
        ]
        
        for i, milestone in enumerate(milestones, 2):
            tasks.append({"WBS编号": f"{i}.0", "任务名称": milestone, "负责人": "", "预计工时": "", "状态": ""})
            tasks.append({"WBS编号": f"{i}.1", "任务名称": f"{milestone}-子任务1", "负责人": "", "预计工时": "16h", "状态": "待开始"})
            tasks.append({"WBS编号": f"{i}.2", "任务名称": f"{milestone}-子任务2", "负责人": "", "预计工时": "16h", "状态": "待开始"})
        
        df = pd.DataFrame(tasks)
        
        # 确保路径以 .xlsx 结尾
        if not str(path).endswith(".xlsx"):
            path = path.with_suffix(".xlsx")
        
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(str(path), index=False, sheet_name="WBS")
        
        return ToolResult.file(
            path=str(path),
            message=f"WBS Excel 已生成: {path.name}",
        )
    
    async def generate_weekly_report(
        self,
        ctx: ToolContext,
        completed: list[str],
        planned: list[str],
        in_progress: Optional[list[str]] = None,
        issues: Optional[list[str]] = None,
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成周报"""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        completed_text = "\n".join(f"- [x] {item}" for item in completed)
        in_progress_text = "\n".join(f"- [ ] {item}" for item in (in_progress or []))
        planned_text = "\n".join(f"- [ ] {item}" for item in planned)
        issues_text = "\n".join(f"- {item}" for item in (issues or [])) or "无"
        
        content = f"""# 周报

**周期**: {week_start.strftime("%Y-%m-%d")} ~ {week_end.strftime("%Y-%m-%d")}  
**提交人**: [姓名]  
**部门**: [部门]

---

## 本周完成

{completed_text}

## 进行中

{in_progress_text if in_progress else "无"}

## 下周计划

{planned_text}

## 问题与风险

{issues_text}

## 需要支持

- [如有需要，请填写]

---

**工作时长**: [X]小时  
**加班时长**: [X]小时
"""
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message="周报已生成")
        
        return ToolResult.success_result(
            data={"content": content},
            message=f"周报已生成: {len(completed)} 项完成, {len(planned)} 项计划",
        )
    
    async def generate_daily_report(
        self,
        ctx: ToolContext,
        completed: list[str],
        planned: Optional[list[str]] = None,
        blockers: Optional[list[str]] = None,
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成日报"""
        today = datetime.now()
        
        completed_text = "\n".join(f"- {item}" for item in completed)
        planned_text = "\n".join(f"- {item}" for item in (planned or []))
        blockers_text = "\n".join(f"- {item}" for item in (blockers or [])) or "无"
        
        content = f"""# 日报 - {today.strftime("%Y-%m-%d")}

**提交人**: [姓名]

---

## 今日完成

{completed_text}

## 明日计划

{planned_text if planned else "[待规划]"}

## 阻塞问题

{blockers_text}
"""
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message="日报已生成")
        
        return ToolResult.success_result(
            data={"content": content},
            message="日报已生成",
        )
    
    async def risk_assessment(
        self,
        ctx: ToolContext,
        project_name: str,
        risks: Optional[list[dict]] = None,
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """风险评估"""
        today = datetime.now()
        
        # 默认风险列表
        default_risks = [
            {"name": "需求变更", "probability": "高", "impact": "中", "mitigation": "变更控制流程"},
            {"name": "资源不足", "probability": "中", "impact": "高", "mitigation": "提前储备、外包"},
            {"name": "技术风险", "probability": "中", "impact": "高", "mitigation": "技术预研、专家支持"},
            {"name": "进度延期", "probability": "中", "impact": "中", "mitigation": "里程碑检查、每日站会"},
            {"name": "沟通不畅", "probability": "低", "impact": "中", "mitigation": "定期同步会"},
        ]
        
        risks = risks or default_risks
        
        # 风险矩阵
        content = f"""# {project_name} - 风险评估报告

**评估日期**: {today.strftime("%Y-%m-%d")}  
**评估人**: [姓名]

---

## 1. 风险矩阵

```
影响程度
高   |  ●○  |  ●●  |  ●●● 
中   |  ○   |  ●○  |  ●●  
低   |  ○   |  ○   |  ●○  
     +------+------+------
          低     中     高    概率
```

**图例**: ○ 可接受  ●○ 需监控  ●● 需应对  ●●● 关键风险

---

## 2. 风险清单

| 序号 | 风险名称 | 发生概率 | 影响程度 | 风险等级 | 应对措施 | 责任人 |
|------|----------|----------|----------|----------|----------|--------|
"""
        
        for i, risk in enumerate(risks, 1):
            name = risk.get("name", f"风险{i}")
            prob = risk.get("probability", "中")
            impact = risk.get("impact", "中")
            mitigation = risk.get("mitigation", "待制定")
            
            # 计算风险等级
            level_map = {
                ("高", "高"): "🔴 关键",
                ("高", "中"): "🟠 高",
                ("中", "高"): "🟠 高",
                ("中", "中"): "🟡 中",
                ("低", "高"): "🟡 中",
                ("高", "低"): "🟡 中",
                ("中", "低"): "🟢 低",
                ("低", "中"): "🟢 低",
                ("低", "低"): "🟢 低",
            }
            level = level_map.get((prob, impact), "🟡 中")
            
            content += f"| {i} | {name} | {prob} | {impact} | {level} | {mitigation} | [待分配] |\n"
        
        content += """
---

## 3. 应对计划

### 3.1 规避策略

- 提前识别高风险领域
- 技术预研降低不确定性

### 3.2 缓解策略

- 分阶段交付降低风险
- 增加测试覆盖

### 3.3 转移策略

- 关键模块外包
- 购买保险

### 3.4 接受策略

- 低影响风险监控即可
- 预留风险缓冲金

---

## 4. 监控机制

| 监控项 | 频率 | 责任人 | 预警阈值 |
|--------|------|--------|----------|
| 进度偏差 | 每周 | PM | >10% |
| 资源使用率 | 每周 | PM | >90% |
| 缺陷密度 | 每周 | QA | >5个/千行 |
| 需求变更 | 每次 | PM | >3次/月 |

---

## 5. 复盘计划

- 每阶段结束进行风险复盘
- 更新风险知识库
- 优化评估方法
"""
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message="风险评估报告已生成")
        
        return ToolResult.success_result(
            data={"content": content, "risk_count": len(risks)},
            message=f"识别了 {len(risks)} 个风险",
        )
    
    async def generate_meeting_notes(
        self,
        ctx: ToolContext,
        title: str,
        content: str,
        attendees: Optional[list[str]] = None,
        action_items: Optional[list[dict]] = None,
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成会议纪要"""
        today = datetime.now()
        
        attendees_text = ", ".join(attendees) if attendees else "[参会人员]"
        
        actions_text = ""
        if action_items:
            actions_text = "\n| 待办事项 | 负责人 | 截止日期 | 状态 |\n|----------|--------|----------|------|\n"
            for item in action_items:
                task = item.get("task", "")
                owner = item.get("owner", "待分配")
                deadline = item.get("deadline", "待定")
                actions_text += f"| {task} | {owner} | {deadline} | ⏳ 进行中 |\n"
        else:
            actions_text = "\n- [ ] [待办1]\n- [ ] [待办2]"
        
        output = f"""# 会议纪要

**会议主题**: {title}  
**会议时间**: {today.strftime("%Y-%m-%d %H:%M")}  
**参会人员**: {attendees_text}  
**记录人**: [姓名]

---

## 会议内容

{content}

---

## 决议事项

1. [决议1]
2. [决议2]

---

## 待办事项
{actions_text}

---

## 下次会议

- **时间**: [待定]
- **议题**: [待定]
"""
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(output, encoding="utf-8")
                return ToolResult.file(path=str(path), message="会议纪要已生成")
        
        return ToolResult.success_result(
            data={"content": output},
            message="会议纪要已生成",
        )
    
    async def generate_gantt_data(
        self,
        ctx: ToolContext,
        project_name: str,
        tasks: list[dict],
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成甘特图数据"""
        # 生成 Mermaid 格式的甘特图
        content = f"""# {project_name} - 甘特图

## Mermaid 格式

```mermaid
gantt
    title {project_name}
    dateFormat  YYYY-MM-DD
    
    section 项目阶段
"""
        
        for task in tasks:
            name = task.get("name", "任务")
            start = task.get("start", datetime.now().strftime("%Y-%m-%d"))
            duration = task.get("duration", 7)
            deps = task.get("dependencies", [])
            
            dep_str = f"after {deps[0]}" if deps else start
            content += f"    {name} :{name.replace(' ', '_')}, {dep_str}, {duration}d\n"
        
        content += """```

## 任务列表

| 任务 | 开始日期 | 工期(天) | 依赖 |
|------|----------|----------|------|
"""
        
        for task in tasks:
            name = task.get("name", "任务")
            start = task.get("start", "-")
            duration = task.get("duration", 0)
            deps = ", ".join(task.get("dependencies", [])) or "-"
            content += f"| {name} | {start} | {duration} | {deps} |\n"
        
        if output_path:
            path = Path(output_path).expanduser()
            if ctx.security.is_allowed_path(path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return ToolResult.file(path=str(path), message="甘特图数据已生成")
        
        return ToolResult.success_result(
            data={"content": content, "task_count": len(tasks)},
            message=f"生成了 {len(tasks)} 个任务的甘特图",
        )
    
    async def estimate_effort(
        self,
        ctx: ToolContext,
        tasks: list[str],
        method: str = "story_points",
    ) -> ToolResult:
        """工作量估算"""
        estimates = []
        
        # 基于任务复杂度的简单估算
        for task in tasks:
            # 根据任务名称长度和关键词估算
            base = 3
            if any(word in task.lower() for word in ["复杂", "重构", "架构", "优化"]):
                base = 8
            elif any(word in task.lower() for word in ["修改", "调整", "更新"]):
                base = 2
            elif any(word in task.lower() for word in ["新增", "开发", "实现"]):
                base = 5
            
            if method == "story_points":
                # Fibonacci 序列
                points = [1, 2, 3, 5, 8, 13][min(base // 2, 5)]
                estimates.append({"task": task, "estimate": points, "unit": "点"})
            elif method == "hours":
                hours = base * 2
                estimates.append({"task": task, "estimate": hours, "unit": "小时"})
            else:  # days
                days = max(1, base // 4)
                estimates.append({"task": task, "estimate": days, "unit": "天"})
        
        total = sum(e["estimate"] for e in estimates)
        
        return ToolResult.table(
            data=estimates,
            message=f"总估算: {total} {estimates[0]['unit'] if estimates else ''}",
        )
