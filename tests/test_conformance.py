"""Backend conformance test suite.

Runs identical contract tests against every available backend.
This ensures all backends satisfy the same observation/action semantics.
"""

from __future__ import annotations

import pytest
from amplifier_module_tool_cua.backends.fixture import FixtureBackend
from amplifier_module_tool_cua.backends.linux import LinuxStubBackend
from amplifier_module_tool_cua.backends.windows import WindowsStubBackend
from amplifier_module_tool_cua.models import ActionStatus
from amplifier_module_tool_cua.target import Target

# All backends to test. macOS is excluded because it requires real pyobjc.
_BACKENDS = [
    pytest.param(FixtureBackend, id="fixture"),
    pytest.param(WindowsStubBackend, id="windows-stub"),
    pytest.param(LinuxStubBackend, id="linux-stub"),
]


@pytest.fixture(params=_BACKENDS)
def backend(request):
    cls = request.param
    return cls()


class TestConformanceProtocol:
    """Every backend satisfies the Target protocol."""

    def test_satisfies_protocol(self, backend):
        assert isinstance(backend, Target)

    def test_platform_is_string(self, backend):
        assert isinstance(backend.platform, str)
        assert len(backend.platform) > 0

    def test_capabilities_is_dict(self, backend):
        caps = backend.capabilities
        assert isinstance(caps, dict)
        # Must declare all standard capabilities
        required = {
            "screenshot",
            "cursor_position",
            "screen_info",
            "window_info",
            "semantic_tree",
            "click",
            "double_click",
            "type_text",
            "key_press",
            "scroll",
            "move_cursor",
        }
        assert required.issubset(set(caps.keys())), f"Missing caps: {required - set(caps.keys())}"


class TestConformanceResults:
    """Every backend returns ActionResult with valid status for all methods."""

    @pytest.mark.asyncio
    async def test_screenshot_returns_valid_status(self, backend):
        result = await backend.screenshot()
        assert result.status in (
            ActionStatus.SUCCESS,
            ActionStatus.FAILURE,
            ActionStatus.BLOCKED,
            ActionStatus.AMBIGUOUS,
        )

    @pytest.mark.asyncio
    async def test_cursor_position_returns_valid_status(self, backend):
        result = await backend.cursor_position()
        assert result.status in (
            ActionStatus.SUCCESS,
            ActionStatus.FAILURE,
            ActionStatus.BLOCKED,
            ActionStatus.AMBIGUOUS,
        )

    @pytest.mark.asyncio
    async def test_click_returns_valid_status(self, backend):
        result = await backend.click(0, 0)
        assert result.status in (
            ActionStatus.SUCCESS,
            ActionStatus.FAILURE,
            ActionStatus.BLOCKED,
            ActionStatus.AMBIGUOUS,
        )

    @pytest.mark.asyncio
    async def test_type_text_returns_valid_status(self, backend):
        result = await backend.type_text("test")
        assert result.status in (
            ActionStatus.SUCCESS,
            ActionStatus.FAILURE,
            ActionStatus.BLOCKED,
            ActionStatus.AMBIGUOUS,
        )

    @pytest.mark.asyncio
    async def test_semantic_tree_returns_valid_status(self, backend):
        result = await backend.semantic_tree()
        assert result.status in (
            ActionStatus.SUCCESS,
            ActionStatus.FAILURE,
            ActionStatus.BLOCKED,
            ActionStatus.AMBIGUOUS,
        )


class TestConformanceCapabilityConsistency:
    """Backends that declare a capability as False should return BLOCKED."""

    @pytest.mark.asyncio
    async def test_unavailable_screenshot_returns_blocked(self, backend):
        if not backend.capabilities.get("screenshot"):
            result = await backend.screenshot()
            assert result.status == ActionStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_unavailable_semantic_tree_returns_blocked(self, backend):
        if not backend.capabilities.get("semantic_tree"):
            result = await backend.semantic_tree()
            assert result.status == ActionStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_unavailable_click_returns_blocked(self, backend):
        if not backend.capabilities.get("click"):
            result = await backend.click(0, 0)
            assert result.status == ActionStatus.BLOCKED
