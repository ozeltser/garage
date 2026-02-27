"""
Tests for the _get_door_status helper function (app.py).

The function calls doorStatus.py as a subprocess and parses its stdout.
All subprocess calls are mocked so no real hardware or scripts are executed.
"""
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from app import _get_door_status


def _make_completed_process(stdout="", stderr="", returncode=0):
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


class TestDoorStatusParsing:
    """Status string is parsed correctly from subprocess stdout."""

    def test_door_closed_detected(self):
        mock_result = _make_completed_process(stdout="Door Closed\n")
        with patch("subprocess.run", return_value=mock_result):
            data = _get_door_status()
        assert data["success"] is True
        assert data["status"] == "closed"

    def test_door_opened_detected(self):
        mock_result = _make_completed_process(stdout="Door Opened\n")
        with patch("subprocess.run", return_value=mock_result):
            data = _get_door_status()
        assert data["success"] is True
        assert data["status"] == "open"

    def test_unknown_status_for_unrecognised_output(self):
        mock_result = _make_completed_process(stdout="Automation HAT not found.\n")
        with patch("subprocess.run", return_value=mock_result):
            data = _get_door_status()
        assert data["success"] is True
        assert data["status"] == "unknown"

    def test_empty_output_gives_unknown(self):
        mock_result = _make_completed_process(stdout="")
        with patch("subprocess.run", return_value=mock_result):
            data = _get_door_status()
        assert data["status"] == "unknown"

    def test_raw_output_returned(self):
        mock_result = _make_completed_process(stdout="Door Closed\n")
        with patch("subprocess.run", return_value=mock_result):
            data = _get_door_status()
        assert data["raw_output"] == "Door Closed"

    def test_stderr_returned_when_present(self):
        mock_result = _make_completed_process(stdout="", stderr="some warning")
        with patch("subprocess.run", return_value=mock_result):
            data = _get_door_status()
        assert data["error"] == "some warning"

    def test_error_is_none_when_stderr_empty(self):
        mock_result = _make_completed_process(stdout="Door Closed\n", stderr="")
        with patch("subprocess.run", return_value=mock_result):
            data = _get_door_status()
        assert data["error"] is None


class TestDoorStatusErrorHandling:
    """Failures are reported as success=False with an error message."""

    def test_timeout_returns_failure(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("python", 10)):
            data = _get_door_status()
        assert data["success"] is False
        assert "timed out" in data["error"].lower()

    def test_generic_exception_returns_failure(self):
        with patch("subprocess.run", side_effect=OSError("script not found")):
            data = _get_door_status()
        assert data["success"] is False
        assert data["error"] is not None

    def test_success_key_present_on_normal_result(self):
        mock_result = _make_completed_process(stdout="Door Opened\n")
        with patch("subprocess.run", return_value=mock_result):
            data = _get_door_status()
        assert "success" in data

    def test_status_key_present_on_normal_result(self):
        mock_result = _make_completed_process(stdout="Door Closed\n")
        with patch("subprocess.run", return_value=mock_result):
            data = _get_door_status()
        assert "status" in data
