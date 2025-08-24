# Advanced MCP Bridge Examples

This document provides more advanced examples of using the MCP Bridge with the Lark MCP Telegram Server. These examples showcase real-world scenarios and complex operations.

## Table of Contents

1. [Multi-step Workflows](#multi-step-workflows)
2. [Dynamic Tool Discovery](#dynamic-tool-discovery)
3. [Working with Bitable Data](#working-with-bitable-data)
4. [Conversation Management](#conversation-management)
5. [Integration with Other Systems](#integration-with-other-systems)

## Multi-step Workflows

This example demonstrates a complete workflow involving multiple MCP tools to create a Bitable app, add data, and then share the results.

### Example: Project Management Workflow

```python
import requests
import json
import uuid

BASE_URL = "https://your-lark-mcp-server.example.com/mcp/invoke"

def mcp_call(method, name=None, arguments=None):
    request_id = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    
    if method == "tools/call":
        payload["params"] = {
            "name": name,
            "arguments": arguments or {}
        }
    else:
        payload["params"] = {}
        
    response = requests.post(BASE_URL, json=payload)
    return response.json()

# Step 1: Create a new Bitable app for project tracking
create_app_response = mcp_call(
    "tools/call",
    "create_bitable_app",
    {
        "name": "Project Tracker",
        "folder_token": "fldcnxxxxxxxx"  # Optional: specify folder to create in
    }
)

# Extract the app token from the response
app_token = create_app_response["result"]["app_token"]
print(f"Created Bitable app with token: {app_token}")

# Step 2: Get the tables in the app
tables_response = mcp_call(
    "tools/call",
    "list_bitable_tables",
    {"app_token": app_token}
)

# The first table is created automatically, get its ID
table_id = tables_response["result"]["tables"][0]["table_id"]

# Step 3: Create a field in the table for project name
# (Using REST API directly for this operation as it's not in MCP Bridge)
create_field_url = f"https://your-lark-mcp-server.example.com/api/v1/bitable/apps/{app_token}/tables/{table_id}/fields"
field_payload = {
    "field_name": "Project Name",
    "type": 1  # Text type
}
create_field_response = requests.post(create_field_url, json=field_payload)
field_id = create_field_response.json()["field_id"]

# Step 4: Add a record to the table
# (Using REST API directly for this operation as it's not in MCP Bridge)
add_record_url = f"https://your-lark-mcp-server.example.com/api/v1/bitable/apps/{app_token}/tables/{table_id}/records"
record_payload = {
    "fields": {
        field_id: "AI Integration Project"
    }
}
add_record_response = requests.post(add_record_url, json=record_payload)

# Step 5: Send a message to a chat with the link to the new Bitable
send_message_response = mcp_call(
    "tools/call",
    "send_lark_message",
    {
        "receive_id": "oc_xxxxxxxx",  # Chat ID
        "msg_type": "text",
        "content": json.dumps({
            "text": f"I've created a new Project Tracker Bitable. View it here: https://bytedance.feishu.cn/base/{app_token}"
        })
    }
)

print("Workflow completed successfully!")
```

## Dynamic Tool Discovery

This example shows how to discover available tools and their parameters dynamically, which is especially useful for AI agents.

```python
import requests
import json

BASE_URL = "https://your-lark-mcp-server.example.com/mcp/invoke"

# Get the list of available tools
response = requests.post(
    BASE_URL,
    json={
        "jsonrpc": "2.0",
        "id": "discovery",
        "method": "tools/list",
        "params": {}
    }
)

tools = response.json()["result"]["tools"]

# Print tool capabilities
print("Available tools:")
for tool in tools:
    print(f"\n-- {tool['name']} --")
    print(f"Description: {tool['description']}")
    print("Parameters:")
    
    if "parameters" in tool:
        params = tool["parameters"].get("properties", {})
        required = tool["parameters"].get("required", [])
        
        for param_name, param_details in params.items():
            req_indicator = "*" if param_name in required else ""
            param_type = param_details.get("type", "any")
            param_desc = param_details.get("description", "No description")
            
            print(f"  - {param_name}{req_indicator}: {param_type}")
            print(f"    {param_desc}")
    else:
        print("  No parameters required")

# Example: Dynamically call a tool based on discovered capabilities
def call_tool_dynamically(tool_name, **kwargs):
    # Find the tool in our discovered tools
    tool = next((t for t in tools if t["name"] == tool_name), None)
    
    if not tool:
        raise ValueError(f"Tool '{tool_name}' not found")
    
    # Validate required parameters
    if "parameters" in tool:
        required_params = tool["parameters"].get("required", [])
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"Missing required parameter: {param}")
    
    # Make the call
    response = requests.post(
        BASE_URL,
        json={
            "jsonrpc": "2.0",
            "id": "dynamic_call",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": kwargs
            }
        }
    )
    
    return response.json()

# Example usage of dynamic tool calling
result = call_tool_dynamically(
    "list_chats",
    page_size=10
)

print("\nDynamic call result:")
print(json.dumps(result, indent=2))
```

## Working with Bitable Data

This example demonstrates a complete workflow for working with Bitable data, including creating tables, adding fields, and querying data.

```python
import requests
import json
import uuid

BASE_URL = "https://your-lark-mcp-server.example.com/mcp/invoke"
REST_BASE_URL = "https://your-lark-mcp-server.example.com/api/v1"

def mcp_call(method, name=None, arguments=None):
    request_id = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    
    if method == "tools/call":
        payload["params"] = {
            "name": name,
            "arguments": arguments or {}
        }
    else:
        payload["params"] = {}
        
    response = requests.post(BASE_URL, json=payload)
    return response.json()

def rest_call(method, endpoint, data=None):
    url = f"{REST_BASE_URL}{endpoint}"
    if method == "GET":
        response = requests.get(url)
    elif method == "POST":
        response = requests.post(url, json=data)
    elif method == "PUT":
        response = requests.put(url, json=data)
    elif method == "DELETE":
        response = requests.delete(url)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    return response.json()

# Step 1: Create a new Bitable app
create_app_response = mcp_call(
    "tools/call",
    "create_bitable_app",
    {"name": "Inventory Tracker"}
)

app_token = create_app_response["result"]["app_token"]
print(f"Created Bitable app: {app_token}")

# Step 2: List tables (should have 1 default table)
tables_response = mcp_call(
    "tools/call",
    "list_bitable_tables",
    {"app_token": app_token}
)

table_id = tables_response["result"]["tables"][0]["table_id"]
print(f"Using table: {table_id}")

# Step 3: Create fields for our inventory
fields = [
    {"field_name": "Item Name", "type": 1},  # Text
    {"field_name": "Category", "type": 3},   # Single Select
    {"field_name": "Quantity", "type": 2},   # Number
    {"field_name": "Price", "type": 2},      # Number
    {"field_name": "Last Restocked", "type": 5}  # DateTime
]

field_ids = {}
for field_data in fields:
    field_response = rest_call(
        "POST",
        f"/bitable/apps/{app_token}/tables/{table_id}/fields",
        field_data
    )
    field_ids[field_data["field_name"]] = field_response["field_id"]
    print(f"Created field: {field_data['field_name']} with ID {field_response['field_id']}")

# Step 4: Create option values for Category field
category_options = ["Electronics", "Office Supplies", "Furniture", "Kitchen"]
for option in category_options:
    option_response = rest_call(
        "POST",
        f"/bitable/apps/{app_token}/tables/{table_id}/fields/{field_ids['Category']}/options",
        {"name": option}
    )
    print(f"Added category option: {option}")

# Step 5: Add sample inventory items
import datetime

sample_items = [
    {
        "Item Name": "Laptop",
        "Category": "Electronics",
        "Quantity": 5,
        "Price": 1200,
        "Last Restocked": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "Item Name": "Office Chair",
        "Category": "Furniture",
        "Quantity": 10,
        "Price": 150,
        "Last Restocked": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "Item Name": "Pens (Box)",
        "Category": "Office Supplies",
        "Quantity": 25,
        "Price": 5,
        "Last Restocked": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]

for item in sample_items:
    # Convert to field_id format
    fields_data = {}
    for name, value in item.items():
        fields_data[field_ids[name]] = value
    
    record_response = rest_call(
        "POST",
        f"/bitable/apps/{app_token}/tables/{table_id}/records",
        {"fields": fields_data}
    )
    print(f"Added inventory item: {item['Item Name']}")

# Step 6: Query the data to verify
filter_formula = 'AND(CurrentValue.[Category] = "Electronics")'
query_response = rest_call(
    "GET",
    f"/bitable/apps/{app_token}/tables/{table_id}/records?filter={filter_formula}"
)

print("\nElectronics items in inventory:")
for record in query_response["data"]["items"]:
    fields = record["fields"]
    item_name = fields.get(field_ids["Item Name"], "Unknown")
    quantity = fields.get(field_ids["Quantity"], 0)
    price = fields.get(field_ids["Price"], 0)
    print(f"- {item_name}: {quantity} units at ${price} each")

# Step 7: Send a message with the Bitable link
send_message_response = mcp_call(
    "tools/call",
    "send_lark_message",
    {
        "receive_id": "oc_xxxxxxxx",  # Chat ID
        "msg_type": "text",
        "content": json.dumps({
            "text": f"I've created a new Inventory Tracker. View it here: https://bytedance.feishu.cn/base/{app_token}"
        })
    }
)

print("\nWorkflow completed successfully!")
```

## Conversation Management

This example demonstrates how to use the HypeTask session management capabilities to track and manage conversations.

```python
import requests
import json
import time
import uuid

BASE_URL = "https://your-lark-mcp-server.example.com/mcp/invoke"

def mcp_call(method, name=None, arguments=None):
    request_id = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    
    if method == "tools/call":
        payload["params"] = {
            "name": name,
            "arguments": arguments or {}
        }
    else:
        payload["params"] = {}
        
    response = requests.post(BASE_URL, json=payload)
    return response.json()

# Step 1: Create a new conversation session
user_id = "ou_xxxxxxxx"  # Replace with an actual user ID
session_response = mcp_call(
    "tools/call",
    "create_hypetask_session",
    {
        "user_id": user_id,
        "session_name": "Customer Support Session"
    }
)

session_token = session_response["result"]["session_token"]
print(f"Created session: {session_token}")

# Step 2: Log initial conversation
initial_query = "Hello, I need help with my order #12345. It hasn't arrived yet."
log_response = mcp_call(
    "tools/call",
    "log_conversation",
    {
        "session_token": session_token,
        "role": "user",
        "message": initial_query
    }
)
print("Logged user message")

# Step 3: Log AI response
ai_response = "I'm sorry to hear about the delay with your order. Let me check the status for you. Could you please confirm your email address associated with the order?"
log_response = mcp_call(
    "tools/call",
    "log_conversation",
    {
        "session_token": session_token,
        "role": "assistant",
        "message": ai_response
    }
)
print("Logged assistant response")

# Step 4: Log user follow-up
user_followup = "My email is customer@example.com"
log_response = mcp_call(
    "tools/call",
    "log_conversation",
    {
        "session_token": session_token,
        "role": "user",
        "message": user_followup
    }
)
print("Logged user follow-up")

# Step 5: Log AI action
ai_action = "I've checked your order status. Your order #12345 is currently in transit and expected to be delivered tomorrow by 5 PM. Would you like me to send you a tracking link?"
log_response = mcp_call(
    "tools/call",
    "log_conversation",
    {
        "session_token": session_token,
        "role": "assistant",
        "message": ai_action
    }
)
print("Logged assistant action")

# Step 6: Retrieve conversation history
history_response = mcp_call(
    "tools/call",
    "get_conversation_history",
    {
        "session_token": session_token
    }
)

print("\nConversation History:")
for message in history_response["result"]["messages"]:
    role = message["role"].upper()
    timestamp = message["timestamp"]
    content = message["message"]
    print(f"[{timestamp}] {role}: {content}")

# Step 7: Get session details
session_details = mcp_call(
    "tools/call",
    "get_hypetask_session",
    {
        "session_token": session_token
    }
)

print("\nSession Details:")
print(f"Session Token: {session_details['result']['session_token']}")
print(f"User ID: {session_details['result']['user_id']}")
print(f"Session Name: {session_details['result']['session_name']}")
print(f"Created At: {session_details['result']['created_at']}")
print(f"Message Count: {session_details['result']['message_count']}")
```

## Integration with Other Systems

This example demonstrates how to integrate the MCP Bridge with other systems like webhook notifications or external APIs.

```python
import requests
import json
import threading
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# Constants
MCP_BASE_URL = "https://your-lark-mcp-server.example.com/mcp/invoke"
WEBHOOK_PORT = 8000
WEBHOOK_PATH = "/webhook"

# Global variables
received_webhooks = []

def mcp_call(method, name=None, arguments=None):
    request_id = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    
    if method == "tools/call":
        payload["params"] = {
            "name": name,
            "arguments": arguments or {}
        }
    else:
        payload["params"] = {}
        
    response = requests.post(MCP_BASE_URL, json=payload)
    return response.json()

# Webhook server to receive notifications
class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.startswith(WEBHOOK_PATH):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode('utf-8'))
            
            received_webhooks.append({
                "timestamp": time.time(),
                "payload": payload
            })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())
            
            print(f"Received webhook: {json.dumps(payload, indent=2)}")
        else:
            self.send_response(404)
            self.end_headers()

# Start webhook server in a separate thread
def start_webhook_server():
    server = HTTPServer(('localhost', WEBHOOK_PORT), WebhookHandler)
    print(f"Starting webhook server on port {WEBHOOK_PORT}")
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server

# Main integration flow
def main():
    # Start webhook server
    server = start_webhook_server()
    
    try:
        # Step 1: Create a new Bitable app for tracking customer requests
        create_app_response = mcp_call(
            "tools/call",
            "create_bitable_app",
            {"name": "Customer Request Tracker"}
        )
        
        app_token = create_app_response["result"]["app_token"]
        print(f"Created Bitable app: {app_token}")
        
        # Step 2: Set up an external API integration to handle notifications
        # This would typically be done through the Lark admin interface
        # For this example, we'll simulate it with our local webhook server
        webhook_url = f"http://localhost:{WEBHOOK_PORT}{WEBHOOK_PATH}"
        print(f"Webhook URL for notifications: {webhook_url}")
        
        # Step 3: Create a new session for tracking this interaction
        session_response = mcp_call(
            "tools/call",
            "create_hypetask_session",
            {
                "user_id": "ou_xxxxxxxx",  # Replace with actual user ID
                "session_name": "External Integration Demo"
            }
        )
        
        session_token = session_response["result"]["session_token"]
        print(f"Created session: {session_token}")
        
        # Step 4: Log the integration setup in the conversation history
        log_response = mcp_call(
            "tools/call",
            "log_conversation",
            {
                "session_token": session_token,
                "role": "system",
                "message": f"Integration setup complete. Bitable app: {app_token}, Webhook URL: {webhook_url}"
            }
        )
        
        # Step 5: Simulate an external event triggering a webhook
        print("Simulating external event...")
        external_event = {
            "event_type": "new_order",
            "order_id": "ORD-12345",
            "customer_email": "customer@example.com",
            "items": [
                {"product_id": "P123", "name": "Widget", "quantity": 2},
                {"product_id": "P456", "name": "Gadget", "quantity": 1}
            ],
            "total_amount": 129.99
        }
        
        # Send this to our own webhook to simulate an external system
        requests.post(f"http://localhost:{WEBHOOK_PORT}{WEBHOOK_PATH}", json=external_event)
        
        # Wait a moment for the webhook to be processed
        time.sleep(1)
        
        # Step 6: Process the webhook data and use it to send a message
        if received_webhooks:
            latest_webhook = received_webhooks[-1]["payload"]
            
            # Send a message about the new order
            order_id = latest_webhook.get("order_id", "unknown")
            customer_email = latest_webhook.get("customer_email", "unknown")
            total_amount = latest_webhook.get("total_amount", 0)
            
            message = f"New order received!\nOrder ID: {order_id}\nCustomer: {customer_email}\nTotal: ${total_amount}"
            
            send_message_response = mcp_call(
                "tools/call",
                "send_lark_message",
                {
                    "receive_id": "oc_xxxxxxxx",  # Replace with actual chat ID
                    "msg_type": "text",
                    "content": json.dumps({"text": message})
                }
            )
            
            print(f"Sent notification message to Lark chat")
            
            # Log this in the conversation history
            log_response = mcp_call(
                "tools/call",
                "log_conversation",
                {
                    "session_token": session_token,
                    "role": "system",
                    "message": f"Processed webhook for order {order_id} and sent notification to Lark"
                }
            )
        
        # Step 7: Retrieve and display the conversation history
        history_response = mcp_call(
            "tools/call",
            "get_conversation_history",
            {
                "session_token": session_token
            }
        )
        
        print("\nIntegration Flow History:")
        for message in history_response["result"]["messages"]:
            role = message["role"].upper()
            timestamp = message["timestamp"]
            content = message["message"]
            print(f"[{timestamp}] {role}: {content}")
            
        print("\nIntegration demo completed successfully!")
        
    except Exception as e:
        print(f"Error during integration: {e}")
    finally:
        # Shutdown the webhook server
        server.shutdown()
        print("Webhook server stopped")

if __name__ == "__main__":
    main()
```

These examples demonstrate how to use the MCP Bridge for complex operations and integrations with external systems. They provide a foundation for building sophisticated applications that leverage the Lark MCP Telegram Server's capabilities through the MCP protocol.
