"""
Basic API Tests for checking endpoints without database operations
"""
import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.main import app


class TestBasicEndpoints:
    """Basic API tests that don't require database operations."""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self, 'client') and self.client:
            self.client.close()
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        # Check if we get any expected response
        assert isinstance(data, dict) or isinstance(data, str)
    
    def test_docs_endpoint(self):
        """Test the docs endpoint is accessible."""
        response = self.client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_endpoint(self):
        """Test the OpenAPI schema endpoint."""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
    
    def test_nonexistent_endpoint(self):
        """Test that non-existent endpoints return 404."""
        response = self.client.get("/nonexistent")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
