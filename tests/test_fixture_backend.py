"""Tests for the fixture/simulator backend."""

from __future__ import annotations

import pytest
from amplifier_module_tool_cua.models import ActionStatus
from amplifier_module_tool_cua.target import Target


@pytest.fixture
def backend():
    from amplifier_module_tool_cua.backends.fixture import FixtureBackend

    return FixtureBackend()


class TestFixtureProtocol:
    def test_satisfies_target_protocol(self, backend):
        assert isinstance(backend, Target)

    def test_platform(self, backend):
        assert backend.platform == "fixture"

    def test_all_capabilities_enabled(self, backend):
        caps = backend.capabilities
        assert caps["screenshot"] is True
        assert caps["click"] is True
        assert caps["semantic_tree"] is True


class TestFixtureObservation:
    @pytest.mark.asyncio
    async def test_screenshot(self, backend):
        result = await backend.screenshot()
        assert result.status == ActionStatus.SUCCESS
        assert "screenshot_base64" in result.data
        assert len(result.data["screenshot_base64"]) > 0

    @pytest.mark.asyncio
    async def test_cursor_position(self, backend):
        result = await backend.cursor_position()
        assert result.status == ActionStatus.SUCCESS
        assert "x" in result.data
        assert "y" in result.data

    @pytest.mark.asyncio
    async def test_screen_info(self, backend):
        result = await backend.screen_info()
        assert result.status == ActionStatus.SUCCESS
        assert result.data["width"] > 0
        assert result.data["height"] > 0
        assert "scale_factor" in result.data

    @pytest.mark.asyncio
    async def test_window_info(self, backend):
        result = await backend.window_info()
        assert result.status == ActionStatus.SUCCESS
        assert "windows" in result.data
        assert "focused_window" in result.data

    @pytest.mark.asyncio
    async def test_semantic_tree(self, backend):
        result = await backend.semantic_tree()
        assert result.status == ActionStatus.SUCCESS
        assert "elements" in result.data
        assert len(result.data["elements"]) > 0


class TestFixtureActions:
    @pytest.mark.asyncio
    async def test_click(self, backend):
        result = await backend.click(500, 300)
        assert result.status == ActionStatus.SUCCESS
        assert backend.action_log[-1]["action"] == "click"
        assert backend.action_log[-1]["x"] == 500

    @pytest.mark.asyncio
    async def test_click_updates_cursor(self, backend):
        await backend.click(500, 300)
        pos = await backend.cursor_position()
        assert pos.data["x"] == 500
        assert pos.data["y"] == 300

    @pytest.mark.asyncio
    async def test_double_click(self, backend):
        result = await backend.double_click(200, 400)
        assert result.status == ActionStatus.SUCCESS
        assert backend.action_log[-1]["action"] == "double_click"

    @pytest.mark.asyncio
    async def test_type_text(self, backend):
        result = await backend.type_text("hello world")
        assert result.status == ActionStatus.SUCCESS
        assert backend.action_log[-1]["text"] == "hello world"

    @pytest.mark.asyncio
    async def test_key_press(self, backend):
        result = await backend.key_press("return", modifiers=["command"])
        assert result.status == ActionStatus.SUCCESS
        assert backend.action_log[-1]["key"] == "return"
        assert backend.action_log[-1]["modifiers"] == ["command"]

    @pytest.mark.asyncio
    async def test_scroll(self, backend):
        result = await backend.scroll(400, 300, dx=0, dy=-3)
        assert result.status == ActionStatus.SUCCESS
        assert backend.action_log[-1]["dy"] == -3

    @pytest.mark.asyncio
    async def test_move_cursor(self, backend):
        result = await backend.move_cursor(100, 200)
        assert result.status == ActionStatus.SUCCESS
        pos = await backend.cursor_position()
        assert pos.data["x"] == 100
        assert pos.data["y"] == 200

    @pytest.mark.asyncio
    async def test_action_log_accumulates(self, backend):
        await backend.click(10, 20)
        await backend.type_text("a")
        await backend.scroll(0, 0, dy=1)
        assert len(backend.action_log) == 3


class TestGoldenObservations:
    """Verify fixture backend returns consistent, known observation shapes."""

    @pytest.mark.asyncio
    async def test_screenshot_is_valid_base64_png(self, backend):
        import base64

        result = await backend.screenshot()
        raw = base64.b64decode(result.data["screenshot_base64"])
        # PNG magic bytes
        assert raw[:4] == b"\x89PNG"

    @pytest.mark.asyncio
    async def test_semantic_tree_structure(self, backend):
        result = await backend.semantic_tree()
        tree = result.data["elements"]
        # Root is an application
        assert tree[0]["role"] == "AXApplication"
        assert tree[0]["label"] == "FixtureApp"
        # Has a window child
        window = tree[0]["children"][0]
        assert window["role"] == "AXWindow"
        # Window has a button and a text field
        roles = {child["role"] for child in window["children"]}
        assert "AXButton" in roles
        assert "AXTextField" in roles

    @pytest.mark.asyncio
    async def test_semantic_tree_has_bounds(self, backend):
        result = await backend.semantic_tree()
        button = result.data["elements"][0]["children"][0]["children"][0]
        assert button["role"] == "AXButton"
        assert button["bounds"]["width"] == 100
        assert button["bounds"]["height"] == 30

    @pytest.mark.asyncio
    async def test_window_info_matches_semantic_tree(self, backend):
        """Fixture's visual and semantic worlds should be consistent."""
        win_result = await backend.window_info()
        sem_result = await backend.semantic_tree()
        focused = win_result.data["focused_window"]
        sem_window = sem_result.data["elements"][0]["children"][0]
        assert focused["title"] == sem_window["label"]

    @pytest.mark.asyncio
    async def test_default_screen_geometry(self, backend):
        result = await backend.screen_info()
        assert result.data == {"width": 1920, "height": 1080, "scale_factor": 1.0}

    @pytest.mark.asyncio
    async def test_default_cursor_is_center(self, backend):
        result = await backend.cursor_position()
        assert result.data == {"x": 960, "y": 540}
