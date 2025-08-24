#!/usr/bin/env python3
"""
Optional security configuration for the Lark-Telegram Bridge Server
Provides backward-compatible security enhancements
"""
import os
import re
import hashlib
from typing import Optional, Dict
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)

# Optional security bearer
security = HTTPBearer(auto_error=False)

class SecurityManager:
    """Manages optional security features with backward compatibility"""
    
    def __init__(self):
        # Load API keys from environment (optional for backward compatibility)
        self.api_keys: Dict[str, str] = {}
        
        # Only add API keys if they exist in environment
        if os.getenv("API_KEY_ADMIN"):
            self.api_keys[os.getenv("API_KEY_ADMIN")] = "admin"
        if os.getenv("API_KEY_USER"):
            self.api_keys[os.getenv("API_KEY_USER")] = "user"
        
        # Security is only enabled if API keys are configured
        self.security_enabled = bool(self.api_keys)
        
        # Content validation settings
        self.max_content_length = 4000  # Lark message limit
        self.forbidden_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'on\w+\s*='
        ]
    
    async def verify_api_key(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
    ) -> Optional[str]:
        """
        Optional API key verification - only enforced if keys are configured
        Returns user role if authenticated, None if security disabled
        """
        if not self.security_enabled:
            return None  # Security disabled - maintain backward compatibility
        
        if not credentials:
            raise HTTPException(
                status_code=401, 
                detail="API key required when security is enabled"
            )
        
        if credentials.credentials not in self.api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return self.api_keys[credentials.credentials]
    
    def validate_content(self, content: str) -> str:
        """
        Validate and sanitize message content
        """
        if not content or not content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        if len(content) > self.max_content_length:
            raise HTTPException(
                status_code=400, 
                detail=f"Content too long (max {self.max_content_length} chars)"
            )
        
        # Check for potentially malicious patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                raise HTTPException(
                    status_code=400, 
                    detail="Content contains forbidden patterns"
                )
        
        return content.strip()
    
    def validate_chat_id(self, chat_id: str) -> str:
        """
        Validate chat ID format
        """
        if not chat_id or not chat_id.strip():
            raise HTTPException(status_code=400, detail="Chat ID cannot be empty")
        
        # Allow alphanumeric, hyphens, underscores, and dots
        if not re.match(r'^[a-zA-Z0-9_.-]+$', chat_id.strip()):
            raise HTTPException(
                status_code=400, 
                detail="Invalid chat ID format (alphanumeric, _, -, . only)"
            )
        
        return chat_id.strip()
    
    def get_rate_limit(self) -> str:
        """
        Get rate limit based on security configuration
        More permissive if security is disabled
        """
        if self.security_enabled:
            return "20/minute"  # Stricter when security is enabled
        else:
            return "50/minute"  # More permissive for backward compatibility
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """
        Hash sensitive data for secure logging
        """
        return hashlib.sha256(data.encode()).hexdigest()[:8]
    
    def get_security_headers(self) -> Dict[str, str]:
        """
        Get security headers based on configuration
        """
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
        }
        
        if self.security_enabled:
            # More restrictive headers when security is enabled
            headers.update({
                "X-Frame-Options": "DENY",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
            })
        else:
            # Less restrictive for backward compatibility
            headers.update({
                "X-Frame-Options": "SAMEORIGIN"
            })
        
        return headers

# Global security manager instance
security_manager = SecurityManager()
