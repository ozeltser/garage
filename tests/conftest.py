"""
Pytest configuration and shared fixtures for the garage door app tests.

Strategy
--------
We set the three required env-vars so DatabaseManager.__init__ doesn't raise
ValueError, then patch only _ensure_database_setup so no real MySQL
connection is attempted during app startup.

The real DatabaseManager class remains untouched, which means
test_database_manager.py can instantiate it via __new__ and inject mock
connections freely.

For route tests, the mock_db fixture temporarily replaces app.db_manager
with a fresh MagicMock (restored automatically after each test).
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure the project root is importable regardless of how pytest is invoked.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Set minimal env-vars so DatabaseManager._get_connection_params() passes its
# validation check.  These values are never used for a real connection because
# _ensure_database_setup is patched out below.
# ---------------------------------------------------------------------------
os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("DB_NAME", "test_db")

# ---------------------------------------------------------------------------
# Patch _ensure_database_setup before importing the app.  This prevents the
# constructor from attempting a real MySQL connection while still leaving the
# DatabaseManager class itself intact (so __new__ works in DB unit tests).
# ---------------------------------------------------------------------------
_init_patcher = patch("database.DatabaseManager._ensure_database_setup")
_init_patcher.start()

from app import app as _flask_app  # noqa: E402
import app as _app_module  # noqa: E402

_flask_app.config["TESTING"] = True
_flask_app.config["SECRET_KEY"] = "test-secret-key-for-testing"


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def app():
    """Flask application configured for testing."""
    return _flask_app


# ---------------------------------------------------------------------------
# Function-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(app):
    """Unauthenticated test client."""
    with app.test_client() as c:
        yield c


@pytest.fixture
def mock_db():
    """
    Replace app.db_manager with a fresh MagicMock for the duration of
    one test, then restore the original.

    Route tests configure return values on this mock; the real
    DatabaseManager instance is never called during these tests.
    """
    original = _app_module.db_manager
    mock_instance = MagicMock()
    _app_module.db_manager = mock_instance
    yield mock_instance
    _app_module.db_manager = original


@pytest.fixture
def auth_client(app, mock_db):
    """Test client logged in as a regular (non-admin) user."""
    from user_roles import UserRole

    mock_db.get_user_by_username.return_value = {
        "id": 1,
        "username": "testuser",
        "role": UserRole.REGULAR.value,
        "is_active": True,
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone": None,
        "sms_notifications_enabled": False,
        "api_key_hash": None,
        "password_hash": "hashed",
    }

    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["_user_id"] = "testuser"
            sess["_fresh"] = True
        yield c


@pytest.fixture
def admin_client(app, mock_db):
    """Test client logged in as an admin user."""
    from user_roles import UserRole

    mock_db.get_user_by_username.return_value = {
        "id": 2,
        "username": "admin",
        "role": UserRole.ADMIN.value,
        "is_active": True,
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@example.com",
        "phone": None,
        "sms_notifications_enabled": False,
        "api_key_hash": None,
        "password_hash": "hashed",
    }

    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["_user_id"] = "admin"
            sess["_fresh"] = True
        yield c


# ---------------------------------------------------------------------------
# Session lifecycle hook
# ---------------------------------------------------------------------------


def pytest_sessionfinish(session, exitstatus):
    """Stop the module-level patcher when the test session ends."""
    _init_patcher.stop()
