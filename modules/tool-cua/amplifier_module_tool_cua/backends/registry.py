"""Backend auto-detection and factory.

Selects the best backend for the current platform or by explicit name.
"""

from __future__ import annotations

import sys

from ..target import Target


def detect_backend() -> Target:
    """Auto-detect and return the appropriate backend for the current platform.

    Falls back to FixtureBackend if no platform-specific backend is available.
    """
    if sys.platform == "darwin":
        try:
            from .macos import MacOSBackend

            backend = MacOSBackend()
            if backend._available:
                return backend
        except Exception:
            pass
        # Fall through to fixture if macOS backend can't initialize
        from .fixture import FixtureBackend

        return FixtureBackend()
    elif sys.platform == "win32":
        from .windows import WindowsStubBackend

        return WindowsStubBackend()
    elif sys.platform == "linux":
        from .linux import LinuxStubBackend

        return LinuxStubBackend()
    else:
        from .fixture import FixtureBackend

        return FixtureBackend()


def get_backend(name: str) -> Target:
    """Get a backend by explicit name.

    Args:
        name: One of "fixture", "macos", "windows", "linux", "auto".

    Raises:
        ValueError: If name is not recognized.
    """
    if name == "auto":
        return detect_backend()
    elif name == "fixture":
        from .fixture import FixtureBackend

        return FixtureBackend()
    elif name == "macos":
        from .macos import MacOSBackend

        return MacOSBackend()
    elif name == "windows":
        from .windows import WindowsStubBackend

        return WindowsStubBackend()
    elif name == "linux":
        from .linux import LinuxStubBackend

        return LinuxStubBackend()
    else:
        raise ValueError(f"Unknown backend: {name}")
