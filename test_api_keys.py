#!/usr/bin/env python3
"""
Test script for API key management in DatabaseManager
Tests the get_user_by_api_key and generate_api_key methods
"""

import sys
import os
import hashlib
import secrets

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test constants
TEST_VALID_API_KEY = "test_api_key_12345"
TEST_INVALID_API_KEY = "invalid_api_key"
TEST_INACTIVE_USER_KEY = "inactive_user_key"
TEST_CONSISTENCY_KEY = "consistency_test_key"
TEST_USERNAME = "testuser"
TEST_NONEXISTENT_USERNAME = "nonexistent_user"
TEST_INACTIVE_USERNAME = "inactive_user"
EXPECTED_API_KEY_LENGTH = 64

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    try:
        import unittest.mock as mock
        with mock.patch('database.DatabaseManager.get_connection'):
            with mock.patch('database.DatabaseManager._ensure_database_setup'):
                from database import DatabaseManager
                print("✓ All imports successful")
                return True
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_get_user_by_api_key_valid():
    """Test get_user_by_api_key with a valid API key."""
    print("\nTesting get_user_by_api_key with valid API key...")
    try:
        import unittest.mock as mock
        from database import DatabaseManager
        
        # Create a test API key and its hash
        api_key_hash = hashlib.sha256(TEST_VALID_API_KEY.encode()).hexdigest()
        
        # Mock user data that would be returned from database
        mock_user = {
            'id': 1,
            'username': 'testuser',
            'role': 'regular',
            'is_active': True
        }
        
        # Mock the database connection and cursor
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = mock_user
        mock_cursor.__enter__ = mock.MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = mock.MagicMock(return_value=False)
        
        mock_connection = mock.MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = mock.MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = mock.MagicMock(return_value=False)
        
        with mock.patch.object(DatabaseManager, '_ensure_database_setup'):
            with mock.patch.object(DatabaseManager, '_get_connection_params', return_value={}):
                db = DatabaseManager()
                with mock.patch.object(db, 'get_connection', return_value=mock_connection):
                    result = db.get_user_by_api_key(TEST_VALID_API_KEY)
                    
                    # Verify the result
                    assert result is not None, "Result should not be None"
                    assert result['username'] == 'testuser', "Username should match"
                    assert result['is_active'] == True, "User should be active"
                    
                    # Verify the SQL query was called with correct hash
                    mock_cursor.execute.assert_called_once()
                    call_args = mock_cursor.execute.call_args
                    assert api_key_hash in call_args[0][1], "API key hash should be in query parameters"
                    
                    print("✓ Valid API key test passed")
                    return True
    except Exception as e:
        print(f"✗ Valid API key test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_get_user_by_api_key_invalid():
    """Test get_user_by_api_key with an invalid API key."""
    print("\nTesting get_user_by_api_key with invalid API key...")
    try:
        import unittest.mock as mock
        from database import DatabaseManager
        
        # Mock the database connection to return None (no user found)
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor.__enter__ = mock.MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = mock.MagicMock(return_value=False)
        
        mock_connection = mock.MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = mock.MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = mock.MagicMock(return_value=False)
        
        with mock.patch.object(DatabaseManager, '_ensure_database_setup'):
            with mock.patch.object(DatabaseManager, '_get_connection_params', return_value={}):
                db = DatabaseManager()
                with mock.patch.object(db, 'get_connection', return_value=mock_connection):
                    result = db.get_user_by_api_key(TEST_INVALID_API_KEY)
                    
                    # Verify the result is None
                    assert result is None, "Result should be None for invalid API key"
                    
                    print("✓ Invalid API key test passed")
                    return True
    except Exception as e:
        print(f"✗ Invalid API key test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_get_user_by_api_key_inactive_user():
    """Test get_user_by_api_key with an inactive user."""
    print("\nTesting get_user_by_api_key with inactive user...")
    try:
        import unittest.mock as mock
        from database import DatabaseManager
        
        # Mock the database to return None (inactive users are filtered by SQL query)
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor.__enter__ = mock.MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = mock.MagicMock(return_value=False)
        
        mock_connection = mock.MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = mock.MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = mock.MagicMock(return_value=False)
        
        with mock.patch.object(DatabaseManager, '_ensure_database_setup'):
            with mock.patch.object(DatabaseManager, '_get_connection_params', return_value={}):
                db = DatabaseManager()
                with mock.patch.object(db, 'get_connection', return_value=mock_connection):
                    result = db.get_user_by_api_key(TEST_INACTIVE_USER_KEY)
                    
                    # Verify the result is None (inactive users are not returned)
                    assert result is None, "Result should be None for inactive user"
                    
                    # Verify the SQL query includes the is_active check
                    call_args = mock_cursor.execute.call_args
                    assert 'is_active = TRUE' in call_args[0][0], "Query should filter by is_active"
                    
                    print("✓ Inactive user test passed")
                    return True
    except Exception as e:
        print(f"✗ Inactive user test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_generate_api_key_success():
    """Test successful API key generation."""
    print("\nTesting successful API key generation...")
    try:
        import unittest.mock as mock
        from database import DatabaseManager
        
        # Mock the database connection to simulate successful update
        mock_cursor = mock.MagicMock()
        mock_cursor.rowcount = 1  # 1 row updated
        mock_cursor.__enter__ = mock.MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = mock.MagicMock(return_value=False)
        
        mock_connection = mock.MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = mock.MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = mock.MagicMock(return_value=False)
        
        with mock.patch.object(DatabaseManager, '_ensure_database_setup'):
            with mock.patch.object(DatabaseManager, '_get_connection_params', return_value={}):
                db = DatabaseManager()
                with mock.patch.object(db, 'get_connection', return_value=mock_connection):
                    api_key = db.generate_api_key(TEST_USERNAME)
                    
                    # Verify the API key was generated
                    assert api_key is not None, "API key should be generated"
                    assert isinstance(api_key, str), "API key should be a string"
                    assert len(api_key) == EXPECTED_API_KEY_LENGTH, f"API key should be {EXPECTED_API_KEY_LENGTH} characters (32 bytes hex)"
                    
                    # Verify the update query was called
                    mock_cursor.execute.assert_called_once()
                    call_args = mock_cursor.execute.call_args
                    assert TEST_USERNAME in call_args[0][1], "Username should be in query parameters"
                    
                    print("✓ Successful API key generation test passed")
                    return True
    except Exception as e:
        print(f"✗ Successful API key generation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_generate_api_key_user_not_found():
    """Test generate_api_key with user not found."""
    print("\nTesting generate_api_key with user not found...")
    try:
        import unittest.mock as mock
        from database import DatabaseManager
        
        # Mock the database connection to simulate no rows updated
        mock_cursor = mock.MagicMock()
        mock_cursor.rowcount = 0  # 0 rows updated
        mock_cursor.__enter__ = mock.MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = mock.MagicMock(return_value=False)
        
        mock_connection = mock.MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = mock.MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = mock.MagicMock(return_value=False)
        
        with mock.patch.object(DatabaseManager, '_ensure_database_setup'):
            with mock.patch.object(DatabaseManager, '_get_connection_params', return_value={}):
                db = DatabaseManager()
                with mock.patch.object(db, 'get_connection', return_value=mock_connection):
                    api_key = db.generate_api_key(TEST_NONEXISTENT_USERNAME)
                    
                    # Verify no API key was generated
                    assert api_key is None, "API key should be None when user not found"
                    
                    print("✓ User not found test passed")
                    return True
    except Exception as e:
        print(f"✗ User not found test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_generate_api_key_inactive_user():
    """Test generate_api_key with inactive user."""
    print("\nTesting generate_api_key with inactive user...")
    try:
        import unittest.mock as mock
        from database import DatabaseManager
        
        # Mock the database connection to simulate no rows updated (inactive user filtered)
        mock_cursor = mock.MagicMock()
        mock_cursor.rowcount = 0  # 0 rows updated
        mock_cursor.__enter__ = mock.MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = mock.MagicMock(return_value=False)
        
        mock_connection = mock.MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = mock.MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = mock.MagicMock(return_value=False)
        
        with mock.patch.object(DatabaseManager, '_ensure_database_setup'):
            with mock.patch.object(DatabaseManager, '_get_connection_params', return_value={}):
                db = DatabaseManager()
                with mock.patch.object(db, 'get_connection', return_value=mock_connection):
                    api_key = db.generate_api_key(TEST_INACTIVE_USERNAME)
                    
                    # Verify no API key was generated
                    assert api_key is None, "API key should be None for inactive user"
                    
                    # Verify the SQL query includes the is_active check
                    call_args = mock_cursor.execute.call_args
                    assert 'is_active = TRUE' in call_args[0][0], "Query should filter by is_active"
                    
                    print("✓ Inactive user test passed")
                    return True
    except Exception as e:
        print(f"✗ Inactive user test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_key_hash_consistency():
    """Test that API key hashing is consistent."""
    print("\nTesting API key hash consistency...")
    try:
        import unittest.mock as mock
        from database import DatabaseManager
        
        # Mock the database connection
        mock_cursor = mock.MagicMock()
        mock_cursor.rowcount = 1
        mock_cursor.__enter__ = mock.MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = mock.MagicMock(return_value=False)
        
        mock_connection = mock.MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = mock.MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = mock.MagicMock(return_value=False)
        
        with mock.patch.object(DatabaseManager, '_ensure_database_setup'):
            with mock.patch.object(DatabaseManager, '_get_connection_params', return_value={}):
                db = DatabaseManager()
                
                # Mock secrets.token_hex to return a known value
                with mock.patch('database.secrets.token_hex', return_value=TEST_CONSISTENCY_KEY):
                    with mock.patch.object(db, 'get_connection', return_value=mock_connection):
                        # Generate API key
                        generated_key = db.generate_api_key(TEST_USERNAME)
                        
                        # Get the hash that was stored
                        generate_call_args = mock_cursor.execute.call_args
                        stored_hash = generate_call_args[0][1][0]
                        
                        # Now mock get_user_by_api_key to return the user
                        mock_cursor.reset_mock()
                        mock_user = {'id': 1, 'username': TEST_USERNAME, 'role': 'regular', 'is_active': True}
                        mock_cursor.fetchone.return_value = mock_user
                        
                        # Retrieve user with the generated key
                        retrieved_user = db.get_user_by_api_key(generated_key)
                        
                        # Get the hash used for lookup
                        lookup_call_args = mock_cursor.execute.call_args
                        lookup_hash = lookup_call_args[0][1][0]
                        
                        # Verify hashes match
                        assert stored_hash == lookup_hash, "Hash used for storage and lookup should match"
                        expected_hash = hashlib.sha256(TEST_CONSISTENCY_KEY.encode()).hexdigest()
                        assert stored_hash == expected_hash, "Hash should match expected SHA256"
                        
                        print("✓ API key hash consistency test passed")
                        return True
    except Exception as e:
        print(f"✗ API key hash consistency test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("API Key Management Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_get_user_by_api_key_valid,
        test_get_user_by_api_key_invalid,
        test_get_user_by_api_key_inactive_user,
        test_generate_api_key_success,
        test_generate_api_key_user_not_found,
        test_generate_api_key_inactive_user,
        test_api_key_hash_consistency,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
