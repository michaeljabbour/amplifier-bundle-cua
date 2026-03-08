"""Tests for the CuaTool Amplifier tool surface."""

from __future__ import annotations

import pytest
from amplifier_module_tool_cua import mount
from amplifier_module_tool_cua.backends.fixture import FixtureBackend
from amplifier_module_tool_cua.tool import CuaTool


@pytest.fixture
def tool():
    return CuaTool(backend=FixtureBackend())


class TestToolProperties:
    def test_name(self, tool):
        assert tool.name == "cua"

    def test_description_not_empty(self, tool):
        assert len(tool.description) > 20

    def test_input_schema_has_action(self, tool):
        schema = tool.input_schema
        assert "action" in schema["properties"]
        assert "enum" in schema["properties"]["action"]


class TestToolObserveActions:
    @pytest.mark.asyncio
    async def test_screenshot(self, tool):
        result = await tool.execute(arguments={"action": "screenshot"})
        assert result["status"] == "success"
        assert "screenshot_base64" in result["data"]

    @pytest.mark.asyncio
    async def test_cursor_position(self, tool):
        result = await tool.execute(arguments={"action": "cursor_position"})
        assert result["status"] == "success"
        assert "x" in result["data"]
        assert "y" in result["data"]

    @pytest.mark.asyncio
    async def test_screen_info(self, tool):
        result = await tool.execute(arguments={"action": "screen_info"})
        assert result["status"] == "success"
        assert result["data"]["width"] == 1920

    @pytest.mark.asyncio
    async def test_window_info(self, tool):
        result = await tool.execute(arguments={"action": "window_info"})
        assert result["status"] == "success"
        assert "windows" in result["data"]

    @pytest.mark.asyncio
    async def test_semantic_tree(self, tool):
        result = await tool.execute(arguments={"action": "semantic_tree"})
        assert result["status"] == "success"
        assert "elements" in result["data"]

    @pytest.mark.asyncio
    async def test_observe_composite(self, tool):
        """observe returns screenshot + cursor + windows + semantic tree together."""
        result = await tool.execute(arguments={"action": "observe"})
        assert result["status"] == "success"
        data = result["data"]
        assert "screenshot_base64" in data
        assert "cursor" in data
        assert "windows" in data
        assert "semantic_tree" in data

    @pytest.mark.asyncio
    async def test_unknown_action_returns_failure(self, tool):
        result = await tool.execute(arguments={"action": "fly_to_moon"})
        assert result["status"] == "failure"
        assert "unknown" in result["message"].lower()


class TestToolInputActions:
    @pytest.mark.asyncio
    async def test_click(self, tool):
        result = await tool.execute(arguments={"action": "click", "x": 500, "y": 300})
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_click_with_button(self, tool):
        result = await tool.execute(
            arguments={"action": "click", "x": 100, "y": 200, "button": "right"}
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_double_click(self, tool):
        result = await tool.execute(arguments={"action": "double_click", "x": 300, "y": 400})
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_type_text(self, tool):
        result = await tool.execute(arguments={"action": "type_text", "text": "hello"})
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_key_press(self, tool):
        result = await tool.execute(
            arguments={"action": "key_press", "key": "return", "modifiers": ["command"]}
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_scroll(self, tool):
        result = await tool.execute(
            arguments={"action": "scroll", "x": 400, "y": 300, "dx": 0, "dy": -3}
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_move_cursor(self, tool):
        result = await tool.execute(arguments={"action": "move_cursor", "x": 100, "y": 200})
        assert result["status"] == "success"


class TestMount:
    @pytest.mark.asyncio
    async def test_mount_registers_tool(self, coordinator):
        await mount(coordinator, config={"backend": "fixture"})
        assert "cua" in coordinator._mounted.get("tools", {})

    @pytest.mark.asyncio
    async def test_mounted_tool_is_cua_tool(self, coordinator):
        await mount(coordinator, config={"backend": "fixture"})
        tool = coordinator._mounted["tools"]["cua"]
        assert tool.name == "cua"

    @pytest.mark.asyncio
    async def test_mount_fixture_backend_works(self, coordinator):
        await mount(coordinator, config={"backend": "fixture"})
        tool = coordinator._mounted["tools"]["cua"]
        result = await tool.execute(arguments={"action": "screenshot"})
        assert result["status"] == "success"


class TestExecuteCallConvention:
    """Regression tests for the execute() call convention.

    The real Amplifier runtime dispatches tool.execute(input_dict) positionally,
    NOT as a keyword argument.  The original signature used a keyword-only '*'
    separator which caused every live tool action to fail with:

        CuaTool.execute() takes 1 positional argument but 2 were given

    These tests explicitly cover BOTH call styles so any future signature
    change that breaks the positional form is caught immediately.
    """

    @pytest.mark.asyncio
    async def test_execute_positional_runtime_form(self, tool):
        """Runtime dispatches positionally: tool.execute(input_dict)."""
        result = await tool.execute({"action": "screenshot"})
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_keyword_form(self, tool):
        """Keyword form must also keep working for direct callers."""
        result = await tool.execute(arguments={"action": "screenshot"})
        assert result["status"] == "success"
