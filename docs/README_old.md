# Lark-MCP-Telegram Server Documentation

## Overview

Lark-MCP-Telegram Server is a powerful bridge service that provides:

1. **REST API** for direct integration with Lark/Feishu and Telegram services
2. **MCP Bridge** (Model Context Protocol) for AI agent integration via JSON-RPC 2.0

This documentation covers both access methods, providing examples, use cases, and implementation details.

## Documentation Index

### General
- [Installation & Setup](./setup.md)
- [Authentication & Security](./security.md)
- [Configuration Options](./configuration.md)

### REST API
- [API Reference](./rest-api/README.md)
- [Lark API Endpoints](./rest-api/lark-endpoints.md)
- [Bitable Operations](./rest-api/bitable-operations.md)
- [Telegram Integration](./rest-api/telegram-endpoints.md)
- [Webhook Management](./rest-api/webhook-endpoints.md)

### MCP Bridge
- [MCP Bridge Overview](./mcp-bridge/README.md)
- [JSON-RPC 2.0 Protocol](./mcp-bridge/json-rpc.md)
- [Tool Discovery](./mcp-bridge/tool-discovery.md)
- [Tool Execution](./mcp-bridge/tool-execution.md)
- [n8n AI Agent Integration](./mcp-bridge/n8n-integration.md)
- [Claude & GPT Integration](./mcp-bridge/llm-integration.md)

### Example Use Cases
- [Real-world Examples](./examples/README.md)
- [Dual Access Method Comparison](./examples/dual-access.md)

## Getting Started

To get started quickly, see the [Installation & Setup](./setup.md) guide, followed by the appropriate section for your integration needs:

- For direct API access, see [REST API Reference](./rest-api/README.md)
- For AI agent integration, see [MCP Bridge Overview](./mcp-bridge/README.md)
