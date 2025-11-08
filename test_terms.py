#!/usr/bin/env python3
"""
Test script for Terms and Conditions page
Tests that the route exists and returns successfully
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_terms_route():
    """Test that the terms and conditions route exists and returns 200."""
    print("Testing terms and conditions route...")
    try:
        import unittest.mock as mock
        
        # Mock database manager class before importing app
        with mock.patch('database.DatabaseManager') as mock_db:
            # Configure mock to not raise errors
            mock_db.return_value = mock.MagicMock()
            
            from app import app
            
            # Create test client
            with app.test_client() as client:
                # Test the route
                response = client.get('/terms-and-conditions')
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                
                # Check that the response contains expected content
                data = response.data.decode('utf-8')
                assert 'Terms and Conditions for home.azuriki.com' in data, "Page title not found in response"
                assert 'November 7, 2025' in data, "Last Updated date not found in response"
                assert 'Account Access and Security' in data, "Section 1 heading not found"
                assert 'home@azuriki.com' in data, "Contact email not found"
                
                print("✓ Terms and conditions route test passed")
                print(f"  - Route returns 200 OK")
                print(f"  - Page contains correct title and content")
                return True
    except Exception as e:
        print(f"✗ Terms and conditions route test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Terms and Conditions Implementation")
    print("=" * 60)
    
    results = []
    results.append(test_terms_route())
    
    print("\n" + "=" * 60)
    if all(results):
        print("All tests passed! ✓")
        return 0
    else:
        print("Some tests failed! ✗")
        return 1

if __name__ == '__main__':
    sys.exit(main())
