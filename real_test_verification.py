#!/usr/bin/env python3
"""
REAL DATA VERIFICATION TEST
Test actual functionality with your specific Lark Base table
"""

import requests
import json
import time

# Your actual table details
BASE_URL = "https://lark-mcp-telegram-server.onrender.com"
APP_TOKEN = "SEkObxgDpaPZbss1T3RlHzamgac"
TABLE_ID = "tblGhWiw3dzgdsfw"
TABLE_URL = "https://tsg9eq7nxo3w.sg.larksuite.com/base/SEkObxgDpaPZbss1T3RlHzamgac?table=tblGhWiw3dzgdsfw&view=vewn7G1dU4"

def test_endpoint(url, description):
    """Test an endpoint and return result"""
    try:
        response = requests.get(url, timeout=10)
        return {
            "status": "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}",
            "content": response.text[:200] if response.text else "Empty response"
        }
    except requests.exceptions.Timeout:
        return {"status": "⏱️ TIMEOUT", "content": "Request timed out"}
    except Exception as e:
        return {"status": f"❌ ERROR", "content": str(e)}

def test_mcp_call(method, params=None):
    """Test MCP JSON-RPC call"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": f"test_{int(time.time())}"
    }
    if params:
        payload["params"] = params
    
    try:
        response = requests.post(
            f"{BASE_URL}/mcp/invoke",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=15
        )
        return {
            "status_code": response.status_code,
            "response": response.json() if response.content else None
        }
    except Exception as e:
        return {"status_code": "ERROR", "response": str(e)}

def main():
    print("🧪 REAL DATA VERIFICATION TEST")
    print("=" * 40)
    print(f"🎯 Target: {TABLE_URL}")
    print(f"📊 Base: {APP_TOKEN}")
    print(f"📄 Table: {TABLE_ID}")
    print()
    
    # Test 1: Basic connectivity
    print("1️⃣ Testing basic server connectivity...")
    health_result = test_endpoint(BASE_URL, "Health check")
    print(f"   Status: {health_result['status']}")
    print(f"   Response: {health_result['content'][:100]}...")
    print()
    
    # Test 2: MCP tools endpoint
    print("2️⃣ Testing MCP tools endpoint...")
    tools_result = test_endpoint(f"{BASE_URL}/mcp/tools", "MCP tools")
    print(f"   Status: {tools_result['status']}")
    
    if tools_result['status'] == "✅ OK":
        try:
            tools_data = json.loads(tools_result['content'])
            if 'tools' in tools_data:
                tools = tools_data['tools']
                print(f"   📊 Found {len(tools)} tools")
                
                # Check for enhanced Bitable tools
                bitable_tools = [t for t in tools if t['name'].startswith('bitable_')]
                if bitable_tools:
                    print(f"   🔥 Enhanced Bitable tools: {len(bitable_tools)}")
                    for tool in bitable_tools[:3]:
                        print(f"      • {tool['name']}")
                else:
                    print("   ⚠️  No enhanced Bitable tools found")
                    print("   📋 Available tools:")
                    for tool in tools[:3]:
                        print(f"      • {tool['name']}")
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response")
    print()
    
    # Test 3: MCP JSON-RPC tools list
    print("3️⃣ Testing MCP JSON-RPC tools/list...")
    jsonrpc_result = test_mcp_call("tools/list")
    print(f"   HTTP Status: {jsonrpc_result['status_code']}")
    
    if jsonrpc_result['status_code'] == 200 and jsonrpc_result['response']:
        resp = jsonrpc_result['response']
        if 'result' in resp and 'tools' in resp['result']:
            tools = resp['result']['tools']
            print(f"   ✅ JSON-RPC working - {len(tools)} tools")
            
            # Check for enhanced tools
            enhanced_tools = [t for t in tools if t['name'].startswith('bitable_')]
            if enhanced_tools:
                print(f"   🔥 Enhanced Bitable tools via JSON-RPC: {len(enhanced_tools)}")
                return "ENHANCED"  # Enhanced version deployed
            else:
                print(f"   ⚠️  Basic tools only via JSON-RPC")
                return "BASIC"  # Basic version deployed
        else:
            print(f"   ❌ Invalid JSON-RPC response: {resp}")
            return "ERROR"
    else:
        print(f"   ❌ JSON-RPC failed: {jsonrpc_result}")
        return "ERROR"

if __name__ == "__main__":
    result = main()
    print()
    print("🎯 FINAL VERDICT:")
    if result == "ENHANCED":
        print("   ✅ Enhanced MCP Bridge with Bitable tools is DEPLOYED and WORKING")
        print("   🔥 Ready for real data testing with your table")
    elif result == "BASIC":
        print("   ⚠️  Basic MCP Bridge deployed - Enhanced version NOT active")
        print("   📋 Need to redeploy or debug enhanced version")
    else:
        print("   ❌ MCP Bridge not working properly")
        print("   🔧 Need to debug deployment issues")
    print()
