# Python Client Library for MCP Bridge

This example provides a simple Python client library for interacting with the Lark MCP Telegram Server's MCP Bridge. The client makes it easy to call MCP methods and handle responses in a Pythonic way.

## Installation

Save this file as `mcp_client.py` in your project directory.

```python
import requests
import json
import uuid
from typing import Dict, List, Any, Optional, Union

class MCPClient:
    """
    Client for interacting with the Lark MCP Bridge.
    
    This client provides a simple interface for calling MCP methods and handling
    responses in a Pythonic way.
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the MCP client.
        
        Args:
            base_url (str): The base URL of the MCP server, e.g., 
                            "https://your-lark-mcp-server.example.com"
            api_key (str, optional): API key for authentication, if required.
        """
        self.base_url = base_url.rstrip('/')
        self.mcp_url = f"{self.base_url}/mcp/invoke"
        self.api_key = api_key
        self.available_tools = None
    
    def _make_request(self, payload: Dict) -> Dict:
        """
        Make a request to the MCP endpoint.
        
        Args:
            payload (dict): The JSON-RPC payload.
            
        Returns:
            dict: The JSON response.
            
        Raises:
            Exception: If the request fails or returns an error.
        """
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        response = requests.post(self.mcp_url, json=payload, headers=headers)
        
        if not response.ok:
            raise Exception(f"HTTP error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        if "error" in result:
            error = result["error"]
            error_message = error.get("message", "Unknown error")
            error_code = error.get("code", -1)
            error_data = error.get("data", {})
            
            raise Exception(f"MCP error {error_code}: {error_message}\nDetails: {json.dumps(error_data, indent=2)}")
        
        return result
    
    def list_tools(self) -> List[Dict]:
        """
        List all available tools on the MCP server.
        
        Returns:
            list: A list of tool definitions.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }
        
        result = self._make_request(payload)
        self.available_tools = result["result"]["tools"]
        return self.available_tools
    
    def call_tool(self, name: str, **kwargs) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            name (str): The name of the tool to call.
            **kwargs: Arguments to pass to the tool.
            
        Returns:
            Any: The result of the tool call.
            
        Raises:
            ValueError: If the tool name is invalid or parameters are missing.
        """
        # Validate tool name and parameters if available_tools is loaded
        if self.available_tools is not None:
            tool = next((t for t in self.available_tools if t["name"] == name), None)
            
            if not tool:
                raise ValueError(f"Tool '{name}' not found. Call list_tools() to see available tools.")
            
            # Validate required parameters
            if "parameters" in tool:
                required_params = tool["parameters"].get("required", [])
                for param in required_params:
                    if param not in kwargs:
                        raise ValueError(f"Missing required parameter: {param}")
        
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": kwargs
            }
        }
        
        result = self._make_request(payload)
        return result["result"]
    
    def send_message(self, receive_id: str, content: Union[str, Dict], msg_type: str = "text") -> Dict:
        """
        Send a message to a Lark chat.
        
        Args:
            receive_id (str): The ID of the recipient (chat or user).
            content (str or dict): The message content. If a string, it will be
                                  wrapped in a text message. If a dict, it will be
                                  used as-is.
            msg_type (str): The message type, default is "text".
            
        Returns:
            dict: The result of the message send operation.
        """
        if isinstance(content, str):
            content = {"text": content}
        
        if isinstance(content, dict):
            content = json.dumps(content)
        
        return self.call_tool(
            "send_lark_message",
            receive_id=receive_id,
            content=content,
            msg_type=msg_type
        )
    
    def list_departments(self, parent_id: Optional[str] = None) -> Dict:
        """
        List departments in Lark.
        
        Args:
            parent_id (str, optional): The parent department ID.
            
        Returns:
            dict: The list of departments.
        """
        args = {}
        if parent_id:
            args["parent_id"] = parent_id
        
        return self.call_tool("list_departments", **args)
    
    def list_chats(self, page_size: int = 10, page_token: Optional[str] = None) -> Dict:
        """
        List Lark chats.
        
        Args:
            page_size (int): Number of chats to return.
            page_token (str, optional): Token for pagination.
            
        Returns:
            dict: The list of chats.
        """
        args = {"page_size": page_size}
        if page_token:
            args["page_token"] = page_token
        
        return self.call_tool("list_chats", **args)
    
    def create_bitable_app(self, name: str, folder_token: Optional[str] = None) -> Dict:
        """
        Create a new Bitable app.
        
        Args:
            name (str): The name of the Bitable app.
            folder_token (str, optional): The folder token to create the app in.
            
        Returns:
            dict: The created Bitable app details.
        """
        args = {"name": name}
        if folder_token:
            args["folder_token"] = folder_token
        
        return self.call_tool("create_bitable_app", **args)
    
    def list_bitable_tables(self, app_token: str) -> Dict:
        """
        List tables in a Bitable app.
        
        Args:
            app_token (str): The Bitable app token.
            
        Returns:
            dict: The list of tables.
        """
        return self.call_tool("list_bitable_tables", app_token=app_token)
    
    def create_hypetask_session(self, user_id: str, session_name: str) -> Dict:
        """
        Create a new HypeTask session.
        
        Args:
            user_id (str): The user ID.
            session_name (str): The session name.
            
        Returns:
            dict: The created session details.
        """
        return self.call_tool(
            "create_hypetask_session",
            user_id=user_id,
            session_name=session_name
        )
    
    def get_hypetask_session(self, session_token: str) -> Dict:
        """
        Get a HypeTask session.
        
        Args:
            session_token (str): The session token.
            
        Returns:
            dict: The session details.
        """
        return self.call_tool("get_hypetask_session", session_token=session_token)
    
    def log_conversation(self, session_token: str, role: str, message: str) -> Dict:
        """
        Log a conversation message.
        
        Args:
            session_token (str): The session token.
            role (str): The role of the message sender (e.g., "user", "assistant").
            message (str): The message content.
            
        Returns:
            dict: The result of the log operation.
        """
        return self.call_tool(
            "log_conversation",
            session_token=session_token,
            role=role,
            message=message
        )
    
    def get_conversation_history(self, session_token: str) -> Dict:
        """
        Get conversation history.
        
        Args:
            session_token (str): The session token.
            
        Returns:
            dict: The conversation history.
        """
        return self.call_tool(
            "get_conversation_history",
            session_token=session_token
        )
```

## Usage Examples

Here are examples of how to use the MCP client library:

### Basic Usage

```python
from mcp_client import MCPClient

# Initialize the client
client = MCPClient("https://your-lark-mcp-server.example.com")

# List available tools
tools = client.list_tools()
print(f"Available tools: {len(tools)}")
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")

# Send a message to a chat
result = client.send_message(
    "oc_12345678",  # Chat ID
    "Hello from the MCP client!"
)
print(f"Message sent: {result['message']}")

# List Lark chats
chats = client.list_chats(page_size=5)
print("Available chats:")
for chat in chats.get("items", []):
    print(f"- {chat['name']} (ID: {chat['chat_id']})")
```

### Working with Bitable

```python
from mcp_client import MCPClient

# Initialize the client
client = MCPClient("https://your-lark-mcp-server.example.com")

# Create a new Bitable app
app = client.create_bitable_app("Project Tracker")
app_token = app["app_token"]
print(f"Created app: {app_token}")

# List tables in the app
tables = client.list_bitable_tables(app_token)
print("Tables in the app:")
for table in tables["tables"]:
    print(f"- {table['name']} (ID: {table['table_id']})")

# To work with table data, you would typically use the REST API
# since those operations aren't in the MCP Bridge
import requests

# Example: Add a record to a table
table_id = tables["tables"][0]["table_id"]
response = requests.post(
    f"https://your-lark-mcp-server.example.com/api/v1/bitable/apps/{app_token}/tables/{table_id}/records",
    json={
        "fields": {
            "text field": "New Project"
        }
    }
)
record = response.json()
print(f"Added record: {record['record_id']}")
```

### Managing Conversations

```python
from mcp_client import MCPClient

# Initialize the client
client = MCPClient("https://your-lark-mcp-server.example.com")

# Create a new session
session = client.create_hypetask_session(
    "ou_12345678",  # User ID
    "Support Session"
)
session_token = session["session_token"]
print(f"Created session: {session_token}")

# Log some conversation messages
client.log_conversation(
    session_token,
    "user",
    "I need help with my account."
)

client.log_conversation(
    session_token,
    "assistant",
    "I'd be happy to help. What specific issue are you having with your account?"
)

client.log_conversation(
    session_token,
    "user",
    "I can't reset my password."
)

# Get session details
session_details = client.get_hypetask_session(session_token)
print(f"Session: {session_details['session_name']}")
print(f"Message count: {session_details['message_count']}")

# Get conversation history
history = client.get_conversation_history(session_token)
print("\nConversation history:")
for message in history["messages"]:
    role = message["role"].upper()
    content = message["message"]
    print(f"{role}: {content}")
```

### Using Custom Tools

You can call any tool available on the MCP server, even if there's no dedicated method for it in the client library:

```python
from mcp_client import MCPClient

# Initialize the client
client = MCPClient("https://your-lark-mcp-server.example.com")

# Call a custom tool (assuming it exists on the server)
result = client.call_tool(
    "custom_tool_name",
    param1="value1",
    param2="value2"
)
print(f"Custom tool result: {result}")
```

## Error Handling

The client library includes error handling for HTTP errors and MCP errors:

```python
from mcp_client import MCPClient

client = MCPClient("https://your-lark-mcp-server.example.com")

try:
    # Try to call a tool with missing parameters
    client.call_tool("send_lark_message")  # Missing required parameters
except Exception as e:
    print(f"Error: {e}")

try:
    # Try to call a non-existent tool
    client.call_tool("nonexistent_tool")
except Exception as e:
    print(f"Error: {e}")
```

## Conclusion

This client library provides a convenient way to interact with the Lark MCP Telegram Server's MCP Bridge from Python applications. It handles the JSON-RPC protocol details and provides a simple, Pythonic interface for calling MCP tools.
