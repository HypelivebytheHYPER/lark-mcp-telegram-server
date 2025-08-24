# MCP Bridge Overview

The Model Context Protocol (MCP) Bridge provides a standardized interface for AI agents to discover and use tools through a JSON-RPC 2.0 API. This enables integration with systems like n8n AI Agent, Claude, GPT, and other AI frameworks.

## What is MCP?

MCP (Model Context Protocol) is a protocol for AI model/agent interaction with external tools and capabilities. It provides a standardized way for models to:

1. Discover available tools (tools/list)
2. Execute tools with arguments (tools/call)
3. Access resources and context (resources, prompts)

## Integration Benefits

- **Standardized Interface**: Consistent tool format across different AI systems
- **Tool Discovery**: AI agents can automatically learn about available capabilities
- **Execution Framework**: Standard method for calling tools with arguments
- **Error Handling**: Consistent error reporting and status codes

## MCP Bridge Endpoints

The MCP Bridge exposes the following endpoints:

- `POST /mcp/invoke` - Main JSON-RPC 2.0 endpoint for all MCP operations
- `GET /mcp/tools` - Direct REST endpoint for tool discovery
- `GET /mcp/resources` - Direct REST endpoint for resource access
- `GET /mcp/prompts` - Direct REST endpoint for prompt templates

## Available Methods

The JSON-RPC 2.0 interface supports these methods:

1. `tools/list` - List all available tools
2. `tools/call` - Execute a specific tool with arguments
3. `resources/list` - List available resources
4. `resources/get` - Get a specific resource
5. `prompts/list` - List available prompt templates

## Available Tools

The MCP Bridge provides access to 9 tools:

1. `send_lark_message` - Send message to Lark chat or user
2. `create_bitable_app` - Create new Bitable (spreadsheet) application
3. `list_bitable_tables` - List all tables in a Bitable app
4. `list_departments` - List all departments in the organization
5. `list_chats` - List all Lark chats the user/bot is in
6. `create_hypetask_session` - Create new HypeTask user session
7. `get_hypetask_session` - Get HypeTask session by token
8. `log_conversation` - Log conversation message to HypeTask history
9. `get_conversation_history` - Get conversation history for HypeTask session

## Basic Usage Example

Here's a simple example of using the MCP Bridge to list available tools:

```bash
curl -X POST "https://lark-mcp-telegram-server.onrender.com/mcp/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test1",
    "method": "tools/list"
  }'
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": "test1",
  "result": {
    "tools": [
      {
        "name": "send_lark_message",
        "description": "Send message to Lark chat or user",
        "inputSchema": {
          "type": "object",
          "properties": {
            "chat_id": {
              "type": "string",
              "description": "Lark chat ID (ou_xxxxx or oc_xxxxx)"
            },
            "text": {
              "type": "string",
              "description": "Message text to send"
            }
          },
          "required": ["chat_id", "text"]
        }
      },
      // ... other tools
    ]
  }
}
```

## Usage with AI Agents

The MCP Bridge is designed to be used with AI agents that support the MCP protocol, including:

- n8n AI Agent
- Claude via JSON-RPC
- GPT via function calling

For detailed integration examples, see:
- [n8n AI Agent Integration](./n8n-integration.md)
- [Claude & GPT Integration](./llm-integration.md)

## Further Documentation

- [JSON-RPC 2.0 Protocol](./json-rpc.md) - Details about the JSON-RPC protocol implementation
- [Tool Discovery](./tool-discovery.md) - How tools are discovered and advertised
- [Tool Execution](./tool-execution.md) - How to execute tools via the MCP Bridge
