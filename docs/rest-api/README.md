# REST API Reference

The Lark-MCP-Telegram Server provides a comprehensive REST API for direct integration with Lark/Feishu and Telegram services.

## Base URL

```
https://lark-mcp-telegram-server.onrender.com
```

## Authentication

API authentication is handled via headers or query parameters, depending on the endpoint. See [Authentication & Security](../security.md) for details.

## Common Response Format

Most endpoints return responses in the following format:

```json
{
  "success": true,
  "message": "Operation successful",
  "details": "Additional details about the operation",
  "api_response": {
    // Original response from upstream API if applicable
  }
}
```

## Error Handling

Error responses follow this structure:

```json
{
  "success": false,
  "message": "Error message",
  "details": "Detailed error information",
  "error_code": 1001
}
```

## Available Endpoints

The API is organized into the following categories:

### Health & Status
- [`GET /health`](#health) - Check server health
- [`GET /ready`](#ready) - Check service readiness

### Lark/Feishu
- [`POST /api/v1/lark/send`](#send-lark-message) - Send message to Lark chat
- [`GET /api/v1/lark/chats`](#list-lark-chats) - List Lark chats
- [`GET /api/v1/lark/chats/{chat_id}/members`](#list-chat-members) - List chat members
- 3 additional endpoints (See [Lark API Endpoints](./lark-endpoints.md))

### Bitable
- [`GET /api/v1/bitable/apps/{app_token}/tables`](#list-bitable-tables) - List tables in app
- [`GET /api/v1/bitable/apps/{app_token}/tables/{table_id}/records`](#get-bitable-records) - Get records
- [`POST /api/v1/bitable/apps/{app_token}/tables/{table_id}/records/create`](#create-bitable-record) - Create record
- [`PUT /api/v1/bitable/apps/{app_token}/tables/{table_id}/records/{record_id}`](#update-bitable-record) - Update record
- [`DELETE /api/v1/bitable/apps/{app_token}/tables/{table_id}/records/{record_id}`](#delete-bitable-record) - Delete record
- 7 additional endpoints (See [Bitable Operations](./bitable-operations.md))

### Contacts
- [`GET /api/v1/contacts/departments`](#list-departments) - List departments
- [`GET /api/v1/contacts/users`](#list-users) - List users

### Telegram
- [`POST /api/v1/telegram/send`](#send-telegram-message) - Send Telegram message

### Webhooks
- [`POST /api/v1/webhooks/register`](#register-webhook) - Register webhook
- [`GET /api/v1/webhooks/list`](#list-webhooks) - List webhooks
- [`DELETE /api/v1/webhooks/unregister`](#unregister-webhook) - Unregister webhook

### HypeTask Session Management
- [`POST /api/v1/hypetask/session/create`](#create-session) - Create user session
- [`GET /api/v1/hypetask/session/{session_token}`](#get-session) - Get session by token
- [`POST /api/v1/hypetask/conversation/log`](#log-conversation) - Log conversation
- [`GET /api/v1/hypetask/conversation/history/{session_token}`](#get-conversation-history) - Get conversation history

## Detailed Endpoint Documentation

### Health

`GET /health`

Check the health status of the server.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-24T12:13:17.576518Z",
  "service": "lark-telegram-bridge",
  "deployment_status": "production-ready-with-real-apis",
  "integrations": {
    "lark_configured": true,
    "telegram_configured": true
  }
}
```

### Ready

`GET /ready`

Check if the service is ready to handle requests.

**Response:**
```json
{
  "ready": true,
  "deployment": "fastapi-server-with-real-apis",
  "services": {
    "server": true,
    "lark_client": true,
    "telegram_client": true
  }
}
```

### Send Lark Message

`POST /api/v1/lark/send`

Send a message to a Lark chat or user.

**Request Body:**
```json
{
  "chat_id": "oc_12345abcdef",
  "text": "Hello from the API!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Message sent",
  "api_response": {
    "code": 0,
    "data": { 
      "message_id": "om_12345abcdef"
    }
  }
}
```

### List Bitable Tables

`GET /api/v1/bitable/apps/{app_token}/tables`

List all tables in a Bitable app.

**Path Parameters:**
- `app_token` (string, required) - The Bitable app token

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 3 tables",
  "api_response": {
    "code": 0,
    "data": {
      "items": [
        {
          "table_id": "tbl12345",
          "name": "My Table",
          "revision": 1
        },
        ...
      ],
      "has_more": false,
      "page_token": "next_page_token"
    }
  }
}
```

For more detailed documentation on each endpoint, see the specific category documentation pages.
