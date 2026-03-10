"""Tests for backend auto-detection and registry."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest
from amplifier_module_tool_cua.backends.registry import detect_backend, get_backend
from amplifier_module_tool_cua.target import Target


class TestDetectBackend:
    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_returns_target_on_known_platform(self, mock_sys):
        """detect_backend returns a Target on platforms with stub backends."""
        mock_sys.platform = "linux"
        backend = detect_backend()
        assert isinstance(backend, Target)

    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_darwin_raises_when_import_fails(self, mock_sys):
        """Regression: darwin auto-detect must NOT silently fall back to fixture on import error."""
        mock_sys.platform = "darwin"
        # Simulate the macos module being unimportable (e.g. pyobjc not installed)
        with patch.dict(sys.modules, {"amplifier_module_tool_cua.backends.macos": None}):
            with pytest.raises(RuntimeError, match="pyobjc|fixture"):
                detect_backend()

    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_darwin_raises_when_backend_not_available(self, mock_sys):
        """Regression: darwin auto-detect must NOT silently fall back to fixture
        when _available is False."""
        mock_sys.platform = "darwin"
        mock_instance = MagicMock()
        mock_instance._available = False
        mock_module = MagicMock()
        mock_module.MacOSBackend.return_value = mock_instance
        with patch.dict(sys.modules, {"amplifier_module_tool_cua.backends.macos": mock_module}):
            with pytest.raises(RuntimeError, match="pyobjc|fixture"):
                detect_backend()

    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_win32_returns_windows_stub(self, mock_sys):
        mock_sys.platform = "win32"
        backend = detect_backend()
        assert backend.platform == "windows"

    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_linux_returns_linux_stub(self, mock_sys):
        mock_sys.platform = "linux"
        backend = detect_backend()
        assert backend.platform == "linux"

    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_unknown_platform_raises(self, mock_sys):
        """Unknown platforms must raise instead of silently returning fixture."""
        mock_sys.platform = "freebsd"
        with pytest.raises(RuntimeError, match="fixture"):
            detect_backend()


class TestGetBackend:
    def test_fixture_by_name(self):
        backend = get_backend("fixture")
        assert backend.platform == "fixture"

    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_auto_returns_something(self, mock_sys):
        """auto backend selection returns a Target on platforms with stub backends."""
        mock_sys.platform = "linux"
        backend = get_backend("auto")
        assert isinstance(backend, Target)

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend("quantum_computer")
