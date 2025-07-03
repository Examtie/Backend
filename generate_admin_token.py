#!/usr/bin/env python3
"""
Quick script to generate an admin token for testing purposes
"""
import sys
import os
sys.path.append('/Users/breadtm/Examtie/Backend')

from app.auth import create_access_token

# Create an admin token
admin_token_data = {
    "sub": "admin@test.com",
    "role": "admin",
    "user_id": "test-admin-id"
}

token = create_access_token(admin_token_data)
print(f"Admin token: {token}")
