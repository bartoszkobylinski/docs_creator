#!/usr/bin/env python3
"""Test script to verify UML Confluence publishing routes."""

import requests
import json

# Test the API endpoints
base_url = "http://localhost:5000"

print("Testing UML Confluence Publishing Routes...")
print("=" * 50)

# Test 1: Check if Confluence status endpoint exists
print("\n1. Testing Confluence status endpoint...")
try:
    response = requests.get(f"{base_url}/api/confluence/status")
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   Connection Error: {e}")

# Test 2: Check if UML publish endpoint exists
print("\n2. Testing UML publish endpoint (without data)...")
try:
    response = requests.post(
        f"{base_url}/api/confluence/publish-uml",
        json={"diagram_data": {}, "title_suffix": "test"},
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status Code: {response.status_code}")
    if response.status_code in [200, 400, 500]:
        print(f"   Response: {response.json()}")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   Connection Error: {e}")

# Test 3: Check if UML page exists
print("\n3. Testing UML page endpoint...")
try:
    response = requests.get(f"{base_url}/uml")
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ UML page loads successfully")
    else:
        print(f"   Error: Status {response.status_code}")
except Exception as e:
    print(f"   Connection Error: {e}")

print("\n" + "=" * 50)
print("Test complete!")