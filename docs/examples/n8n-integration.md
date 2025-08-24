# n8n AI Agent Integration with MCP Bridge

This guide demonstrates how to integrate the Lark MCP Telegram Server with n8n AI Agent using the MCP Bridge protocol. This integration enables AI agents to perform actions in Lark through a standardized protocol.

## Prerequisites

- n8n instance with AI Agent module enabled
- Lark MCP Telegram Server deployed and accessible
- Authentication credentials for the Lark MCP Telegram Server (if required)

## Setup Process

### 1. Create a new n8n AI Agent workflow

Create a new workflow in n8n and add an AI Agent node to it.

### 2. Configure the AI Agent node

In the AI Agent configuration, add a custom API integration that points to the MCP Bridge endpoint:

```
https://your-lark-mcp-server.example.com/mcp/invoke
```

### 3. Create the AI Agent tools definition

Add the following tools definition to your AI Agent configuration:

```json
{
  "tools": [
    {
      "name": "lark_mcp_bridge",
      "description": "Connect to Lark/Feishu workspace to send messages, manage documents, and interact with Bitable databases",
      "requestFormat": {
        "type": "json",
        "schema": {
          "type": "object",
          "properties": {
            "jsonrpc": {
              "type": "string",
              "enum": ["2.0"]
            },
            "id": {
              "type": "string"
            },
            "method": {
              "type": "string",
              "enum": ["tools/list", "tools/call"]
            },
            "params": {
              "type": "object",
              "properties": {
                "name": {
                  "type": "string",
                  "description": "The name of the tool to call"
                },
                "arguments": {
                  "type": "object",
                  "description": "The arguments to pass to the tool"
                }
              },
              "required": ["name"]
            }
          },
          "required": ["jsonrpc", "id", "method", "params"]
        }
      }
    }
  ]
}
```

### 4. Test the integration with tools/list

To verify that your integration is working, use the n8n AI Agent to make a call to the `tools/list` method:

```json
{
  "jsonrpc": "2.0",
  "id": "test1",
  "method": "tools/list",
  "params": {}
}
```

This should return a list of available tools from the MCP Bridge.

## Using the MCP Bridge with n8n AI Agent

Here are some examples of how to use the MCP Bridge with n8n AI Agent:

### Example 1: Sending a message to Lark

```json
{
  "jsonrpc": "2.0",
  "id": "msg1",
  "method": "tools/call",
  "params": {
    "name": "send_lark_message",
    "arguments": {
      "receive_id": "oc_123456789",
      "content": "{\"text\":\"Hello from n8n AI Agent!\"}",
      "msg_type": "text"
    }
  }
}
```

### Example 2: Listing Bitable tables in an app

```json
{
  "jsonrpc": "2.0",
  "id": "bitable1",
  "method": "tools/call",
  "params": {
    "name": "list_bitable_tables",
    "arguments": {
      "app_token": "bascnxxxxxxxxx"
    }
  }
}
```

### Example 3: Creating a new HypeTask session

```json
{
  "jsonrpc": "2.0",
  "id": "hypetask1",
  "method": "tools/call",
  "params": {
    "name": "create_hypetask_session",
    "arguments": {
      "user_id": "ou_xxxxxxxx",
      "session_name": "n8n Test Session"
    }
  }
}
```

## AI Agent Prompt Examples

Here are some examples of prompts you can use with your n8n AI Agent to interact with the Lark MCP Telegram Server:

### 1. Discovering available tools

```
Please list all the tools available through the Lark MCP Bridge. Use the tools/list method to discover them.
```

### 2. Sending a message to a chat

```
Send a message to the Lark chat with ID "oc_12345678". The message should say "Hello from n8n AI Agent! This is a test message." Use the appropriate tool from the MCP Bridge.
```

### 3. Working with Bitable

```
First, list all the Bitable apps I have access to. Then, for the first app in the list, show me all the tables in that app. Use the appropriate MCP Bridge tools.
```

### 4. Managing a conversation session

```
Create a new HypeTask session for user "ou_12345678" with the name "Customer Support Session". Then log a conversation message in this session with the text "Initial customer inquiry about product pricing". Finally, retrieve the conversation history for this session.
```

## Error Handling

When interacting with the MCP Bridge through n8n AI Agent, you might encounter errors. Here's how to interpret and handle common error responses:

### Invalid Method Error

```json
{
  "jsonrpc": "2.0",
  "id": "test1",
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

This error indicates that the method you're trying to call doesn't exist. Check the available methods using `tools/list`.

### Invalid Parameters Error

```json
{
  "jsonrpc": "2.0",
  "id": "test1",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "errors": [
        {
          "loc": ["arguments", "receive_id"],
          "msg": "field required",
          "type": "value_error.missing"
        }
      ]
    }
  }
}
```

This error indicates that you're missing required parameters or they're invalid. Check the tool's schema for required parameters.

## Conclusion

Using the MCP Bridge with n8n AI Agent provides a powerful way to integrate AI capabilities with Lark/Feishu. The structured protocol makes it easy for the AI to discover and use available tools without having to understand the complexities of the underlying API.
