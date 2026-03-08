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
