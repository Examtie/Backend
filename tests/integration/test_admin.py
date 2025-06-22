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

def run_comprehensive_test():
    """Run comprehensive admin API tests"""
    print("🔐 Testing Admin Login...")
    token = test_admin_login()
    
    if not token:
        print("❌ Failed to get admin token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Admin login successful\n")
    
    # Test 1: List all users with pagination
    print("📋 Testing user listing with pagination...")
    response = requests.get(f"{BASE_URL}/admin/api/v1/users?page=1&limit=3", headers=headers)
    assert response.status_code == 200
    users = response.json()
    print(f"✅ Retrieved {len(users)} users (page 1, limit 3)")
    
    # Test 2: Search users
    print("\n🔍 Testing user search...")
    response = requests.get(f"{BASE_URL}/admin/api/v1/users?search=admin", headers=headers)
    assert response.status_code == 200
    print(f"✅ Search found {len(response.json())} users")
    
    # Test 3: Filter by role
    print("\n👥 Testing role filter...")
    response = requests.get(f"{BASE_URL}/admin/api/v1/users?role=user", headers=headers)
    assert response.status_code == 200
    print(f"✅ Found {len(response.json())} users with 'user' role")
    
    # Test 4: Get user details
    print("\n👤 Testing user detail retrieval...")
    response = requests.get(f"{BASE_URL}/admin/api/v1/users/@data?username=admin@admin.com", headers=headers)
    assert response.status_code == 200
    user_detail = response.json()
    print(f"✅ Retrieved details for user: {user_detail['email']}")
    
    # Test 5: Get system stats
    print("\n📊 Testing system statistics...")
    response = requests.get(f"{BASE_URL}/admin/api/v1/stats", headers=headers)
    assert response.status_code == 200
    stats = response.json()
    print(f"✅ System stats: {stats['users']['total']} total users")
    print(f"   - Admin: {stats['users']['by_role']['admin']}")
    print(f"   - User: {stats['users']['by_role']['user']}")
    print(f"   - Staff: {stats['users']['by_role']['staff']}")
    
    # Test 6: Update user role
    print("\n🔄 Testing role update...")
    # Find a user to update (not admin)
    response = requests.get(f"{BASE_URL}/admin/api/v1/users?role=user&limit=1", headers=headers)
    if response.status_code == 200 and response.json():
        test_user = response.json()[0]
        test_user_id = test_user['id']
        
        role_data = {"role": "staff"}
        response = requests.patch(f"{BASE_URL}/admin/api/v1/users/{test_user_id}/role", json=role_data, headers=headers)
        assert response.status_code == 200
        print(f"✅ Updated user {test_user['email']} role to staff")
        
        # Revert the change
        role_data = {"role": "user"}
        requests.patch(f"{BASE_URL}/admin/api/v1/users/{test_user_id}/role", json=role_data, headers=headers)
    
    # Test 7: Update user profile
    print("\n✏️ Testing profile update...")
    if 'test_user_id' in locals():
        profile_data = {"full_name": "Test User Updated", "bio": "Updated via admin API"}
        response = requests.patch(f"{BASE_URL}/admin/api/v1/users/{test_user_id}", json=profile_data, headers=headers)
        assert response.status_code == 200
        print("✅ User profile updated successfully")
    
    # Test 8: Error handling
    print("\n🚫 Testing error handling...")
    # Invalid user ID
    response = requests.get(f"{BASE_URL}/admin/api/v1/users/@data?user_id=invalid_id", headers=headers)
    assert response.status_code == 400
    print("✅ Invalid user ID handled correctly")
    
    # Invalid role
    invalid_role_data = {"role": "invalid_role"}
    response = requests.patch(f"{BASE_URL}/admin/api/v1/users/{test_user_id}/role", json=invalid_role_data, headers=headers)
    assert response.status_code == 422
    print("✅ Invalid role handled correctly")
    
    print("\n🎉 All admin API tests passed!")
    print("\n📋 Summary of Available Admin Endpoints:")
    print("   GET    /admin/api/v1/users              - List users (with pagination, search, filtering)")
    print("   GET    /admin/api/v1/users/@data        - Get user details by ID or username")
    print("   GET    /admin/api/v1/stats              - Get system statistics")
    print("   PATCH  /admin/api/v1/users/{id}/role    - Update user role")
    print("   PATCH  /admin/api/v1/users/{id}         - Update user profile")
    print("   DELETE /admin/api/v1/users/{id}         - Delete user")
    print("   PATCH  /admin/api/v1/users/bulk/role    - Bulk update user roles")
    print("   DELETE /admin/api/v1/users/bulk         - Bulk delete users")

if __name__ == "__main__":
    run_comprehensive_test()
