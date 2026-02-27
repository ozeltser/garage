"""
Unit tests for DatabaseManager (database.py).

All tests use a mock database connection so no real MySQL instance is needed.
Each test creates a fresh DatabaseManager via __new__ (skipping __init__)
and injects a mock connection via patch.object.
"""
import hashlib
import secrets
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.security import generate_password_hash, check_password_hash

from database import DatabaseManager
from user_roles import UserRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db() -> DatabaseManager:
    """Create a DatabaseManager instance bypassing __init__ (no real DB)."""
    return DatabaseManager.__new__(DatabaseManager)


def _make_mock_connection(fetchone=None, fetchall=None, rowcount=1):
    """Build a mock connection/cursor stack.

    Returns (mock_connection, mock_cursor) so tests can inspect calls.
    """
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone
    cursor.fetchall.return_value = fetchall if fetchall is not None else []
    cursor.rowcount = rowcount

    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    return conn, cursor


# ---------------------------------------------------------------------------
# generate_api_key
# ---------------------------------------------------------------------------


class TestGenerateApiKey:
    def test_returns_64_char_hex_string(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            key = db.generate_api_key("alice")
        assert key is not None
        assert len(key) == 64
        int(key, 16)  # raises ValueError if not valid hex

    def test_stores_sha256_hash_in_db(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            key = db.generate_api_key("alice")
        expected_hash = hashlib.sha256(key.encode()).hexdigest()
        call_params = cursor.execute.call_args[0][1]
        assert call_params[0] == expected_hash

    def test_username_passed_to_update(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            db.generate_api_key("bob")
        call_params = cursor.execute.call_args[0][1]
        assert call_params[1] == "bob"

    def test_returns_none_when_user_not_found(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=0)
        with patch.object(db, "get_connection", return_value=conn):
            key = db.generate_api_key("nonexistent")
        assert key is None

    def test_returns_none_on_db_exception(self):
        db = _make_db()
        with patch.object(db, "get_connection", side_effect=Exception("DB error")):
            key = db.generate_api_key("alice")
        assert key is None

    def test_each_call_generates_unique_key(self):
        db = _make_db()
        keys = set()
        for _ in range(10):
            conn, _ = _make_mock_connection(rowcount=1)
            with patch.object(db, "get_connection", return_value=conn):
                keys.add(db.generate_api_key("alice"))
        assert len(keys) == 10


# ---------------------------------------------------------------------------
# get_user_by_api_key
# ---------------------------------------------------------------------------


class TestGetUserByApiKey:
    def test_returns_user_for_valid_key(self):
        db = _make_db()
        user_row = {"id": 1, "username": "alice", "role": "regular", "is_active": True}
        conn, cursor = _make_mock_connection(fetchone=user_row)
        with patch.object(db, "get_connection", return_value=conn):
            result = db.get_user_by_api_key("somekey")
        assert result == user_row

    def test_queries_with_sha256_hash(self):
        db = _make_db()
        test_key = secrets.token_hex(32)
        conn, cursor = _make_mock_connection(fetchone=None)
        with patch.object(db, "get_connection", return_value=conn):
            db.get_user_by_api_key(test_key)
        expected_hash = hashlib.sha256(test_key.encode()).hexdigest()
        call_params = cursor.execute.call_args[0][1]
        assert call_params[0] == expected_hash

    def test_returns_none_for_invalid_key(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(fetchone=None)
        with patch.object(db, "get_connection", return_value=conn):
            result = db.get_user_by_api_key("bad_key")
        assert result is None

    def test_returns_none_on_db_exception(self):
        db = _make_db()
        with patch.object(db, "get_connection", side_effect=Exception("DB error")):
            result = db.get_user_by_api_key("somekey")
        assert result is None


# ---------------------------------------------------------------------------
# get_user_by_username
# ---------------------------------------------------------------------------


class TestGetUserByUsername:
    def test_returns_user_dict(self):
        db = _make_db()
        row = {"id": 1, "username": "alice", "role": "regular", "is_active": True}
        conn, _ = _make_mock_connection(fetchone=row)
        with patch.object(db, "get_connection", return_value=conn):
            result = db.get_user_by_username("alice")
        assert result == row

    def test_returns_none_when_not_found(self):
        db = _make_db()
        conn, _ = _make_mock_connection(fetchone=None)
        with patch.object(db, "get_connection", return_value=conn):
            result = db.get_user_by_username("ghost")
        assert result is None

    def test_returns_none_on_exception(self):
        db = _make_db()
        with patch.object(db, "get_connection", side_effect=Exception("DB error")):
            result = db.get_user_by_username("alice")
        assert result is None


# ---------------------------------------------------------------------------
# verify_password
# ---------------------------------------------------------------------------


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        db = _make_db()
        hashed = generate_password_hash("secret")
        user_row = {"username": "alice", "password_hash": hashed, "is_active": True}
        with patch.object(db, "get_user_by_username", return_value=user_row):
            assert db.verify_password("alice", "secret") is True

    def test_wrong_password_returns_false(self):
        db = _make_db()
        hashed = generate_password_hash("secret")
        user_row = {"username": "alice", "password_hash": hashed, "is_active": True}
        with patch.object(db, "get_user_by_username", return_value=user_row):
            assert db.verify_password("alice", "wrong") is False

    def test_unknown_user_returns_false(self):
        db = _make_db()
        with patch.object(db, "get_user_by_username", return_value=None):
            assert db.verify_password("ghost", "anything") is False


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------


class TestCreateUser:
    def test_creates_user_with_hashed_password(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            result = db.create_user("alice", "password123")
        assert result is True
        # Verify password is NOT stored as plain text
        stored_hash = cursor.execute.call_args[0][1][1]
        assert stored_hash != "password123"
        assert check_password_hash(stored_hash, "password123")

    def test_default_role_is_regular(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            db.create_user("alice", "password123")
        stored_role = cursor.execute.call_args[0][1][2]
        assert stored_role == UserRole.REGULAR.value

    def test_explicit_admin_role_stored(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            db.create_user("boss", "password123", role=UserRole.ADMIN.value)
        stored_role = cursor.execute.call_args[0][1][2]
        assert stored_role == UserRole.ADMIN.value

    def test_duplicate_username_returns_false(self):
        import pymysql

        db = _make_db()
        conn = MagicMock()
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        cursor = MagicMock()
        cursor.execute.side_effect = pymysql.IntegrityError("Duplicate entry")
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        with patch.object(db, "get_connection", return_value=conn):
            result = db.create_user("alice", "password")
        assert result is False

    def test_db_exception_returns_false(self):
        db = _make_db()
        with patch.object(db, "get_connection", side_effect=Exception("DB down")):
            result = db.create_user("alice", "password")
        assert result is False


# ---------------------------------------------------------------------------
# update_password
# ---------------------------------------------------------------------------


class TestUpdatePassword:
    def test_successful_update_returns_true(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            assert db.update_password("alice", "newpass") is True

    def test_stores_hashed_password(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            db.update_password("alice", "newpass")
        stored = cursor.execute.call_args[0][1][0]
        assert stored != "newpass"
        assert check_password_hash(stored, "newpass")

    def test_user_not_found_returns_false(self):
        db = _make_db()
        conn, _ = _make_mock_connection(rowcount=0)
        with patch.object(db, "get_connection", return_value=conn):
            assert db.update_password("ghost", "newpass") is False

    def test_db_exception_returns_false(self):
        db = _make_db()
        with patch.object(db, "get_connection", side_effect=Exception("DB down")):
            assert db.update_password("alice", "newpass") is False


# ---------------------------------------------------------------------------
# update_user_profile
# ---------------------------------------------------------------------------


class TestUpdateUserProfile:
    def test_successful_update_returns_true(self):
        db = _make_db()
        conn, _ = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            result = db.update_user_profile(
                "alice", "Alice", "Smith", "alice@example.com", "555-1234", True
            )
        assert result is True

    def test_all_fields_passed_to_cursor(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            db.update_user_profile("alice", "Alice", "Smith", "a@b.com", "555", False)
        params = cursor.execute.call_args[0][1]
        assert params == ("Alice", "Smith", "a@b.com", "555", False, "alice")

    def test_sms_enabled_stored_correctly(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            db.update_user_profile("alice", None, None, None, None, True)
        params = cursor.execute.call_args[0][1]
        assert params[4] is True  # sms_notifications_enabled

    def test_user_not_found_returns_false(self):
        db = _make_db()
        conn, _ = _make_mock_connection(rowcount=0)
        with patch.object(db, "get_connection", return_value=conn):
            assert db.update_user_profile("ghost") is False

    def test_db_exception_returns_false(self):
        db = _make_db()
        with patch.object(db, "get_connection", side_effect=Exception("DB down")):
            assert db.update_user_profile("alice") is False


# ---------------------------------------------------------------------------
# deactivate_user
# ---------------------------------------------------------------------------


class TestDeactivateUser:
    def test_successful_deactivation_returns_true(self):
        db = _make_db()
        conn, _ = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            assert db.deactivate_user("alice") is True

    def test_user_not_found_returns_false(self):
        db = _make_db()
        conn, _ = _make_mock_connection(rowcount=0)
        with patch.object(db, "get_connection", return_value=conn):
            assert db.deactivate_user("ghost") is False

    def test_db_exception_returns_false(self):
        db = _make_db()
        with patch.object(db, "get_connection", side_effect=Exception("DB down")):
            assert db.deactivate_user("alice") is False


# ---------------------------------------------------------------------------
# get_all_users
# ---------------------------------------------------------------------------


class TestGetAllUsers:
    def test_returns_list_of_users(self):
        db = _make_db()
        rows = [{"id": 1, "username": "alice"}, {"id": 2, "username": "bob"}]
        conn, _ = _make_mock_connection(fetchall=rows)
        with patch.object(db, "get_connection", return_value=conn):
            result = db.get_all_users()
        assert result == rows

    def test_returns_empty_list_when_no_users(self):
        db = _make_db()
        conn, _ = _make_mock_connection(fetchall=[])
        with patch.object(db, "get_connection", return_value=conn):
            assert db.get_all_users() == []

    def test_returns_empty_list_on_exception(self):
        db = _make_db()
        with patch.object(db, "get_connection", side_effect=Exception("DB down")):
            assert db.get_all_users() == []


# ---------------------------------------------------------------------------
# delete_user
# ---------------------------------------------------------------------------


class TestDeleteUser:
    def _make_delete_connection(self, admin_count, user_role, rowcount=1):
        """Build a cursor that returns admin count first, then user role."""
        cursor = MagicMock()
        cursor.fetchone.side_effect = [
            {"count": admin_count},
            {"role": user_role} if user_role else None,
        ]
        cursor.rowcount = rowcount

        conn = MagicMock()
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return conn, cursor

    def test_deletes_regular_user_successfully(self):
        db = _make_db()
        conn, _ = self._make_delete_connection(
            admin_count=1, user_role=UserRole.REGULAR.value, rowcount=1
        )
        with patch.object(db, "get_connection", return_value=conn):
            assert db.delete_user("alice") is True

    def test_blocks_deletion_of_last_admin(self):
        db = _make_db()
        conn, _ = self._make_delete_connection(
            admin_count=1, user_role=UserRole.ADMIN.value, rowcount=1
        )
        with patch.object(db, "get_connection", return_value=conn):
            assert db.delete_user("admin") is False

    def test_allows_deletion_of_admin_when_another_admin_exists(self):
        db = _make_db()
        conn, _ = self._make_delete_connection(
            admin_count=2, user_role=UserRole.ADMIN.value, rowcount=1
        )
        with patch.object(db, "get_connection", return_value=conn):
            assert db.delete_user("admin2") is True

    def test_returns_false_when_user_not_found(self):
        db = _make_db()
        conn, _ = self._make_delete_connection(
            admin_count=1, user_role=UserRole.REGULAR.value, rowcount=0
        )
        with patch.object(db, "get_connection", return_value=conn):
            assert db.delete_user("ghost") is False

    def test_returns_false_on_exception(self):
        db = _make_db()
        with patch.object(db, "get_connection", side_effect=Exception("DB down")):
            assert db.delete_user("alice") is False


# ---------------------------------------------------------------------------
# update_user_password_by_admin
# ---------------------------------------------------------------------------


class TestUpdateUserPasswordByAdmin:
    def test_successful_update_returns_true(self):
        db = _make_db()
        conn, _ = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            assert db.update_user_password_by_admin("alice", "newpass") is True

    def test_stores_hashed_password(self):
        db = _make_db()
        conn, cursor = _make_mock_connection(rowcount=1)
        with patch.object(db, "get_connection", return_value=conn):
            db.update_user_password_by_admin("alice", "adminset")
        stored = cursor.execute.call_args[0][1][0]
        assert check_password_hash(stored, "adminset")

    def test_user_not_found_returns_false(self):
        db = _make_db()
        conn, _ = _make_mock_connection(rowcount=0)
        with patch.object(db, "get_connection", return_value=conn):
            assert db.update_user_password_by_admin("ghost", "newpass") is False

    def test_db_exception_returns_false(self):
        db = _make_db()
        with patch.object(db, "get_connection", side_effect=Exception("DB down")):
            assert db.update_user_password_by_admin("alice", "newpass") is False
