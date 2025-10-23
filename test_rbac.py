#!/usr/bin/env python3
"""
Test script for RBAC implementation
Tests the database schema and basic functionality without requiring a real database
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    try:
        # Mock database connection to avoid initialization errors
        import unittest.mock as mock
        with mock.patch('database.DatabaseManager.get_connection'):
            with mock.patch('database.DatabaseManager._ensure_database_setup'):
                from app import User, admin_required, app
                from database import DatabaseManager
                print("✓ All imports successful")
                return True
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_user_class():
    """Test the User class with roles."""
    print("\nTesting User class...")
    try:
        import unittest.mock as mock
        with mock.patch('database.DatabaseManager.get_connection'):
            with mock.patch('database.DatabaseManager._ensure_database_setup'):
                from app import User
                from user_roles import UserRole
                
                # Test regular user
                regular_user = User('testuser', 1, UserRole.REGULAR.value)
                assert regular_user.role == UserRole.REGULAR.value
                assert regular_user.is_admin() == False
                print("✓ Regular user creation and is_admin() check passed")
                
                # Test admin user
                admin_user = User('admin', 2, UserRole.ADMIN.value)
                assert admin_user.role == UserRole.ADMIN.value
                assert admin_user.is_admin() == True
                print("✓ Admin user creation and is_admin() check passed")
                
                # Test default role
                default_user = User('default', 3)
                assert default_user.role == UserRole.REGULAR.value
                assert default_user.is_admin() == False
                print("✓ Default role assignment passed")
                
                return True
    except Exception as e:
        print(f"✗ User class test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_routes_exist():
    """Test that all RBAC routes are registered."""
    print("\nTesting route registration...")
    try:
        import unittest.mock as mock
        with mock.patch('database.DatabaseManager.get_connection'):
            with mock.patch('database.DatabaseManager._ensure_database_setup'):
                from app import app
                
                routes = [rule.rule for rule in app.url_map.iter_rules()]
                
                required_routes = [
                    '/admin',
                    '/admin/create_user',
                    '/admin/delete_user/<username>',
                    '/admin/change_password/<username>'
                ]
                
                for route in required_routes:
                    if route in routes:
                        print(f"✓ Route {route} registered")
                    else:
                        print(f"✗ Route {route} NOT registered")
                        return False
                
                return True
    except Exception as e:
        print(f"✗ Route registration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_methods():
    """Test that DatabaseManager has all required methods."""
    print("\nTesting DatabaseManager methods...")
    try:
        from database import DatabaseManager
        
        required_methods = [
            'get_all_users',
            'delete_user',
            'update_user_password_by_admin',
            'create_user',
        ]
        
        for method_name in required_methods:
            if hasattr(DatabaseManager, method_name):
                print(f"✓ Method {method_name} exists")
            else:
                print(f"✗ Method {method_name} NOT found")
                return False
        
        # Check create_user signature accepts role parameter
        import inspect
        sig = inspect.signature(DatabaseManager.create_user)
        params = list(sig.parameters.keys())
        if 'role' in params:
            print("✓ create_user method accepts 'role' parameter")
        else:
            print("✗ create_user method does NOT accept 'role' parameter")
            return False
        
        return True
    except Exception as e:
        print(f"✗ DatabaseManager methods test failed: {str(e)}")
        return False

def test_templates_exist():
    """Test that all required templates exist."""
    print("\nTesting template files...")
    try:
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        required_templates = [
            'admin.html',
            'create_user.html',
            'change_password.html',
            'dashboard.html',
            'profile.html'
        ]
        
        for template in required_templates:
            template_path = os.path.join(templates_dir, template)
            if os.path.exists(template_path):
                print(f"✓ Template {template} exists")
            else:
                print(f"✗ Template {template} NOT found")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Template test failed: {str(e)}")
        return False

def test_admin_link_in_templates():
    """Test that admin link is present in templates."""
    print("\nTesting admin link in templates...")
    try:
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        templates_to_check = ['dashboard.html', 'profile.html']
        
        for template in templates_to_check:
            template_path = os.path.join(templates_dir, template)
            with open(template_path, 'r') as f:
                content = f.read()
                if "current_user.is_admin()" in content and "url_for('admin')" in content:
                    print(f"✓ Admin link found in {template}")
                else:
                    print(f"✗ Admin link NOT found in {template}")
                    return False
        
        return True
    except Exception as e:
        print(f"✗ Admin link test failed: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("RBAC Implementation Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_user_class,
        test_routes_exist,
        test_database_methods,
        test_templates_exist,
        test_admin_link_in_templates,
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
