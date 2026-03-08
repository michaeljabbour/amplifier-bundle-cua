"""CuaTool — the Amplifier-visible tool surface for computer-use automation.

Dispatches actions to the active backend. Provides mechanisms, not policy.
"""

from __future__ import annotations

import logging
from typing import Any

from .target import Target

logger = logging.getLogger(__name__)

_ACTIONS = [
    "screenshot",
    "cursor_position",
    "screen_info",
    "window_info",
    "semantic_tree",
    "observe",
    "click",
    "double_click",
    "type_text",
    "key_press",
    "scroll",
    "move_cursor",
]


class CuaTool:
    """LLM-callable tool for computer-use automation."""

    def __init__(self, backend: Target) -> None:
        self._backend = backend

    @property
    def name(self) -> str:
        return "cua"

    @property
    def description(self) -> str:
        return (
            "Computer-use automation: observe screens, interact with desktop elements, "
            "and inspect UI semantics. Use 'observe' for a full dual-world snapshot. "
            "Use specific actions (screenshot, click, type_text, etc.) for precise control."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": _ACTIONS,
                    "description": "The action to perform.",
                },
                "x": {"type": "integer", "description": "X coordinate (for click/scroll/move)."},
                "y": {"type": "integer", "description": "Y coordinate (for click/scroll/move)."},
                "button": {
                    "type": "string",
                    "enum": ["left", "right", "middle"],
                    "description": "Mouse button (for click). Default: left.",
                },
                "text": {"type": "string", "description": "Text to type (for type_text)."},
                "key": {"type": "string", "description": "Key name (for key_press)."},
                "modifiers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Modifier keys (for key_press). e.g. ['command', 'shift'].",
                },
                "dx": {"type": "integer", "description": "Horizontal scroll delta."},
                "dy": {"type": "integer", "description": "Vertical scroll delta."},
                "window_title": {
                    "type": "string",
                    "description": "Window title filter (for semantic_tree).",
                },
            },
            "required": ["action"],
        }

    async def execute(self, *, arguments: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Dispatch to the appropriate action handler."""
        action = arguments.get("action", "")

        try:
            if action == "screenshot":
                return self._to_dict(await self._backend.screenshot())
            elif action == "cursor_position":
                return self._to_dict(await self._backend.cursor_position())
            elif action == "screen_info":
                return self._to_dict(await self._backend.screen_info())
            elif action == "window_info":
                return self._to_dict(await self._backend.window_info())
            elif action == "semantic_tree":
                wt = arguments.get("window_title")
                return self._to_dict(await self._backend.semantic_tree(window_title=wt))
            elif action == "observe":
                return await self._handle_observe()
            elif action == "click":
                return self._to_dict(
                    await self._backend.click(
                        x=arguments.get("x", 0),
                        y=arguments.get("y", 0),
                        button=arguments.get("button", "left"),
                    )
                )
            elif action == "double_click":
                return self._to_dict(
                    await self._backend.double_click(
                        x=arguments.get("x", 0),
                        y=arguments.get("y", 0),
                    )
                )
            elif action == "type_text":
                return self._to_dict(await self._backend.type_text(text=arguments.get("text", "")))
            elif action == "key_press":
                return self._to_dict(
                    await self._backend.key_press(
                        key=arguments.get("key", ""),
                        modifiers=arguments.get("modifiers"),
                    )
                )
            elif action == "scroll":
                return self._to_dict(
                    await self._backend.scroll(
                        x=arguments.get("x", 0),
                        y=arguments.get("y", 0),
                        dx=arguments.get("dx", 0),
                        dy=arguments.get("dy", 0),
                    )
                )
            elif action == "move_cursor":
                return self._to_dict(
                    await self._backend.move_cursor(
                        x=arguments.get("x", 0),
                        y=arguments.get("y", 0),
                    )
                )
            else:
                return {"status": "failure", "message": f"Unknown action: {action}", "data": {}}
        except Exception as exc:
            logger.exception("CuaTool action '%s' raised", action)
            return {"status": "failure", "message": str(exc), "data": {}}

    async def _handle_observe(self) -> dict[str, Any]:
        """Composite observe: screenshot + cursor + windows + semantic tree."""
        data: dict[str, Any] = {}

        screenshot = await self._backend.screenshot()
        if screenshot.status.value == "success":
            data["screenshot_base64"] = screenshot.data.get("screenshot_base64")

        cursor = await self._backend.cursor_position()
        if cursor.status.value == "success":
            data["cursor"] = cursor.data

        windows = await self._backend.window_info()
        if windows.status.value == "success":
            data["windows"] = windows.data.get("windows", [])
            data["focused_window"] = windows.data.get("focused_window")

        semantic = await self._backend.semantic_tree()
        if semantic.status.value == "success":
            data["semantic_tree"] = semantic.data.get("elements", [])

        return {"status": "success", "data": data, "message": ""}

    @staticmethod
    def _to_dict(result: Any) -> dict[str, Any]:
        return {
            "status": result.status.value,
            "data": result.data,
            "message": result.message,
        }
