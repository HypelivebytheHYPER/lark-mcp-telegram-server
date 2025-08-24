#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ตัวอย่างการใช้งาน MCP Bridge ด้วย Python (ภาษาไทย)
"""

import requests
import json
from datetime import datetime

# ตั้งค่าระบบ
MCP_URL = "https://lark-mcp-telegram-server.onrender.com/mcp/invoke"
YOUR_APP_TOKEN = "SEkObxgDpaPZbss1T3RlHzamgac"  # App token ของคุณ
YOUR_TABLE_ID = "tblGhWiw3dzgdsfw"              # Table ID ของคุณ

def call_mcp(tool_name, arguments=None):
    """
    เรียกใช้ MCP tool
    
    Args:
        tool_name (str): ชื่อ tool ที่ต้องการใช้
        arguments (dict): พารามิเตอร์สำหรับ tool
    
    Returns:
        dict: ผลลัพธ์จาก MCP
    """
    if arguments is None:
        arguments = {}
    
    payload = {
        "jsonrpc": "2.0",
        "id": f"python_client_{datetime.now().strftime('%H%M%S')}",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    try:
        response = requests.post(MCP_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode error: {str(e)}"}

def get_available_tools():
    """ดูเครื่องมือทั้งหมดที่ใช้ได้"""
    print("🔧 กำลังดึงรายการเครื่องมือทั้งหมด...")
    
    payload = {
        "jsonrpc": "2.0",
        "id": "tools_list",
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(MCP_URL, json=payload, timeout=10)
        result = response.json()
        
        if 'result' in result and 'tools' in result['result']:
            tools = result['result']['tools']
            print(f"✅ พบเครื่องมือทั้งหมด {len(tools)} ตัว:")
            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool['name']}")
                print(f"      📝 {tool['description']}")
            return tools
        else:
            print("❌ ไม่สามารถดึงรายการเครื่องมือได้")
            return []
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        return []

def list_bitable_tables():
    """แสดงตารางทั้งหมดใน Bitable"""
    print(f"\n📊 กำลังดึงรายการตารางจาก Bitable...")
    
    result = call_mcp("list_bitable_tables", {
        "app_token": YOUR_APP_TOKEN
    })
    
    if 'result' in result:
        data = result['result']
        if 'tables' in data:
            tables = data['tables']
            print(f"✅ พบตารางทั้งหมด {len(tables)} ตาราง:")
            for i, table in enumerate(tables, 1):
                name = table.get('name', 'ไม่มีชื่อ')
                table_id = table.get('table_id', 'N/A')
                print(f"   {i}. {name}")
                print(f"      🆔 {table_id}")
                if table_id == YOUR_TABLE_ID:
                    print(f"      🎯 นี่คือตารางเป้าหมายของคุณ!")
            return tables
        else:
            print("📊 ข้อมูล:", json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("❌ เกิดข้อผิดพลาด:", result.get('error', 'Unknown error'))
    
    return []

def search_table_records():
    """ค้นหาข้อมูลในตาราง"""
    print(f"\n🔍 กำลังค้นหาข้อมูลในตาราง {YOUR_TABLE_ID}...")
    
    result = call_mcp("bitable.v1.appTableRecord.search", {
        "app_token": YOUR_APP_TOKEN,
        "table_id": YOUR_TABLE_ID
    })
    
    if 'result' in result:
        data = result['result']
        if 'items' in data:
            records = data['items']
            print(f"✅ พบข้อมูลทั้งหมด {len(records)} รายการ:")
            
            for i, record in enumerate(records[:3], 1):  # แสดงแค่ 3 รายการแรก
                print(f"\n   📄 รายการที่ {i}:")
                print(f"      🆔 Record ID: {record.get('record_id', 'N/A')}")
                
                fields = record.get('fields', {})
                print(f"      📝 ฟิลด์ทั้งหมด {len(fields)} ฟิลด์:")
                
                for field_id, value in list(fields.items())[:3]:  # แสดงแค่ 3 ฟิลด์แรก
                    value_str = str(value)[:50]
                    if len(str(value)) > 50:
                        value_str += "..."
                    print(f"         • {field_id}: {value_str}")
                
                if len(fields) > 3:
                    print(f"         ... และอีก {len(fields) - 3} ฟิลด์")
            
            if len(records) > 3:
                print(f"\n   ... และอีก {len(records) - 3} รายการ")
            
            return records
        else:
            print("📄 ข้อมูลที่ได้:", json.dumps(data, indent=2, ensure_ascii=False)[:500])
    else:
        error = result.get('error', {})
        print(f"❌ เกิดข้อผิดพลาด {error.get('code', 'N/A')}: {error.get('message', 'Unknown error')}")
    
    return []

def list_departments():
    """แสดงรายการแผนกทั้งหมด"""
    print(f"\n🏢 กำลังดึงรายการแผนก...")
    
    result = call_mcp("list_departments", {})
    
    if 'result' in result:
        data = result['result']
        if 'items' in data:
            departments = data['items']
            print(f"✅ พบแผนกทั้งหมด {len(departments)} แผนก:")
            for i, dept in enumerate(departments, 1):
                name = dept.get('name', 'ไม่มีชื่อ')
                dept_id = dept.get('department_id', 'N/A')
                member_count = dept.get('member_count', 0)
                print(f"   {i}. {name}")
                print(f"      🆔 {dept_id} | 👥 สมาชิก {member_count} คน")
            return departments
        else:
            print("🏢 ข้อมูล:", json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("❌ เกิดข้อผิดพลาด:", result.get('error', 'Unknown error'))
    
    return []

def create_sample_record():
    """สร้างรายการตัวอย่าง (ถ้าต้องการ)"""
    print(f"\n➕ ต้องการสร้างรายการใหม่หรือไม่? (y/n): ", end="")
    choice = input().lower().strip()
    
    if choice == 'y':
        print("📝 กำลังสร้างรายการตัวอย่าง...")
        
        # ตัวอย่างข้อมูลที่จะสร้าง
        sample_data = {
            "app_token": YOUR_APP_TOKEN,
            "table_id": YOUR_TABLE_ID,
            "fields": {
                "text_field": f"รายการทดสอบ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "number_field": 42
            }
        }
        
        result = call_mcp("bitable.v1.appTableRecord.create", sample_data)
        
        if 'result' in result:
            print("✅ สร้างรายการใหม่สำเร็จ!")
            print("📄 ข้อมูล:", json.dumps(result['result'], indent=2, ensure_ascii=False))
        else:
            print("❌ ไม่สามารถสร้างรายการได้:", result.get('error', 'Unknown error'))

def main():
    """ฟังก์ชันหลัก"""
    print("🎯 ยินดีต้อนรับสู่ MCP Bridge Testing Tool!")
    print("=" * 50)
    
    print("\n🔗 ทดสอบการเชื่อมต่อ...")
    print(f"📡 Server: {MCP_URL}")
    print(f"📊 App Token: {YOUR_APP_TOKEN}")
    print(f"📋 Table ID: {YOUR_TABLE_ID}")
    
    # ทดสอบการเชื่อมต่อ
    try:
        response = requests.get("https://lark-mcp-telegram-server.onrender.com/health", timeout=5)
        if response.status_code == 200:
            print("✅ เชื่อมต่อ server สำเร็จ!")
        else:
            print(f"⚠️ Server ตอบกลับ status code: {response.status_code}")
    except:
        print("❌ ไม่สามารถเชื่อมต่อ server ได้")
        return
    
    # เริ่มทดสอบฟีเจอร์ต่างๆ
    print("\n" + "=" * 50)
    
    # 1. ดูเครื่องมือทั้งหมด
    tools = get_available_tools()
    
    # 2. ดูตารางใน Bitable
    tables = list_bitable_tables()
    
    # 3. ค้นหาข้อมูลในตาราง
    records = search_table_records()
    
    # 4. ดูรายการแผนก
    departments = list_departments()
    
    # 5. สร้างรายการใหม่ (เป็นตัวเลือก)
    create_sample_record()
    
    print("\n" + "=" * 50)
    print("🎉 การทดสอบเสร็จสิ้น!")
    print(f"📊 สรุป: พบ {len(tools)} เครื่องมือ, {len(tables)} ตาราง, {len(records)} รายการ, {len(departments)} แผนก")
    print("\n📖 อ่านคู่มือเพิ่มเติมได้ที่: docs/คู่มือการใช้งาน-ไทย.md")

if __name__ == "__main__":
    main()
