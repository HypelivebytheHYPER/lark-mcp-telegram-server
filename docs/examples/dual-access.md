# Dual Access Method Comparison

The Lark-MCP-Telegram Server provides two distinct methods for accessing its functionality:

1. **Direct REST API** - Traditional HTTP endpoints
2. **MCP Bridge (JSON-RPC 2.0)** - AI-agent friendly protocol

This document compares these two approaches and helps you choose the right one for your use case.

## Feature Comparison

| Feature | REST API | MCP Bridge |
|---------|----------|------------|
| **Protocol** | HTTP REST | JSON-RPC 2.0 |
| **Primary Endpoint** | Various specific endpoints | Single `/mcp/invoke` endpoint |
| **Authentication** | Headers/Query params | Same as REST API |
| **Primary Users** | Developers, applications | AI agents, LLMs |
| **Discovery** | OpenAPI documentation | `tools/list` method |
| **Parameter Validation** | FastAPI validation | JSON Schema validation |
| **Error Format** | HTTP status codes + JSON | JSON-RPC error objects |
| **Batch Operations** | Separate endpoints | Not supported directly |
| **Available Operations** | All (36+ endpoints) | 9 core tools |

## When to Use REST API

The REST API is ideal for:

1. **Direct Integration**: When you're building a traditional application or service that directly integrates with Lark/Telegram
2. **Batch Operations**: When you need to perform batch operations efficiently
3. **Complete Control**: When you need access to all available functionality
4. **Standard Development**: When working with standard web development frameworks and libraries

**Example Use Case:** A dashboard application that displays and manages Bitable data.

## When to Use MCP Bridge

The MCP Bridge is ideal for:

1. **AI Agent Integration**: When connecting AI systems like n8n AI Agent, Claude, or GPT
2. **Tool Discovery**: When the consumer needs to discover available capabilities programmatically
3. **Simplified Interface**: When you prefer a single endpoint with method-based dispatch
4. **Standardized Protocol**: When working with systems that already support JSON-RPC or MCP

**Example Use Case:** An AI assistant that needs to perform actions in Lark based on user requests.

## Example: Same Operation, Two Methods

Let's compare the same operation (listing departments) using both methods:

### REST API Approach

```bash
curl -X GET "https://lark-mcp-telegram-server.onrender.com/api/v1/contacts/departments"
```

Response:
```json
{
  "success": true,
  "message": "Retrieved 1 departments",
  "details": "Parent ID: Root",
  "api_response": {
    "code": 0,
    "data": {
      "has_more": false,
      "items": [
        {
          "department_id": "0",
          "member_count": 10,
          "name": "",
          "open_department_id": "0",
          "primary_member_count": 10
        }
      ]
    }
  }
}
```

### MCP Bridge Approach

```bash
curl -X POST "https://lark-mcp-telegram-server.onrender.com/mcp/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test1",
    "method": "tools/call",
    "params": {
      "name": "list_departments",
      "arguments": {}
    }
  }'
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": "test1",
  "result": {
    "success": true,
    "message": "Retrieved 1 departments",
    "details": "Parent ID: Root",
    "api_response": {
      "code": 0,
      "data": {
        "has_more": false,
        "items": [
          {
            "department_id": "0",
            "member_count": 10,
            "name": "",
            "open_department_id": "0",
            "primary_member_count": 10
          }
        ]
      }
    }
  }
}
```

## Hybrid Approach

You can also adopt a hybrid approach, using:

- **REST API** for batch operations and complex queries
- **MCP Bridge** for AI agent integration and tool discovery

The server supports both methods simultaneously, so you can choose the right approach for each specific use case.

## Mapping Between Methods

For developers wanting to use both methods interchangeably, here's a quick reference for how tools in the MCP Bridge map to REST API endpoints:

| MCP Tool Name | REST API Endpoint |
|---------------|------------------|
| `send_lark_message` | `POST /api/v1/lark/send` |
| `create_bitable_app` | `POST /api/v1/bitable/apps/create` |
| `list_bitable_tables` | `GET /api/v1/bitable/apps/{app_token}/tables` |
| `list_departments` | `GET /api/v1/contacts/departments` |
| `list_chats` | `GET /api/v1/lark/chats` |
| `create_hypetask_session` | `POST /api/v1/hypetask/session/create` |
| `get_hypetask_session` | `GET /api/v1/hypetask/session/{session_token}` |
| `log_conversation` | `POST /api/v1/hypetask/conversation/log` |
| `get_conversation_history` | `GET /api/v1/hypetask/conversation/history/{session_token}` |

## Conclusion

Both access methods provide equivalent functionality with different interfaces optimized for different use cases. The MCP Bridge is particularly valuable for AI agent integration, while the REST API provides more direct control for traditional application development.
