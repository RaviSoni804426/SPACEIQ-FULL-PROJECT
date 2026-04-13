#!/usr/bin/env python3
"""
Test script to verify login is working correctly.
Run: python TEST_LOGIN.py
"""
import requests
import json

BACKEND_URL = "http://localhost:8000"

# Test credentials
test_users = [
    {"email": "user1@spaceiq.demo", "password": "Demo1234!", "name": "User 1"},
    {"email": "admin@spaceiq.demo", "password": "Admin1234!", "name": "Admin"},
    {"email": "kumarsoniravi705@gmail.com", "password": "Ravi@123", "name": "Super Admin"},
]

print("=" * 60)
print("SPACEIQ LOGIN TEST")
print("=" * 60)

for user in test_users:
    print(f"\n🔐 Testing {user['name']}...")
    print(f"   Email: {user['email']}")
    print(f"   Password: {user['password']}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": user['email'], "password": user['password']},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token", "")
            print(f"   ✅ SUCCESS - Token: {token[:20]}...")
        else:
            print(f"   ❌ FAILED - {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {str(e)}")

print("\n" + "=" * 60)
print("If all tests show ✅, login credentials are working!")
print("=" * 60)
