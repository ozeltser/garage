#!/usr/bin/env python3
"""
Test script for API key generation and authentication
Tests the API key functionality without requiring a real database
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all API key related imports work correctly."""
    print("Testing imports...")
    try:
        # Mock database connection to avoid initialization errors
        import unittest.mock as mock
        with mock.patch('database.DatabaseManager._get_connection_params'):
            with mock.patch('database.DatabaseManager._ensure_database_setup'):
                from app import api_key_required, app
                from database import DatabaseManager
                print("✓ All imports successful")
                return True
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_methods():
    """Test that DatabaseManager has all required API key methods."""
    print("\nTesting DatabaseManager API key methods...")
    try:
        from database import DatabaseManager
        
        required_methods = [
            'generate_api_key',
            'get_user_by_api_key',
        ]
        
        for method_name in required_methods:
            if hasattr(DatabaseManager, method_name):
                print(f"✓ Method {method_name} exists")
            else:
                print(f"✗ Method {method_name} NOT found")
                return False
        
        # Check method signatures
        import inspect
        
        # Check generate_api_key signature
        sig = inspect.signature(DatabaseManager.generate_api_key)
        params = list(sig.parameters.keys())
        if 'username' in params:
            print("✓ generate_api_key method accepts 'username' parameter")
        else:
            print("✗ generate_api_key method does NOT accept 'username' parameter")
            return False
        
        # Check get_user_by_api_key signature
        sig = inspect.signature(DatabaseManager.get_user_by_api_key)
        params = list(sig.parameters.keys())
        if 'api_key' in params:
            print("✓ get_user_by_api_key method accepts 'api_key' parameter")
        else:
            print("✗ get_user_by_api_key method does NOT accept 'api_key' parameter")
            return False
        
        return True
    except Exception as e:
        print(f"✗ DatabaseManager methods test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_key_generation():
    """Test API key generation functionality."""
    print("\nTesting API key generation...")
    try:
        import unittest.mock as mock
        from database import DatabaseManager
        import hashlib
        
        # Create a mock database manager
        db_manager = DatabaseManager.__new__(DatabaseManager)
        
        # Mock the connection and cursor
        mock_cursor = mock.MagicMock()
        mock_cursor.rowcount = 1
        mock_connection = mock.MagicMock()
        mock_connection.__enter__ = mock.MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = mock.MagicMock(return_value=False)
        mock_connection.cursor.return_value.__enter__ = mock.MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = mock.MagicMock(return_value=False)
        
        with mock.patch.object(db_manager, 'get_connection', return_value=mock_connection):
            api_key = db_manager.generate_api_key('testuser')
            
            # Verify API key was generated
            if api_key is None:
                print("✗ API key generation returned None")
                return False
            
            # Verify API key is a 64-character hex string (32 bytes as hex)
            if len(api_key) != 64:
                print(f"✗ API key length is {len(api_key)}, expected 64")
                return False
            
            try:
                int(api_key, 16)
                print("✓ API key is valid hex string")
            except ValueError:
                print("✗ API key is not a valid hex string")
                return False
            
            # Verify the database was updated with the hashed API key
            if mock_cursor.execute.called:
                call_args = mock_cursor.execute.call_args
                sql = call_args[0][0]
                params = call_args[0][1]
                
                if 'UPDATE users SET api_key_hash' in sql:
                    print("✓ Database update query is correct")
                else:
                    print("✗ Database update query is incorrect")
                    return False
                
                # Verify the hash is correct
                expected_hash = hashlib.sha256(api_key.encode()).hexdigest()
                if params[0] == expected_hash:
                    print("✓ API key is correctly hashed")
                else:
                    print("✗ API key hash is incorrect")
                    return False
                
                if params[1] == 'testuser':
                    print("✓ Username parameter is correct")
                else:
                    print("✗ Username parameter is incorrect")
                    return False
            else:
                print("✗ Database execute was not called")
                return False
        
        print("✓ API key generation test passed")
        return True
    except Exception as e:
        print(f"✗ API key generation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_key_authentication():
    """Test API key authentication via get_user_by_api_key."""
    print("\nTesting API key authentication...")
    try:
        import unittest.mock as mock
        from database import DatabaseManager
        import hashlib
        
        # Create a mock database manager
        db_manager = DatabaseManager.__new__(DatabaseManager)
        
        # Test with valid API key
        test_api_key = "a" * 64  # 64-character hex string
        test_api_key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()
        
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'username': 'testuser',
            'role': 'regular',
            'is_active': True
        }
        
        mock_connection = mock.MagicMock()
        mock_connection.__enter__ = mock.MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = mock.MagicMock(return_value=False)
        mock_connection.cursor.return_value.__enter__ = mock.MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = mock.MagicMock(return_value=False)
        
        with mock.patch.object(db_manager, 'get_connection', return_value=mock_connection):
            user_data = db_manager.get_user_by_api_key(test_api_key)
            
            # Verify user data was returned
            if user_data is None:
                print("✗ get_user_by_api_key returned None for valid key")
                return False
            
            if user_data.get('username') != 'testuser':
                print("✗ Username is incorrect")
                return False
            
            print("✓ Valid API key returns user data")
            
            # Verify the database query used the hashed API key
            if mock_cursor.execute.called:
                call_args = mock_cursor.execute.call_args
                sql = call_args[0][0]
                params = call_args[0][1]
                
                if 'api_key_hash' in sql and 'is_active = TRUE' in sql:
                    print("✓ Database query is correct")
                else:
                    print("✗ Database query is incorrect")
                    return False
                
                if params[0] == test_api_key_hash:
                    print("✓ API key is correctly hashed in query")
                else:
                    print("✗ API key hash is incorrect in query")
                    return False
            else:
                print("✗ Database execute was not called")
                return False
        
        # Test with invalid API key (user not found)
        mock_cursor.fetchone.return_value = None
        mock_connection = mock.MagicMock()
        mock_connection.__enter__ = mock.MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = mock.MagicMock(return_value=False)
        mock_connection.cursor.return_value.__enter__ = mock.MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = mock.MagicMock(return_value=False)
        
        with mock.patch.object(db_manager, 'get_connection', return_value=mock_connection):
            user_data = db_manager.get_user_by_api_key("invalid_key")
            
            if user_data is not None:
                print("✗ get_user_by_api_key should return None for invalid key")
                return False
            
            print("✓ Invalid API key returns None")
        
        print("✓ API key authentication test passed")
        return True
    except Exception as e:
        print(f"✗ API key authentication test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_key_decorator():
    """Test the api_key_required decorator."""
    print("\nTesting api_key_required decorator...")
    try:
        import unittest.mock as mock
        from flask import Flask
        
        # Mock database connection
        with mock.patch('database.DatabaseManager._get_connection_params'):
            with mock.patch('database.DatabaseManager._ensure_database_setup'):
                from app import api_key_required, app, db_manager
                
                # Create a test route
                @api_key_required
                def test_route():
                    return {'status': 'ok'}
                
                # Test with missing API key
                with app.test_client() as client:
                    # Mock db_manager
                    with mock.patch.object(db_manager, 'get_user_by_api_key') as mock_get_user:
                        # Test missing API key header
                        response = client.get('/api/door_status')
                        if response.status_code != 401:
                            print(f"✗ Missing API key should return 401, got {response.status_code}")
                            return False
                        
                        response_data = response.get_json()
                        if response_data.get('error') != 'Invalid API key':
                            print(f"✗ Error message is incorrect: {response_data}")
                            return False
                        
                        print("✓ Missing API key returns 401 error")
                        
                        # Test with invalid API key
                        mock_get_user.return_value = None
                        response = client.get('/api/door_status', headers={'X-API-Key': 'invalid_key'})
                        if response.status_code != 401:
                            print(f"✗ Invalid API key should return 401, got {response.status_code}")
                            return False
                        
                        print("✓ Invalid API key returns 401 error")
                        
                        # Test with valid API key
                        from user_roles import UserRole
                        mock_get_user.return_value = {
                            'id': 1,
                            'username': 'testuser',
                            'role': UserRole.REGULAR.value,
                            'is_active': True
                        }
                        
                        # Mock the door status function
                        with mock.patch('app._get_door_status') as mock_door_status:
                            mock_door_status.return_value = {'status': 'closed', 'timestamp': '2024-01-01'}
                            
                            response = client.get('/api/door_status', headers={'X-API-Key': 'valid_key'})
                            if response.status_code != 200:
                                print(f"✗ Valid API key should return 200, got {response.status_code}")
                                return False
                            
                            response_data = response.get_json()
                            if 'status' not in response_data:
                                print(f"✗ Response data is missing 'status': {response_data}")
                                return False
                            
                            print("✓ Valid API key returns 200 and data")
        
        print("✓ API key decorator test passed")
        return True
    except Exception as e:
        print(f"✗ API key decorator test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_routes_exist():
    """Test that all API key related routes are registered."""
    print("\nTesting API route registration...")
    try:
        import unittest.mock as mock
        with mock.patch('database.DatabaseManager._get_connection_params'):
            with mock.patch('database.DatabaseManager._ensure_database_setup'):
                from app import app
                
                routes = [rule.rule for rule in app.url_map.iter_rules()]
                
                required_routes = [
                    '/api/door_status',
                    '/generate_api_key',
                ]
                
                for route in required_routes:
                    if route in routes:
                        print(f"✓ Route {route} registered")
                    else:
                        print(f"✗ Route {route} NOT registered")
                        return False
                
                # Verify methods for each route
                for rule in app.url_map.iter_rules():
                    if rule.rule == '/api/door_status':
                        if 'GET' in rule.methods:
                            print("✓ /api/door_status accepts GET requests")
                        else:
                            print("✗ /api/door_status does NOT accept GET requests")
                            return False
                    elif rule.rule == '/generate_api_key':
                        if 'POST' in rule.methods:
                            print("✓ /generate_api_key accepts POST requests")
                        else:
                            print("✗ /generate_api_key does NOT accept POST requests")
                            return False
                
                return True
    except Exception as e:
        print(f"✗ Route registration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_generate_api_key_route():
    """Test the generate_api_key route functionality."""
    print("\nTesting generate_api_key route...")
    try:
        import unittest.mock as mock
        
        with mock.patch('database.DatabaseManager._get_connection_params'):
            with mock.patch('database.DatabaseManager._ensure_database_setup'):
                from app import app, db_manager
                from user_roles import UserRole
                
                with app.test_client() as client:
                    # Test without login (should redirect)
                    response = client.post('/generate_api_key')
                    if response.status_code not in [302, 401]:
                        print(f"✗ Unauthenticated request should redirect or return 401, got {response.status_code}")
                        return False
                    
                    print("✓ Unauthenticated request is rejected")
                    
                    # Test with login
                    with mock.patch('flask_login.utils._get_user') as mock_get_user:
                        mock_user = mock.MagicMock()
                        mock_user.id = 'testuser'
                        mock_user.is_authenticated = True
                        mock_get_user.return_value = mock_user
                        
                        with mock.patch.object(db_manager, 'generate_api_key') as mock_generate:
                            mock_generate.return_value = 'a' * 64
                            
                            # Set up session
                            with client.session_transaction() as sess:
                                sess['_user_id'] = 'testuser'
                            
                            response = client.post('/generate_api_key', follow_redirects=False)
                            if response.status_code != 302:
                                print(f"✗ Authenticated request should redirect, got {response.status_code}")
                                return False
                            
                            print("✓ Authenticated request is processed")
                            
                            # Verify the method was called with correct username
                            if mock_generate.called:
                                call_args = mock_generate.call_args
                                if call_args[0][0] == 'testuser':
                                    print("✓ generate_api_key called with correct username")
                                else:
                                    print(f"✗ generate_api_key called with incorrect username: {call_args[0][0]}")
                                    return False
                            else:
                                print("✗ generate_api_key was not called")
                                return False
        
        print("✓ generate_api_key route test passed")
        return True
    except Exception as e:
        print(f"✗ generate_api_key route test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_profile_template():
    """Test that profile.html contains the API key generation button."""
    print("\nTesting profile.html template for API key section...")
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'profile.html')
        with open(template_path, 'r') as f:
            content = f.read()
            
            # Check for API key section
            if 'API Key' not in content:
                print("✗ API Key section NOT found")
                return False
            print("✓ API Key section found")
            
            # Check for generate button/form
            if 'generate_api_key' not in content:
                print("✗ API key generation form/button NOT found")
                return False
            print("✓ API key generation form/button found")
            
        return True
    except Exception as e:
        print(f"✗ Profile template test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("API Key Implementation Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_database_methods,
        test_api_key_generation,
        test_api_key_authentication,
        test_api_key_decorator,
        test_api_routes_exist,
        test_generate_api_key_route,
        test_profile_template,
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
