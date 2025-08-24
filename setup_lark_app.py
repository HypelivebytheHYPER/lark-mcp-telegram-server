#!/usr/bin/env python3
"""
LarkSuite App Setup Helper
Creates a test configuration for your LarkSuite app
"""

import os
import requests
import json

def test_app_credentials(app_id, app_secret):
    """Test if LarkSuite app credentials work"""
    print(f"🧪 Testing LarkSuite App Credentials...")
    print(f"   App ID: {app_id[:10]}...")
    print(f"   App Secret: {'*' * len(app_secret)}")
    
    # Test token generation
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        
        if response.status_code == 200 and result.get("code") == 0:
            token = result["tenant_access_token"]
            print(f"   ✅ SUCCESS! Token generated: {token[:20]}...")
            
            # Test a simple API call
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Try to list apps (this should work with any valid token)
            test_url = "https://open.larksuite.com/open-apis/bitable/v1/apps"
            test_response = requests.get(test_url, headers=headers, timeout=10)
            
            if test_response.status_code == 200:
                print(f"   ✅ API Access confirmed!")
                return True, token
            else:
                print(f"   ⚠️  Token works but API access limited: {test_response.status_code}")
                return True, token
        else:
            print(f"   ❌ Token generation failed: {result}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None

def test_table_access(token, app_token, table_id):
    """Test access to specific table"""
    print(f"\n🎯 Testing Your Specific Table Access...")
    print(f"   Base Token: {app_token}")
    print(f"   Table ID: {table_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test table schema access
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                table_data = result["data"]["table"]
                print(f"   ✅ Table access successful!")
                print(f"   📋 Table name: {table_data.get('name', 'Unknown')}")
                print(f"   📊 Table ID confirmed: {table_data.get('table_id')}")
                return True
            else:
                print(f"   ❌ Table access failed: {result}")
                return False
        else:
            print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def create_env_file(app_id, app_secret):
    """Create .env file for local testing"""
    env_content = f"""# LarkSuite API Configuration
LARK_APP_ID={app_id}
LARK_APP_SECRET={app_secret}

# Your Table Details  
YOUR_APP_TOKEN=SEkObxgDpaPZbss1T3RlHzamgac
YOUR_TABLE_ID=tblGhWiw3dzgdsfw
"""
    
    with open(".env.lark", "w") as f:
        f.write(env_content)
    print(f"   📄 Created .env.lark file for local testing")

def main():
    print("🚀 LARKSUITE APP SETUP HELPER")
    print("=" * 50)
    
    # Check if credentials are already set
    app_id = os.getenv("LARK_APP_ID")
    app_secret = os.getenv("LARK_APP_SECRET")
    
    if not app_id or not app_secret:
        print("⚠️  LarkSuite credentials not found in environment")
        print("\n📋 To set up:")
        print("1. Go to: https://open.larksuite.com/app")
        print("2. Create or select your app")
        print("3. Copy App ID and App Secret")
        print("4. Set environment variables:")
        print("   export LARK_APP_ID='your_app_id'")
        print("   export LARK_APP_SECRET='your_app_secret'")
        print("\n💡 Or add them to Render dashboard environment variables")
        return
    
    # Test credentials
    success, token = test_app_credentials(app_id, app_secret)
    
    if success and token:
        # Test table access
        table_success = test_table_access(
            token, 
            "SEkObxgDpaPZbss1T3RlHzamgac", 
            "tblGhWiw3dzgdsfw"
        )
        
        if table_success:
            print(f"\n🎉 COMPLETE SUCCESS!")
            print(f"✅ Your LarkSuite app can access the table")
            print(f"✅ Enhanced MCP bridge will work with real data")
        else:
            print(f"\n⚠️  App works but table access limited")
            print(f"💡 Check if your app has permission to access this specific Base")
        
        # Create local env file
        create_env_file(app_id, app_secret)
        
        print(f"\n📋 Next Steps:")
        print(f"1. Add these to Render environment variables:")
        print(f"   LARK_APP_ID={app_id}")
        print(f"   LARK_APP_SECRET={app_secret}")
        print(f"2. Redeploy your Render service")
        print(f"3. Test with: python3 final_verification.py")
        
    else:
        print(f"\n❌ Setup incomplete - check your credentials")

if __name__ == "__main__":
    main()
