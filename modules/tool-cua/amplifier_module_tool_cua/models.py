"""Core data models for computer-use automation.

All backends, tools, and agents share these types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionStatus(str, Enum):
    """Normalized status for every tool call result.

    - SUCCESS: action completed, post-state confirms expected outcome
    - FAILURE: action could not be performed (clear error)
    - BLOCKED: denied due to approvals, permissions, missing capabilities, or policy
    - AMBIGUOUS: action executed but post-state did not confirm expected change
    """

    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"
    AMBIGUOUS = "ambiguous"


@dataclass
class ActionResult:
    """Normalized result returned by every backend method."""

    status: ActionStatus
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScreenInfo:
    """Display geometry."""

    width: int
    height: int
    scale_factor: float = 1.0


@dataclass
class CursorPosition:
    """Cursor coordinates in screen space."""

    x: int
    y: int


@dataclass
class WindowInfo:
    """Metadata about a single window."""

    title: str
    app_name: str
    bounds: dict[str, int]
    is_focused: bool = False
