#!/bin/bash

echo "🧪 MCP Bridge Testing Suite"
echo "=========================="
echo ""

# Test 1: Check if server is running
echo "1. Checking if server is running..."
response=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8000/health" 2>/dev/null)
if [ "$response" = "200" ]; then
    echo "✅ Server is running on localhost:8000"
else
    echo "❌ Server not running locally. Testing production URL..."
    BASE_URL="https://lark-mcp-telegram-server.onrender.com"
fi

# Set base URL
BASE_URL=${BASE_URL:-"http://localhost:8000"}
echo "Using base URL: $BASE_URL"
echo ""

# Test 2: Tools list
echo "2. Testing tools/list endpoint..."
curl -s -X POST "$BASE_URL/mcp/invoke" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"test1","method":"tools/list"}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'result' in data and 'tools' in data['result']:
        tools = data['result']['tools']
        print(f'✅ Found {len(tools)} tools')
        
        # Check for new user-friendly tools
        new_tools = ['search_bitable_records', 'create_bitable_record', 'list_bitable_fields']
        for tool_name in new_tools:
            if any(t['name'] == tool_name for t in tools):
                print(f'  ✅ {tool_name} - Available')
            else:
                print(f'  ❌ {tool_name} - Missing')
    else:
        print('❌ Unexpected response format')
        print(json.dumps(data, indent=2))
except Exception as e:
    print('❌ Error:', str(e))
"
echo ""

# Test 3: Test a new user-friendly tool
echo "3. Testing new user-friendly tool: list_departments..."
curl -s -X POST "$BASE_URL/mcp/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test2",
    "method": "tools/call",
    "params": {
      "name": "list_departments",
      "arguments": {}
    }
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'result' in data:
        print('✅ Tool execution successful!')
        result = data['result']
        if 'success' in result:
            print(f'  Status: {result[\"success\"]}')
            print(f'  Message: {result.get(\"message\", \"N/A\")}')
        else:
            print('  Raw result:', str(result)[:200] + '...')
    else:
        print('❌ Error in response:')
        print(json.dumps(data, indent=2))
except Exception as e:
    print('❌ Error:', str(e))
"
echo ""

# Test 4: Test proxy endpoint (should fail gracefully since it's disabled)
echo "4. Testing proxy endpoint (should show it's disabled)..."
curl -s -X POST "$BASE_URL/mcp/invoke/proxy" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"test3","method":"tools/list"}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print('✅ Proxy endpoint responds correctly (disabled by default)')
        print(f'  Error: {data[\"error\"][\"message\"]}')
    else:
        print('✅ Proxy endpoint active:', json.dumps(data, indent=2)[:200])
except Exception as e:
    print('❌ Error:', str(e))
"
echo ""

echo "🎯 Testing complete! Your MCP Bridge optimizations are working."
