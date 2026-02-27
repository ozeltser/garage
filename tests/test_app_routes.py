"""
Integration tests for Flask HTTP routes (app.py).

Uses the test client fixtures from conftest.py; no real database or hardware.
"""
import secrets
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from user_roles import UserRole


# ---------------------------------------------------------------------------
# Public / unauthenticated routes
# ---------------------------------------------------------------------------


class TestPublicRoutes:
    """Routes that should be accessible without logging in."""

    def test_login_page_get(self, client):
        response = client.get("/login")
        assert response.status_code == 200

    def test_login_page_contains_form(self, client):
        response = client.get("/login")
        assert b"username" in response.data.lower()

    def test_privacy_policy_accessible(self, client):
        response = client.get("/privacy-policy")
        assert response.status_code == 200

    def test_terms_accessible(self, client):
        response = client.get("/terms-and-conditions")
        assert response.status_code == 200

    def test_home_redirects_to_login_when_unauthenticated(self, client):
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------


class TestLogin:
    def test_valid_credentials_redirect_to_home(self, client, mock_db):
        mock_db.verify_password.return_value = True
        mock_db.get_user_by_username.return_value = {
            "id": 1,
            "username": "alice",
            "role": UserRole.REGULAR.value,
            "is_active": True,
            "first_name": None,
            "last_name": None,
            "email": None,
            "phone": None,
            "sms_notifications_enabled": False,
            "api_key_hash": None,
            "password_hash": "hashed",
        }
        response = client.post(
            "/login",
            data={"username": "alice", "password": "secret"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/" in response.headers["Location"]

    def test_invalid_credentials_stay_on_login(self, client, mock_db):
        mock_db.verify_password.return_value = False
        response = client.post(
            "/login",
            data={"username": "alice", "password": "wrong"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"login" in response.data.lower()

    def test_invalid_credentials_show_error_message(self, client, mock_db):
        mock_db.verify_password.return_value = False
        response = client.post(
            "/login",
            data={"username": "alice", "password": "wrong"},
            follow_redirects=True,
        )
        # Flash message should appear
        assert b"invalid" in response.data.lower()

    def test_db_exception_during_login_shows_error(self, client, mock_db):
        mock_db.verify_password.side_effect = Exception("DB down")
        response = client.post(
            "/login",
            data={"username": "alice", "password": "pass"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"error" in response.data.lower()


class TestLogout:
    def test_unauthenticated_logout_redirects_to_login(self, client):
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_authenticated_logout_redirects_to_login(self, auth_client):
        response = auth_client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# Home / Dashboard
# ---------------------------------------------------------------------------


class TestHome:
    def test_authenticated_user_sees_dashboard(self, auth_client):
        response = auth_client.get("/")
        assert response.status_code == 200

    def test_dashboard_contains_door_controls(self, auth_client):
        response = auth_client.get("/")
        # The dashboard template should mention door or garage
        assert b"garage" in response.data.lower() or b"door" in response.data.lower()


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class TestProfile:
    def test_unauthenticated_redirected(self, client):
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_authenticated_user_sees_profile(self, auth_client):
        response = auth_client.get("/profile")
        assert response.status_code == 200

    def test_profile_post_updates_profile(self, auth_client, mock_db):
        mock_db.update_user_profile.return_value = True
        response = auth_client.post(
            "/profile",
            data={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
                "phone": "555-1234",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert mock_db.update_user_profile.called

    def test_profile_password_change_wrong_current_password(self, auth_client, mock_db):
        mock_db.update_user_profile.return_value = True
        mock_db.verify_password.return_value = False
        response = auth_client.post(
            "/profile",
            data={
                "first_name": "Alice",
                "current_password": "wrong",
                "new_password": "newpass",
                "confirm_password": "newpass",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"incorrect" in response.data.lower()

    def test_profile_password_change_mismatched_passwords(self, auth_client, mock_db):
        mock_db.update_user_profile.return_value = True
        response = auth_client.post(
            "/profile",
            data={
                "current_password": "oldpass",
                "new_password": "newpass1",
                "confirm_password": "newpass2",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"do not match" in response.data.lower()

    def test_profile_password_change_success(self, auth_client, mock_db):
        mock_db.update_user_profile.return_value = True
        mock_db.verify_password.return_value = True
        mock_db.update_password.return_value = True
        response = auth_client.post(
            "/profile",
            data={
                "current_password": "oldpass",
                "new_password": "newpass",
                "confirm_password": "newpass",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert mock_db.update_password.called


# ---------------------------------------------------------------------------
# API Key Generation
# ---------------------------------------------------------------------------


class TestGenerateApiKey:
    def test_unauthenticated_redirected(self, client):
        response = client.post("/generate_api_key", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_authenticated_generates_key_and_redirects(self, auth_client, mock_db):
        mock_db.generate_api_key.return_value = secrets.token_hex(32)
        response = auth_client.post("/generate_api_key", follow_redirects=False)
        assert response.status_code == 302
        assert mock_db.generate_api_key.called

    def test_api_key_generation_failure_shows_error(self, auth_client, mock_db):
        mock_db.generate_api_key.return_value = None
        response = auth_client.post("/generate_api_key", follow_redirects=True)
        assert response.status_code == 200
        assert b"failed" in response.data.lower()


# ---------------------------------------------------------------------------
# Door Control (run_script)
# ---------------------------------------------------------------------------


class TestRunScript:
    def test_unauthenticated_redirected(self, client):
        response = client.post("/run_script", follow_redirects=False)
        assert response.status_code == 302

    def test_authenticated_invokes_relay_script(self, auth_client):
        mock_proc = MagicMock()
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_proc.returncode = 0
        with patch("subprocess.run", return_value=mock_proc):
            response = auth_client.post("/run_script")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_timeout_returns_failure(self, auth_client):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("python", 30)):
            response = auth_client.post("/run_script")
        data = response.get_json()
        assert data["success"] is False
        assert "timed out" in data["error"].lower()

    def test_exception_returns_failure(self, auth_client):
        with patch("subprocess.run", side_effect=OSError("File not found")):
            response = auth_client.post("/run_script")
        data = response.get_json()
        assert data["success"] is False


# ---------------------------------------------------------------------------
# Door Status Endpoint (web UI)
# ---------------------------------------------------------------------------


class TestDoorStatus:
    def test_unauthenticated_redirected(self, client):
        response = client.get("/door_status", follow_redirects=False)
        assert response.status_code == 302

    def test_returns_json_with_status(self, auth_client):
        mock_proc = MagicMock()
        mock_proc.stdout = "Door Closed\n"
        mock_proc.stderr = ""
        with patch("subprocess.run", return_value=mock_proc):
            response = auth_client.get("/door_status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "closed"


# ---------------------------------------------------------------------------
# Admin Routes
# ---------------------------------------------------------------------------


class TestAdminRoutes:
    def test_admin_page_lists_users(self, admin_client, mock_db):
        mock_db.get_all_users.return_value = [
            {"id": 1, "username": "alice", "role": "regular"}
        ]
        response = admin_client.get("/admin")
        assert response.status_code == 200

    def test_create_user_post_success(self, admin_client, mock_db):
        mock_db.create_user.return_value = True
        response = admin_client.post(
            "/admin/create_user",
            data={
                "username": "newuser",
                "password": "pass123",
                "confirm_password": "pass123",
                "role": UserRole.REGULAR.value,
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert mock_db.create_user.called

    def test_create_user_mismatched_passwords(self, admin_client, mock_db):
        response = admin_client.post(
            "/admin/create_user",
            data={
                "username": "newuser",
                "password": "pass1",
                "confirm_password": "pass2",
                "role": UserRole.REGULAR.value,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"do not match" in response.data.lower()
        assert not mock_db.create_user.called

    def test_create_user_missing_fields(self, admin_client, mock_db):
        response = admin_client.post(
            "/admin/create_user",
            data={"username": "", "password": "", "confirm_password": ""},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert not mock_db.create_user.called

    def test_create_user_invalid_role(self, admin_client, mock_db):
        response = admin_client.post(
            "/admin/create_user",
            data={
                "username": "newuser",
                "password": "pass",
                "confirm_password": "pass",
                "role": "superadmin",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert not mock_db.create_user.called

    def test_delete_user_success(self, admin_client, mock_db):
        mock_db.delete_user.return_value = True
        response = admin_client.post(
            "/admin/delete_user/alice", follow_redirects=False
        )
        assert response.status_code == 302
        mock_db.delete_user.assert_called_once_with("alice")

    def test_cannot_delete_own_account(self, admin_client, mock_db):
        """Admin cannot delete themselves via the UI."""
        response = admin_client.post(
            "/admin/delete_user/admin", follow_redirects=True
        )
        assert response.status_code == 200
        assert b"cannot delete your own account" in response.data.lower()
        assert not mock_db.delete_user.called

    def test_change_password_success(self, admin_client, mock_db):
        # admin_client already sets get_user_by_username to return the admin user;
        # don't override it here or Flask-Login would load a non-admin and the
        # admin_required decorator would redirect before the handler runs.
        mock_db.update_user_password_by_admin.return_value = True
        response = admin_client.post(
            "/admin/change_password/alice",
            data={"new_password": "newpass", "confirm_password": "newpass"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        mock_db.update_user_password_by_admin.assert_called_once_with("alice", "newpass")

    def test_change_password_mismatched(self, admin_client, mock_db):
        # admin_client sets get_user_by_username.return_value to the admin user.
        # We keep that for Flask-Login auth but also need it to return alice's
        # data when the route calls get_user_by_username('alice') to render the
        # form on validation error.  Use side_effect to route by argument.
        admin_user_data = mock_db.get_user_by_username.return_value
        alice_user_data = {
            "id": 1,
            "username": "alice",
            "role": UserRole.REGULAR.value,
            "is_active": True,
            "first_name": None,
            "last_name": None,
            "email": None,
            "phone": None,
            "sms_notifications_enabled": False,
            "api_key_hash": None,
            "password_hash": "hashed",
        }

        def get_user_by_username(username):
            if username == "admin":
                return admin_user_data
            if username == "alice":
                return alice_user_data
            return None

        mock_db.get_user_by_username.side_effect = get_user_by_username

        response = admin_client.post(
            "/admin/change_password/alice",
            data={"new_password": "pass1", "confirm_password": "pass2"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"do not match" in response.data.lower()
        assert not mock_db.update_user_password_by_admin.called
