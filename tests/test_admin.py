import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_admin_login():
    """Test admin login"""
    login_data = {
        "username": "admin@admin.com",  # OAuth2PasswordRequestForm uses 'username' field for email
        "password": "admin@admin.com"
    }
    
    response = requests.post(f"{BASE_URL}/auth/api/v1/login", data=login_data)  # Use form data, not JSON
    print(f"Login Status: {response.status_code}")
    print(f"Login Response: {response.json()}")
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_admin_routes(token):
    """Test admin routes with authentication"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get all users
    print("\n=== Testing GET /admin/api/v1/users ===")
    response = requests.get(f"{BASE_URL}/admin/api/v1/users", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test get user stats
    print("\n=== Testing GET /admin/api/v1/stats ===")
    response = requests.get(f"{BASE_URL}/admin/api/v1/stats", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test get user detail by username
    print("\n=== Testing GET /admin/api/v1/users/@data with username ===")
    response = requests.get(f"{BASE_URL}/admin/api/v1/users/@data?username=admin@admin.com", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test get user detail by user_id
    print("\n=== Testing GET /admin/api/v1/users/@data with user_id ===")
    admin_user_id = "6852db38ddd3b2f67cfbc483"  # From the users list
    response = requests.get(f"{BASE_URL}/admin/api/v1/users/@data?user_id={admin_user_id}", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test updating user role
    print("\n=== Testing PATCH /admin/api/v1/users/{user_id}/role ===")
    test_user_id = "685158473fd69b7d2e101c81"  # Regular user from the list
    role_data = {"role": "staff"}
    response = requests.patch(f"{BASE_URL}/admin/api/v1/users/{test_user_id}/role", json=role_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test updating user profile
    print("\n=== Testing PATCH /admin/api/v1/users/{user_id} ===")
    profile_data = {"full_name": "Updated Name", "bio": "Updated bio"}
    response = requests.patch(f"{BASE_URL}/admin/api/v1/users/{test_user_id}", json=profile_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test deleting a user (be careful - this actually deletes)
    print("\n=== Testing DELETE /admin/api/v1/users/{user_id} ===")
    # Let's create a test user first to delete safely
    test_user_data = {
        "email": "deleteme@test.com",
        "password": "testpassword123",
        "full_name": "Delete Me User",
        "username": "deletemeuser",
        "roles": ["user"]
    }
    create_response = requests.post(f"{BASE_URL}/auth/api/v1/register", json=test_user_data)
    if create_response.status_code == 200:
        new_user_id = create_response.json()["id"]
        print(f"Created test user with ID: {new_user_id}")
        
        # Now delete the user
        delete_response = requests.delete(f"{BASE_URL}/admin/api/v1/users/{new_user_id}", headers=headers)
        print(f"Delete Status: {delete_response.status_code}")
        print(f"Delete Response: {delete_response.json()}")
    else:
        print(f"Failed to create test user: {create_response.status_code}")
        print(f"Response: {create_response.json()}")

if __name__ == "__main__":
    # Test admin login
    token = test_admin_login()
    
    if token:
        print(f"\nAdmin token received: {token[:20]}...")
        test_admin_routes(token)
    else:
        print("Failed to get admin token")
