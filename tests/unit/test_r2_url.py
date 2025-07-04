"""
Unit tests for R2 URL generation.
"""
import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.storage.r2_client import PUBLIC_ENDPOINT, R2_CONFIGURED

class TestR2URL:
    """Test R2 URL generation functionality."""
    
    def test_r2_public_endpoint_format(self):
        """Test that the R2 public endpoint has the correct format."""
        if R2_CONFIGURED:
            # The PUBLIC_ENDPOINT should be just the domain without https://
            assert PUBLIC_ENDPOINT == "pub-ec581fd3be54492190988525aca67c77.r2.dev"
            # It should NOT start with https://
            assert not PUBLIC_ENDPOINT.startswith("https://")
            assert not PUBLIC_ENDPOINT.startswith("http://")
        else:
            # If R2 is not configured, PUBLIC_ENDPOINT should be None
            assert PUBLIC_ENDPOINT is None
    
    def test_r2_url_construction(self):
        """Test that R2 URLs are constructed correctly."""
        if R2_CONFIGURED:
            # Test URL construction for a sample file
            file_id = "test_file_123.txt"
            expected_url = f"{PUBLIC_ENDPOINT}/{file_id}"
            
            # The URL should be domain/filename without https://
            assert expected_url == "pub-ec581fd3be54492190988525aca67c77.r2.dev/test_file_123.txt"
            assert not expected_url.startswith("https://")
            assert not expected_url.startswith("http://")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])