#!/usr/bin/env python3
"""
Quran Bot Setup Script
This script helps you configure and test your Telegram Quran Bot.
"""

import os
import sys
import requests
import json
from pathlib import Path

def print_header():
    print("=" * 60)
    print("🕌 QURAN BOT SETUP & CONFIGURATION 🕌")
    print("=" * 60)
    print()

def check_environment():
    print("📋 Checking Environment Variables...")
    print("-" * 40)
    
    required_vars = {
        'TELEGRAM_TOKEN': 'Telegram Bot Token (from @BotFather)',
        'ADMIN_ID': 'Your Telegram User ID (numeric)',
        'CHANNEL_ID': 'Channel ID (optional, with @ prefix)',
        'JSONBIN_API_KEY': 'JSONBin.io API Key',
        'JSONBIN_BIN_ID': 'JSONBin.io Bin ID'
    }
    
    missing_vars = []
    set_vars = []
    
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value and value != f"your_{var.lower()}_here":
            print(f"✅ {var}: SET")
            set_vars.append(var)
        else:
            print(f"❌ {var}: MISSING - {description}")
            missing_vars.append(var)
    
    print()
    if missing_vars:
        print(f"⚠️  Missing {len(missing_vars)} environment variables.")
        print("🔧 Please set these variables in your environment or .env file.")
        return False
    else:
        print("✅ All environment variables are configured!")
        return True

def test_telegram_bot():
    print("🤖 Testing Telegram Bot Connection...")
    print("-" * 40)
    
    token = os.environ.get('TELEGRAM_TOKEN')
    if not token:
        print("❌ TELEGRAM_TOKEN not set")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Bot connected successfully!")
                print(f"   Bot Name: {bot_info.get('first_name')}")
                print(f"   Username: @{bot_info.get('username')}")
                print(f"   Bot ID: {bot_info.get('id')}")
                return True
            else:
                print(f"❌ Telegram API Error: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_jsonbin():
    print("🗄️  Testing JSONBin.io Connection...")
    print("-" * 40)
    
    api_key = os.environ.get('JSONBIN_API_KEY')
    bin_id = os.environ.get('JSONBIN_BIN_ID')
    
    if not api_key or not bin_id:
        print("❌ JSONBin credentials not set")
        return False
    
    try:
        headers = {'X-Master-Key': api_key, 'X-Bin-Meta': 'false'}
        url = f'https://api.jsonbin.io/v3/b/{bin_id}'
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ JSONBin.io connected successfully!")
            data = response.json()
            user_count = len(data.get('users', {}))
            print(f"   Current users in database: {user_count}")
            return True
        else:
            print(f"❌ JSONBin Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_quran_api():
    print("📖 Testing Quran API Connection...")
    print("-" * 40)
    
    try:
        url = "http://api.alquran.cloud/v1/surah/1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                surah_data = data['data']
                print("✅ Quran API connected successfully!")
                print(f"   Test Surah: {surah_data['englishName']}")
                print(f"   Verses: {surah_data['numberOfAyahs']}")
                return True
            else:
                print(f"❌ API Error: {data}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        return False

def create_env_file():
    print("📝 Creating .env file template...")
    print("-" * 40)
    
    env_content = """# Quran Bot Environment Variables
# Fill in the actual values below

# Get this from @BotFather on Telegram
TELEGRAM_TOKEN=your_telegram_bot_token_here

# Your Telegram user ID (numeric)
ADMIN_ID=your_telegram_user_id_here

# Optional: Channel users must join (with @ prefix)
CHANNEL_ID=@your_channel_username

# JSONBin.io credentials (sign up at https://jsonbin.io/)
JSONBIN_API_KEY=your_jsonbin_api_key_here
JSONBIN_BIN_ID=your_jsonbin_bin_id_here
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file successfully!")
        print("📝 Please edit .env file with your actual credentials.")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    if env_file.exists():
        print("📁 Loading .env file...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Environment variables loaded from .env file")

def main():
    print_header()
    
    # Load .env file if it exists
    load_env_file()
    
    # Check environment variables
    env_ok = check_environment()
    print()
    
    if not env_ok:
        print("🔧 Would you like to create a .env file template? (y/n): ", end="")
        try:
            choice = input().lower().strip()
            if choice in ['y', 'yes']:
                create_env_file()
                print()
                print("📋 Next steps:")
                print("1. Edit the .env file with your actual credentials")
                print("2. Run this script again to test the configuration")
                print("3. Start your bot with: python api/index.py")
        except KeyboardInterrupt:
            print("\n👋 Setup cancelled.")
        return
    
    # Run all tests
    print("🧪 Running Connection Tests...")
    print("=" * 60)
    
    tests = [
        ("Telegram Bot", test_telegram_bot),
        ("JSONBin.io", test_jsonbin),
        ("Quran API", test_quran_api)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        result = test_func()
        if result:
            passed += 1
        print()
    
    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Your bot is ready to run.")
        print("🚀 Start your bot with: python api/index.py")
    else:
        print("⚠️  Some tests failed. Please check your configuration.")
        print("📖 Refer to the README or .env.example for setup instructions.")

if __name__ == "__main__":
    main()