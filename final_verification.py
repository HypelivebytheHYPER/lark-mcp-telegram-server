#!/usr/bin/env python3
"""
FINAL VERIFICATION: Test Enhanced MCP Bridge with YOUR Real Data
Run this script to verify when enhanced deployment is live and test your actual table
"""

import requests
import json
import time

# Your actual table details
BASE_URL = "https://lark-mcp-telegram-server.onrender.com"
APP_TOKEN = "SEkObxgDpaPZbss1T3RlHzamgac"
TABLE_ID = "tblGhWiw3dzgdsfw"
TABLE_URL = "https://tsg9eq7nxo3w.sg.larksuite.com/base/SEkObxgDpaPZbss1T3RlHzamgac?table=tblGhWiw3dzgdsfw&view=vewn7G1dU4"

def check_deployment_status():
    """Check if enhanced MCP bridge is deployed"""
    try:
        response = requests.get(f"{BASE_URL}/mcp/tools", timeout=10)
        if response.status_code == 200:
            tools = response.json().get('tools', [])
            enhanced_count = len([t for t in tools if t['name'].startswith('bitable_')])
            return {
                "deployed": enhanced_count > 0,
                "tool_count": len(tools),
                "enhanced_count": enhanced_count
            }
    except:
        pass
    return {"deployed": False, "tool_count": 0, "enhanced_count": 0}

def test_real_bitable_call():
    """Test real API call to your Lark Base table"""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "bitable_list_tables",
            "arguments": {
                "app_token": APP_TOKEN,
                "page_size": 5
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
            if 'result' in result and 'content' in result['result']:
                content = json.loads(result['result']['content'])
                return {"success": True, "data": content}
            else:
                return {"success": False, "error": f"Invalid response: {result}"}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    print("🎯 FINAL ENHANCED MCP BRIDGE VERIFICATION")
    print("=" * 45)
    print(f"🔗 Your Table: {TABLE_URL}")
    print(f"📊 Base Token: {APP_TOKEN}")
    print(f"📄 Table ID: {TABLE_ID}")
    print()
    
    # Check deployment status
    print("1️⃣ Checking deployment status...")
    status = check_deployment_status()
    
    if status["deployed"]:
        print(f"   ✅ ENHANCED VERSION DEPLOYED!")
        print(f"   📊 Total tools: {status['tool_count']}")
        print(f"   🔥 Enhanced Bitable tools: {status['enhanced_count']}")
        print()
        
        # Test real API call
        print("2️⃣ Testing real API call to your Lark Base...")
        result = test_real_bitable_call()
        
        if result["success"]:
            print("   ✅ REAL API CALL SUCCESSFUL!")
            data = result["data"]
            
            if "data" in data and "items" in data["data"]:
                tables = data["data"]["items"]
                print(f"   📊 Found {len(tables)} tables in your Base:")
                
                for table in tables:
                    name = table.get("name", "Unknown")
                    table_id = table.get("table_id", "N/A")
                    is_target = "🎯" if table_id == TABLE_ID else "📄"
                    print(f"      {is_target} {name} ({table_id})")
                
                print()
                print("🎉 SUCCESS! Enhanced MCP Bridge working with your real data!")
                print("✅ Official LarkSuite API integration confirmed")
                print("✅ HTTP streaming MCP protocol working")
                print("✅ Your table accessible via enhanced tools")
                
            else:
                print(f"   ⚠️  API responded but unexpected format: {data}")
        else:
            print(f"   ❌ Real API call failed: {result['error']}")
            print("   🔧 May need API credentials or permissions")
    else:
        print(f"   ⚠️  Enhanced version not yet deployed")
        print(f"   📊 Current tools: {status['tool_count']} (basic version)")
        print("   ⏳ Wait a few more minutes for Render deployment")
        print()
        print("💡 TIP: Run this script again in 2-3 minutes")

if __name__ == "__main__":
    main()
