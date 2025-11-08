#!/usr/bin/env python3
"""
Test script for SMS notification opt-in feature
Tests that the necessary fields and UI elements are in place
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_profile_template():
    """Test that profile.html contains the SMS notification checkbox."""
    print("Testing profile.html template...")
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'profile.html')
        with open(template_path, 'r') as f:
            content = f.read()
            
            # Check for checkbox
            if 'sms_notifications_enabled' not in content:
                print("✗ SMS notifications checkbox NOT found")
                return False
            print("✓ SMS notifications checkbox found")
            
            # Check for label
            if 'Notification Opt-In' not in content:
                print("✗ Notification Opt-In label NOT found")
                return False
            print("✓ Notification Opt-In label found")
            
            # Check for description about SMS
            if 'SMS notifications about door status changes' not in content:
                print("✗ SMS notification description NOT found")
                return False
            print("✓ SMS notification description found")
            
            # Check for carrier charges mention
            if 'carrier charges may apply' not in content:
                print("✗ Carrier charges warning NOT found")
                return False
            print("✓ Carrier charges warning found")
            
            # Check for disable mention
            if 'unchecking this box' not in content:
                print("✗ Disable instructions NOT found")
                return False
            print("✓ Disable instructions found")
            
        return True
    except Exception as e:
        print(f"✗ Profile template test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_module():
    """Test that database.py has been updated for SMS notifications."""
    print("\nTesting database.py module...")
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'database.py')
        with open(db_path, 'r') as f:
            content = f.read()
            
            # Check for sms_notifications_enabled in table creation
            if 'sms_notifications_enabled BOOLEAN DEFAULT FALSE' not in content:
                print("✗ sms_notifications_enabled column NOT found in table creation")
                return False
            print("✓ sms_notifications_enabled column found in table creation")
            
            # Check for parameter in update_user_profile
            if 'sms_notifications_enabled: bool = False' not in content:
                print("✗ sms_notifications_enabled parameter NOT found in update_user_profile")
                return False
            print("✓ sms_notifications_enabled parameter found in update_user_profile")
            
        return True
    except Exception as e:
        print(f"✗ Database module test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_app_module():
    """Test that app.py has been updated for SMS notifications."""
    print("\nTesting app.py module...")
    try:
        app_path = os.path.join(os.path.dirname(__file__), 'app.py')
        with open(app_path, 'r') as f:
            content = f.read()
            
            # Check for checkbox handling in profile route
            if "sms_notifications_enabled = request.form.get('sms_notifications_enabled') == 'on'" not in content:
                print("✗ SMS notifications checkbox handling NOT found in profile route")
                return False
            print("✓ SMS notifications checkbox handling found in profile route")
            
        return True
    except Exception as e:
        print(f"✗ App module test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_migration_script():
    """Test that migration script exists."""
    print("\nTesting migration script...")
    try:
        migration_path = os.path.join(os.path.dirname(__file__), 'migrate_sms_notifications.py')
        
        if not os.path.exists(migration_path):
            print("✗ Migration script NOT found")
            return False
        print("✓ Migration script exists")
        
        # Check if it's executable
        if not os.access(migration_path, os.X_OK):
            print("✗ Migration script is NOT executable")
            return False
        print("✓ Migration script is executable")
        
        # Check content
        with open(migration_path, 'r') as f:
            content = f.read()
            
            if 'sms_notifications_enabled' not in content:
                print("✗ Migration script does NOT mention sms_notifications_enabled")
                return False
            print("✓ Migration script contains sms_notifications_enabled")
            
        return True
    except Exception as e:
        print(f"✗ Migration script test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("SMS Notification Opt-In Feature Tests")
    print("=" * 60)
    
    tests = [
        test_profile_template,
        test_database_module,
        test_app_module,
        test_migration_script,
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

if __name__ == "__main__":
    sys.exit(main())
