#!/usr/bin/env python3
"""
Debug the exam file update issue with detailed error reporting
"""
import requests
import json
import traceback

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your actual API base URL
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin@admin.com"

def debug_update_issue():
    """Debug the exam file update issue"""
    print("=== DEBUGGING EXAM FILE UPDATE ISSUE ===")
    
    # Get admin token
    print("\n1. Testing login...")
    response = requests.post(f"{BASE_URL}/auth/api/v1/login", data={
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print("✅ Login successful")
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # List exam files
    print("\n2. Listing exam files...")
    response = requests.get(f"{BASE_URL}/admin/api/v1/exam-files", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to list exam files: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    exam_files = response.json()
    print(f"✅ Found {len(exam_files)} exam files")
    
    if not exam_files:
        print("❌ No exam files found to test")
        return False
    
    # Get first exam file for testing
    exam_file = exam_files[0]
    file_id = exam_file["id"]
    print(f"\n3. Testing with file:")
    print(f"   ID: {file_id}")
    print(f"   Title: {exam_file['title']}")
    print(f"   Current essay_count: {exam_file.get('essay_count', 'N/A')}")
    print(f"   Current choice_count: {exam_file.get('choice_count', 'N/A')}")
    print(f"   Current tags: {exam_file.get('tags', [])}")
    
    # Test 1: Simple title update only
    print("\n4. Test 1: Simple title update...")
    simple_update = {
        "title": exam_file["title"] + " (Simple Update)"
    }
    
    response = requests.put(
        f"{BASE_URL}/admin/api/v1/exam-files/{file_id}",
        headers=headers,
        json=simple_update
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
        try:
            error_detail = response.json()
            print(f"   Detail: {error_detail}")
        except:
            pass
    else:
        result = response.json()
        print(f"   ✅ Success! New title: {result.get('title')}")
    
    # Test 2: Update with essay_count and choice_count
    print("\n5. Test 2: Update with question counts...")
    full_update = {
        "title": exam_file["title"] + " (Full Update)",
        "description": exam_file["description"] + " - Updated",
        "essay_count": 2,
        "choice_count": 3
    }
    
    response = requests.put(
        f"{BASE_URL}/admin/api/v1/exam-files/{file_id}",
        headers=headers,
        json=full_update
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
        try:
            error_detail = response.json()
            print(f"   Detail: {error_detail}")
        except:
            pass
    else:
        result = response.json()
        print(f"   ✅ Success!")
        print(f"   Title: {result.get('title')}")
        print(f"   Essay count: {result.get('essay_count')}")
        print(f"   Choice count: {result.get('choice_count')}")
    
    # Test 3: Edge case - one count is 0
    print("\n6. Test 3: Edge case with one count as 0...")
    edge_update = {
        "essay_count": 0,
        "choice_count": 5
    }
    
    response = requests.put(
        f"{BASE_URL}/admin/api/v1/exam-files/{file_id}",
        headers=headers,
        json=edge_update
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
        try:
            error_detail = response.json()
            print(f"   Detail: {error_detail}")
        except:
            pass
    else:
        result = response.json()
        print(f"   ✅ Success! Essay: {result.get('essay_count')}, Choice: {result.get('choice_count')}")
    
    # Test 4: Invalid case - both counts are 0
    print("\n7. Test 4: Invalid case - both counts are 0...")
    invalid_update = {
        "essay_count": 0,
        "choice_count": 0
    }
    
    response = requests.put(
        f"{BASE_URL}/admin/api/v1/exam-files/{file_id}",
        headers=headers,
        json=invalid_update
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 422:
        print(f"   ✅ Correctly rejected invalid data")
        try:
            error_detail = response.json()
            print(f"   Validation error: {error_detail}")
        except:
            pass
    elif response.status_code != 200:
        print(f"   Error: {response.text}")
    else:
        print(f"   ⚠️  Unexpectedly succeeded - this should have failed")
    
    # Revert to original values
    print("\n8. Reverting to original values...")
    revert_data = {
        "title": exam_file["title"],
        "description": exam_file["description"],
        "tags": exam_file.get("tags", []),
        "essay_count": exam_file.get("essay_count", 1),
        "choice_count": exam_file.get("choice_count", 1)
    }
    
    response = requests.put(
        f"{BASE_URL}/admin/api/v1/exam-files/{file_id}",
        headers=headers,
        json=revert_data
    )
    
    if response.status_code == 200:
        print("✅ Successfully reverted changes")
    else:
        print(f"❌ Failed to revert: {response.status_code} - {response.text}")
    
    return True

if __name__ == "__main__":
    try:
        debug_update_issue()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
