#!/usr/bin/env python3
"""
Test MCP Bridge using FastAPI TestClient
"""
import sys
import os
sys.path.insert(0, '/workspaces/lark-mcp-telegram-server')

from fastapi.testclient import TestClient
import json

def test_mcp_bridge():
    # Import the app
    import app
    client = TestClient(app.app)
    
    print("🔧 Testing MCP Bridge Integration")
    print("="*50)
    
    # Test 1: Check if MCP route is registered
    print("1. Testing /mcp/invoke endpoint availability")
    try:
        response = client.post(
            "/mcp/invoke",
            json={"jsonrpc": "2.0", "id": "test1", "method": "tools/list"}
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ MCP Bridge is working!")
            print(f"   Response: {json.dumps(data, indent=4)}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Check if original REST APIs still work
    print("2. Testing original REST API endpoints (zero risk verification)")
    try:
        response = client.get("/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Root endpoint working: {data.get('service')} v{data.get('version')}")
            
            # Check bitable endpoints
            bitable_endpoints = data.get("endpoints", {}).get("bitable", {})
            print(f"   ✅ Bitable endpoints available: {len(bitable_endpoints)}")
            
        else:
            print(f"   ❌ Root endpoint error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Check specific tool call
    print("3. Testing MCP tool call (if tools/list works)")
    try:
        response = client.post(
            "/mcp/invoke",
            json={
                "jsonrpc": "2.0", 
                "id": "test2", 
                "method": "tools/call",
                "params": {
                    "name": "send_lark_message",
                    "arguments": {
                        "chat_id": "test_chat",
                        "text": "Test message"
                    }
                }
            }
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Tool call response received")
            print(f"   Response type: {type(data)}")
        else:
            print(f"   ℹ️ Expected behavior - tool call may fail without real credentials")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_mcp_bridge()
