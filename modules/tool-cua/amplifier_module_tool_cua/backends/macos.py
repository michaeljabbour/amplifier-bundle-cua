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

    # -- Cursor position --

    async def cursor_position(self) -> ActionResult:
        try:
            x, y = self._get_cursor_sync()
            return ActionResult(status=ActionStatus.SUCCESS, data={"x": x, "y": y})
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    def _get_cursor_sync(self) -> tuple[int, int]:
        """Get cursor position via Quartz."""
        import Quartz  # type: ignore[reportMissingImports]

        event = Quartz.CGEventCreate(None)
        point = Quartz.CGEventGetLocation(event)
        return int(point.x), int(point.y)

    # -- Window info --

    async def window_info(self) -> ActionResult:
        try:
            windows = self._get_windows_sync()
            focused = next((w for w in windows if w.get("is_focused")), None)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                data={"windows": windows, "focused_window": focused},
            )
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    def _get_windows_sync(self) -> list[dict[str, Any]]:
        """Get on-screen window list via Quartz."""
        import Quartz  # type: ignore[reportMissingImports]

        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID,
        )
        results = []
        for w in window_list or []:
            bounds_dict = w.get(Quartz.kCGWindowBounds, {})
            results.append(
                {
                    "title": str(w.get(Quartz.kCGWindowName, "") or ""),
                    "app_name": str(w.get(Quartz.kCGWindowOwnerName, "") or ""),
                    "bounds": {
                        "x": int(bounds_dict.get("X", 0)),
                        "y": int(bounds_dict.get("Y", 0)),
                        "width": int(bounds_dict.get("Width", 0)),
                        "height": int(bounds_dict.get("Height", 0)),
                    },
                    "is_focused": int(w.get(Quartz.kCGWindowLayer, 999)) == 0,
                }
            )
        return results

    # -- Click --

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        try:
            await self._perform_click(x, y, button)
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    async def _perform_click(self, x: int, y: int, button: str) -> None:
        """Perform a mouse click via Quartz CGEvent."""
        import Quartz  # type: ignore[reportMissingImports]

        point = Quartz.CGPoint(x, y)
        btn_map = {
            "left": (
                Quartz.kCGEventLeftMouseDown,
                Quartz.kCGEventLeftMouseUp,
                Quartz.kCGMouseButtonLeft,
            ),
            "right": (
                Quartz.kCGEventRightMouseDown,
                Quartz.kCGEventRightMouseUp,
                Quartz.kCGMouseButtonRight,
            ),
        }
        down_type, up_type, btn = btn_map.get(button, btn_map["left"])
        ev_down = Quartz.CGEventCreateMouseEvent(None, down_type, point, btn)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_down)
        ev_up = Quartz.CGEventCreateMouseEvent(None, up_type, point, btn)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_up)

    # -- Double click --

    async def double_click(self, x: int, y: int) -> ActionResult:
        try:
            await self._perform_click(x, y, "left")
            await self._perform_click(x, y, "left")
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    # -- Type text --

    async def type_text(self, text: str) -> ActionResult:
        try:
            await self._perform_type(text)
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    async def _perform_type(self, text: str) -> None:
        """Type characters via Quartz keyboard events."""
        import Quartz  # type: ignore[reportMissingImports]

        for char in text:
            ev_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
            Quartz.CGEventKeyboardSetUnicodeString(ev_down, len(char), char)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_down)
            ev_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
            Quartz.CGEventKeyboardSetUnicodeString(ev_up, len(char), char)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_up)

    # -- Key press --

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        try:
            await self._perform_key_press(key, modifiers)
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    _KEY_CODES: dict[str, int] = {
        "return": 36,
        "tab": 48,
        "space": 49,
        "delete": 51,
        "escape": 53,
        "up": 126,
        "down": 125,
        "left": 123,
        "right": 124,
        "f1": 122,
        "f2": 120,
        "f3": 99,
        "f4": 118,
        "f5": 96,
        "f6": 97,
    }

    async def _perform_key_press(self, key: str, modifiers: list[str] | None) -> None:
        """Press a key with optional modifiers via Quartz."""
        import Quartz  # type: ignore[reportMissingImports]

        key_code = self._KEY_CODES.get(key.lower(), 0)
        flags = 0
        for mod in modifiers or []:
            if mod == "command":
                flags |= Quartz.kCGEventFlagMaskCommand
            elif mod == "shift":
                flags |= Quartz.kCGEventFlagMaskShift
            elif mod == "option":
                flags |= Quartz.kCGEventFlagMaskAlternate
            elif mod == "control":
                flags |= Quartz.kCGEventFlagMaskControl

        ev_down = Quartz.CGEventCreateKeyboardEvent(None, key_code, True)
        if flags:
            Quartz.CGEventSetFlags(ev_down, flags)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_down)

        ev_up = Quartz.CGEventCreateKeyboardEvent(None, key_code, False)
        if flags:
            Quartz.CGEventSetFlags(ev_up, flags)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_up)

    # -- Scroll --

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        try:
            await self._perform_scroll(x, y, dx, dy)
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    async def _perform_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Scroll at position via Quartz."""
        import Quartz  # type: ignore[reportMissingImports]

        # Move cursor to position first
        move_ev = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventMouseMoved, Quartz.CGPoint(x, y), 0
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move_ev)
        # Scroll
        scroll_ev = Quartz.CGEventCreateScrollWheelEvent(
            None, Quartz.kCGScrollEventUnitLine, 2, dy, dx
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, scroll_ev)

    # -- Move cursor --

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        try:
            await self._perform_move(x, y)
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    async def _perform_move(self, x: int, y: int) -> None:
        """Move cursor without clicking via Quartz."""
        import Quartz  # type: ignore[reportMissingImports]

        event = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventMouseMoved, Quartz.CGPoint(x, y), 0
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

    # -- Semantic tree (stub — implemented in Task 16) --

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        raise NotImplementedError
