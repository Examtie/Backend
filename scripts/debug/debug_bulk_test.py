import requests
import json

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin@admin.com"

def get_admin_token():
    """Get admin authentication token"""
    login_data = {
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    response = requests.post(f"{BASE_URL}/auth/api/v1/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Auth failed: {response.status_code} - {response.json()}")
        return None

def test_bulk_role_update():
    token = get_admin_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test user first
    test_user_data = {
        "email": "bulktest2@example.com",
        "password": "testpass123",
        "full_name": "Bulk Test User",
        "username": "bulktestuser2"
    }
    
    response = requests.post(f"{BASE_URL}/auth/api/v1/register", json=test_user_data)
    if response.status_code != 200:
        print(f"Failed to create test user: {response.status_code} - {response.json()}")
        return
    
    test_user_id = response.json()["id"]
    print(f"Created test user with ID: {test_user_id}")
    
    # Test individual role update first 
    individual_data = {"role": "staff"}
    response = requests.patch(f"{BASE_URL}/admin/api/v1/users/{test_user_id}/role", 
                             json=individual_data, headers=headers)
    print(f"Individual role update status: {response.status_code}")
    if response.status_code != 200:
        print(f"Individual role update failed: {response.json()}")
    
    # Test bulk role update with user role
    bulk_data = {
        "user_ids": [test_user_id],
        "role": "user"
    }
    
    print(f"Sending bulk data: {bulk_data}")
    response = requests.patch(f"{BASE_URL}/admin/api/v1/users/bulk/role", 
                             json=bulk_data, headers=headers)
    
    print(f"Response status: {response.status_code}")
    try:
        print(f"Response body: {response.json()}")
    except:
        print(f"Response text: {response.text}")
    
    # Cleanup
    requests.delete(f"{BASE_URL}/admin/api/v1/users/{test_user_id}", headers=headers)

if __name__ == "__main__":
    test_bulk_role_update()
