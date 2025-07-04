#!/usr/bin/env python3
"""
Debug script to check R2 configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables from the Backend directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

print("🔍 R2 Configuration Debug")
print("=" * 50)

# Check all R2 related environment variables
r2_vars = [
    "R2_ACCESS_KEY",
    "R2_SECRET_KEY", 
    "R2_BUCKET_NAME",
    "R2_ENDPOINT_URL",
    "R2_ACCOUNT_ID",
    "R2_REGION",
    "R2_PUBLIC_DOMAIN"
]

for var in r2_vars:
    value = os.getenv(var)
    if var in ["R2_ACCESS_KEY", "R2_SECRET_KEY"]:
        # Mask sensitive data
        masked_value = f"{value[:8]}...{value[-4:]}" if value else None
        print(f"{var}: {masked_value}")
    else:
        print(f"{var}: {value}")

print("\n" + "=" * 50)

# Test the public domain construction logic
account_id = os.getenv("R2_ACCOUNT_ID")
public_domain = os.getenv("R2_PUBLIC_DOMAIN")

print(f"Account ID: {account_id}")
print(f"Public Domain (from env): {public_domain}")

if account_id:
    constructed_domain = f"pub-{account_id[:16]}.r2.dev"
    print(f"Constructed Domain (first 16 chars): {constructed_domain}")

# Test the logic from r2_client.py
if public_domain:
    if public_domain.startswith("http"):
        final_endpoint = public_domain
    else:
        final_endpoint = f"https://{public_domain}"
    print(f"Final Public Endpoint: {final_endpoint}")
elif account_id:
    final_endpoint = f"https://pub-{account_id[:16]}.r2.dev"
    print(f"Final Public Endpoint (fallback): {final_endpoint}")
else:
    print("❌ No public endpoint could be determined")
