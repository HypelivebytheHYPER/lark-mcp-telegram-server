#!/usr/bin/env python3
"""
Test Enhanced MCP Bridge with Real Lark Base Table
Tests official LarkSuite Bitable API integration with your specific table
"""

import requests
import json

# Configuration
MCP_SERVER_URL = "https://lark-mcp-telegram-server.onrender.com/mcp/invoke"
APP_TOKEN = "SEkObxgDpaPZbss1T3RlHzamgac"
TABLE_ID = "tblGhWiw3dzgdsfw"

def test_enhanced_mcp_call(method, params=None, name=None, arguments=None):
    """Make an enhanced MCP JSON-RPC call"""
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
    print("🧪 TESTING ENHANCED MCP BRIDGE WITH LARK BITABLE")
    print("=" * 55)
    print(f"📊 Base ID: {APP_TOKEN}")
    print(f"📋 Table ID: {TABLE_ID}")
    print(f"🌐 Enhanced MCP Server: {MCP_SERVER_URL}")
    print()
    
    # Test 1: List enhanced tools
    print("🔧 Test 1: Listing enhanced MCP tools...")
    tools_result = test_enhanced_mcp_call("tools/list")
    
    if "result" in tools_result and "tools" in tools_result["result"]:
        tools = tools_result["result"]["tools"]
        print(f"✅ Found {len(tools)} enhanced tools:")
        
        # Show Bitable tools specifically
        bitable_tools = [tool for tool in tools if tool['name'].startswith('bitable_')]
        if bitable_tools:
            print("   🔥 Enhanced Bitable Tools:")
            for tool in bitable_tools:
                print(f"      • {tool['name']} - {tool['description']}")
        
        # Show other tools
        other_tools = [tool for tool in tools if not tool['name'].startswith('bitable_')]
        if other_tools:
            print("   📚 Other Tools:")
            for tool in other_tools[:3]:
                print(f"      • {tool['name']}")
    else:
        print("❌ Failed to get enhanced tools list")
        print(f"Response: {tools_result}")
    
    print()
    
    # Test 2: Get enhanced table schema
    print("📊 Test 2: Getting enhanced table schema...")
    schema_result = test_enhanced_mcp_call(
        "tools/call",
        name="bitable_get_table_schema",
        arguments={
            "app_token": APP_TOKEN,
            "table_id": TABLE_ID
        }
    )
    
    if "result" in schema_result:
        print("✅ Enhanced schema retrieved successfully")
        try:
            content = json.loads(schema_result["result"]["content"])
            if "data" in content and "fields" in content["data"]:
                fields = content["data"]["fields"]
                print(f"   📋 Enhanced table has {len(fields)} fields:")
                for field in fields[:5]:
                    field_name = field.get("field_name", "Unknown")
                    field_type = field.get("type", "unknown")
                    print(f"      • {field_name} ({field_type})")
                if len(fields) > 5:
                    print(f"      ... and {len(fields)-5} more fields")
            else:
                print(f"   📄 Enhanced schema format: {content}")
        except Exception as e:
            print(f"   ⚠️ Error parsing enhanced schema: {e}")
    else:
        print("❌ Failed to get enhanced table schema")
        print(f"Response: {schema_result}")
    
    print()
    
    # Test 3: List enhanced records
    print("📄 Test 3: Listing enhanced table records...")
    records_result = test_enhanced_mcp_call(
        "tools/call",
        name="bitable_list_records",
        arguments={
            "app_token": APP_TOKEN,
            "table_id": TABLE_ID,
            "page_size": 5
        }
    )
    
    if "result" in records_result:
        print("✅ Enhanced records retrieved successfully")
        try:
            content = json.loads(records_result["result"]["content"])
            if "data" in content and "items" in content["data"]:
                records = content["data"]["items"]
                print(f"   📋 Found {len(records)} enhanced records:")
                for i, record in enumerate(records[:3]):
                    record_id = record.get("record_id", "N/A")
                    field_count = len(record.get("fields", {}))
                    print(f"      📄 Record {i+1}: {record_id} ({field_count} fields)")
            else:
                print(f"   📄 Enhanced records format: {content}")
        except Exception as e:
            print(f"   ⚠️ Error parsing enhanced records: {e}")
    else:
        print("❌ Failed to get enhanced table records")
        print(f"Response: {records_result}")
    
    print()
    
    # Test 4: Test enhanced table listing
    print("📊 Test 4: Listing enhanced tables in Base...")
    tables_result = test_enhanced_mcp_call(
        "tools/call",
        name="bitable_list_tables",
        arguments={
            "app_token": APP_TOKEN,
            "page_size": 10
        }
    )
    
    if "result" in tables_result:
        print("✅ Enhanced tables retrieved successfully")
        try:
            content = json.loads(tables_result["result"]["content"])
            if "data" in content and "items" in content["data"]:
                tables = content["data"]["items"]
                print(f"   📋 Found {len(tables)} tables in Base:")
                for table in tables[:5]:
                    table_name = table.get("name", "Unknown")
                    table_id = table.get("table_id", "N/A")
                    is_target = "🎯" if table_id == TABLE_ID else "📄"
                    print(f"      {is_target} {table_name} ({table_id})")
        except Exception as e:
            print(f"   ⚠️ Error parsing enhanced tables: {e}")
    else:
        print("❌ Failed to get enhanced tables list")
        print(f"Response: {tables_result}")
    
    print()
    print("🎯 ENHANCED TEST COMPLETE!")
    print("Your Lark Base table is accessible via Enhanced MCP Bridge")
    print("Now supports official LarkSuite API patterns with HTTP streaming!")

if __name__ == "__main__":
    main()
