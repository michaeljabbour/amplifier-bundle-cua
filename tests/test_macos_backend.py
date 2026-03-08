"""Tests for the macOS backend. Uses mocks — runs on any platform."""

from __future__ import annotations

import pytest
from amplifier_module_tool_cua.models import ActionStatus
from amplifier_module_tool_cua.target import Target


@pytest.fixture
def macos_backend():
    from amplifier_module_tool_cua.backends.macos import MacOSBackend

    return MacOSBackend(_skip_availability_check=True)


class TestMacOSProtocol:
    def test_satisfies_target_protocol(self, macos_backend):
        assert isinstance(macos_backend, Target)

    def test_platform(self, macos_backend):
        assert macos_backend.platform == "macos"


class TestMacOSScreenshot:
    @pytest.mark.asyncio
    async def test_screenshot_success(self, macos_backend, monkeypatch):
        async def fake_capture():
            return "iVBORw0KGgoAAAANSUhEUg=="

        monkeypatch.setattr(macos_backend, "_capture_screenshot", fake_capture)
        result = await macos_backend.screenshot()
        assert result.status == ActionStatus.SUCCESS
        assert result.data["screenshot_base64"] == "iVBORw0KGgoAAAANSUhEUg=="

    @pytest.mark.asyncio
    async def test_screenshot_failure(self, macos_backend, monkeypatch):
        async def failing_capture():
            raise RuntimeError("screencapture failed")

        monkeypatch.setattr(macos_backend, "_capture_screenshot", failing_capture)
        result = await macos_backend.screenshot()
        assert result.status == ActionStatus.FAILURE
        assert "screencapture failed" in result.message


class TestMacOSScreenInfo:
    @pytest.mark.asyncio
    async def test_screen_info_success(self, macos_backend, monkeypatch):
        def fake_get_screen():
            return {"width": 2560, "height": 1440, "scale_factor": 2.0}

        monkeypatch.setattr(macos_backend, "_get_screen_info_sync", fake_get_screen)
        result = await macos_backend.screen_info()
        assert result.status == ActionStatus.SUCCESS
        assert result.data["width"] == 2560
        assert result.data["scale_factor"] == 2.0
