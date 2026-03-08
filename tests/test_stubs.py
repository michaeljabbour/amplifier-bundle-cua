"""Tests for Windows and Linux stub backends."""

from __future__ import annotations

import pytest
from amplifier_module_tool_cua.models import ActionStatus
from amplifier_module_tool_cua.target import Target


class TestWindowsStub:
    @pytest.fixture
    def backend(self):
        from amplifier_module_tool_cua.backends.windows import WindowsStubBackend

        return WindowsStubBackend()

    def test_satisfies_protocol(self, backend):
        assert isinstance(backend, Target)

    def test_platform(self, backend):
        assert backend.platform == "windows"

    def test_all_capabilities_blocked(self, backend):
        for cap, available in backend.capabilities.items():
            assert available is False, f"{cap} should be False in stub"

    @pytest.mark.asyncio
    async def test_screenshot_blocked(self, backend):
        result = await backend.screenshot()
        assert result.status == ActionStatus.BLOCKED
        assert "not implemented" in result.message.lower()

    @pytest.mark.asyncio
    async def test_click_blocked(self, backend):
        result = await backend.click(0, 0)
        assert result.status == ActionStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_semantic_tree_blocked(self, backend):
        result = await backend.semantic_tree()
        assert result.status == ActionStatus.BLOCKED


class TestLinuxStub:
    @pytest.fixture
    def backend(self):
        from amplifier_module_tool_cua.backends.linux import LinuxStubBackend

        return LinuxStubBackend()

    def test_satisfies_protocol(self, backend):
        assert isinstance(backend, Target)

    def test_platform(self, backend):
        assert backend.platform == "linux"

    def test_all_capabilities_blocked(self, backend):
        for cap, available in backend.capabilities.items():
            assert available is False

    @pytest.mark.asyncio
    async def test_screenshot_blocked(self, backend):
        result = await backend.screenshot()
        assert result.status == ActionStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_type_text_blocked(self, backend):
        result = await backend.type_text("test")
        assert result.status == ActionStatus.BLOCKED
