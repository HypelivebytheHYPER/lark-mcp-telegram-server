#!/bin/bash

echo "🎯 TESTING WITH REAL BITABLE DATA"
echo "================================="
echo ""
echo "App Token: SEkObxgDpaPZbss1T3RlHzamgac"
echo "Table ID: tblGhWiw3dzgdsfw" 
echo "Production URL: https://lark-mcp-telegram-server.onrender.com"
echo ""

# Test 1: Check tools/list
echo "🧪 Test 1: Check available tools on production server"
echo "----------------------------------------------------"
curl -s -X POST "https://lark-mcp-telegram-server.onrender.com/mcp/invoke" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"test1","method":"tools/list"}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'result' in data and 'tools' in data['result']:
        tools = data['result']['tools']
        print(f'✅ Found {len(tools)} tools on production server')
        
        # Check for new optimized tools
        new_tools = ['search_bitable_records', 'create_bitable_record', 'list_bitable_fields']
        found_new = 0
        for tool_name in new_tools:
            if any(t['name'] == tool_name for t in tools):
                print(f'  ✅ {tool_name} - Available')
                found_new += 1
            else:
                print(f'  ❌ {tool_name} - Not found')
        
        if found_new == 0:
            print('')
            print('⚠️  New optimized tools not found. Server needs redeployment.')
        else:
            print(f'🎉 Found {found_new}/{len(new_tools)} new optimized tools!')
            
    else:
        print('❌ Unexpected response')
        print(json.dumps(data, indent=2))
except Exception as e:
    print('❌ Error:', str(e))
"
echo ""

# Test 2: List tables in the app
echo "🧪 Test 2: List tables in your Bitable app"
echo "------------------------------------------"
curl -s -X POST "https://lark-mcp-telegram-server.onrender.com/mcp/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test2", 
    "method": "tools/call",
    "params": {
      "name": "list_bitable_tables",
      "arguments": {
        "app_token": "SEkObxgDpaPZbss1T3RlHzamgac"
      }
    }
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'result' in data:
        result = data['result']
        print('✅ Successfully connected to your Bitable!')
        
        if 'tables' in result:
            tables = result['tables']
            print(f'📊 Found {len(tables)} tables:')
            for table in tables:
                name = table.get('name', 'Unnamed')
                table_id = table.get('table_id', 'N/A')
                print(f'  - {name} (ID: {table_id})')
                if table_id == 'tblGhWiw3dzgdsfw':
                    print(f'    🎯 This is your target table!')
        else:
            print('Response:', str(result)[:200] + '...')
    else:
        print('❌ Error:', json.dumps(data.get('error', {}), indent=2))
except Exception as e:
    print('❌ Error:', str(e))
"
echo ""

# Test 3: Search records in specific table
echo "🧪 Test 3: Search records in your table"
echo "---------------------------------------"
curl -s -X POST "https://lark-mcp-telegram-server.onrender.com/mcp/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test3",
    "method": "tools/call", 
    "params": {
      "name": "bitable.v1.appTableRecord.search",
      "arguments": {
        "app_token": "SEkObxgDpaPZbss1T3RlHzamgac",
        "table_id": "tblGhWiw3dzgdsfw"
      }
    }
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'result' in data:
        result = data['result']
        print('✅ Successfully queried your table!')
        
        if 'items' in result:
            records = result['items']
            print(f'📋 Found {len(records)} records in table')
            
            if records:
                print('Sample record:')
                first_record = records[0]
                fields = first_record.get('fields', {})
                print(f'  Record ID: {first_record.get(\"record_id\", \"N/A\")}')
                print(f'  Fields: {len(fields)} total')
                for field_id, value in list(fields.items())[:3]:
                    print(f'    {field_id}: {str(value)[:50]}')
                if len(fields) > 3:
                    print(f'    ... and {len(fields) - 3} more')
            else:
                print('  (Table is empty)')
        else:
            print('Response:', str(result)[:200] + '...')
    else:
        error = data.get('error', {})
        print(f'❌ Error {error.get(\"code\", \"N/A\")}: {error.get(\"message\", \"N/A\")}')
except Exception as e:
    print('❌ Error:', str(e))
"
echo ""

# Test 4: Test proxy endpoint
echo "🧪 Test 4: Test proxy endpoint (should be disabled)"
echo "--------------------------------------------------"
curl -s -X POST "https://lark-mcp-telegram-server.onrender.com/mcp/invoke/proxy" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"test4","method":"tools/list"}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print('✅ Proxy endpoint responds correctly (disabled by default)')
        print(f'  Message: {data[\"error\"][\"message\"]}')
    else:
        print('✅ Proxy endpoint active:', str(data)[:100] + '...')
except Exception as e:
    print('❌ Error:', str(e))
"
echo ""

echo "🎯 Testing complete!"
echo ""
echo "📝 Summary:"
echo "- If optimized tools are missing: Deploy latest commit on Render"
echo "- If connection works: Your MCP Bridge is functional with real data"
echo "- Use the working tools for AI agent integration"
