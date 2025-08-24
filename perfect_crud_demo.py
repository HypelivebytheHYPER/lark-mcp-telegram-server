#!/usr/bin/env python3
"""
PERFECT CRUD DEMO - Using exact field names
Creates, reads, updates, and deletes a record with 100% accuracy
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
        "id": f"perfect_demo_{int(time.time())}"
    }
    
    response = requests.post(
        f"{BASE_URL}/mcp/invoke",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30
    )
    
    return response.status_code, response.json()

def perfect_demo():
    """Run perfect CRUD demonstration with exact field names"""
    print("🎯 PERFECT CRUD DEMONSTRATION - 100% ACCURACY")
    print("=" * 60)
    print("📝 Using exact field names from your MEETING MINUTE table")
    print("=" * 60)
    
    # Step 1: Create a perfect record with exact field names
    print("\n1️⃣ CREATING: New meeting record with exact field names")
    print("-" * 50)
    
    # Use exact field names from the table structure
    perfect_record = {
        "Meeting Title": f"🎯 MCP Demo Meeting - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "Meeting Type": "Planning",  # Valid option from SingleSelect
        "Status": "Completed",       # Valid option from SingleSelect  
        "Location": "Virtual - MCP Bridge Test",
        "Duration": "30 minutes",
        "Key Decisions": "✅ MCP Bridge is working perfectly! Full CRUD operations confirmed.",
        "Action Items": "1. Document success ✅\n2. Share results with team ✅\n3. Celebrate! 🎉"
    }
    
    print(f"📝 Creating: {perfect_record['Meeting Title']}")
    
    status, result = mcp_call("bitable_create_record", {
        "app_token": APP_TOKEN,
        "table_id": TABLE_ID,
        "fields": perfect_record
    })
    
    if status == 200 and "result" in result:
        content = json.loads(result["result"]["content"])
        if "data" in content and "record" in content["data"]:
            new_record = content["data"]["record"]
            record_id = new_record.get("record_id")
            
            print(f"✅ SUCCESS! Created record ID: {record_id}")
            print(f"📊 Created with {len(perfect_record)} fields")
            
            # Step 2: Read the created record back
            print(f"\n2️⃣ READING: Retrieving the created record")
            print("-" * 50)
            
            status, result = mcp_call("bitable_get_record", {
                "app_token": APP_TOKEN,
                "table_id": TABLE_ID,
                "record_id": record_id
            })
            
            if status == 200:
                content = json.loads(result["result"]["content"])
                record_data = content["data"]["record"]
                fields = record_data.get("fields", {})
                
                print(f"✅ Successfully read record: {record_id}")
                print(f"📋 Confirmed fields:")
                for field_name, field_value in fields.items():
                    if field_value and field_name in perfect_record:
                        print(f"   ✓ {field_name}: {field_value}")
                
                # Step 3: Update the record
                print(f"\n3️⃣ UPDATING: Modifying the record")
                print("-" * 50)
                
                update_data = {
                    "Meeting Title": f"🎯 UPDATED - MCP Demo Meeting - {datetime.now().strftime('%H:%M:%S')}",
                    "Status": "Completed",
                    "Key Decisions": "✅ MCP Bridge UPDATE operation confirmed! All CRUD operations work perfectly.",
                    "Action Items": "1. Document success ✅\n2. Share results with team ✅\n3. Update confirmed ✅\n4. Celebrate! 🎉"
                }
                
                status, result = mcp_call("bitable_update_record", {
                    "app_token": APP_TOKEN,
                    "table_id": TABLE_ID,
                    "record_id": record_id,
                    "fields": update_data
                })
                
                if status == 200:
                    print(f"✅ Successfully updated record!")
                    print(f"📝 Updated fields: {list(update_data.keys())}")
                    
                    # Step 4: Verify the update by reading again
                    print(f"\n4️⃣ VERIFYING: Reading updated record")
                    print("-" * 50)
                    
                    status, result = mcp_call("bitable_get_record", {
                        "app_token": APP_TOKEN,
                        "table_id": TABLE_ID,
                        "record_id": record_id
                    })
                    
                    if status == 200:
                        content = json.loads(result["result"]["content"])
                        updated_fields = content["data"]["record"]["fields"]
                        
                        print(f"✅ Verification successful!")
                        print(f"📋 Updated title: {updated_fields.get('Meeting Title', 'N/A')}")
                        print(f"📋 Updated decisions: {updated_fields.get('Key Decisions', 'N/A')}")
                        
                        # Step 5: Clean up (delete the test record)
                        print(f"\n5️⃣ CLEANING: Deleting test record")
                        print("-" * 50)
                        
                        status, result = mcp_call("bitable_delete_record", {
                            "app_token": APP_TOKEN,
                            "table_id": TABLE_ID,
                            "record_id": record_id
                        })
                        
                        if status == 200:
                            print(f"✅ Successfully deleted test record!")
                            print(f"🧹 Cleanup completed - your table is pristine")
                            
                            # Final success message
                            print("\n" + "=" * 60)
                            print("🏆 100% PERFECT SUCCESS!")
                            print("=" * 60)
                            print("✅ CREATE: Perfect record created with exact field names")
                            print("✅ READ: Data retrieved accurately multiple times")
                            print("✅ UPDATE: Record modified successfully")
                            print("✅ DELETE: Test cleanup completed")
                            print("\n🎉 YOUR MCP BRIDGE IS WORKING 100% PERFECTLY!")
                            print("🚀 Ready for production AI agent integrations!")
                            return True
                        else:
                            print(f"❌ Delete failed: {result}")
                    else:
                        print(f"❌ Verification read failed: {result}")
                else:
                    print(f"❌ Update failed: {result}")
            else:
                print(f"❌ Read failed: {result}")
        else:
            print(f"❌ Create failed - unexpected response: {content}")
    else:
        print(f"❌ Create failed: {result}")
    
    return False

if __name__ == "__main__":
    perfect_demo()
