"""Tests for the Target protocol contract."""

from __future__ import annotations

import pytest
from amplifier_module_tool_cua.models import ActionResult, ActionStatus
from amplifier_module_tool_cua.target import Target


class MinimalTarget:
    """A bare-minimum Target implementation for protocol verification."""

    @property
    def platform(self) -> str:
        return "test"

    @property
    def capabilities(self) -> dict[str, bool]:
        return {"screenshot": True, "click": True, "type_text": True, "semantic_tree": False}

    async def screenshot(self) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS, data={"screenshot_base64": ""})

    async def cursor_position(self) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS, data={"x": 0, "y": 0})

    async def screen_info(self) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS, data={"width": 100, "height": 100})

    async def window_info(self) -> ActionResult:
        return ActionResult(
            status=ActionStatus.SUCCESS, data={"windows": [], "focused_window": None}
        )

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message="not supported")

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)

    async def double_click(self, x: int, y: int) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)

    async def type_text(self, text: str) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)


class TestTargetProtocol:
    def test_minimal_target_satisfies_protocol(self):
        target = MinimalTarget()
        assert isinstance(target, Target)

    def test_platform_property(self):
        target = MinimalTarget()
        assert target.platform == "test"

    def test_capabilities_property(self):
        target = MinimalTarget()
        caps = target.capabilities
        assert caps["screenshot"] is True
        assert caps["semantic_tree"] is False

    @pytest.mark.asyncio
    async def test_screenshot_returns_action_result(self):
        target = MinimalTarget()
        result = await target.screenshot()
        assert isinstance(result, ActionResult)
        assert result.status == ActionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_blocked_capability_returns_blocked(self):
        target = MinimalTarget()
        result = await target.semantic_tree()
        assert result.status == ActionStatus.BLOCKED
