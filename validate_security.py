#!/usr/bin/env python3
"""
Security validation script for the Garage Web App.
This script verifies that security best practices are implemented.
"""
import os
import ast
import re

def check_security_implementation():
    """Check that security features are properly implemented."""
    print("Garage Web App - Security Validation")
    print("=" * 40)
    
    security_checks = []
    
    # Check 1: No hardcoded passwords in app.py
    print("1. Checking for hardcoded passwords...")
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    # Check for actual hardcoded password values, not legitimate usage
    hardcoded_patterns = [
        r"password\s*=\s*['\"][^'\"]{3,}['\"]",  # password = "actual_password"
        r"SECRET_KEY\s*=\s*['\"][a-zA-Z0-9-]{10,}['\"]"  # hardcoded secret key
    ]
    
    hardcoded_found = False
    for pattern in hardcoded_patterns:
        if re.search(pattern, app_content, re.IGNORECASE):
            hardcoded_found = True
            break
    
    if not hardcoded_found:
        print("   ✓ No hardcoded secrets found in app.py")
        security_checks.append(True)
    else:
        print("   ✗ Hardcoded secrets found in app.py")
        security_checks.append(False)
    
    # Check 2: Environment variable usage
    print("2. Checking environment variable usage...")
    
    # Check both app.py and database.py
    with open('database.py', 'r') as f:
        db_content = f.read()
    
    env_vars_used = []
    all_content = app_content + db_content
    
    env_patterns = [
        (r"os\.getenv\(['\"]SECRET_KEY['\"]", "SECRET_KEY"),
        (r"os\.getenv\(['\"]DB_HOST['\"]", "DB_HOST"),
        (r"os\.getenv\(['\"]DB_USER['\"]", "DB_USER"),
        (r"os\.getenv\(['\"]DB_PASSWORD['\"]", "DB_PASSWORD"),
        (r"os\.getenv\(['\"]DB_NAME['\"]", "DB_NAME")
    ]
    
    for pattern, var_name in env_patterns:
        if re.search(pattern, all_content):
            env_vars_used.append(var_name)
    
    
    if len(env_vars_used) >= 4:  # At least SECRET_KEY and DB config
        print(f"   ✓ Environment variables used: {', '.join(env_vars_used)}")
        security_checks.append(True)
    else:
        print(f"   ✗ Insufficient environment variable usage: {env_vars_used}")
        security_checks.append(False)
    
    # Check 3: .env file excluded from git
    print("3. Checking .gitignore configuration...")
    try:
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
        
        if '.env' in gitignore_content:
            print("   ✓ .env files excluded from git")
            security_checks.append(True)
        else:
            print("   ✗ .env files not excluded from git")
            security_checks.append(False)
    except FileNotFoundError:
        print("   ✗ .gitignore file not found")
        security_checks.append(False)
    
    # Check 4: Database module uses parameterized queries
    print("4. Checking database security...")
    
    # Look for parameterized queries (using %s placeholders)
    parameterized_queries = db_content.count('execute(') > 0 and '%s' in db_content
    
    if parameterized_queries and 'pymysql' in db_content:
        print("   ✓ Database uses parameterized queries")
        security_checks.append(True)
    else:
        print("   ✗ Database security issues detected")
        security_checks.append(False)
    
    # Check 5: Password hashing
    print("5. Checking password hashing...")
    password_hashing = 'generate_password_hash' in db_content and 'check_password_hash' in db_content
    
    if password_hashing:
        print("   ✓ Password hashing implemented")
        security_checks.append(True)
    else:
        print("   ✗ Password hashing not found")
        security_checks.append(False)
    
    # Check 6: SSL support
    print("6. Checking SSL/TLS support...")
    ssl_support = 'ssl' in db_content.lower() and 'DB_SSL' in db_content
    
    if ssl_support:
        print("   ✓ SSL/TLS support implemented")
        security_checks.append(True)
    else:
        print("   ✗ SSL/TLS support not found")
        security_checks.append(False)
    
    # Check 7: .env.example exists and doesn't contain real secrets
    print("7. Checking .env.example configuration...")
    try:
        with open('.env.example', 'r') as f:
            env_example = f.read()
        
        # Should have placeholders, not real values
        has_placeholders = ('your-secure' in env_example.lower() or 
                          'change-in-production' in env_example.lower() or
                          'your-unique' in env_example.lower())
        
        if has_placeholders and 'DB_HOST' in env_example:
            print("   ✓ .env.example properly configured with placeholders")
            security_checks.append(True)
        else:
            print("   ✗ .env.example issues detected")
            security_checks.append(False)
    except FileNotFoundError:
        print("   ✗ .env.example file not found")
        security_checks.append(False)
    
    # Summary
    print("\n" + "=" * 40)
    passed_checks = sum(security_checks)
    total_checks = len(security_checks)
    
    print(f"Security Validation Results: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("🎉 All security checks passed! Implementation looks secure.")
        return True
    elif passed_checks >= total_checks * 0.8:
        print("⚠️  Most security checks passed. Review failed checks.")
        return True
    else:
        print("❌ Several security issues detected. Please review and fix.")
        return False

if __name__ == "__main__":
    check_security_implementation()