#!/usr/bin/env python3
"""
Simplified test suite for FastMCP server components
"""
import pytest
import os
from unittest.mock import Mock, patch
from dotenv import load_dotenv

# Load test environment
load_dotenv('.env')

# Import server components - just the functions, not the tools
from server_enhanced import (
    authenticate_request, 
    check_rate_limit,
    rate_limit_storage
)

class TestAuthentication:
    """Test authentication functionality"""
    
    def test_authenticate_request_no_api_key(self):
        """Test authentication when no API key is required"""
        # Clear any existing MCP_API_KEY for this test
        with patch('server_enhanced.API_KEY', None):
            assert authenticate_request() == True
            assert authenticate_request("any_key") == True
    
    def test_authenticate_request_with_api_key(self):
        """Test authentication with API key required"""
        with patch('server_enhanced.API_KEY', "secret123"):
            assert authenticate_request("secret123") == True
            assert authenticate_request("wrong_key") == False
            assert authenticate_request(None) == False

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def setup_method(self):
        """Clean rate limit storage before each test"""
        rate_limit_storage.clear()
    
    def test_rate_limit_allows_initial_requests(self):
        """Test that initial requests are allowed"""
        assert check_rate_limit("test_user") == True
    
    def test_rate_limit_blocks_excessive_requests(self):
        """Test that excessive requests are blocked"""
        # Simulate many requests
        user_id = "heavy_user"
        for i in range(10):  # Default limit
            result = check_rate_limit(user_id)
            assert result == True, f"Request {i+1} should be allowed"
        
        # Next request should be blocked
        assert check_rate_limit(user_id) == False

class TestServerComponents:
    """Test basic server components functionality"""
    
    def test_rate_limit_storage_cleanup(self):
        """Test that old entries are cleaned up"""
        import time
        from unittest.mock import patch
        
        user_id = "test_cleanup"
        rate_limit_storage.clear()
        
        # Mock time to simulate old requests
        with patch('server_enhanced.time.time') as mock_time:
            mock_time.return_value = 1000  # Old time
            check_rate_limit(user_id)
            
            # Move time forward beyond window
            mock_time.return_value = 2000  # New time (beyond 60s window)
            
            # Should allow new request after cleanup
            assert check_rate_limit(user_id) == True

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])