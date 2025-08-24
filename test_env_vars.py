#!/usr/bin/env python3
"""
Quick test to verify environment variables are loaded in production
"""

import requests
import json

def test_env_vars():
    """Test if environment variables are available via a simple MCP call"""
    
    # Test a simple MCP call that would reveal if credentials are loaded
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call", 
        "params": {
            "name": "bitable_list_tables",
            "arguments": {
                "app_token": "test_token"  # This will fail but reveal the actual error
            }
        },
        "id": "env_test"
    }
    
    try:
        response = requests.post(
            "https://lark-mcp-telegram-server.onrender.com/mcp/invoke",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=15
        )
        
        result = response.json()
        print("🔍 Environment Variable Test Result:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Check the error message to understand what's happening
        if "result" in result and "error" in result["result"]:
            error_msg = result["result"]["error"]["message"]
            if "App ID and App Secret required" in error_msg:
                print("❌ Environment variables NOT loaded yet")
                print("💡 Render is probably still deploying the new variables")
            elif "invalid" in error_msg.lower() or "unauthorized" in error_msg.lower():
                print("✅ Environment variables loaded but API call failed (expected)")
            else:
                print(f"❓ Unexpected error: {error_msg}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_env_vars()
