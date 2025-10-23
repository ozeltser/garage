#!/usr/bin/env python3
"""
Test script for database connection pooling implementation.
Tests that connection pool is properly initialized and reuses connections.
"""
import sys
import os
import unittest.mock as mock

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_pool_initialization():
    """Test that connection pool is initialized correctly."""
    print("Testing connection pool initialization...")
    
    # Mock environment variables
    test_env = {
        'DB_HOST': 'localhost',
        'DB_PORT': '3306',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'DB_NAME': 'test_db',
        'DB_POOL_SIZE': '5',
        'DB_POOL_MAX_CONNECTIONS': '10'
    }
    
    try:
        with mock.patch.dict(os.environ, test_env):
            # Mock pymysql.connect to prevent actual database connection
            with mock.patch('pymysql.connect') as mock_connect:
                # Mock the PooledDB class to track initialization
                with mock.patch('database.PooledDB') as mock_pooled_db:
                    # Configure the mock to return a mock pool
                    mock_pool_instance = mock.MagicMock()
                    mock_pooled_db.return_value = mock_pool_instance
                    
                    # Import and initialize DatabaseManager
                    from database import DatabaseManager
                    
                    # Create DatabaseManager instance (with mocked pool)
                    db_manager = DatabaseManager()
                    
                    # Verify PooledDB was called
                    assert mock_pooled_db.called, "PooledDB was not initialized"
                    print("✓ PooledDB was initialized")
                    
                    # Verify pool configuration
                    call_kwargs = mock_pooled_db.call_args[1]
                    assert call_kwargs['maxconnections'] == 10, "Max connections not set correctly"
                    print("✓ Max connections set to 10")
                    
                    assert call_kwargs['mincached'] == 5, "Min cached connections not set correctly"
                    print("✓ Min cached connections set to 5")
                    
                    assert call_kwargs['maxcached'] == 5, "Max cached connections not set correctly"
                    print("✓ Max cached connections set to 5")
                    
                    assert call_kwargs['blocking'] == True, "Blocking not set correctly"
                    print("✓ Blocking mode enabled")
                    
                    assert call_kwargs['ping'] == 1, "Ping not set correctly"
                    print("✓ Connection health check enabled")
                    
                    # Verify pool is stored in db_manager
                    assert hasattr(db_manager, 'pool'), "Pool not stored in DatabaseManager"
                    print("✓ Connection pool stored in DatabaseManager")
                    
                    return True
                    
    except Exception as e:
        print(f"✗ Connection pool initialization test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_pool_get_connection():
    """Test that get_connection retrieves from pool."""
    print("\nTesting connection retrieval from pool...")
    
    test_env = {
        'DB_HOST': 'localhost',
        'DB_PORT': '3306',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'DB_NAME': 'test_db',
    }
    
    try:
        with mock.patch.dict(os.environ, test_env):
            with mock.patch('pymysql.connect') as mock_connect:
                with mock.patch('database.PooledDB') as mock_pooled_db:
                    # Create a mock connection
                    mock_connection = mock.MagicMock()
                    
                    # Create a mock pool that returns our mock connection
                    mock_pool_instance = mock.MagicMock()
                    mock_pool_instance.connection.return_value = mock_connection
                    mock_pooled_db.return_value = mock_pool_instance
                    
                    from database import DatabaseManager
                    db_manager = DatabaseManager()
                    
                    # Get a connection
                    conn = db_manager.get_connection()
                    
                    # Verify pool.connection() was called
                    assert mock_pool_instance.connection.called, "Pool connection method not called"
                    print("✓ Connection retrieved from pool")
                    
                    # Verify the returned connection is from the pool
                    assert conn == mock_connection, "Returned connection is not from pool"
                    print("✓ Returned connection is from the pool")
                    
                    return True
                    
    except Exception as e:
        print(f"✗ Connection retrieval test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_pool_default_values():
    """Test that default pool values are used when env vars not set."""
    print("\nTesting default pool configuration values...")
    
    test_env = {
        'DB_HOST': 'localhost',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'DB_NAME': 'test_db',
        # No pool size or max connections set
    }
    
    try:
        with mock.patch.dict(os.environ, test_env, clear=True):
            with mock.patch('pymysql.connect') as mock_connect:
                with mock.patch('database.PooledDB') as mock_pooled_db:
                    mock_pool_instance = mock.MagicMock()
                    mock_pooled_db.return_value = mock_pool_instance
                    
                    from database import DatabaseManager
                    db_manager = DatabaseManager()
                    
                    # Verify default values were used
                    call_kwargs = mock_pooled_db.call_args[1]
                    
                    # Default pool size should be 5
                    assert call_kwargs['mincached'] == 5, "Default min cached not 5"
                    print("✓ Default min cached connections is 5")
                    
                    # Default max connections should be 10
                    assert call_kwargs['maxconnections'] == 10, "Default max connections not 10"
                    print("✓ Default max connections is 10")
                    
                    return True
                    
    except Exception as e:
        print(f"✗ Default values test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("Database Connection Pooling Tests")
    print("=" * 60)
    
    tests = [
        test_pool_initialization,
        test_pool_get_connection,
        test_pool_default_values,
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
        print("\n✓ All connection pooling tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
