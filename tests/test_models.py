"""Tests for core CUA data models."""

from __future__ import annotations

from amplifier_module_tool_cua.models import (
    ActionResult,
    ActionStatus,
    CursorPosition,
    ScreenInfo,
    WindowInfo,
)


class TestActionStatus:
    def test_status_values_exist(self):
        assert ActionStatus.SUCCESS == "success"
        assert ActionStatus.FAILURE == "failure"
        assert ActionStatus.BLOCKED == "blocked"
        assert ActionStatus.AMBIGUOUS == "ambiguous"

    def test_status_is_string(self):
        assert isinstance(ActionStatus.SUCCESS, str)
        assert isinstance(ActionStatus.FAILURE, str)


class TestActionResult:
    def test_success_result(self):
        result = ActionResult(status=ActionStatus.SUCCESS)
        assert result.status == ActionStatus.SUCCESS
        assert result.message == ""
        assert result.data == {}

    def test_failure_result_with_message(self):
        result = ActionResult(status=ActionStatus.FAILURE, message="permission denied")
        assert result.status == ActionStatus.FAILURE
        assert result.message == "permission denied"

    def test_result_with_data(self):
        result = ActionResult(
            status=ActionStatus.SUCCESS,
            data={"screenshot_base64": "abc123"},
        )
        assert result.data["screenshot_base64"] == "abc123"

    def test_blocked_result(self):
        result = ActionResult(status=ActionStatus.BLOCKED, message="accessibility not enabled")
        assert result.status == ActionStatus.BLOCKED

    def test_ambiguous_result(self):
        result = ActionResult(
            status=ActionStatus.AMBIGUOUS,
            message="click executed but state unchanged",
        )
        assert result.status == ActionStatus.AMBIGUOUS


class TestScreenInfo:
    def test_basic_screen(self):
        screen = ScreenInfo(width=1920, height=1080)
        assert screen.width == 1920
        assert screen.height == 1080
        assert screen.scale_factor == 1.0

    def test_retina_screen(self):
        screen = ScreenInfo(width=1440, height=900, scale_factor=2.0)
        assert screen.scale_factor == 2.0


class TestCursorPosition:
    def test_position(self):
        pos = CursorPosition(x=100, y=200)
        assert pos.x == 100
        assert pos.y == 200


class TestWindowInfo:
    def test_basic_window(self):
        win = WindowInfo(
            title="Untitled",
            app_name="TextEdit",
            bounds={"x": 0, "y": 0, "width": 800, "height": 600},
        )
        assert win.title == "Untitled"
        assert win.app_name == "TextEdit"
        assert win.bounds["width"] == 800
        assert win.is_focused is False

    def test_focused_window(self):
        win = WindowInfo(
            title="main.py",
            app_name="VS Code",
            bounds={"x": 100, "y": 50, "width": 1200, "height": 800},
            is_focused=True,
        )
        assert win.is_focused is True
