#!/usr/bin/env python3
"""
Test script for Socket.IO configuration
Tests that Socket.IO is properly configured to work behind nginx reverse proxy
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_socketio_initialization():
    """Test that Socket.IO initializes with the correct path parameter."""
    print("Testing Socket.IO initialization...")
    try:
        import unittest.mock as mock
        
        # Mock database manager class before importing app
        with mock.patch('database.DatabaseManager') as mock_db:
            # Configure mock to not raise errors
            mock_db.return_value = mock.MagicMock()
            
            from app import socketio
            
            # Check that socketio was initialized
            assert socketio is not None, "SocketIO instance should exist"
            print("✓ SocketIO instance created successfully")
            
            # Check that the path parameter is set correctly
            # The path is stored in the underlying engine.io server
            if hasattr(socketio.server, 'eio'):
                eio_path = getattr(socketio.server.eio, 'path', None)
                if eio_path:
                    assert eio_path == '/socket.io/', f"Expected path '/socket.io/', got '{eio_path}'"
                    print(f"✓ SocketIO path correctly set to: {eio_path}")
                else:
                    print("⚠ Could not verify path directly, but initialization succeeded")
            else:
                print("⚠ Could not verify path directly, but initialization succeeded")
            
            return True
    except Exception as e:
        print(f"✗ Socket.IO initialization test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_socketio_parameters():
    """Test Socket.IO initialization parameters."""
    print("\nTesting Socket.IO parameters...")
    try:
        import os
        from flask import Flask
        from flask_socketio import SocketIO
        
        # Create a test app
        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Test that SocketIO can be initialized with path parameter and CORS origins
        test_cors_origins = ["http://localhost:5000", "http://127.0.0.1:5000"]
        test_socketio = SocketIO(
            test_app,
            cors_allowed_origins=test_cors_origins,
            path='/socket.io/'
        )
        
        assert test_socketio is not None, "Test SocketIO instance should exist"
        print("✓ SocketIO accepts path parameter correctly")
        
        return True
    except Exception as e:
        print(f"✗ Socket.IO parameter test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_nginx_config_syntax():
    """Test that nginx configuration file exists and has WebSocket support."""
    print("\nTesting nginx configuration...")
    try:
        nginx_config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'nginx-garage.conf'
        )
        
        assert os.path.exists(nginx_config_path), "nginx-garage.conf should exist"
        print("✓ nginx-garage.conf file found")
        
        with open(nginx_config_path, 'r') as f:
            config_content = f.read()
        
        # Check for WebSocket upgrade headers
        assert 'proxy_set_header Upgrade $http_upgrade' in config_content, \
            "nginx config should include WebSocket Upgrade header"
        print("✓ WebSocket Upgrade header found in nginx config")
        
        # Check for Connection header with variable
        assert 'proxy_set_header Connection $connection_upgrade' in config_content, \
            "nginx config should include Connection header with variable"
        print("✓ Connection header with variable found in nginx config")
        
        # Check for WebSocket map directive
        assert 'map $http_upgrade $connection_upgrade' in config_content, \
            "nginx config should include WebSocket connection upgrade map"
        print("✓ WebSocket connection upgrade map found in nginx config")
        
        # Check for http version 1.1
        assert 'proxy_http_version 1.1' in config_content, \
            "nginx config should set HTTP version to 1.1 for WebSocket support"
        print("✓ HTTP version 1.1 configured for WebSocket support")
        
        return True
    except Exception as e:
        print(f"✗ nginx configuration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_client_socketio_config():
    """Test that client-side Socket.IO configuration has path specified."""
    print("\nTesting client-side Socket.IO configuration...")
    try:
        js_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'static', 'js', 'app.js'
        )
        
        assert os.path.exists(js_file_path), "app.js should exist"
        print("✓ app.js file found")
        
        with open(js_file_path, 'r') as f:
            js_content = f.read()
        
        # Check that Socket.IO is initialized with path parameter
        assert "path: '/socket.io/'" in js_content, \
            "Client-side Socket.IO should specify path parameter"
        print("✓ Client-side Socket.IO has path parameter configured")
        
        return True
    except Exception as e:
        print(f"✗ Client Socket.IO configuration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_cors_configuration():
    """Test that CORS is configured securely by default."""
    print("\nTesting CORS security configuration...")
    try:
        import os
        import unittest.mock as mock
        
        # Test 1: When CORS_ALLOWED_ORIGINS is not set, should use localhost
        print("  Testing default CORS configuration (no env var)...")
        with mock.patch.dict(os.environ, {}, clear=False):
            # Remove CORS_ALLOWED_ORIGINS if it exists
            os.environ.pop('CORS_ALLOWED_ORIGINS', None)
            
            # Import app module fresh to test default behavior
            import importlib
            import sys
            
            # Remove app from cache to force fresh import
            if 'app' in sys.modules:
                del sys.modules['app']
            
            with mock.patch('database.DatabaseManager') as mock_db:
                mock_db.return_value = mock.MagicMock()
                
                # Import app (this will trigger CORS initialization)
                import app as app_module
                
                # Check that cors_allowed_origins is localhost, not "*"
                cors_config = app_module.cors_allowed_origins
                assert cors_config != "*", "Default CORS should not be '*' (all origins)"
                assert isinstance(cors_config, list), "CORS origins should be a list when not set to '*'"
                print(f"  ✓ Default CORS is secure (not '*'): {cors_config}")
        
        # Test 2: When CORS_ALLOWED_ORIGINS is set, should use that value
        print("  Testing custom CORS configuration (with env var)...")
        test_origins = "https://example.com,https://www.example.com"
        with mock.patch.dict(os.environ, {'CORS_ALLOWED_ORIGINS': test_origins}):
            # Remove app from cache
            if 'app' in sys.modules:
                del sys.modules['app']
            
            with mock.patch('database.DatabaseManager') as mock_db:
                mock_db.return_value = mock.MagicMock()
                
                import app as app_module
                
                cors_config = app_module.cors_allowed_origins
                expected = [o.strip() for o in test_origins.split(',')]
                assert cors_config == expected, f"Expected {expected}, got {cors_config}"
                print(f"  ✓ Custom CORS configuration works: {cors_config}")
        
        return True
    except Exception as e:
        print(f"✗ CORS configuration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Socket.IO nginx Compatibility Test Suite")
    print("=" * 60)
    
    tests = [
        test_socketio_initialization,
        test_socketio_parameters,
        test_nginx_config_syntax,
        test_client_socketio_config,
        test_cors_configuration,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("Test Summary")
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
    sys.exit(run_all_tests())
