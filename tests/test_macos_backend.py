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


class TestMacOSCursorAndWindow:
    @pytest.mark.asyncio
    async def test_cursor_position(self, macos_backend, monkeypatch):
        def fake_cursor():
            return (500, 300)

        monkeypatch.setattr(macos_backend, "_get_cursor_sync", fake_cursor)
        result = await macos_backend.cursor_position()
        assert result.status == ActionStatus.SUCCESS
        assert result.data["x"] == 500
        assert result.data["y"] == 300

    @pytest.mark.asyncio
    async def test_window_info(self, macos_backend, monkeypatch):
        def fake_windows():
            return [
                {
                    "title": "main.py",
                    "app_name": "VS Code",
                    "bounds": {"x": 0, "y": 0, "width": 1200, "height": 800},
                    "is_focused": True,
                },
            ]

        monkeypatch.setattr(macos_backend, "_get_windows_sync", fake_windows)
        result = await macos_backend.window_info()
        assert result.status == ActionStatus.SUCCESS
        assert len(result.data["windows"]) == 1
        assert result.data["focused_window"]["title"] == "main.py"


class TestMacOSInputActions:
    @pytest.mark.asyncio
    async def test_click(self, macos_backend, monkeypatch):
        calls = []

        async def fake_click(x, y, button):
            calls.append(("click", x, y, button))

        monkeypatch.setattr(macos_backend, "_perform_click", fake_click)
        result = await macos_backend.click(500, 300, "left")
        assert result.status == ActionStatus.SUCCESS
        assert calls == [("click", 500, 300, "left")]

    @pytest.mark.asyncio
    async def test_type_text(self, macos_backend, monkeypatch):
        calls = []

        async def fake_type(text):
            calls.append(text)

        monkeypatch.setattr(macos_backend, "_perform_type", fake_type)
        result = await macos_backend.type_text("hello")
        assert result.status == ActionStatus.SUCCESS
        assert calls == ["hello"]

    @pytest.mark.asyncio
    async def test_key_press(self, macos_backend, monkeypatch):
        calls = []

        async def fake_key(key, modifiers):
            calls.append((key, modifiers))

        monkeypatch.setattr(macos_backend, "_perform_key_press", fake_key)
        result = await macos_backend.key_press("return", modifiers=["command"])
        assert result.status == ActionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_scroll(self, macos_backend, monkeypatch):
        calls = []

        async def fake_scroll(x, y, dx, dy):
            calls.append((x, y, dx, dy))

        monkeypatch.setattr(macos_backend, "_perform_scroll", fake_scroll)
        result = await macos_backend.scroll(400, 300, dx=0, dy=-3)
        assert result.status == ActionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_move_cursor(self, macos_backend, monkeypatch):
        calls = []

        async def fake_move(x, y):
            calls.append((x, y))

        monkeypatch.setattr(macos_backend, "_perform_move", fake_move)
        result = await macos_backend.move_cursor(100, 200)
        assert result.status == ActionStatus.SUCCESS
