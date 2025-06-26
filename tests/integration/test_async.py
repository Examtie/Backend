"""
Working async tests for Examtie Backend using requests for simplicity
"""
import requests
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

# Configuration  
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin@admin.com"

class AsyncTestRunner:
    """Async-compatible test runner using requests in thread pool"""
    
    def __init__(self):
        self.admin_token = None
        self.test_cleanup = []
        
    async def run_in_thread(self, func, *args, **kwargs):
        """Run a synchronous function in a thread pool"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, func, *args, **kwargs)
    
    async def get_admin_token(self):
        """Get admin token asynchronously"""
        if self.admin_token:
            return self.admin_token
            
        def _login():
            response = requests.post(f"{BASE_URL}/auth/api/v1/login", data={
                "username": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            if response.status_code == 200:
                return response.json()["access_token"]
            return None
            
        self.admin_token = await self.run_in_thread(_login)
        return self.admin_token
    
    async def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request asynchronously"""
        def _request():
            return requests.request(method, f"{BASE_URL}{endpoint}", **kwargs)
        return await self.run_in_thread(_request)
    
    async def make_authenticated_request(self, method, endpoint, **kwargs):
        """Make authenticated request asynchronously"""
        token = await self.get_admin_token()
        if not token:
            raise Exception("Failed to get admin token")
            
        headers = kwargs.get('headers', {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs['headers'] = headers
        
        return await self.make_request(method, endpoint, **kwargs)

class TestExamtieAPIAsync:
    """Async test suite for Examtie API"""
    
    def __init__(self):
        self.runner = AsyncTestRunner()
    
    async def test_root_endpoint(self):
        """Test the root endpoint"""
        print("🏠 Testing root endpoint...")
        response = await self.runner.make_request("GET", "/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "message" in data, f"Expected 'message' in response, got {data}"
        print("✅ Root endpoint working")
    
    async def test_admin_login(self):
        """Test admin login"""
        print("🔐 Testing admin login...")
        response = await self.runner.make_request("POST", "/auth/api/v1/login", data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.status_code}, {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access token in response: {data}"
        assert data["token_type"] == "bearer", f"Wrong token type: {data.get('token_type')}"
        print("✅ Admin login successful")
    
    async def test_invalid_login(self):
        """Test invalid login credentials"""
        print("❌ Testing invalid login...")
        response = await self.runner.make_request("POST", "/auth/api/v1/login", data={
            "username": "invalid@test.com",
            "password": "invalid"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Invalid login handled correctly")
    
    async def test_user_registration(self):
        """Test user registration"""
        print("👤 Testing user registration...")
        unique_id = str(int(time.time()))
        user_data = {
            "email": f"testuser_{unique_id}@test.com",
            "password": "testpass123",
            "full_name": "Test User",
            "username": f"testuser_{unique_id}"
        }
        
        response = await self.runner.make_request("POST", "/auth/api/v1/register", json=user_data)
        if response.status_code != 200:
            print(f"Registration failed: {response.status_code}, {response.text}")
            return False
            
        data = response.json()
        assert "id" in data, f"No user ID in response: {data}"
        assert data["email"] == user_data["email"], f"Email mismatch: {data.get('email')} != {user_data['email']}"
        
        # Store for cleanup
        self.runner.test_cleanup.append(("user", data["id"]))
        print("✅ User registration successful")
        return True
    
    async def test_admin_user_listing(self):
        """Test admin user listing"""
        print("📋 Testing admin user listing...")
        response = await self.runner.make_authenticated_request("GET", "/admin/api/v1/users?page=1&limit=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.text}"
        users = response.json()
        assert isinstance(users, list), f"Expected list, got {type(users)}"
        print(f"✅ Retrieved {len(users)} users")
    
    async def test_admin_system_stats(self):
        """Test admin system stats"""
        print("📊 Testing system stats...")
        response = await self.runner.make_authenticated_request("GET", "/admin/api/v1/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}, {response.text}"
        stats = response.json()
        assert "users" in stats, f"No users stats in response: {stats}"
        assert "total" in stats["users"], f"No total users count: {stats.get('users')}"
        print(f"✅ System stats: {stats['users']['total']} total users")
    
    async def test_unauthorized_access(self):
        """Test unauthorized access"""
        print("🚫 Testing unauthorized access...")
        response = await self.runner.make_request("GET", "/admin/api/v1/users")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Unauthorized access blocked correctly")
    
    async def test_invalid_token(self):
        """Test invalid token"""
        print("🔑 Testing invalid token...")
        headers = {"Authorization": "Bearer invalid_token"}
        response = await self.runner.make_request("GET", "/admin/api/v1/users", headers=headers)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Invalid token rejected correctly")
    
    async def cleanup(self):
        """Clean up test data"""
        if not self.runner.test_cleanup:
            return
            
        print("🧹 Cleaning up test data...")
        for item_type, item_id in self.runner.test_cleanup:
            if item_type == "user":
                try:
                    response = await self.runner.make_authenticated_request("DELETE", f"/admin/api/v1/users/{item_id}")
                    if response.status_code == 200:
                        print(f"✅ Cleaned up user {item_id}")
                    else:
                        print(f"⚠️ Failed to cleanup user {item_id}: {response.status_code}")
                except Exception as e:
                    print(f"⚠️ Error cleaning up user {item_id}: {e}")
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Examtie API async tests...")
        print("=" * 50)
        
        tests = [
            self.test_root_endpoint,
            self.test_admin_login,
            self.test_invalid_login,
            self.test_user_registration,
            self.test_admin_user_listing,
            self.test_admin_system_stats,
            self.test_unauthorized_access,
            self.test_invalid_token
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                await test()
                passed += 1
            except Exception as e:
                print(f"❌ {test.__name__} failed: {e}")
                failed += 1
                
        await self.cleanup()
                
        print("\n" + "=" * 50)
        print(f"🎯 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed!")
        else:
            print("💥 Some tests failed!")
            
        return failed == 0

async def main():
    """Main async function"""
    test_suite = TestExamtieAPIAsync()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    # Run the async tests
    success = asyncio.run(main())
    exit(0 if success else 1)
