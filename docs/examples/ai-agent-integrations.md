# MCP Bridge Integration with AI Agent Systems

This guide demonstrates how to integrate various AI agent systems with the Lark MCP Telegram Server using the MCP Bridge. The MCP Bridge provides a standardized JSON-RPC 2.0 interface for AI agents to interact with Lark/Feishu.

## Table of Contents

1. [n8n AI Agent Integration](#n8n-ai-agent-integration)
2. [LangChain Integration](#langchain-integration)
3. [OpenAI Function Calling Integration](#openai-function-calling-integration)
4. [Microsoft AutoGen Integration](#microsoft-autogen-integration)
5. [Anthropic Claude Integration](#anthropic-claude-integration)
6. [LlamaIndex Integration](#llamaindex-integration)

## n8n AI Agent Integration

For detailed n8n AI Agent integration instructions, see the [dedicated n8n integration guide](n8n-integration.md).

## LangChain Integration

LangChain provides a flexible framework for building applications with LLMs. Here's how to integrate the MCP Bridge with LangChain:

### Setup

First, install the required packages:

```bash
pip install langchain langchain-openai requests
```

### Implementation

```python
from langchain.agents import tool
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate
from langchain.tools import StructuredTool
import requests
import json
import uuid

MCP_BASE_URL = "https://your-lark-mcp-server.example.com/mcp/invoke"

def call_mcp(method, name=None, arguments=None):
    """Helper function to call the MCP Bridge"""
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

def discover_mcp_tools():
    """Discover available tools on the MCP Bridge"""
    response = call_mcp("tools/list")
    return response["result"]["tools"]

# Dynamically create LangChain tools from MCP tools
def create_langchain_tools():
    tools = []
    mcp_tools = discover_mcp_tools()
    
    for mcp_tool in mcp_tools:
        tool_name = mcp_tool["name"]
        tool_description = mcp_tool["description"]
        
        # Create a function that will call the MCP tool
        def make_tool_function(name):
            def tool_function(**kwargs):
                result = call_mcp("tools/call", name=name, arguments=kwargs)
                return json.dumps(result["result"])
            return tool_function
        
        # Create the LangChain tool
        langchain_tool = StructuredTool.from_function(
            func=make_tool_function(tool_name),
            name=tool_name,
            description=tool_description,
            # Add argument schema based on MCP tool parameters
            args_schema=mcp_tool.get("parameters", None)
        )
        
        tools.append(langchain_tool)
    
    return tools

# Create LangChain tools
langchain_tools = create_langchain_tools()

# Create the LangChain agent
llm = ChatOpenAI(model="gpt-4", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI assistant that helps users interact with Lark/Feishu. "
              "You have access to tools that allow you to send messages, work with Bitable, "
              "and manage conversations."),
    ("human", "{input}"),
])

agent = create_openai_tools_agent(llm, langchain_tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=langchain_tools, verbose=True)

# Example usage
result = agent_executor.invoke({"input": "Send a message to the chat with ID 'oc_12345678' saying 'Hello from LangChain!'"})
print(result["output"])
```

## OpenAI Function Calling Integration

You can directly integrate the MCP Bridge with OpenAI's function calling capabilities:

```python
import openai
import requests
import json
import uuid

# Configure your OpenAI API key
openai.api_key = "your-openai-api-key"

MCP_BASE_URL = "https://your-lark-mcp-server.example.com/mcp/invoke"

def call_mcp(method, name=None, arguments=None):
    """Helper function to call the MCP Bridge"""
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

def discover_mcp_tools():
    """Discover available tools on the MCP Bridge"""
    response = call_mcp("tools/list")
    return response["result"]["tools"]

def convert_to_openai_functions(mcp_tools):
    """Convert MCP tools to OpenAI function definitions"""
    functions = []
    
    for tool in mcp_tools:
        function = {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        if "parameters" in tool:
            # Convert parameters to OpenAI format
            properties = tool["parameters"].get("properties", {})
            required = tool["parameters"].get("required", [])
            
            for param_name, param_details in properties.items():
                function["parameters"]["properties"][param_name] = {
                    "type": param_details.get("type", "string"),
                    "description": param_details.get("description", "")
                }
                
                if "enum" in param_details:
                    function["parameters"]["properties"][param_name]["enum"] = param_details["enum"]
            
            function["parameters"]["required"] = required
        
        functions.append(function)
    
    return functions

# Discover MCP tools and convert to OpenAI functions
mcp_tools = discover_mcp_tools()
openai_functions = convert_to_openai_functions(mcp_tools)

# Example conversation with function calling
def chat_with_functions(user_message):
    messages = [
        {"role": "system", "content": "You are an AI assistant that helps users interact with Lark/Feishu."},
        {"role": "user", "content": user_message}
    ]
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=messages,
        functions=openai_functions,
        function_call="auto"
    )
    
    ai_message = response.choices[0].message
    
    # Check if the model wants to call a function
    if ai_message.function_call:
        function_name = ai_message.function_call.name
        function_args = json.loads(ai_message.function_call.arguments)
        
        # Call the MCP tool
        result = call_mcp("tools/call", name=function_name, arguments=function_args)
        
        # Add the function result to the conversation
        messages.append({
            "role": "function",
            "name": function_name,
            "content": json.dumps(result["result"])
        })
        
        # Get the final response from the model
        final_response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        
        return final_response.choices[0].message.content
    else:
        return ai_message.content

# Example usage
result = chat_with_functions("Send a message to the Lark chat with ID 'oc_12345678' saying 'Hello from OpenAI!'")
print(result)
```

## Microsoft AutoGen Integration

Microsoft AutoGen is a framework for building agent-based applications. Here's how to integrate with MCP Bridge:

```python
import autogen
from autogen import config_list_from_json
import requests
import json
import uuid

MCP_BASE_URL = "https://your-lark-mcp-server.example.com/mcp/invoke"

def call_mcp(method, name=None, arguments=None):
    """Helper function to call the MCP Bridge"""
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

# Define MCP tool functions
def list_mcp_tools():
    """List all available tools on the MCP server."""
    response = call_mcp("tools/list")
    return response["result"]["tools"]

def send_lark_message(receive_id, content, msg_type="text"):
    """Send a message to a Lark chat or user."""
    if isinstance(content, str):
        content = {"text": content}
    
    if isinstance(content, dict):
        content = json.dumps(content)
    
    response = call_mcp("tools/call", name="send_lark_message", arguments={
        "receive_id": receive_id,
        "content": content,
        "msg_type": msg_type
    })
    
    return response["result"]

def list_departments(parent_id=None):
    """List departments in Lark."""
    args = {}
    if parent_id:
        args["parent_id"] = parent_id
    
    response = call_mcp("tools/call", name="list_departments", arguments=args)
    return response["result"]

# Create AutoGen agents
config_list = config_list_from_json("OAI_CONFIG_LIST")

assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={
        "config_list": config_list,
    },
    system_message="You are an AI assistant that helps users interact with Lark/Feishu. You can send messages, list departments, and perform other actions."
)

# Create a user proxy agent with MCP tools
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
    code_execution_config={"use_docker": False},
    function_map={
        "list_mcp_tools": list_mcp_tools,
        "send_lark_message": send_lark_message,
        "list_departments": list_departments,
    }
)

# Example conversation
user_proxy.initiate_chat(
    assistant,
    message="Send a message to Lark chat 'oc_12345678' saying 'Hello from AutoGen!'"
)
```

## Anthropic Claude Integration

Anthropic's Claude has tool-calling capabilities that can be used with the MCP Bridge:

```python
import anthropic
import requests
import json
import uuid

# Configure your Claude API key
client = anthropic.Anthropic(api_key="your-anthropic-api-key")

MCP_BASE_URL = "https://your-lark-mcp-server.example.com/mcp/invoke"

def call_mcp(method, name=None, arguments=None):
    """Helper function to call the MCP Bridge"""
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

def discover_mcp_tools():
    """Discover available tools on the MCP Bridge"""
    response = call_mcp("tools/list")
    return response["result"]["tools"]

def convert_to_claude_tools(mcp_tools):
    """Convert MCP tools to Claude tool definitions"""
    tools = []
    
    for tool in mcp_tools:
        claude_tool = {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        if "parameters" in tool:
            # Convert parameters to Claude format
            properties = tool["parameters"].get("properties", {})
            required = tool["parameters"].get("required", [])
            
            for param_name, param_details in properties.items():
                claude_tool["input_schema"]["properties"][param_name] = {
                    "type": param_details.get("type", "string"),
                    "description": param_details.get("description", "")
                }
                
                if "enum" in param_details:
                    claude_tool["input_schema"]["properties"][param_name]["enum"] = param_details["enum"]
            
            claude_tool["input_schema"]["required"] = required
        
        tools.append(claude_tool)
    
    return tools

# Discover MCP tools and convert to Claude tools
mcp_tools = discover_mcp_tools()
claude_tools = convert_to_claude_tools(mcp_tools)

# Example conversation with Claude tool calling
def chat_with_claude(user_message):
    messages = [
        {
            "role": "user", 
            "content": "You are an AI assistant that helps users interact with Lark/Feishu. " + user_message
        }
    ]
    
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=messages,
        tools=claude_tools
    )
    
    ai_message = response.content[0].text
    tool_calls = response.tool_use or []
    
    if tool_calls:
        for tool_call in tool_calls:
            # Call the MCP tool
            result = call_mcp(
                "tools/call", 
                name=tool_call.name, 
                arguments=tool_call.input
            )
            
            # Add the tool result to the conversation
            messages.append({
                "role": "assistant",
                "content": ai_message,
                "tool_use": [tool_call]
            })
            
            messages.append({
                "role": "tool",
                "tool_use_id": tool_call.id,
                "content": json.dumps(result["result"])
            })
            
            # Get the final response from Claude
            final_response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=messages
            )
            
            return final_response.content[0].text
    else:
        return ai_message

# Example usage
result = chat_with_claude("Send a message to the Lark chat with ID 'oc_12345678' saying 'Hello from Claude!'")
print(result)
```

## LlamaIndex Integration

LlamaIndex is a data framework for LLM applications. Here's how to integrate with MCP Bridge:

```python
import json
import uuid
import requests
from llama_index.core import Tool
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI

MCP_BASE_URL = "https://your-lark-mcp-server.example.com/mcp/invoke"

def call_mcp(method, name=None, arguments=None):
    """Helper function to call the MCP Bridge"""
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

def discover_mcp_tools():
    """Discover available tools on the MCP Bridge"""
    response = call_mcp("tools/list")
    return response["result"]["tools"]

# Create LlamaIndex tools from MCP tools
def create_llamaindex_tools():
    tools = []
    mcp_tools = discover_mcp_tools()
    
    for mcp_tool in mcp_tools:
        tool_name = mcp_tool["name"]
        tool_description = mcp_tool["description"]
        
        # Create a function that will call the MCP tool
        def make_tool_function(name):
            def tool_function(**kwargs):
                result = call_mcp("tools/call", name=name, arguments=kwargs)
                return json.dumps(result["result"], indent=2)
            return tool_function
        
        # Create the LlamaIndex tool
        llamaindex_tool = Tool.from_function(
            func=make_tool_function(tool_name),
            name=tool_name,
            description=tool_description
        )
        
        tools.append(llamaindex_tool)
    
    return tools

# Create LlamaIndex tools and agent
llamaindex_tools = create_llamaindex_tools()

llm = OpenAI(model="gpt-4")
agent = ReActAgent.from_tools(
    tools=llamaindex_tools,
    llm=llm,
    verbose=True,
    system_prompt=(
        "You are an AI assistant that helps users interact with Lark/Feishu. "
        "You have access to tools that allow you to send messages, work with Bitable, "
        "and manage conversations."
    )
)

# Example usage
response = agent.chat("Send a message to Lark chat 'oc_12345678' saying 'Hello from LlamaIndex!'")
print(response)
```

These examples demonstrate how to integrate the MCP Bridge with various AI agent frameworks. You can adapt these patterns to other frameworks or build custom integrations based on your specific needs.
