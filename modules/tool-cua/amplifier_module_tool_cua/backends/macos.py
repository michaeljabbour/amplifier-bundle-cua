"""macOS host-desktop backend using Quartz and ApplicationServices.

Screenshots use the screencapture CLI (always available on macOS).
Input events use Quartz CGEvent APIs.
Accessibility uses ApplicationServices AXUIElement APIs.

All pyobjc imports are deferred so the module can be loaded on any platform
for testing. Pass _skip_availability_check=True to bypass platform detection.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import tempfile
from typing import Any

from ..models import ActionResult, ActionStatus

logger = logging.getLogger(__name__)


class MacOSBackend:
    """Real macOS backend. Requires macOS + appropriate permissions."""

    def __init__(self, *, _skip_availability_check: bool = False) -> None:
        self._available = True
        if not _skip_availability_check:
            self._check_availability()

    def _check_availability(self) -> None:
        import sys

        if sys.platform != "darwin":
            self._available = False
            return
        try:
            import Quartz  # noqa: F401  # type: ignore[reportMissingImports]
        except ImportError:
            self._available = False

    @property
    def platform(self) -> str:
        return "macos"

    @property
    def capabilities(self) -> dict[str, bool]:
        return {
            "screenshot": self._available,
            "cursor_position": self._available,
            "screen_info": self._available,
            "window_info": self._available,
            "semantic_tree": self._available,
            "click": self._available,
            "double_click": self._available,
            "type_text": self._available,
            "key_press": self._available,
            "scroll": self._available,
            "move_cursor": self._available,
        }

    def _blocked(self, msg: str = "macOS backend not available") -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=msg)

    # -- Screenshot --

    async def screenshot(self) -> ActionResult:
        try:
            data = await self._capture_screenshot()
            return ActionResult(status=ActionStatus.SUCCESS, data={"screenshot_base64": data})
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    async def _capture_screenshot(self) -> str:
        """Capture screenshot via screencapture CLI. Returns base64 PNG."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name
        try:
            proc = await asyncio.create_subprocess_exec(
                "screencapture",
                "-x",
                "-t",
                "png",
                tmp_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"screencapture exited with code {proc.returncode}")
            with open(tmp_path, "rb") as img:
                return base64.b64encode(img.read()).decode("ascii")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # -- Screen info --

    async def screen_info(self) -> ActionResult:
        try:
            data = self._get_screen_info_sync()
            return ActionResult(status=ActionStatus.SUCCESS, data=data)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    def _get_screen_info_sync(self) -> dict[str, Any]:
        """Get main display geometry via Quartz."""
        import Quartz  # type: ignore[reportMissingImports]

        display = Quartz.CGMainDisplayID()
        width = Quartz.CGDisplayPixelsWide(display)
        height = Quartz.CGDisplayPixelsHigh(display)
        mode = Quartz.CGDisplayCopyDisplayMode(display)
        if mode:
            pixel_w = Quartz.CGDisplayModeGetPixelWidth(mode)
            scale = pixel_w / width if width else 1.0
        else:
            scale = 1.0
        return {"width": int(width), "height": int(height), "scale_factor": float(scale)}

    # -- Stubs for remaining methods (implemented in Task 15 and 16) --

    async def cursor_position(self) -> ActionResult:
        raise NotImplementedError

    async def window_info(self) -> ActionResult:
        raise NotImplementedError

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        raise NotImplementedError

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
