"""Smoke tests for the amplifier_module_tool_cua package structure."""

from __future__ import annotations

import amplifier_module_tool_cua as cua
import pytest
from amplifier_module_tool_cua import mount


def test_module_type() -> None:
    """The module declares itself as an Amplifier tool module."""
    assert cua.__amplifier_module_type__ == "tool"


@pytest.mark.asyncio
async def test_mount_raises_not_implemented() -> None:
    """mount() raises NotImplementedError until Task 13 implements it."""
    with pytest.raises(NotImplementedError):
        await mount(coordinator=None)
