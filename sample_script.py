#!/usr/bin/env python3
"""
Sample Python script for the Garage App
This script demonstrates what can be executed from the web interface.
"""

import datetime
import platform
import os

def main():
    print("🚗 Garage App Script Execution")
    print("=" * 40)
    print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Current Directory: {os.getcwd()}")
    print(f"User: {os.getenv('USER', 'Unknown')}")
    print("=" * 40)
    
    # Simulate some work
    print("Performing system check...")
    
    # Check disk space
    import shutil
    total, used, free = shutil.disk_usage('/')
    print(f"Disk Usage:")
    print(f"  Total: {total // (2**30)} GB")
    print(f"  Used: {used // (2**30)} GB")
    print(f"  Free: {free // (2**30)} GB")
    
    print("\n✅ Script completed successfully!")
    print("You can customize this script to perform any server-side tasks.")

if __name__ == "__main__":
    main()