#!/usr/bin/env python3
"""
COMPLETE CRUD DEMO - 100% Working Proof
Demonstrates all operations on your MEETING MINUTE table with real data
"""

import requests
import json
import time
from datetime import datetime

# Your table details
BASE_URL = "https://lark-mcp-telegram-server.onrender.com"
APP_TOKEN = "SEkObxgDpaPZbss1T3RlHzamgac"
TABLE_ID = "tblxxX1koDNyEkkF"  # 📝 MEETING MINUTE table

def mcp_call(tool_name, arguments):
    """Helper function to make MCP calls"""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": f"demo_{int(time.time())}"
    }
    
    response = requests.post(
        f"{BASE_URL}/mcp/invoke",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30
    )
    
    return response.status_code, response.json()

def demo_1_read_existing_records():
    """Demo 1: Read existing records to show data access works"""
    print("1️⃣ DEMO: Reading Existing Meeting Minutes")
    print("-" * 50)
    
    status, result = mcp_call("bitable_list_records", {
        "app_token": APP_TOKEN,
        "table_id": TABLE_ID,
        "page_size": 3
    })
    
    if status == 200 and "result" in result:
        content = json.loads(result["result"]["content"])
        records = content["data"]["items"]
        
        print(f"✅ Successfully retrieved {len(records)} meeting records")
        print(f"📊 Total records in table: {content['data'].get('total', 'unknown')}")
        
        for i, record in enumerate(records, 1):
            fields = record.get("fields", {})
            record_id = record.get("record_id", "unknown")
            
            print(f"\n📋 Meeting Record #{i} ({record_id[:8]}...):")
            
            # Show key fields
            if "Meeting Title" in fields:
                print(f"   📝 Title: {fields['Meeting Title']}")
            if "Meeting Date" in fields:
                print(f"   📅 Date: {fields['Meeting Date']}")
            if "Attendees" in fields and fields["Attendees"]:
                attendee_count = len(fields["Attendees"]) if isinstance(fields["Attendees"], list) else 1
                print(f"   👥 Attendees: {attendee_count} people")
            if "Action Items" in fields:
                action_status = "Yes" if fields["Action Items"] else "None"
                print(f"   ✅ Action Items: {action_status}")
            
            print(f"   📊 Total fields: {len(fields)}")
        
        return True, records[0]["record_id"] if records else None
    else:
        print(f"❌ Failed to read records: {result}")
        return False, None

def demo_2_get_specific_record(record_id):
    """Demo 2: Get a specific record by ID"""
    print(f"\n2️⃣ DEMO: Getting Specific Record Details")
    print("-" * 50)
    
    status, result = mcp_call("bitable_get_record", {
        "app_token": APP_TOKEN,
        "table_id": TABLE_ID,
        "record_id": record_id
    })
    
    if status == 200 and "result" in result:
        content = json.loads(result["result"]["content"])
        record = content["data"]["record"]
        fields = record.get("fields", {})
        
        print(f"✅ Successfully retrieved record: {record_id[:8]}...")
        print(f"📊 Record contains {len(fields)} fields:")
        
        # Display all fields with their values
        for field_name, field_value in fields.items():
            if field_value is not None:
                value_str = str(field_value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                print(f"   • {field_name}: {value_str}")
        
        return True
    else:
        print(f"❌ Failed to get record: {result}")
        return False

def demo_3_create_test_record():
    """Demo 3: Create a new test meeting record"""
    print(f"\n3️⃣ DEMO: Creating New Test Meeting Record")
    print("-" * 50)
    
    # Create a test meeting record
    test_data = {
        "Meeting Title": f"Test Meeting - MCP Demo {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "Meeting Date": datetime.now().strftime('%Y-%m-%d'),
        "Status": "Completed",
        "Meeting Type": "Demo"
    }
    
    print(f"📝 Creating test meeting: {test_data['Meeting Title']}")
    
    status, result = mcp_call("bitable_create_record", {
        "app_token": APP_TOKEN,
        "table_id": TABLE_ID,
        "fields": test_data
    })
    
    if status == 200 and "result" in result:
        content = json.loads(result["result"]["content"])
        if "data" in content and "record" in content["data"]:
            new_record = content["data"]["record"]
            record_id = new_record.get("record_id")
            
            print(f"✅ Successfully created new record!")
            print(f"🆔 New Record ID: {record_id}")
            print(f"📊 Created with {len(test_data)} fields")
            
            return True, record_id
        else:
            print(f"❌ Unexpected response format: {content}")
            return False, None
    else:
        print(f"❌ Failed to create record: {result}")
        return False, None

def demo_4_update_record(record_id):
    """Demo 4: Update the test record"""
    print(f"\n4️⃣ DEMO: Updating Test Record")
    print("-" * 50)
    
    update_data = {
        "Meeting Title": f"Updated Test Meeting - MCP Demo {datetime.now().strftime('%H:%M:%S')}",
        "Status": "Updated via MCP",
        "Notes": "This record was created and updated via MCP Bridge to demonstrate full CRUD functionality!"
    }
    
    print(f"📝 Updating record {record_id[:8]}... with new data")
    
    status, result = mcp_call("bitable_update_record", {
        "app_token": APP_TOKEN,
        "table_id": TABLE_ID,
        "record_id": record_id,
        "fields": update_data
    })
    
    if status == 200 and "result" in result:
        content = json.loads(result["result"]["content"])
        if "data" in content:
            print(f"✅ Successfully updated record!")
            print(f"📝 Updated fields: {list(update_data.keys())}")
            return True
        else:
            print(f"❌ Unexpected response: {content}")
            return False
    else:
        print(f"❌ Failed to update record: {result}")
        return False

def demo_5_search_records():
    """Demo 5: Search for records with filter"""
    print(f"\n5️⃣ DEMO: Searching Records with Filter")
    print("-" * 50)
    
    # Search for records containing "Test" in the title
    print("🔍 Searching for records with 'Test' in Meeting Title...")
    
    status, result = mcp_call("bitable_search_records", {
        "app_token": APP_TOKEN,
        "table_id": TABLE_ID,
        "filter": 'SEARCH([Meeting Title], "Test")',
        "page_size": 10
    })
    
    if status == 200 and "result" in result:
        content = json.loads(result["result"]["content"])
        if "data" in content and "items" in content["data"]:
            records = content["data"]["items"]
            total = content["data"].get("total", len(records))
            
            print(f"✅ Found {len(records)} matching records (total: {total})")
            
            for i, record in enumerate(records, 1):
                fields = record.get("fields", {})
                title = fields.get("Meeting Title", "No title")
                status_field = fields.get("Status", "No status")
                print(f"   {i}. {title} - Status: {status_field}")
            
            return True
        else:
            print(f"❌ No matching records found")
            return False
    else:
        print(f"❌ Search failed: {result}")
        return False

def demo_6_cleanup_test_record(record_id):
    """Demo 6: Clean up test record (optional)"""
    print(f"\n6️⃣ DEMO: Cleaning Up Test Record")
    print("-" * 50)
    
    print(f"🧹 Deleting test record {record_id[:8]}...")
    
    status, result = mcp_call("bitable_delete_record", {
        "app_token": APP_TOKEN,
        "table_id": TABLE_ID,
        "record_id": record_id
    })
    
    if status == 200:
        print(f"✅ Successfully deleted test record!")
        print(f"🧹 Cleanup completed")
        return True
    else:
        print(f"❌ Failed to delete record: {result}")
        print(f"ℹ️  You may need to manually delete record {record_id[:8]}...")
        return False

def main():
    """Run complete CRUD demonstration"""
    print("🚀 COMPLETE CRUD DEMONSTRATION")
    print("=" * 60)
    print("📝 Target: MEETING MINUTE table")
    print("🎯 Goal: Prove 100% functionality with real operations")
    print("=" * 60)
    
    success_count = 0
    total_demos = 6
    
    # Demo 1: Read existing data
    read_success, sample_record_id = demo_1_read_existing_records()
    if read_success:
        success_count += 1
    
    # Demo 2: Get specific record (if we have one)
    if sample_record_id:
        if demo_2_get_specific_record(sample_record_id):
            success_count += 1
    else:
        print(f"\n2️⃣ DEMO: Skipped (no existing records)")
        total_demos -= 1
    
    # Demo 3: Create new record
    create_success, new_record_id = demo_3_create_test_record()
    if create_success:
        success_count += 1
    
    # Demo 4: Update record (if created successfully)
    if new_record_id:
        if demo_4_update_record(new_record_id):
            success_count += 1
    else:
        print(f"\n4️⃣ DEMO: Skipped (creation failed)")
        total_demos -= 1
    
    # Demo 5: Search records
    if demo_5_search_records():
        success_count += 1
    
    # Demo 6: Cleanup (if we created a record)
    if new_record_id:
        if demo_6_cleanup_test_record(new_record_id):
            success_count += 1
    else:
        print(f"\n6️⃣ DEMO: Skipped (no record to cleanup)")
        total_demos -= 1
    
    # Final results
    print("\n" + "=" * 60)
    print("📊 FINAL DEMONSTRATION RESULTS")
    print("=" * 60)
    print(f"✅ Successful operations: {success_count}/{total_demos}")
    
    if success_count == total_demos:
        print("🎉 100% SUCCESS - ALL CRUD OPERATIONS WORKING!")
        print("✅ CREATE: New records successfully added")
        print("✅ READ: Existing data retrieved perfectly") 
        print("✅ UPDATE: Records modified successfully")
        print("✅ DELETE: Test cleanup completed")
        print("✅ SEARCH: Filtered queries working")
        print("\n🏆 YOUR MCP BRIDGE IS FULLY OPERATIONAL!")
    else:
        print(f"⚠️  {total_demos - success_count} operations had issues")
        print("📋 Check the output above for details")
    
    print(f"\n🔗 Table URL: https://tsg9eq7nxo3w.sg.larksuite.com/base/SEkObxgDpaPZbss1T3RlHzamgac?table=tblxxX1koDNyEkkF&view=vewt8TGKD0")
    print(f"🌐 MCP Endpoint: {BASE_URL}/mcp/invoke")

if __name__ == "__main__":
    main()
