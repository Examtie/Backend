#!/usr/bin/env python3
"""
Test script to verify R2 configuration and public access.
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

def test_r2_config():
    print("🔍 Testing R2 Configuration")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["R2_ACCESS_KEY", "R2_SECRET_KEY", "R2_BUCKET_NAME", "R2_ENDPOINT_URL", "R2_ACCOUNT_ID"]
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:10]}..." if len(value) > 10 else f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    # Test public domain construction
    account_id = os.getenv("R2_ACCOUNT_ID")
    public_domain = os.getenv("R2_PUBLIC_DOMAIN")
    
    if public_domain:
        print(f"✅ Using custom public domain: {public_domain}")
    elif account_id:
        constructed_domain = f"https://pub-{account_id[:16]}.r2.dev"
        print(f"✅ Constructed public domain: {constructed_domain}")
    else:
        print("❌ Cannot determine public domain")
    
    # Test a sample file URL (the one from your error)
    test_url = "https://pub-9b972972e4f7c03f.r2.dev/0588c2f6-dcf6-4917-b9b9-f119bacae574_posn1-67-com.pdf"
    print(f"\n🔗 Testing file access: {test_url}")
    
    try:
        response = requests.head(test_url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ File is accessible")
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - Bucket public access is not configured")
        elif response.status_code == 404:
            print("❌ 404 Not Found - File doesn't exist or wrong URL")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    print("\n📋 Next Steps:")
    print("1. Go to Cloudflare Dashboard > R2 Object Storage")
    print("2. Select your 'examtie' bucket")
    print("3. Go to Settings > Public access")
    print("4. Enable 'Allow Access' for public access")
    print("5. Your public URL should be: https://pub-{account_id}.r2.dev")

if __name__ == "__main__":
    test_r2_config()
