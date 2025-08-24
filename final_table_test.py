#!/usr/bin/env python3
"""
FINAL TABLE TEST - Testing specific LarkSuite table access
Target: 📝 MEETING MINUTE table (tblxxX1koDNyEkkF)
URL: https://tsg9eq7nxo3w.sg.larksuite.com/base/SEkObxgDpaPZbss1T3RlHzamgac?table=tblxxX1koDNyEkkF&view=vewt8TGKD0
"""

import requests
import json
import time

# Your specific table details from the URL
BASE_URL = "https://lark-mcp-telegram-server.onrender.com"
APP_TOKEN = "SEkObxgDpaPZbss1T3RlHzamgac"
TARGET_TABLE_ID = "tblxxX1koDNyEkkF"  # 📝 MEETING MINUTE table
VIEW_ID = "vewt8TGKD0"

def test_table_access():
    """Test comprehensive access to your specific MEETING MINUTE table"""
    print("🎯 FINAL TABLE TEST")
    print("=" * 60)
    print(f"📝 Testing: MEETING MINUTE table")
    print(f"🔗 Base: {APP_TOKEN}")
    print(f"📋 Table: {TARGET_TABLE_ID}")
    print(f"👁️ View: {VIEW_ID}")
    print()

def test_1_list_tables():
    """Test 1: Verify table exists in base"""
    print("1️⃣ Testing: List all tables and find target")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "bitable_list_tables",
            "arguments": {
                "app_token": APP_TOKEN,
                "page_size": 20
            }
        },
        "id": "test_list_tables"
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
                    print(f"   ✅ Found {len(tables)} tables in Base")
                    
                    target_found = False
                    for table in tables:
                        name = table.get("name", "Unknown")
                        table_id = table.get("table_id", "N/A")
                        is_target = table_id == TARGET_TABLE_ID
                        marker = "🎯" if is_target else "📄"
                        print(f"      {marker} {name} ({table_id})")
                        if is_target:
                            target_found = True
                    
                    if target_found:
                        print(f"   ✅ Target table found: 📝 MEETING MINUTE")
                        return True
                    else:
                        print(f"   ❌ Target table {TARGET_TABLE_ID} not found")
                        return False
                else:
                    print(f"   ❌ Unexpected response format")
                    return False
            else:
                print(f"   ❌ Error in response: {result}")
                return False
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

def test_2_table_schema():
    """Test 2: Get table schema and field definitions"""
    print("\n2️⃣ Testing: Get table schema and fields")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "bitable_get_table_schema",
            "arguments": {
                "app_token": APP_TOKEN,
                "table_id": TARGET_TABLE_ID
            }
        },
        "id": "test_schema"
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
            if "result" in result and result["result"].get("code") == 0:
                data = result["result"]["data"]
                fields = data.get("fields", [])
                
                print(f"   ✅ Table schema retrieved successfully")
                print(f"   📊 Found {len(fields)} fields:")
                
                for field in fields[:10]:  # Show first 10 fields
                    field_name = field.get("field_name", "Unknown")
                    field_type = field.get("type", "unknown")
                    print(f"      • {field_name} ({field_type})")
                
                if len(fields) > 10:
                    print(f"      ... and {len(fields) - 10} more fields")
                
                return True, fields
            else:
                print(f"   ❌ Schema error: {result}")
                return False, []
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False, []
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False, []

def test_3_list_records():
    """Test 3: List records from the table"""
    print("\n3️⃣ Testing: List records from MEETING MINUTE table")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "bitable_list_records",
            "arguments": {
                "app_token": APP_TOKEN,
                "table_id": TARGET_TABLE_ID,
                "view_id": VIEW_ID,
                "page_size": 5
            }
        },
        "id": "test_records"
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
                    records = content["data"]["items"]
                    total = content["data"].get("total", len(records))
                    
                    print(f"   ✅ Records retrieved successfully")
                    print(f"   📊 Total records: {total}")
                    print(f"   📋 Sample records: {len(records)}")
                    
                    for i, record in enumerate(records, 1):
                        record_id = record.get("record_id", "Unknown")
                        fields = record.get("fields", {})
                        print(f"      {i}. Record {record_id[:8]}... ({len(fields)} fields)")
                        
                        # Show first few field values
                        field_count = 0
                        for field_name, field_value in fields.items():
                            if field_count < 3:  # Show first 3 fields
                                value_preview = str(field_value)[:50]
                                if len(str(field_value)) > 50:
                                    value_preview += "..."
                                print(f"         • {field_name}: {value_preview}")
                                field_count += 1
                        
                        if len(fields) > 3:
                            print(f"         ... and {len(fields) - 3} more fields")
                        print()
                    
                    return True, records
                else:
                    print(f"   ❌ No records found or unexpected format")
                    return False, []
            else:
                print(f"   ❌ Error in response: {result}")
                return False, []
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False, []
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False, []

def test_4_mcp_tools():
    """Test 4: Verify all MCP tools are available"""
    print("\n4️⃣ Testing: MCP Tools availability")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": "test_tools"
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
            if "result" in result and "tools" in result["result"]:
                tools = result["result"]["tools"]
                
                print(f"   ✅ MCP Tools available: {len(tools)}")
                
                bitable_tools = [t for t in tools if t["name"].startswith("bitable_")]
                print(f"   🔥 Bitable tools: {len(bitable_tools)}")
                
                for tool in bitable_tools:
                    print(f"      • {tool['name']}")
                
                return True, len(tools)
            else:
                print(f"   ❌ Error: {result}")
                return False, 0
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False, 0
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False, 0

def main():
    """Run all tests"""
    print()
    test_table_access()
    
    # Run all tests
    success_count = 0
    total_tests = 4
    
    # Test 1: List tables
    if test_1_list_tables():
        success_count += 1
    
    # Test 2: Table schema
    schema_success, fields = test_2_table_schema()
    if schema_success:
        success_count += 1
    
    # Test 3: List records
    records_success, records = test_3_list_records()
    if records_success:
        success_count += 1
    
    # Test 4: MCP tools
    tools_success, tool_count = test_4_mcp_tools()
    if tools_success:
        success_count += 1
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"✅ Tests passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Enhanced MCP Bridge working perfectly")
        print("✅ LarkSuite API integration confirmed")
        print("✅ Your MEETING MINUTE table is fully accessible")
        print("✅ Ready for production use!")
        
        if records:
            print(f"\n📋 Your table contains {len(records)} sample records")
            print(f"🔗 Direct access via: {BASE_URL}/mcp/invoke")
    else:
        print("⚠️  Some tests failed - check output above")
    
    print("\n🔗 Table URL: https://tsg9eq7nxo3w.sg.larksuite.com/base/SEkObxgDpaPZbss1T3RlHzamgac?table=tblxxX1koDNyEkkF&view=vewt8TGKD0")

if __name__ == "__main__":
    main()
