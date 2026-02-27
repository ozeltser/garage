"""
Tests for the User model class (defined in app.py).

The User class wraps Flask-Login's UserMixin and adds role-based helpers.
"""
import pytest
from user_roles import UserRole


# Import User from the already-patched app module (DB mock is in conftest.py).
from app import User


class TestUserCreation:
    """User instances are created with correct attributes."""

    def test_id_is_username(self):
        user = User("alice", user_id=1, role=UserRole.REGULAR.value)
        assert user.id == "alice"

    def test_user_id_stored(self):
        user = User("alice", user_id=42, role=UserRole.REGULAR.value)
        assert user.user_id == 42

    def test_role_stored(self):
        user = User("alice", user_id=1, role=UserRole.ADMIN.value)
        assert user.role == UserRole.ADMIN.value

    def test_default_role_is_regular_when_none_passed(self):
        user = User("alice", user_id=1, role=None)
        assert user.role == UserRole.REGULAR.value

    def test_default_role_when_role_omitted(self):
        user = User("alice", user_id=1)
        assert user.role == UserRole.REGULAR.value


class TestUserIsAdmin:
    """is_admin() correctly reflects the user's role."""

    def test_admin_user_is_admin(self):
        user = User("admin", user_id=1, role=UserRole.ADMIN.value)
        assert user.is_admin() is True

    def test_regular_user_is_not_admin(self):
        user = User("regular", user_id=2, role=UserRole.REGULAR.value)
        assert user.is_admin() is False

    def test_default_user_is_not_admin(self):
        user = User("regular")
        assert user.is_admin() is False


class TestUserMixinIntegration:
    """User inherits Flask-Login's UserMixin correctly."""

    def test_is_authenticated_true(self):
        """UserMixin provides is_authenticated = True by default."""
        user = User("alice", user_id=1)
        assert user.is_authenticated is True

    def test_is_active_true(self):
        user = User("alice", user_id=1)
        assert user.is_active is True

    def test_is_anonymous_false(self):
        user = User("alice", user_id=1)
        assert user.is_anonymous is False

    def test_get_id_returns_username(self):
        """get_id() is used by Flask-Login; it should return the user's id."""
        user = User("alice", user_id=1)
        assert user.get_id() == "alice"
