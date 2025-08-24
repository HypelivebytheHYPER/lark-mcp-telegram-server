# 🚀 Lark MCP Telegram Server

A production-ready **Model Context Protocol (MCP)** server that provides seamless integration with **LarkSuite/Feishu** and **Telegram** platforms. Built with enhanced security, comprehensive Bitable operations, and dual API access.

## ✨ Features

### 🔧 **MCP Bridge (Enhanced)**
- **12 MCP Tools** for LarkSuite Bitable operations
- **Official LarkSuite SDK** patterns implementation
- **JSON-RPC 2.0** protocol support
- **Real-time data** integration with LarkSuite tables

### 🌐 **HTTP REST API**
- **FastAPI** powered endpoints
- **Security features** with rate limiting
- **Health monitoring** and status checks
- **CORS support** for web applications

### 🛡️ **Security & Production Ready**
- **Environment variable** based configuration
- **JWT token validation** and authentication
- **Rate limiting** and DDoS protection
- **Secure credential management**

### 🔗 **Integrations**
- **LarkSuite/Feishu** - Complete Bitable CRUD operations
- **Telegram** - Message sending capabilities
- **Render Cloud** - Production deployment ready

## 🚀 **Quick Start**

### **Production Deployment (Render)**
1. **Fork this repository**
2. **Connect to Render** and deploy
3. **Set environment variables** in Render dashboard:
   ```
   LARK_APP_ID=your_lark_app_id
   LARK_APP_SECRET=your_lark_app_secret
   TELEGRAM_TOKEN=your_telegram_bot_token
   PORT=8000
   ```
4. **Access your deployed API**:
   - Health: `https://your-app.onrender.com/health`
   - MCP Tools: `https://your-app.onrender.com/mcp/tools`

### **Local Development**
```bash
# 1. Clone the repository
git clone https://github.com/HypelivebytheHYPER/lark-mcp-telegram-server.git
cd lark-mcp-telegram-server

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (copy and edit)
cp .env.example .env
# Edit .env with your credentials

# 4. Run the server
python app.py
```

## 📚 **Documentation**

- **[Complete Setup Guide](docs/HOW_TO_TEST_AND_USE.md)** - Detailed setup instructions
- **[MCP Bridge Documentation](docs/mcp-bridge/README.md)** - MCP server details
- **[REST API Reference](docs/rest-api/README.md)** - HTTP endpoints
- **[Integration Examples](docs/examples/README.md)** - Code examples and integrations
- **[Security Guide](SECURITY.md)** - Security best practices

## 🛠️ **Available MCP Tools**

| Tool | Description |
|------|-------------|
| `bitable_list_tables` | List all tables in a LarkSuite Base |
| `bitable_get_table_schema` | Get table structure and field definitions |
| `bitable_list_fields` | List all fields in a table |
| `bitable_list_records` | List records with filtering and pagination |
| `bitable_get_record` | Get a specific record by ID |
| `bitable_create_record` | Create new records |
| `bitable_update_record` | Update existing records |
| `bitable_delete_record` | Delete records |
| `bitable_batch_create_records` | Create multiple records |
| `bitable_search_records` | Advanced record search |
| `send_lark_message` | Send messages to Lark/Feishu |
| `create_bitable_app` | Create new Bitable applications |

## 🔗 **API Endpoints**

### **Health & Status**
- `GET /health` - Service health check
- `GET /status` - Detailed service status

### **MCP Protocol**
- `GET /mcp/tools` - List available MCP tools
- `POST /mcp/invoke` - Invoke MCP tools with JSON-RPC 2.0

### **Legacy REST** *(Maintained for compatibility)*
- `POST /send-message` - Send messages
- `POST /create-session` - Create user sessions

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Agents     │    │   Web Apps       │    │   Direct HTTP   │
│   (MCP Client)  │    │   (REST API)     │    │   (cURL/Tools)  │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          │ MCP Protocol         │ HTTP REST             │ HTTP REST
          │ (JSON-RPC 2.0)       │                       │
          │                      │                       │
    ┌─────▼──────────────────────▼───────────────────────▼─────┐
    │                FastAPI Server                            │
    │  ┌─────────────────┐  ┌─────────────────────────────────┐│
    │  │  MCP Bridge     │  │       HTTP Endpoints            ││
    │  │  Enhanced       │  │       (REST API)                ││
    │  └─────────────────┘  └─────────────────────────────────┘│
    └──────────────────┬─────────────────────────────────────────┘
                       │
    ┌──────────────────▼─────────────────────────────────────────┐
    │              External APIs                                 │
    │  ┌─────────────────┐  ┌─────────────────────────────────┐ │
    │  │   LarkSuite API │  │      Telegram API               │ │
    │  │   (Bitable CRUD)│  │      (Message Send)             │ │
    │  └─────────────────┘  └─────────────────────────────────┘ │
    └────────────────────────────────────────────────────────────┘
```

## 📋 **Requirements**

- **Python 3.8+**
- **FastAPI** - Web framework
- **httpx** - HTTP client
- **python-dotenv** - Environment management
- **pydantic** - Data validation
- **slowapi** - Rate limiting

## 🔐 **Security**

- **Environment variables** for sensitive data
- **Rate limiting** on all endpoints
- **CORS** configuration for web security
- **Input validation** with Pydantic models
- **Secure credential** handling

## 📈 **Production Status**

- ✅ **Deployed** on Render Cloud
- ✅ **Environment variables** configured securely
- ✅ **Real LarkSuite integration** verified
- ✅ **HTTP APIs** fully functional
- ✅ **MCP Bridge** operational with 12 tools
- ✅ **Security audit** completed

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

**🚀 Ready for AI agent integrations and production use!**
