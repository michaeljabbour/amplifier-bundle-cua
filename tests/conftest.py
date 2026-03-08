"""Shared test fixtures for amplifier-bundle-cua."""

from __future__ import annotations

from typing import Any

import pytest


class FakeCoordinator:
    """Minimal coordinator for testing module mount."""

    def __init__(self) -> None:
        self._mounted: dict[str, dict[str, Any]] = {}

    async def mount(self, mount_point: str, module: Any, name: str | None = None) -> None:
        bucket = self._mounted.setdefault(mount_point, {})
        bucket[name or type(module).__name__] = module


@pytest.fixture
def coordinator() -> FakeCoordinator:
    return FakeCoordinator()
