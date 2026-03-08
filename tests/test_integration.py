"""Bounded integration tests — full stack with fixture backend.

Tests the complete flow: mount -> CuaTool -> FixtureBackend -> ActionResult.
Emphasizes safety, bounded loops, and recovery patterns.
"""

from __future__ import annotations

import pytest
from amplifier_module_tool_cua import mount


@pytest.fixture
async def mounted_tool(coordinator):
    await mount(coordinator, config={"backend": "fixture"})
    return coordinator._mounted["tools"]["cua"]


class TestObserveFlow:
    """Test the observation pipeline end-to-end."""

    @pytest.mark.asyncio
    async def test_full_observe(self, mounted_tool):
        result = await mounted_tool.execute(arguments={"action": "observe"})
        assert result["status"] == "success"
        data = result["data"]
        # Visual world
        assert data["screenshot_base64"] is not None
        assert data["cursor"]["x"] == 960  # fixture default
        assert len(data["windows"]) > 0
        # Semantic world
        assert len(data["semantic_tree"]) > 0

    @pytest.mark.asyncio
    async def test_observe_then_act_then_verify(self, mounted_tool):
        """The core observe-act-verify loop."""
        # 1. Observe
        obs1 = await mounted_tool.execute(arguments={"action": "observe"})
        assert obs1["status"] == "success"
        initial_cursor = obs1["data"]["cursor"]

        # 2. Act — click somewhere else
        act = await mounted_tool.execute(arguments={"action": "click", "x": 200, "y": 400})
        assert act["status"] == "success"

        # 3. Verify — cursor should have moved
        obs2 = await mounted_tool.execute(arguments={"action": "cursor_position"})
        assert obs2["status"] == "success"
        assert obs2["data"]["x"] == 200
        assert obs2["data"]["y"] == 400
        # Cursor changed from initial position
        assert (obs2["data"]["x"], obs2["data"]["y"]) != (initial_cursor["x"], initial_cursor["y"])


class TestActionAndVerify:
    @pytest.mark.asyncio
    async def test_type_text_flow(self, mounted_tool):
        result = await mounted_tool.execute(
            arguments={"action": "type_text", "text": "hello world"}
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_key_press_with_modifiers(self, mounted_tool):
        result = await mounted_tool.execute(
            arguments={"action": "key_press", "key": "c", "modifiers": ["command"]}
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_scroll_flow(self, mounted_tool):
        result = await mounted_tool.execute(
            arguments={"action": "scroll", "x": 500, "y": 500, "dx": 0, "dy": -5}
        )
        assert result["status"] == "success"


class TestSafetyBehavior:
    @pytest.mark.asyncio
    async def test_unknown_action_does_not_crash(self, mounted_tool):
        """Unknown actions should return failure, never raise."""
        result = await mounted_tool.execute(arguments={"action": "format_hard_drive"})
        assert result["status"] == "failure"

    @pytest.mark.asyncio
    async def test_missing_action_does_not_crash(self, mounted_tool):
        """Missing action key should return failure, never raise."""
        result = await mounted_tool.execute(arguments={})
        assert result["status"] == "failure"

    @pytest.mark.asyncio
    async def test_all_observation_actions_succeed(self, mounted_tool):
        """All observation actions should succeed with fixture backend."""
        for action in [
            "screenshot",
            "cursor_position",
            "screen_info",
            "window_info",
            "semantic_tree",
            "observe",
        ]:
            result = await mounted_tool.execute(arguments={"action": action})
            assert result["status"] == "success", f"{action} failed: {result}"

    @pytest.mark.asyncio
    async def test_all_input_actions_succeed(self, mounted_tool):
        """All input actions should succeed with fixture backend."""
        actions = [
            {"action": "click", "x": 100, "y": 100},
            {"action": "double_click", "x": 200, "y": 200},
            {"action": "type_text", "text": "test"},
            {"action": "key_press", "key": "return"},
            {"action": "scroll", "x": 0, "y": 0, "dy": 1},
            {"action": "move_cursor", "x": 50, "y": 50},
        ]
        for args in actions:
            result = await mounted_tool.execute(arguments=args)
            assert result["status"] == "success", f"{args['action']} failed: {result}"
