#!/usr/bin/env python3

import requests

base_url = "http://localhost"
session = requests.Session()

# Step 1: Login
print("Step 1: Authenticating...")
auth_response = session.post(
    f"{base_url}/auth",
    data={"username": "admin", "password": "admin123"},
    allow_redirects=False
)
print(f"Auth status: {auth_response.status_code}")
print(f"Auth headers: {dict(auth_response.headers)}")
print(f"Session cookies after auth: {session.cookies}")
print(f"Session cookies dict: {session.cookies.get_dict()}")

# Step 2: Verify
print("\nStep 2: Verifying...")
verify_response = session.get(f"{base_url}/verify")
print(f"Verify status: {verify_response.status_code}")
print(f"Verify response: {verify_response.text}")
print(f"Request headers sent: {verify_response.request.headers}")
print(f"Session cookies during verify: {session.cookies}")

# Step 3: Try manually setting cookie
print("\nStep 3: Manual cookie test...")
manual_response = requests.get(
    f"{base_url}/verify",
    cookies=session.cookies
)
print(f"Manual verify status: {manual_response.status_code}")
print(f"Manual verify response: {manual_response.text}")