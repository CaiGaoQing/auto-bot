"""角色管理系统"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RoleConfig:
    """角色配置"""
    # 启用的技能包
    enabled_skills: list[str] = field(default_factory=list)
    
    # 禁用的技能包
    disabled_skills: list[str] = field(default_factory=list)
    
    # 默认模型
    default_model: Optional[str] = None
    
    # 系统提示词前缀
    system_prompt_prefix: str = ""
    
    # 工作目录
    working_directory: Optional[str] = None
    
    # 交付物类型
    output_types: list[str] = field(default_factory=list)
    
    # 权限
    permissions: list[str] = field(default_factory=list)
    
    # 自定义配置
    custom: dict = field(default_factory=dict)


@dataclass
class Role:
    """用户角色
    
    定义不同职业角色的 AI 助手行为和能力。
    """
    id: str
    name: str
    display_name: str
    description: str
    
    # 系统提示词
    system_prompt: str
    
    # 配置
    config: RoleConfig = field(default_factory=RoleConfig)
    
    # 图标
    icon: str = "👤"
    
    # 是否内置
    builtin: bool = False


# 内置角色定义
BUILTIN_ROLES = {
    "developer": Role(
        id="developer",
        name="developer",
        display_name="开发人员",
        description="软件开发、代码编写、调试",
        icon="👨‍💻",
        builtin=True,
        system_prompt="""你是一个专业的软件开发助手，擅长：
- 编写高质量代码
- 代码审查和调试
- 技术方案设计
- 自动化脚本开发

交付物类型：代码文件 (.py, .js, .ts, etc.)

工作原则：
1. 代码简洁、可读性强
2. 添加必要的注释
3. 考虑边界情况
4. 遵循最佳实践""",
        config=RoleConfig(
            enabled_skills=["developer", "devops", "testing", "deploy"],
            output_types=[".py", ".js", ".ts", ".go", ".java"],
            permissions=["execute_code", "file_write", "shell_access"],
        ),
    ),
    
    "finance": Role(
        id="finance",
        name="finance",
        display_name="财务人员",
        description="财务报表、数据分析、Excel 处理",
        icon="💰",
        builtin=True,
        system_prompt="""你是一个专业的财务助手，擅长：
- Excel 数据处理和分析
- 财务报表制作
- 数据汇总和统计
- 工资表整理

交付物类型：Excel 文件 (.xlsx)

工作原则：
1. 数据准确无误
2. 格式规范清晰
3. 公式正确可验证
4. 保护敏感数据""",
        config=RoleConfig(
            enabled_skills=["finance", "file_manager"],
            output_types=[".xlsx", ".csv"],
            permissions=["file_read", "file_write"],
        ),
    ),
    
    "product": Role(
        id="product",
        name="product",
        display_name="产品经理",
        description="需求分析、PRD 编写、原型设计",
        icon="📋",
        builtin=True,
        system_prompt="""你是一个专业的产品经理助手，擅长：
- 需求分析和梳理
- PRD 文档编写
- 用户故事撰写
- 竞品分析

交付物类型：Markdown 文档 (.md)

工作原则：
1. 需求描述清晰完整
2. 考虑用户场景
3. 明确验收标准
4. 遵循 SMART 原则""",
        config=RoleConfig(
            enabled_skills=["product", "web_search", "knowledge"],
            output_types=[".md"],
            permissions=["file_read", "file_write", "web_search"],
        ),
    ),
    
    "project_manager": Role(
        id="project_manager",
        name="project_manager",
        display_name="项目经理",
        description="项目管理、任务拆分、进度跟踪",
        icon="📊",
        builtin=True,
        system_prompt="""你是一个专业的项目经理助手，熟悉 PMP 规范，擅长：
- 工作分解结构 (WBS)
- 进度计划和甘特图
- 风险识别和管理
- 周报日报撰写

交付物类型：Markdown 和 Excel 文件

工作原则：
1. 任务粒度适中
2. 明确责任人和截止时间
3. 识别关键路径
4. 持续跟踪和调整""",
        config=RoleConfig(
            enabled_skills=["project", "calendar", "notes"],
            output_types=[".md", ".xlsx"],
            permissions=["file_read", "file_write"],
        ),
    ),
    
    "operator": Role(
        id="operator",
        name="operator",
        display_name="运营人员",
        description="内容运营、社媒管理、数据分析",
        icon="📢",
        builtin=True,
        system_prompt="""你是一个专业的运营助手，擅长：
- 社交媒体内容创作
- 用户评论互动
- 数据分析和报告
- 活动策划

交付物类型：内容文案、数据报告

工作原则：
1. 内容吸引人
2. 符合平台调性
3. 数据驱动决策
4. 及时响应用户""",
        config=RoleConfig(
            enabled_skills=["social", "web_search", "email"],
            output_types=[".md", ".xlsx"],
            permissions=["file_read", "file_write", "web_search"],
        ),
    ),
    
    "tester": Role(
        id="tester",
        name="tester",
        display_name="测试人员",
        description="软件测试、自动化测试、质量保证",
        icon="🔍",
        builtin=True,
        system_prompt="""你是一个专业的软件测试助手，擅长：
- 测试用例设计
- 自动化测试脚本
- Bug 分析和报告
- 性能测试

交付物类型：测试用例、测试报告

工作原则：
1. 覆盖正常和异常场景
2. 边界值测试
3. 清晰的测试报告
4. 可重现的步骤""",
        config=RoleConfig(
            enabled_skills=["testing", "developer"],
            output_types=[".md", ".py"],
            permissions=["file_read", "file_write", "execute_code"],
        ),
    ),
    
    "researcher": Role(
        id="researcher",
        name="researcher",
        display_name="研究员",
        description="行业研究、数据分析、报告撰写",
        icon="🔬",
        builtin=True,
        system_prompt="""你是一个专业的研究分析师，擅长：
- 行业研究和分析
- 数据收集和处理
- 研究报告撰写
- 趋势预测

交付物类型：研究报告

工作原则：
1. 数据来源可靠
2. 分析客观中立
3. 结论有据可依
4. 图表清晰直观""",
        config=RoleConfig(
            enabled_skills=["stock_research", "web_search", "knowledge"],
            output_types=[".md", ".xlsx"],
            permissions=["file_read", "file_write", "web_search"],
        ),
    ),
    
    "assistant": Role(
        id="assistant",
        name="assistant",
        display_name="通用助手",
        description="通用任务处理、日程管理、信息检索",
        icon="🤖",
        builtin=True,
        system_prompt="""你是一个全能的个人助手，可以帮助处理各种任务：
- 日程安排和提醒
- 信息查询和总结
- 文件整理和管理
- 邮件处理

工作原则：
1. 高效准确
2. 主动提醒
3. 保护隐私
4. 持续学习""",
        config=RoleConfig(
            enabled_skills=[
                "file_manager", "calendar", "notes", "email", 
                "web_search", "translate", "knowledge"
            ],
            output_types=[".md", ".txt"],
            permissions=["file_read", "file_write", "web_search"],
        ),
    ),
}


class RoleManager:
    """角色管理器
    
    管理用户角色定义和切换。
    """
    
    def __init__(self):
        self._roles: dict[str, Role] = {}
        self._current_role: Optional[Role] = None
        
        # 加载内置角色
        self._load_builtin_roles()
    
    def _load_builtin_roles(self) -> None:
        """加载内置角色"""
        for role_id, role in BUILTIN_ROLES.items():
            self._roles[role_id] = role
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """获取角色"""
        return self._roles.get(role_id)
    
    def list_roles(self) -> list[Role]:
        """列出所有角色"""
        return list(self._roles.values())
    
    def list_builtin_roles(self) -> list[Role]:
        """列出内置角色"""
        return [r for r in self._roles.values() if r.builtin]
    
    def list_custom_roles(self) -> list[Role]:
        """列出自定义角色"""
        return [r for r in self._roles.values() if not r.builtin]
    
    def add_role(self, role: Role) -> None:
        """添加自定义角色"""
        self._roles[role.id] = role
    
    def remove_role(self, role_id: str) -> bool:
        """移除角色"""
        role = self._roles.get(role_id)
        if role and not role.builtin:
            del self._roles[role_id]
            return True
        return False
    
    def set_current_role(self, role_id: str) -> bool:
        """设置当前角色"""
        role = self.get_role(role_id)
        if role:
            self._current_role = role
            return True
        return False
    
    def get_current_role(self) -> Optional[Role]:
        """获取当前角色"""
        return self._current_role
    
    def get_system_prompt(self, role_id: Optional[str] = None) -> str:
        """获取角色的系统提示词"""
        role = self.get_role(role_id) if role_id else self._current_role
        
        if not role:
            return ""
        
        prompt = role.system_prompt
        
        if role.config.system_prompt_prefix:
            prompt = role.config.system_prompt_prefix + "\n\n" + prompt
        
        return prompt
    
    def get_enabled_skills(self, role_id: Optional[str] = None) -> list[str]:
        """获取角色启用的技能包"""
        role = self.get_role(role_id) if role_id else self._current_role
        
        if not role:
            return []
        
        return role.config.enabled_skills
    
    def is_skill_enabled(
        self,
        skill_name: str,
        role_id: Optional[str] = None,
    ) -> bool:
        """检查技能是否对角色启用"""
        role = self.get_role(role_id) if role_id else self._current_role
        
        if not role:
            return True  # 无角色限制时允许所有技能
        
        # 显式禁用
        if skill_name in role.config.disabled_skills:
            return False
        
        # 显式启用
        if role.config.enabled_skills:
            return skill_name in role.config.enabled_skills
        
        return True
    
    def has_permission(
        self,
        permission: str,
        role_id: Optional[str] = None,
    ) -> bool:
        """检查角色是否有权限"""
        role = self.get_role(role_id) if role_id else self._current_role
        
        if not role:
            return True  # 无角色限制时允许所有权限
        
        return permission in role.config.permissions
    
    def create_custom_role(
        self,
        role_id: str,
        name: str,
        display_name: str,
        description: str,
        system_prompt: str,
        enabled_skills: Optional[list[str]] = None,
        permissions: Optional[list[str]] = None,
        icon: str = "👤",
    ) -> Role:
        """创建自定义角色"""
        role = Role(
            id=role_id,
            name=name,
            display_name=display_name,
            description=description,
            system_prompt=system_prompt,
            icon=icon,
            builtin=False,
            config=RoleConfig(
                enabled_skills=enabled_skills or [],
                permissions=permissions or [],
            ),
        )
        
        self.add_role(role)
        return role
    
    def export_role(self, role_id: str) -> Optional[dict]:
        """导出角色配置"""
        role = self.get_role(role_id)
        if not role:
            return None
        
        return {
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "system_prompt": role.system_prompt,
            "icon": role.icon,
            "config": {
                "enabled_skills": role.config.enabled_skills,
                "disabled_skills": role.config.disabled_skills,
                "default_model": role.config.default_model,
                "system_prompt_prefix": role.config.system_prompt_prefix,
                "output_types": role.config.output_types,
                "permissions": role.config.permissions,
            },
        }
    
    def import_role(self, data: dict) -> Role:
        """导入角色配置"""
        config = data.get("config", {})
        
        role = Role(
            id=data["id"],
            name=data.get("name", data["id"]),
            display_name=data.get("display_name", data["id"]),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            icon=data.get("icon", "👤"),
            builtin=False,
            config=RoleConfig(
                enabled_skills=config.get("enabled_skills", []),
                disabled_skills=config.get("disabled_skills", []),
                default_model=config.get("default_model"),
                system_prompt_prefix=config.get("system_prompt_prefix", ""),
                output_types=config.get("output_types", []),
                permissions=config.get("permissions", []),
            ),
        )
        
        self.add_role(role)
        return role


# 全局角色管理器
_role_manager: Optional[RoleManager] = None


def get_role_manager() -> RoleManager:
    """获取全局角色管理器"""
    global _role_manager
    if _role_manager is None:
        _role_manager = RoleManager()
    return _role_manager
