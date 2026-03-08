"""Tests for core CUA data models."""

from __future__ import annotations

from amplifier_module_tool_cua.models import (
    ActionResult,
    ActionStatus,
    CursorPosition,
    Observation,
    ScreenInfo,
    SemanticElement,
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


class TestSemanticElement:
    def test_basic_element(self):
        el = SemanticElement(role="AXButton", label="Submit")
        assert el.role == "AXButton"
        assert el.label == "Submit"
        assert el.value is None
        assert el.children == []

    def test_element_with_children(self):
        child = SemanticElement(role="AXStaticText", label="OK")
        parent = SemanticElement(role="AXButton", label="Submit", children=[child])
        assert len(parent.children) == 1
        assert parent.children[0].role == "AXStaticText"

    def test_element_with_bounds(self):
        el = SemanticElement(
            role="AXTextField",
            label="Search",
            bounds={"x": 10, "y": 20, "width": 200, "height": 30},
        )
        assert el.bounds["width"] == 200


class TestObservation:
    def test_empty_observation(self):
        obs = Observation()
        assert obs.screenshot_base64 is None
        assert obs.screen_info is None
        assert obs.cursor_position is None
        assert obs.focused_window is None
        assert obs.windows == []
        assert obs.semantic_tree == []

    def test_full_observation(self):
        obs = Observation(
            screenshot_base64="iVBORw...",
            screen_info=ScreenInfo(width=1920, height=1080),
            cursor_position=CursorPosition(x=500, y=300),
            focused_window=WindowInfo(
                title="test",
                app_name="App",
                bounds={"x": 0, "y": 0, "width": 800, "height": 600},
                is_focused=True,
            ),
            windows=[],
            semantic_tree=[SemanticElement(role="AXWindow", label="test")],
        )
        assert obs.screenshot_base64 == "iVBORw..."
        assert obs.screen_info.width == 1920
        assert obs.cursor_position.x == 500
        assert obs.focused_window.is_focused is True
        assert len(obs.semantic_tree) == 1
