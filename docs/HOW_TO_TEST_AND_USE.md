# How to Test and Use Your Optimized MCP Bridge

## 🚀 Deployment Status

**Current Status**: Your optimizations are committed to GitHub but not yet deployed to production.

### Next Steps:
1. **Deploy to Render**: Go to [Render Dashboard](https://dashboard.render.com) → Select your service → Click "Manual Deploy"
2. **Or wait for auto-deploy**: If enabled, Render will automatically deploy your latest commit

## 🧪 Testing Guide

### 1. Local Testing (Development)

If running locally on port 8000:

```bash
# Run the test suite
./test_mcp_optimizations.sh

# Or manual tests:
# Test tools list
curl -X POST "http://localhost:8000/mcp/invoke" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"test1","method":"tools/list"}'

# Test new user-friendly tool
curl -X POST "http://localhost:8000/mcp/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test2",
    "method": "tools/call",
    "params": {
      "name": "create_bitable_record",
      "arguments": {
        "app_token": "your_app_token",
        "table_id": "your_table_id",
        "fields": {"text_field": "Hello World"}
      }
    }
  }'
```

### 2. Production Testing (After Deployment)

```bash
# Test production server
curl -X POST "https://lark-mcp-telegram-server.onrender.com/mcp/invoke" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"test1","method":"tools/list"}'
```

## 🎯 New Features Available

### User-Friendly Tool Names

Instead of complex legacy names, you can now use:

```json
{
  "jsonrpc": "2.0",
  "id": "example",
  "method": "tools/call",
  "params": {
    "name": "search_bitable_records",  // Instead of "bitable.v1.appTableRecord.search"
    "arguments": {
      "app_token": "bascnxxxxxxxxx",
      "table_id": "tblxxxxxxxx"
    }
  }
}
```

**Available New Tools**:
- `search_bitable_records` - Search/query records in a table
- `create_bitable_record` - Create a single record
- `update_bitable_record` - Update a single record
- `delete_bitable_record` - Delete a single record
- `batch_create_records` - Create multiple records
- `batch_update_records` - Update multiple records
- `batch_delete_records` - Delete multiple records
- `list_bitable_fields` - Get field schema for a table

### Proxy Support

Enable connection to native Lark-tenant MCP servers:

```bash
# Set environment variables
export MCP_PROXY_ENABLED=true
export MCP_PROXY_URL=https://your-lark-tenant-mcp.example.com/mcp/invoke

# Then use the proxy endpoint
curl -X POST "https://lark-mcp-telegram-server.onrender.com/mcp/invoke/proxy" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"test","method":"tools/list"}'
```

## 🤖 AI Agent Integration

### n8n AI Agent

1. **Configure n8n AI Agent**:
   - Add custom tool: `https://lark-mcp-telegram-server.onrender.com/mcp/invoke`
   - Use JSON-RPC 2.0 format

2. **Example prompts**:
   ```
   "List all available tools in the Lark MCP Bridge"
   "Create a new record in Bitable app bascnxxxxxxxxx table tblxxxxxxxx with name 'Test Record'"
   "Search for records in my Bitable table"
   ```

### Python Client Example

```python
from docs.examples.python_client import MCPClient

# Initialize client
client = MCPClient("https://lark-mcp-telegram-server.onrender.com")

# List available tools
tools = client.list_tools()
print(f"Available tools: {len(tools)}")

# Use new user-friendly tools
result = client.call_tool(
    "create_bitable_record",
    app_token="bascnxxxxxxxxx",
    table_id="tblxxxxxxxx",
    fields={"name": "Test Record", "status": "Active"}
)
print(f"Created record: {result}")
```

### LangChain Integration

```python
from langchain.tools import StructuredTool
import requests

def create_bitable_record(**kwargs):
    response = requests.post(
        "https://lark-mcp-telegram-server.onrender.com/mcp/invoke",
        json={
            "jsonrpc": "2.0",
            "id": "langchain",
            "method": "tools/call",
            "params": {
                "name": "create_bitable_record",
                "arguments": kwargs
            }
        }
    )
    return response.json()["result"]

# Create LangChain tool
bitable_tool = StructuredTool.from_function(
    func=create_bitable_record,
    name="create_bitable_record",
    description="Create a new record in a Bitable table"
)
```

## 📊 Monitoring and Debugging

### Check Tool Availability

```bash
# Quick check for new tools
curl -s "https://lark-mcp-telegram-server.onrender.com/mcp/invoke" \
  -d '{"jsonrpc":"2.0","id":"check","method":"tools/list"}' | \
  jq '.result.tools[] | select(.name | contains("bitable_record")) | .name'
```

### Error Handling

The optimized bridge provides better error responses:

```json
{
  "jsonrpc": "2.0",
  "id": "error_example",
  "error": {
    "code": -32601,
    "message": "Tool not found: invalid_tool_name",
    "data": {
      "available_tools": ["list_departments", "send_lark_message", ...]
    }
  }
}
```

## 🔧 Configuration Options

### Environment Variables

```bash
# Basic MCP Bridge
MCP_BRIDGE_ENABLED=true
MCP_BRIDGE_INTERNAL_BASE=https://lark-mcp-telegram-server.onrender.com

# Proxy support (optional)
MCP_PROXY_ENABLED=false
MCP_PROXY_URL=https://your-lark-tenant-mcp.example.com/mcp/invoke
```

## 🎉 Ready to Use!

Once deployed, your optimized MCP Bridge will provide:
- ✅ User-friendly tool names for better AI agent integration
- ✅ Proxy support for advanced Lark-tenant MCP features
- ✅ Better error handling and debugging
- ✅ Comprehensive documentation and examples
- ✅ Full backward compatibility with existing integrations

Deploy to Render and start using these enhanced capabilities!
