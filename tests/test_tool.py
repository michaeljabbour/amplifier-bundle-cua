"""Tests for the CuaTool Amplifier tool surface."""

from __future__ import annotations

import pytest
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
