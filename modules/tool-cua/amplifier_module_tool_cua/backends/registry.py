"""Backend auto-detection and factory.

Selects the best backend for the current platform or by explicit name.
"""

from __future__ import annotations

import sys

from ..target import Target


def detect_backend() -> Target:
    """Auto-detect and return the appropriate backend for the current platform.

    Raises RuntimeError if the platform backend cannot be initialized.
    Use get_backend("fixture") or set ``backend: fixture`` explicitly for CI/testing.
    """
    if sys.platform == "darwin":
        try:
            from .macos import MacOSBackend

            backend = MacOSBackend()
        except Exception as exc:
            raise RuntimeError(
                "macOS backend could not be initialized. "
                "Install the required dependencies:\n\n"
                "  python -m pip install"
                ' "pyobjc-framework-Quartz>=10.0"'
                ' "pyobjc-framework-ApplicationServices>=10.0"\n\n'
                "Accessibility permission is also required (System Settings > Privacy"
                " & Security > Accessibility) for semantic tree and input actions.\n\n"
                "For CI or testing without a real desktop, set backend: fixture explicitly."
            ) from exc
        if not backend._available:
            raise RuntimeError(
                "macOS backend is not available. Quartz/pyobjc may be missing or"
                " Accessibility permission has not been granted.\n\n"
                "Install the required dependencies:\n\n"
                "  python -m pip install"
                ' "pyobjc-framework-Quartz>=10.0"'
                ' "pyobjc-framework-ApplicationServices>=10.0"\n\n'
                "Accessibility permission is also required (System Settings > Privacy"
                " & Security > Accessibility) for semantic tree and input actions.\n\n"
                "For CI or testing without a real desktop, set backend: fixture explicitly."
            )
        return backend
    elif sys.platform == "win32":
        from .windows import WindowsStubBackend

        return WindowsStubBackend()
    elif sys.platform == "linux":
        from .linux import LinuxStubBackend

        return LinuxStubBackend()
    else:
        raise RuntimeError(
            f"No backend is available for platform {sys.platform!r}. "
            "For CI or testing without a real desktop, set backend: fixture explicitly."
        )


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
