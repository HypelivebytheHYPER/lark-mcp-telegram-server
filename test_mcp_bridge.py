#!/usr/bin/env python3
"""
Test MCP Bridge functionality
"""
import httpx
import json
import sys

async def test_mcp_bridge():
    base_url = "http://localhost:8000"
    
    # Test 1: tools/list
    print("🔧 Testing MCP Bridge - tools/list")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/mcp/invoke",
                json={"jsonrpc": "2.0", "id": "test1", "method": "tools/list"},
                timeout=10.0
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Check if /mcp endpoints are in root
    print("🔧 Testing root endpoint for MCP routes")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                data = response.json()
                endpoints = data.get("endpoints", {})
                print("Available endpoint categories:")
                for category in endpoints.keys():
                    print(f"  - {category}")
                    
                if "mcp-bridge" in endpoints:
                    print(f"✅ MCP Bridge found: {endpoints['mcp-bridge']}")
                else:
                    print("ℹ️ MCP Bridge not in root endpoints (expected)")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_mcp_bridge())
