"""
Tests for the UserRole enum (user_roles.py).

Covers role values, validation, and default role logic.
"""
import pytest
from user_roles import UserRole


class TestUserRoleValues:
    """Enum values match the expected strings stored in the database."""

    def test_admin_value(self):
        assert UserRole.ADMIN.value == "admin"

    def test_regular_value(self):
        assert UserRole.REGULAR.value == "regular"

    def test_enum_has_exactly_two_roles(self):
        assert len(list(UserRole)) == 2


class TestUserRoleIsValid:
    """UserRole.is_valid() correctly accepts and rejects role strings."""

    def test_admin_string_is_valid(self):
        assert UserRole.is_valid("admin") is True

    def test_regular_string_is_valid(self):
        assert UserRole.is_valid("regular") is True

    def test_unknown_role_is_invalid(self):
        assert UserRole.is_valid("superuser") is False

    def test_empty_string_is_invalid(self):
        assert UserRole.is_valid("") is False

    def test_none_is_invalid(self):
        # is_valid compares against enum values (strings); None should not match
        assert UserRole.is_valid(None) is False

    def test_uppercase_admin_is_invalid(self):
        """Role validation is case-sensitive – DB stores lowercase."""
        assert UserRole.is_valid("Admin") is False
        assert UserRole.is_valid("ADMIN") is False

    def test_uppercase_regular_is_invalid(self):
        assert UserRole.is_valid("Regular") is False
        assert UserRole.is_valid("REGULAR") is False


class TestUserRoleGetDefault:
    """get_default() always returns the REGULAR role."""

    def test_get_default_returns_regular(self):
        assert UserRole.get_default() == UserRole.REGULAR

    def test_get_default_value_is_regular_string(self):
        assert UserRole.get_default().value == "regular"
