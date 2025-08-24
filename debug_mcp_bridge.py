#!/usr/bin/env python3
"""
Debug script to test MCP Bridge import and routing
"""

import sys
import os

print("🔍 MCP BRIDGE IMPORT DEBUG")
print("==========================")
print(f"Python path: {sys.path}")
print(f"Current dir: {os.getcwd()}")
print(f"Files in current dir: {[f for f in os.listdir('.') if 'mcp' in f.lower()]}")

print("\n📋 TESTING IMPORTS:")

# Test 1: Import mcp_bridge
try:
    from mcp_bridge import router
    print("✅ from mcp_bridge import router: SUCCESS")
    print(f"   Router type: {type(router)}")
    print(f"   Routes: {len(router.routes)}")
    
    # Check routes
    for route in router.routes:
        print(f"   - {route.methods} {route.path}")
        
except Exception as e:
    print(f"❌ from mcp_bridge import router: FAILED - {e}")

print("\n📋 TESTING MCP_BRIDGE_ENABLED:")
MCP_BRIDGE_ENABLED = os.getenv("MCP_BRIDGE_ENABLED", "true").lower() == "true"
print(f"MCP_BRIDGE_ENABLED: {MCP_BRIDGE_ENABLED}")

print("\n📋 TESTING APP.PY INTEGRATION:")
try:
    # Simulate what app.py does
    if MCP_BRIDGE_ENABLED:
        from mcp_bridge import router as mcp_bridge
        print("✅ App.py style import: SUCCESS")
        print(f"   Endpoints available: {[r.path for r in mcp_bridge.routes]}")
    else:
        print("❌ MCP_BRIDGE_ENABLED is False")
except Exception as e:
    print(f"❌ App.py style import: FAILED - {e}")

print("\n🎯 DIAGNOSIS:")
print("============")

# Check environment
env_vars = ["MCP_BRIDGE_ENABLED", "MCP_PROXY_ENABLED", "SUPABASE_URL"]
for var in env_vars:
    value = os.getenv(var, "NOT_SET")
    print(f"{var}: {value}")

print("\n💡 SOLUTION:")
print("===========")
print("If imports work locally but not in production:")
print("1. Check if mcp_bridge.py is deployed")
print("2. Verify environment variables")
print("3. Check FastAPI router inclusion order")
print("4. Test with explicit app restart")
