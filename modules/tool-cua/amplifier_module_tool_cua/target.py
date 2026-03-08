"""Target protocol — the contract all CUA backends must satisfy.

A Target represents what the agent is controlling (host desktop, sandbox, VM).
The transport (how control is implemented) is an internal detail of each backend.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import ActionResult


@runtime_checkable
class Target(Protocol):
    """Protocol defining the observation/action contract for all backends.

    Every method returns an ActionResult with a normalized status.
    Backends that lack a capability should return BLOCKED, not raise.
    """

    @property
    def platform(self) -> str:
        """Platform identifier (e.g. 'macos', 'windows', 'linux', 'fixture')."""
        ...

    @property
    def capabilities(self) -> dict[str, bool]:
        """Map of capability name to availability.

        Standard keys: screenshot, cursor_position, screen_info, window_info,
        semantic_tree, click, double_click, type_text, key_press, scroll, move_cursor.
        """
        ...

    # -- Observation methods --

    async def screenshot(self) -> ActionResult:
        """Capture a screenshot. Returns base64 PNG in data['screenshot_base64']."""
        ...

    async def cursor_position(self) -> ActionResult:
        """Get cursor position. Returns data['x'] and data['y']."""
        ...

    async def screen_info(self) -> ActionResult:
        """Get screen geometry. Returns data['width'], data['height'], data['scale_factor']."""
        ...

    async def window_info(self) -> ActionResult:
        """Get window list. Returns data['windows'] list and data['focused_window']."""
        ...

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        """Get accessibility/semantic tree. Returns data['elements'] list."""
        ...

    # -- Action methods --

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """Click at screen coordinates."""
        ...

    async def double_click(self, x: int, y: int) -> ActionResult:
        """Double-click at screen coordinates."""
        ...

    async def type_text(self, text: str) -> ActionResult:
        """Type a text string."""
        ...

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        """Press a key with optional modifiers."""
        ...

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        """Scroll at screen coordinates."""
        ...

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        """Move cursor to screen coordinates without clicking."""
        ...
