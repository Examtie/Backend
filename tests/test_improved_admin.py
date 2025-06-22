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

def test_improved_admin_routes(token):
    """Test improved admin routes with authentication"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test pagination
    print("\n=== Testing GET /admin/api/v1/users with pagination ===")
    response = requests.get(f"{BASE_URL}/admin/api/v1/users?page=1&limit=5", headers=headers)
    print(f"Status: {response.status_code}")
    users = response.json()
    print(f"Number of users returned: {len(users)}")
    
    # Test search
    print("\n=== Testing GET /admin/api/v1/users with search ===")
    response = requests.get(f"{BASE_URL}/admin/api/v1/users?search=admin", headers=headers)
    print(f"Status: {response.status_code}")
    users = response.json()
    print(f"Search results: {len(users)} users")
    
    # Test role filter
    print("\n=== Testing GET /admin/api/v1/users with role filter ===")
    response = requests.get(f"{BASE_URL}/admin/api/v1/users?role=admin", headers=headers)
    print(f"Status: {response.status_code}")
    users = response.json()
    print(f"Admin users: {len(users)}")
    
    # Test improved stats
    print("\n=== Testing GET /admin/api/v1/stats (improved) ===")
    response = requests.get(f"{BASE_URL}/admin/api/v1/stats", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test improved role update
    print("\n=== Testing PATCH /admin/api/v1/users/{user_id}/role (improved) ===")
    test_user_id = "685158473fd69b7d2e101c81"  # Regular user from the list
    role_data = {"role": "admin"}
    response = requests.patch(f"{BASE_URL}/admin/api/v1/users/{test_user_id}/role", json=role_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test invalid role
    print("\n=== Testing PATCH with invalid role ===")
    invalid_role_data = {"role": "invalid_role"}
    response = requests.patch(f"{BASE_URL}/admin/api/v1/users/{test_user_id}/role", json=invalid_role_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    # Test admin login
    token = test_admin_login()
    
    if token:
        print(f"\nAdmin token received: {token[:20]}...")
        test_improved_admin_routes(token)
    else:
        print("Failed to get admin token")
