"""Linux stub backend — all capabilities return BLOCKED.

This preserves the host-agnostic architecture. A real Linux backend
will replace these stubs in a future version.
"""

from __future__ import annotations

from ..models import ActionResult, ActionStatus

_MSG = "Linux backend not implemented yet"


class LinuxStubBackend:
    """Stub that satisfies the Target protocol but blocks all operations."""

    @property
    def platform(self) -> str:
        return "linux"

    @property
    def capabilities(self) -> dict[str, bool]:
        return {
            k: False
            for k in [
                "screenshot",
                "cursor_position",
                "screen_info",
                "window_info",
                "semantic_tree",
                "click",
                "double_click",
                "type_text",
                "key_press",
                "scroll",
                "move_cursor",
            ]
        }

    async def screenshot(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def cursor_position(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def screen_info(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def window_info(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def double_click(self, x: int, y: int) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def type_text(self, text: str) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)
