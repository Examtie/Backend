import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_admin_login():
    """Test admin login"""
    login_data = {
        "username": "admin@admin.com",
        "password": "admin@admin.com"
    }
    
    response = requests.post(f"{BASE_URL}/auth/api/v1/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_bulk_operations():
    """Test bulk operations"""
    print("🔐 Testing Admin Login...")
    token = test_admin_login()
    
    if not token:
        print("❌ Failed to get admin token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Admin login successful\n")
    
    # Get some user IDs for testing
    print("📋 Getting user IDs for bulk operations...")
    response = requests.get(f"{BASE_URL}/admin/api/v1/users?role=user&limit=3", headers=headers)
    users = response.json()
    user_ids = [user['id'] for user in users[:2]]  # Take only 2 for testing
    print(f"✅ Got {len(user_ids)} user IDs for testing")
    
    # Test bulk role update
    print("\n🔄 Testing bulk role update...")
    bulk_data = {
        "user_ids": user_ids,
        "role": "staff"
    }
    response = requests.patch(f"{BASE_URL}/admin/api/v1/users/bulk/role", json=bulk_data, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Bulk role update successful: {result['updated_count']} users updated")
        print(f"   Message: {result['message']}")
    else:
        print(f"❌ Bulk role update failed: {response.json()}")
    
    # Revert the changes
    print("\n↩️ Reverting role changes...")
    bulk_data["role"] = "user"
    response = requests.patch(f"{BASE_URL}/admin/api/v1/users/bulk/role", json=bulk_data, headers=headers)
    if response.status_code == 200:
        print("✅ Roles reverted successfully")
    
    # Test error cases
    print("\n🚫 Testing bulk operation error cases...")
    
    # Invalid role
    invalid_bulk_data = {
        "user_ids": user_ids,
        "role": "invalid_role"
    }
    response = requests.patch(f"{BASE_URL}/admin/api/v1/users/bulk/role", json=invalid_bulk_data, headers=headers)
    print(f"Invalid role test: {response.status_code} - {'✅' if response.status_code == 400 else '❌'}")
    
    # Too many users (simulate)
    many_ids = ["60" + "0" * 22 + str(i).zfill(2) for i in range(51)]  # Create 51 fake IDs
    too_many_data = {
        "user_ids": many_ids,
        "role": "user"
    }
    response = requests.patch(f"{BASE_URL}/admin/api/v1/users/bulk/role", json=too_many_data, headers=headers)
    print(f"Too many users test: {response.status_code} - {'✅' if response.status_code == 400 else '❌'}")
    
    print("\n🎉 Bulk operations tests completed!")

if __name__ == "__main__":
    test_bulk_operations()
