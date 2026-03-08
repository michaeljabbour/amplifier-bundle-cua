"""Tests for core CUA data models."""

from __future__ import annotations

from amplifier_module_tool_cua.models import ActionResult, ActionStatus


class TestActionStatus:
    def test_status_values_exist(self):
        assert ActionStatus.SUCCESS == "success"
        assert ActionStatus.FAILURE == "failure"
        assert ActionStatus.BLOCKED == "blocked"
        assert ActionStatus.AMBIGUOUS == "ambiguous"

    def test_status_is_string(self):
        assert isinstance(ActionStatus.SUCCESS, str)
        assert isinstance(ActionStatus.FAILURE, str)


class TestActionResult:
    def test_success_result(self):
        result = ActionResult(status=ActionStatus.SUCCESS)
        assert result.status == ActionStatus.SUCCESS
        assert result.message == ""
        assert result.data == {}

    def test_failure_result_with_message(self):
        result = ActionResult(status=ActionStatus.FAILURE, message="permission denied")
        assert result.status == ActionStatus.FAILURE
        assert result.message == "permission denied"

    def test_result_with_data(self):
        result = ActionResult(
            status=ActionStatus.SUCCESS,
            data={"screenshot_base64": "abc123"},
        )
        assert result.data["screenshot_base64"] == "abc123"

    def test_blocked_result(self):
        result = ActionResult(status=ActionStatus.BLOCKED, message="accessibility not enabled")
        assert result.status == ActionStatus.BLOCKED

    def test_ambiguous_result(self):
        result = ActionResult(
            status=ActionStatus.AMBIGUOUS,
            message="click executed but state unchanged",
        )
        assert result.status == ActionStatus.AMBIGUOUS
