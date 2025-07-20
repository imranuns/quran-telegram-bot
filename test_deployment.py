#!/usr/bin/env python3
"""
Simple test script to verify the Quran Bot deployment and database connectivity.
Run this locally to test your environment variables and JSONBin connection.
"""

import os
import requests
import json

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🔍 Testing Environment Variables...")
    
    required_vars = {
        'TELEGRAM_TOKEN': os.environ.get('TELEGRAM_TOKEN'),
        'ADMIN_ID': os.environ.get('ADMIN_ID'),
        'JSONBIN_API_KEY': os.environ.get('JSONBIN_API_KEY'),
        'JSONBIN_BIN_ID': os.environ.get('JSONBIN_BIN_ID')
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        status = '✅' if var_value else '❌'
        print(f"  {var_name}: {status}")
        if not var_value:
            all_set = False
    
    return all_set

def test_jsonbin_connection():
    """Test JSONBin.io connection"""
    print("\n🔗 Testing JSONBin Connection...")
    
    JSONBIN_API_KEY = os.environ.get('JSONBIN_API_KEY')
    JSONBIN_BIN_ID = os.environ.get('JSONBIN_BIN_ID')
    
    if not JSONBIN_API_KEY or not JSONBIN_BIN_ID:
        print("  ❌ Missing JSONBin credentials")
        return False
    
    headers = {
        'X-Master-Key': JSONBIN_API_KEY,
        'X-Bin-Meta': 'false'
    }
    
    try:
        print(f"  📡 Connecting to bin: {JSONBIN_BIN_ID}")
        response = requests.get(
            f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}',
            headers=headers,
            timeout=10
        )
        
        print(f"  📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Connection successful!")
            print(f"  📋 Current data: {data}")
            return True
        else:
            print(f"  ❌ Connection failed: {response.status_code}")
            print(f"  📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run tests"""
    print("🧪 Quran Bot - Quick Connection Test")
    print("=" * 40)
    
    env_ok = test_environment_variables()
    jsonbin_ok = test_jsonbin_connection()
    
    print("\n" + "=" * 40)
    if env_ok and jsonbin_ok:
        print("🎉 Basic tests passed! Deploy to Vercel and test with /debug command.")
    else:
        print("⚠️ Issues found. Fix them before deploying.")

if __name__ == "__main__":
    main()