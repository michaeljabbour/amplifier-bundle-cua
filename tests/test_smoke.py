"""Smoke tests for the amplifier_module_tool_cua package structure."""

from __future__ import annotations

import amplifier_module_tool_cua as cua


def test_module_type() -> None:
    """The module declares itself as an Amplifier tool module."""
    assert cua.__amplifier_module_type__ == "tool"
