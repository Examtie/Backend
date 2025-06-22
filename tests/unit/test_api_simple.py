"""
Simple API Tests for Examtie Backend
These are basic tests that don't require complex async handling
"""
import pytest
import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.main import app

# Create a test client
client = TestClient(app)


class TestExamtieAPISimple:
    """Simple API tests using FastAPI TestClient."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
        self.admin_token = None
    
    def teardown_method(self):
        """Clean up after tests"""
        if self.client:
            self.client.close()
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "niga56" in data
    
    def test_admin_login_success(self):
        """Test successful admin login."""
        response = self.client.post("/auth/api/v1/login", data={
            "username": "admin@admin.com",
            "password": "admin@admin.com"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post("/auth/api/v1/login", data={
            "username": "invalid@test.com",
            "password": "invalid"
        })
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def get_admin_token(self) -> str:
        """Helper method to get admin token."""
        if self.admin_token:
            return self.admin_token
            
        response = self.client.post("/auth/api/v1/login", data={
            "username": "admin@admin.com",
            "password": "admin@admin.com"
        })
        assert response.status_code == 200
        self.admin_token = response.json()["access_token"]
        return self.admin_token
    
    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints."""
        response = self.client.get("/admin/api/v1/users")
        assert response.status_code == 401
    
    def test_invalid_token(self):
        """Test access with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.client.get("/admin/api/v1/users", headers=headers)
        assert response.status_code == 401
    
    def test_admin_endpoints_with_valid_token(self):
        """Test admin endpoints with valid token."""
        token = self.get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test user listing
        response = self.client.get("/admin/api/v1/users", headers=headers)
        assert response.status_code == 200
        
        # Test system stats
        response = self.client.get("/admin/api/v1/stats", headers=headers)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])