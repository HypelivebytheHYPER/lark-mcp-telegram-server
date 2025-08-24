#!/usr/bin/env python3
"""
Test script to verify JWT encoding fixes for HypeTask features
"""

import os
import base64
import json
import asyncio
import httpx
from datetime import datetime

# Mock Supabase JWT with newlines (simulate the problem)
MOCK_JWT_WITH_NEWLINES = """eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBlbGplZ251c2h0cW1tZW55Z2RvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM0MzU1OTUsImV4cCI6MjA2OTAxMTU5NX0.PyrCEUuUuexevIxEZ8KEKBq1XDD7j2fEoyk8paMpefc
"""

def test_jwt_cleaning():
    """Test JWT token cleaning function"""
    print("🧪 Testing JWT cleaning...")
    
    # Simulate the old problematic way
    dirty_jwt = MOCK_JWT_WITH_NEWLINES
    print(f"❌ Dirty JWT (has newlines): {repr(dirty_jwt)}")
    print(f"   Length: {len(dirty_jwt)} chars")
    print(f"   Contains \\n: {'\\n' in dirty_jwt}")
    
    # Clean it the new way
    clean_jwt = dirty_jwt.strip().replace('\n', '').replace(' ', '')
    print(f"✅ Clean JWT: {clean_jwt[:50]}...")
    print(f"   Length: {len(clean_jwt)} chars")
    print(f"   Contains \\n: {'\\n' in clean_jwt}")
    
    # Validate JWT format
    jwt_parts = clean_jwt.split('.')
    print(f"🔍 JWT parts: {len(jwt_parts)} (should be 3)")
    
    if len(jwt_parts) == 3:
        try:
            # Decode header
            header_data = base64.b64decode(jwt_parts[0] + '==').decode('utf-8')
            payload_data = base64.b64decode(jwt_parts[1] + '==').decode('utf-8')
            
            print(f"📋 Header: {json.loads(header_data)}")
            print(f"📋 Payload: {json.loads(payload_data)}")
            print("✅ JWT is valid!")
            return True
        except Exception as e:
            print(f"❌ JWT decode error: {e}")
            return False
    else:
        print("❌ JWT format invalid")
        return False

def test_header_creation():
    """Test header creation with clean JWT"""
    print("\n🧪 Testing header creation...")
    
    clean_jwt = MOCK_JWT_WITH_NEWLINES.strip().replace('\n', '').replace(' ', '')
    
    headers = {
        "apikey": clean_jwt,
        "Authorization": f"Bearer {clean_jwt}",
        "Content-Type": "application/json"
    }
    
    print("✅ Headers created successfully:")
    for key, value in headers.items():
        value_preview = value[:50] + "..." if len(value) > 50 else value
        print(f"   {key}: {value_preview}")
    
    # Test if headers would cause encoding issues
    try:
        # This is what httpx does internally
        for key, value in headers.items():
            encoded = value.encode('latin1')
        print("✅ Headers pass latin1 encoding test")
        return True
    except Exception as e:
        print(f"❌ Header encoding error: {e}")
        return False

async def test_hypetask_session_creation():
    """Test actual HypeTask session creation with production server"""
    print("\n🧪 Testing HypeTask session creation...")
    
    url = "https://lark-mcp-telegram-server.onrender.com/mcp/invoke"
    
    payload = {
        "jsonrpc": "2.0",
        "id": "jwt_test",
        "method": "tools/call",
        "params": {
            "name": "create_hypetask_session",
            "arguments": {
                "user_id": f"test_user_{datetime.now().strftime('%H%M%S')}",
                "platform": "test_jwt_fix"
            }
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            result = response.json()
            
            print(f"📡 Response status: {response.status_code}")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            
            if 'result' in result:
                if result['result'].get('success'):
                    print("✅ HypeTask session creation successful!")
                    return True
                else:
                    error_details = result['result'].get('details', 'Unknown error')
                    if 'Illegal header value' in error_details:
                        print("❌ Still has header encoding issues")
                    else:
                        print(f"⚠️  Different error: {error_details}")
                    return False
            else:
                print("❌ Unexpected response format")
                return False
                
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 JWT Encoding Fix Tests")
    print("=" * 50)
    
    # Test 1: JWT cleaning
    jwt_ok = test_jwt_cleaning()
    
    # Test 2: Header creation
    header_ok = test_header_creation()
    
    # Test 3: Live session creation
    session_ok = await test_hypetask_session_creation()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   JWT Cleaning: {'✅' if jwt_ok else '❌'}")
    print(f"   Header Creation: {'✅' if header_ok else '❌'}")
    print(f"   Live Session Test: {'✅' if session_ok else '❌'}")
    
    if all([jwt_ok, header_ok, session_ok]):
        print("\n🎉 All tests passed! JWT encoding is fixed!")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")

if __name__ == "__main__":
    asyncio.run(main())
