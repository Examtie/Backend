#!/usr/bin/env python3
"""
Script to help find your Cloudflare Account ID for R2 configuration.

Run this script and follow the instructions to get your account ID.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🔍 Cloudflare R2 Account ID Helper")
    print("=" * 50)
    
    print("\nTo find your Cloudflare Account ID:")
    print("1. Go to https://dash.cloudflare.com/")
    print("2. Login to your account")
    print("3. Click on 'R2 Object Storage' in the sidebar")
    print("4. Go to 'Manage R2 API tokens'")
    print("5. Your Account ID will be displayed at the top of the page")
    print("   (It's a 32-character string like: abcd1234efgh5678ijkl9012mnop3456)")
    
    print("\nAlternatively:")
    print("1. Go to any Cloudflare dashboard page")
    print("2. Look at the URL - it will be like:")
    print("   https://dash.cloudflare.com/{account-id}/...")
    print("3. The account ID is the part after dash.cloudflare.com/")
    
    current_account_id = os.getenv("R2_ACCOUNT_ID")
    if current_account_id:
        print(f"\n✅ Current R2_ACCOUNT_ID in .env: {current_account_id}")
    else:
        print(f"\n❌ R2_ACCOUNT_ID not found in .env file")
        
        account_id = input("\nEnter your Account ID (or press Enter to skip): ").strip()
        
        if account_id:
            # Add to .env file
            try:
                with open('.env', 'a') as f:
                    f.write(f"\nR2_ACCOUNT_ID={account_id}\n")
                print(f"✅ Added R2_ACCOUNT_ID to .env file")
                print("Please restart your server for the changes to take effect.")
            except Exception as e:
                print(f"❌ Error writing to .env file: {e}")
                print(f"Please manually add this line to your .env file:")
                print(f"R2_ACCOUNT_ID={account_id}")

if __name__ == "__main__":
    main()
