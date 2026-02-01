"""技能引擎测试"""

import pytest

from auto.core.skill.engine import SkillEngine
from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class MockSkill(Skill):
    """测试用技能"""
    
    @property
    def name(self) -> str:
        return "mock_skill"
    
    @property
    def description(self) -> str:
        return "测试技能"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="mock_tool",
                description="测试工具",
                parameters={
                    "type": "object",
                    "properties": {
                        "input": {"type": "string"},
                    },
                },
                handler=self.mock_tool_handler,
            ),
        ]
    
    async def mock_tool_handler(self, ctx: ToolContext, input: str = "") -> ToolResult:
        return ToolResult.success_result(
            data={"result": f"echo: {input}"},
            message="执行成功",
        )


class TestSkillEngine:
    """测试技能引擎"""
    
    def test_register_skill(self):
        """测试注册技能"""
        engine = SkillEngine()
        skill = MockSkill()
        
        engine.register_skill(skill)
        
        assert "mock_skill" in [s["name"] for s in engine.list_skills()]
    
    def test_get_skill(self):
        """测试获取技能"""
        engine = SkillEngine()
        skill = MockSkill()
        engine.register_skill(skill)
        
        retrieved = engine.get_skill("mock_skill")
        
        assert retrieved is not None
        assert retrieved.name == "mock_skill"
    
    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """测试执行工具"""
        engine = SkillEngine()
        skill = MockSkill()
        engine.register_skill(skill)
        
        ctx = ToolContext()
        result = await engine.execute_tool(
            "mock_skill.mock_tool",
            {"input": "hello"},
            ctx,
        )
        
        assert result.success
        assert result.data["result"] == "echo: hello"
    
    def test_get_tools_for_skill(self):
        """测试获取技能工具"""
        engine = SkillEngine()
        skill = MockSkill()
        engine.register_skill(skill)
        
        tools = engine.get_tools_for_skill("mock_skill")
        
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "mock_skill.mock_tool"
