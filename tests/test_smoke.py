"""Smoke tests for the amplifier_module_tool_cua package structure."""

from __future__ import annotations

import amplifier_module_tool_cua as cua
import pytest
from amplifier_module_tool_cua import mount


def test_module_type() -> None:
    """The module declares itself as an Amplifier tool module."""
    assert cua.__amplifier_module_type__ == "tool"


@pytest.mark.asyncio
async def test_mount_works_after_task13(coordinator) -> None:
    """mount() completes successfully now that Task 13 has implemented it."""
    await mount(coordinator, config={"backend": "fixture"})
    assert "cua" in coordinator._mounted.get("tools", {})
