"""Fixture/simulator backend for deterministic testing.

Returns canned observations and records actions without touching a real desktop.
All capabilities are always available.
"""

from __future__ import annotations

from ..models import ActionResult, ActionStatus

# Minimal 1x1 transparent PNG, base64-encoded
_TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "2mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

# Default fixture semantic tree
_DEFAULT_SEMANTIC_TREE = [
    {
        "role": "AXApplication",
        "label": "FixtureApp",
        "value": None,
        "bounds": {"x": 0, "y": 0, "width": 1920, "height": 1080},
        "children": [
            {
                "role": "AXWindow",
                "label": "Fixture Window",
                "value": None,
                "bounds": {"x": 100, "y": 100, "width": 800, "height": 600},
                "children": [
                    {
                        "role": "AXButton",
                        "label": "OK",
                        "value": None,
                        "bounds": {"x": 350, "y": 500, "width": 100, "height": 30},
                        "children": [],
                    },
                    {
                        "role": "AXTextField",
                        "label": "Search",
                        "value": "",
                        "bounds": {"x": 200, "y": 200, "width": 400, "height": 30},
                        "children": [],
                    },
                ],
            },
        ],
    },
]


class FixtureBackend:
    """Deterministic backend for testing. No real desktop interaction."""

    def __init__(self) -> None:
        self._cursor_x: int = 960
        self._cursor_y: int = 540
        self._action_log: list[dict] = []

    @property
    def platform(self) -> str:
        return "fixture"

    @property
    def capabilities(self) -> dict[str, bool]:
        return {
            "screenshot": True,
            "cursor_position": True,
            "screen_info": True,
            "window_info": True,
            "semantic_tree": True,
            "click": True,
            "double_click": True,
            "type_text": True,
            "key_press": True,
            "scroll": True,
            "move_cursor": True,
        }

    @property
    def action_log(self) -> list[dict]:
        """Recorded actions — useful for test assertions."""
        return list(self._action_log)

    # -- Observation methods --

    async def screenshot(self) -> ActionResult:
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={"screenshot_base64": _TINY_PNG_B64},
        )

    async def cursor_position(self) -> ActionResult:
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={"x": self._cursor_x, "y": self._cursor_y},
        )

    async def screen_info(self) -> ActionResult:
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={"width": 1920, "height": 1080, "scale_factor": 1.0},
        )

    async def window_info(self) -> ActionResult:
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={
                "windows": [
                    {
                        "title": "Fixture Window",
                        "app_name": "FixtureApp",
                        "bounds": {"x": 100, "y": 100, "width": 800, "height": 600},
                        "is_focused": True,
                    },
                ],
                "focused_window": {
                    "title": "Fixture Window",
                    "app_name": "FixtureApp",
                    "bounds": {"x": 100, "y": 100, "width": 800, "height": 600},
                    "is_focused": True,
                },
            },
        )

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={"elements": _DEFAULT_SEMANTIC_TREE},
        )

    # -- Action methods (implemented in Task 9) --

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        raise NotImplementedError

    async def double_click(self, x: int, y: int) -> ActionResult:
        raise NotImplementedError

    async def type_text(self, text: str) -> ActionResult:
        raise NotImplementedError

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        raise NotImplementedError

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        raise NotImplementedError

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        raise NotImplementedError
