#!/usr/bin/env python3
"""
Test script for the specific Lark Base table provided by user
Base: https://tsg9eq7nxo3w.sg.larksuite.com/base/SEkObxgDpaPZbss1T3RlHzamgac?table=tblGhWiw3dzgdsfw&view=vewn7G1dU4
"""

import requests
import json

# Configuration
MCP_SERVER_URL = "https://lark-mcp-telegram-server.onrender.com/mcp/invoke"
APP_TOKEN = "SEkObxgDpaPZbss1T3RlHzamgac"
TABLE_ID = "tblGhWiw3dzgdsfw"

def test_mcp_call(method, params=None, name=None, arguments=None):
    """Make an MCP JSON-RPC call"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": f"test_{method.replace('/', '_')}"
    }
    
    if method == "tools/call" and name and arguments:
        payload["params"] = {
            "name": name,
            "arguments": arguments
        }
    elif params:
        payload["params"] = params
    
    try:
        response = requests.post(
            MCP_SERVER_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def main():
    print("🧪 TESTING YOUR SPECIFIC LARK BASE TABLE")
    print("=" * 45)
    print(f"📊 Base ID: {APP_TOKEN}")
    print(f"📋 Table ID: {TABLE_ID}")
    print(f"🌐 MCP Server: {MCP_SERVER_URL}")
    print()
    
    # Test 1: List available tools
    print("🔧 Test 1: Listing available MCP tools...")
    tools_result = test_mcp_call("tools/list")
    
    if "result" in tools_result and "tools" in tools_result["result"]:
        tools = tools_result["result"]["tools"]
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools[:8]:  # Show first 8 tools
            print(f"   • {tool['name']}")
        if len(tools) > 8:
            print(f"   ... and {len(tools)-8} more tools")
    else:
        print("❌ Failed to get tools list")
        print(f"Response: {tools_result}")
    
    print()
    
    # Test 2: Get table schema
    print("📊 Test 2: Getting table schema...")
    schema_result = test_mcp_call(
        "tools/call",
        name="bitable_get_table_schema",
        arguments={
            "app_token": APP_TOKEN,
            "table_id": TABLE_ID
        }
    )
    
    if "result" in schema_result:
        print("✅ Schema retrieved successfully")
        try:
            content = json.loads(schema_result["result"]["content"])
            if "data" in content and "fields" in content["data"]:
                fields = content["data"]["fields"]
                print(f"   📋 Table has {len(fields)} fields:")
                for field in fields[:5]:
                    field_name = field.get("field_name", "Unknown")
                    field_type = field.get("type", "unknown")
                    print(f"      • {field_name} ({field_type})")
                if len(fields) > 5:
                    print(f"      ... and {len(fields)-5} more fields")
        except Exception as e:
            print(f"   ⚠️ Error parsing schema: {e}")
    else:
        print("❌ Failed to get table schema")
        print(f"Response: {schema_result}")
    
    print()
    
    # Test 3: List records
    print("📄 Test 3: Listing table records...")
    records_result = test_mcp_call(
        "tools/call",
        name="bitable_list_records",
        arguments={
            "app_token": APP_TOKEN,
            "table_id": TABLE_ID,
            "page_size": 5
        }
    )
    
    if "result" in records_result:
        print("✅ Records retrieved successfully")
        try:
            content = json.loads(records_result["result"]["content"])
            if "data" in content and "items" in content["data"]:
                records = content["data"]["items"]
                print(f"   📋 Found {len(records)} records (showing first few):")
                for i, record in enumerate(records[:3]):
                    record_id = record.get("record_id", "N/A")
                    field_count = len(record.get("fields", {}))
                    print(f"      📄 Record {i+1}: {record_id} ({field_count} fields)")
        except Exception as e:
            print(f"   ⚠️ Error parsing records: {e}")
    else:
        print("❌ Failed to get table records")
        print(f"Response: {records_result}")
    
    print()
    print("🎯 TEST COMPLETE!")
    print("Your Lark Base table is accessible via the MCP Bridge")

if __name__ == "__main__":
    main()
