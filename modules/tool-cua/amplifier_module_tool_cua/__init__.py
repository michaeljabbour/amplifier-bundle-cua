"""Computer-use automation tool module for Amplifier."""

from typing import Any

__amplifier_module_type__ = "tool"


async def mount(coordinator: Any, config: dict[str, Any] | None = None) -> None:
    """Mount the CUA tool into the Amplifier coordinator.

    Called by Amplifier when loading the module via its entry point.
    """
    # Implementation will be added in Task 13
    raise NotImplementedError("mount() not yet implemented")
