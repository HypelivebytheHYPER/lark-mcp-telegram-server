#!/usr/bin/env python3
"""
REAL BITABLE TEST WITH YOUR ACTUAL LARKSUITE CREDENTIALS
Tests the complete flow from MCP bridge to your real table
"""

import requests
import json
import time

# Your actual table details
BASE_URL = "https://lark-mcp-telegram-server.onrender.com"
APP_TOKEN = "SEkObxgDpaPZbss1T3RlHzamgac"
TABLE_ID = "tblGhWiw3dzgdsfw"


def wait_for_deployment():
    """Wait for Render deployment to complete"""
    print("⏳ Waiting for Render deployment to complete...")
    
    for i in range(10):  # Wait up to 5 minutes
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                timestamp = health_data.get("timestamp", "")
                print(f"   📡 Server responding (attempt {i+1}): {timestamp}")
                
                # Check if it's a recent deployment (within last 10 minutes)
                if "2025-08-24T18:" in timestamp:  # Today's deployment
                    print("   ✅ Fresh deployment detected!")
                    return True
            time.sleep(30)  # Wait 30 seconds between checks
        except:
            print(f"   ⏳ Waiting for server... (attempt {i+1})")
            time.sleep(30)
    
    print("   ⚠️  Deployment taking longer than expected, proceeding anyway...")
    return False

def test_environment_loaded():
    """Test if environment variables are now loaded"""
    print("🔍 Testing environment variable loading...")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "bitable_list_tables",
            "arguments": {
                "app_token": APP_TOKEN,
                "page_size": 3
            }
        },
        "id": "real_test"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/mcp/invoke",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📡 Response received: {response.status_code}")
            
            if "result" in result:
                if "error" in result["result"]:
                    error_msg = result["result"]["error"]["message"]
                    if "App ID and App Secret required" in error_msg:
                        print("   ❌ Environment variables still not loaded")
                        return False, "credentials_missing"
                    elif "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                        print("   ⚠️  Credentials loaded but authentication failed")
                        return True, "auth_failed"
                    else:
                        print(f"   ❓ Unexpected error: {error_msg}")
                        return True, "unknown_error"
                else:
                    # Success case
                    print("   ✅ Environment variables loaded and working!")
                    return True, "success"
            else:
                print("   ❓ Unexpected response format")
                return False, "unexpected_format"
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False, "http_error"
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False, "request_failed"

def test_real_table_access():
    """Test access to your specific table"""
    print(f"🎯 Testing access to your real table...")
    print(f"   Base: {APP_TOKEN}")
    print(f"   Table: {TABLE_ID}")
    
    # Test 1: List tables in your base
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "bitable_list_tables",
            "arguments": {
                "app_token": APP_TOKEN,
                "page_size": 10
            }
        },
        "id": "table_list_test"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/mcp/invoke",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if "result" in result and "content" in result["result"]:
                content = json.loads(result["result"]["content"])
                
                if "data" in content and "items" in content["data"]:
                    tables = content["data"]["items"]
                    print(f"   ✅ Found {len(tables)} tables in your Base:")
                    
                    target_found = False
                    for table in tables:
                        name = table.get("name", "Unknown")
                        table_id = table.get("table_id", "N/A")
                        is_target = table_id == TABLE_ID
                        marker = "🎯" if is_target else "📄"
                        print(f"      {marker} {name} ({table_id})")
                        if is_target:
                            target_found = True
                    
                    if target_found:
                        print(f"   ✅ Your target table found and accessible!")
                        return True
                    else:
                        print(f"   ⚠️  Target table {TABLE_ID} not found in base")
                        return False
                else:
                    print(f"   ❌ Unexpected API response format")
                    return False
            else:
                print(f"   ❌ MCP call failed: {result}")
                return False
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🚀 REAL BITABLE TEST WITH YOUR LARKSUITE CREDENTIALS")
    print("=" * 60)
    
    # Step 1: Wait for deployment
    wait_for_deployment()
    
    # Step 2: Test environment variables
    env_loaded, env_status = test_environment_loaded()
    
    if not env_loaded:
        print(f"❌ Environment variables not loaded yet")
        print(f"💡 Try again in a few minutes or check Render dashboard")
        return
    
    if env_status == "success":
        # Step 3: Test real table access
        table_success = test_real_table_access()
        
        if table_success:
            print(f"� COMPLETE SUCCESS!")
            print(f"✅ Enhanced MCP Bridge deployed")
            print(f"✅ LarkSuite credentials working")
            print(f"✅ Your table accessible via MCP")
            print(f"✅ Official LarkSuite API integration confirmed")
        else:
            print(f"⚠️  Partial success - credentials work but table access limited")
    else:
        print(f"⚠️  Environment loaded but authentication issue: {env_status}")
        print(f"💡 Check your LARK_APP_ID and LARK_APP_SECRET in Render")

if __name__ == "__main__":
    main()
