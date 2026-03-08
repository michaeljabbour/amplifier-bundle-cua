"""Backend auto-detection and factory."""

from __future__ import annotations

from ..target import Target


def get_backend(name: str) -> Target:
    """Get a backend by name. Full implementation in Task 18."""
    if name == "fixture":
        from .fixture import FixtureBackend

        return FixtureBackend()
    elif name == "auto":
        # Full auto-detection will be implemented in Task 18.
        # For now, always return fixture backend.
        from .fixture import FixtureBackend

        return FixtureBackend()
    else:
        raise ValueError(f"Unknown backend: {name}")


def detect_backend() -> Target:
    """Auto-detect backend. Full implementation in Task 18."""
    from .fixture import FixtureBackend

    return FixtureBackend()
