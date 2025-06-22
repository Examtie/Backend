"""
Simple Performance Tests for Examtie Backend using requests
"""
import pytest
import requests
import time
from concurrent.futures import ThreadPoolExecutor

# Configuration
BASE_URL = "http://localhost:8000"


class TestAPIPerformanceSimple:
    """Simple performance tests using requests against running server."""
    
    def setup_method(self):
        """Set up test data"""
        self.admin_token = None
    
    def get_admin_token(self):
        """Get admin authentication token"""
        if self.admin_token:
            return self.admin_token
        
        response = requests.post(f"{BASE_URL}/auth/api/v1/login", data={
            "username": "admin@admin.com",
            "password": "admin@admin.com"
        })
        assert response.status_code == 200
        self.admin_token = response.json()["access_token"]
        return self.admin_token

    def make_authenticated_request(self, method, endpoint, **kwargs):
        """Make an authenticated request"""
        token = self.get_admin_token()
        headers = kwargs.get('headers', {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs['headers'] = headers
        
        return requests.request(method, endpoint, **kwargs)

    def test_login_performance(self):
        """Test login endpoint performance"""
        start_time = time.time()
        
        for _ in range(5):  # Reduced iterations for faster test
            response = requests.post(f"{BASE_URL}/auth/api/v1/login", data={
                "username": "admin@admin.com",
                "password": "admin@admin.com"
            })
            assert response.status_code == 200
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 5
        
        print(f"Average login time: {avg_time:.3f} seconds")
        assert avg_time < 2.0, f"Login taking too long: {avg_time:.3f}s"

    def test_user_listing_performance(self):
        """Test user listing endpoint performance with different page sizes"""
        token = self.get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        for limit in [5, 10, 20]:
            start_time = time.time()
            
            response = requests.get(f"{BASE_URL}/admin/api/v1/users?page=1&limit={limit}", headers=headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            print(f"User listing (limit={limit}): {response_time:.3f} seconds")
            assert response_time < 5.0, f"User listing too slow: {response_time:.3f}s"

    def test_concurrent_requests(self):
        """Test API under concurrent load"""
        token = self.get_admin_token()
        
        def make_request():
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/admin/api/v1/stats", headers=headers)
            return response.status_code == 200
        
        start_time = time.time()
        
        # Test with 3 concurrent requests (reduced for stability)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request) for _ in range(3)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"3 concurrent requests completed in: {total_time:.3f} seconds")
        assert all(results), "Some concurrent requests failed"
        assert total_time < 10.0, f"Concurrent requests too slow: {total_time:.3f}s"

    def test_endpoint_response_times(self):
        """Test response times for all major endpoints"""
        token = self.get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        endpoints = [
            ("GET", f"{BASE_URL}/admin/api/v1/users"),
            ("GET", f"{BASE_URL}/admin/api/v1/stats"),
            ("GET", f"{BASE_URL}/admin/api/v1/users/@data?username=admin@admin.com"),
        ]
        
        for method, endpoint in endpoints:
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(endpoint, headers=headers)
            else:
                response = requests.request(method, endpoint, headers=headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            print(f"{method} {endpoint}: {response_time:.3f} seconds")
            assert response_time < 5.0, f"Endpoint too slow: {response_time:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
