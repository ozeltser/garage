"""
Tests for the custom route decorators (app.py):

  - admin_required  – blocks non-admin authenticated users; passes admins through
  - api_key_required – validates X-API-Key header against the database
"""
import secrets
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from user_roles import UserRole


# ---------------------------------------------------------------------------
# admin_required
# ---------------------------------------------------------------------------


class TestAdminRequired:
    """admin_required redirects regular users and allows admins."""

    def test_unauthenticated_redirected_to_login(self, client):
        """Unauthenticated request is redirected to /login by Flask-Login."""
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_regular_user_cannot_access_admin(self, auth_client):
        """Authenticated regular user is redirected away from /admin."""
        response = auth_client.get("/admin", follow_redirects=False)
        # Should redirect (admin_required sends them to home, login_required to login)
        assert response.status_code == 302

    def test_admin_user_can_access_admin_page(self, admin_client, mock_db):
        """Authenticated admin user gets a 200 from /admin."""
        mock_db.get_all_users.return_value = []
        response = admin_client.get("/admin", follow_redirects=False)
        assert response.status_code == 200

    def test_regular_user_cannot_access_create_user(self, auth_client):
        response = auth_client.get("/admin/create_user", follow_redirects=False)
        assert response.status_code == 302

    def test_admin_can_access_create_user(self, admin_client):
        response = admin_client.get("/admin/create_user", follow_redirects=False)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# api_key_required
# ---------------------------------------------------------------------------


class TestApiKeyRequired:
    """api_key_required validates API keys via X-API-Key header."""

    def test_missing_header_returns_401(self, client):
        response = client.get("/api/door_status")
        assert response.status_code == 401

    def test_missing_header_returns_error_json(self, client):
        response = client.get("/api/door_status")
        data = response.get_json()
        assert data is not None
        assert "error" in data
        assert data["error"] == "Invalid API key"

    def test_invalid_key_returns_401(self, client, mock_db):
        mock_db.get_user_by_api_key.return_value = None
        response = client.get("/api/door_status", headers={"X-API-Key": "bad_key"})
        assert response.status_code == 401

    def test_invalid_key_returns_error_json(self, client, mock_db):
        mock_db.get_user_by_api_key.return_value = None
        response = client.get("/api/door_status", headers={"X-API-Key": "bad_key"})
        data = response.get_json()
        assert data["error"] == "Invalid API key"

    def test_valid_key_returns_200(self, client, mock_db):
        mock_db.get_user_by_api_key.return_value = {
            "id": 1,
            "username": "apiuser",
            "role": UserRole.REGULAR.value,
            "is_active": True,
        }
        mock_proc = MagicMock()
        mock_proc.stdout = "Door Closed\n"
        mock_proc.stderr = ""
        with patch("subprocess.run", return_value=mock_proc):
            response = client.get(
                "/api/door_status",
                headers={"X-API-Key": secrets.token_hex(32)},
            )
        assert response.status_code == 200

    def test_valid_key_response_contains_status(self, client, mock_db):
        mock_db.get_user_by_api_key.return_value = {
            "id": 1,
            "username": "apiuser",
            "role": UserRole.REGULAR.value,
            "is_active": True,
        }
        mock_proc = MagicMock()
        mock_proc.stdout = "Door Opened\n"
        mock_proc.stderr = ""
        with patch("subprocess.run", return_value=mock_proc):
            response = client.get(
                "/api/door_status",
                headers={"X-API-Key": secrets.token_hex(32)},
            )
        data = response.get_json()
        assert "status" in data
        assert data["status"] == "open"
