"""Tests for backend auto-detection and registry."""

from __future__ import annotations

from unittest.mock import patch

from amplifier_module_tool_cua.backends.registry import detect_backend, get_backend
from amplifier_module_tool_cua.target import Target


class TestDetectBackend:
    def test_returns_target(self):
        backend = detect_backend()
        assert isinstance(backend, Target)

    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_darwin_returns_macos_or_fixture(self, mock_sys):
        mock_sys.platform = "darwin"
        backend = detect_backend()
        assert isinstance(backend, Target)
        # On macOS without pyobjc, falls back to fixture
        assert backend.platform in ("macos", "fixture")

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
    def test_unknown_platform_returns_fixture(self, mock_sys):
        mock_sys.platform = "freebsd"
        backend = detect_backend()
        assert backend.platform == "fixture"


class TestGetBackend:
    def test_fixture_by_name(self):
        backend = get_backend("fixture")
        assert backend.platform == "fixture"

    def test_auto_returns_something(self):
        backend = get_backend("auto")
        assert isinstance(backend, Target)

    def test_unknown_name_raises(self):
        import pytest

        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend("quantum_computer")
