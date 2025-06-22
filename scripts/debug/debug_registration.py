"""
Debug script to understand the user registration issue
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_user_registration_debug():
    """Debug user registration to understand the 422 error"""
    
    # Test 1: Try different user data formats
    user_data_formats = [
        {
            "email": "test1@test.com",
            "password": "password123",
            "full_name": "Test User",
            "username": "testuser1"
        },
        {
            "email": "test2@test.com", 
            "password": "password123",
            "full_name": "Test User",
            "username": "testuser2",
            "roles": ["user"]
        },
        {
            "email": "test3@test.com",
            "password": "password123",
            "firstName": "Test",
            "lastName": "User"
        }
    ]
    
    for i, user_data in enumerate(user_data_formats, 1):
        print(f"\n=== Test {i}: User Data Format ===")
        print(f"Data: {json.dumps(user_data, indent=2)}")
        
        response = requests.post(f"{BASE_URL}/auth/api/v1/register", json=user_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:
            try:
                errors = response.json()
                print("Validation Errors:")
                for error in errors.get('detail', []):
                    print(f"  - {error}")
            except:
                print("Could not parse error response")
        elif response.status_code == 200:
            print("✅ Registration successful!")
            break
        else:
            print(f"❌ Unexpected status code: {response.status_code}")

if __name__ == "__main__":
    test_user_registration_debug()
