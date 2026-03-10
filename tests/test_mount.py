"""Regression tests for the mount() entrypoint fail-fast behaviour.

Verifies that mount() raises RuntimeError on darwin when the pyobjc/macOS
backend is unavailable, rather than silently falling back to fixture data.
This is the complement to test_registry.py, which tests detect_backend()
directly — here we test the full public entrypoint path.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import amplifier_module_tool_cua as cua
import pytest


class TestMountFailFastDarwin:
    """mount() must propagate RuntimeError on darwin when backend cannot initialise."""

    async def test_mount_raises_when_macos_module_missing(self, coordinator) -> None:
        """Regression: mount() raises when the macos backend module is unimportable.

        Simulates pyobjc not installed so the import inside detect_backend() fails.
        """
        with patch("amplifier_module_tool_cua.backends.registry.sys") as mock_sys:
            mock_sys.platform = "darwin"
            with patch.dict(sys.modules, {"amplifier_module_tool_cua.backends.macos": None}):
                with pytest.raises(RuntimeError, match="pyobjc|fixture"):
                    await cua.mount(coordinator, config={})

    async def test_mount_raises_when_macos_backend_not_available(self, coordinator) -> None:
        """Regression: mount() raises when MacOSBackend._available is False.

        Simulates pyobjc importable but Accessibility / Quartz init failing.
        """
        mock_instance = MagicMock()
        mock_instance._available = False
        mock_module = MagicMock()
        mock_module.MacOSBackend.return_value = mock_instance

        with patch("amplifier_module_tool_cua.backends.registry.sys") as mock_sys:
            mock_sys.platform = "darwin"
            with patch.dict(sys.modules, {"amplifier_module_tool_cua.backends.macos": mock_module}):
                with pytest.raises(RuntimeError, match="pyobjc|fixture"):
                    await cua.mount(coordinator, config={})

    async def test_mount_with_explicit_fixture_backend_succeeds(self, coordinator) -> None:
        """Explicit backend=fixture must always succeed, even when platform is darwin.

        Ensures the escape hatch for CI/testing is not accidentally broken.
        """
        with patch("amplifier_module_tool_cua.backends.registry.sys") as mock_sys:
            mock_sys.platform = "darwin"
            await cua.mount(coordinator, config={"backend": "fixture"})

        assert "tools" in coordinator._mounted, "fixture backend should mount the cua tool"
