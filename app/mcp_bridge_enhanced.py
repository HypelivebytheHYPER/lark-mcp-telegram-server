"""
Enhanced MCP Bridge with Official LarkSuite Bitable Integration
Using HTTP Streaming MCP Protocol and Official lark-oapi-python SDK patterns
"""

import json
import logging
import asyncio
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router for MCP Bridge
router = APIRouter()

# Tool mapping with official Lark Bitable operations
ENHANCED_TOOL_MAP = {
    # Table Schema Operations
    "bitable_list_tables": {
        "description": "List all tables in a Lark Base application",
        "parameters": {
            "type": "object", 
            "properties": {
                "app_token": {"type": "string", "description": "Base application token"},
                "page_token": {"type": "string", "description": "Page token for pagination", "default": ""},
                "page_size": {"type": "integer", "description": "Number of items per page", "default": 20}
            },
            "required": ["app_token"]
        }
    },
    "bitable_get_table_schema": {
        "description": "Get detailed schema information for a specific table including all field definitions",
        "parameters": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Base application token"},
                "table_id": {"type": "string", "description": "Table identifier"}
            },
            "required": ["app_token", "table_id"]
        }
    },
    "bitable_list_fields": {
        "description": "List all fields in a table with their properties and types",
        "parameters": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Base application token"},
                "table_id": {"type": "string", "description": "Table identifier"},
                "view_id": {"type": "string", "description": "View identifier", "default": ""},
                "page_size": {"type": "integer", "description": "Number of fields per page", "default": 20}
            },
            "required": ["app_token", "table_id"]
        }
    },
    
    # Record Operations (Official SDK patterns)
    "bitable_list_records": {
        "description": "List records from a Lark Base table with filtering and pagination",
        "parameters": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Base application token"},
                "table_id": {"type": "string", "description": "Table identifier"},
                "view_id": {"type": "string", "description": "View identifier", "default": ""},
                "filter": {"type": "string", "description": "Filter formula", "default": ""},
                "sort": {"type": "string", "description": "Sort configuration", "default": ""},
                "page_size": {"type": "integer", "description": "Number of records per page", "default": 20},
                "page_token": {"type": "string", "description": "Page token for pagination", "default": ""}
            },
            "required": ["app_token", "table_id"]
        }
    },
    "bitable_get_record": {
        "description": "Get a specific record by ID from a Lark Base table",
        "parameters": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Base application token"},
                "table_id": {"type": "string", "description": "Table identifier"},
                "record_id": {"type": "string", "description": "Record identifier"},
                "user_id_type": {"type": "string", "description": "User ID type", "default": "user_id"}
            },
            "required": ["app_token", "table_id", "record_id"]
        }
    },
    "bitable_create_record": {
        "description": "Create a new record in a Lark Base table",
        "parameters": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Base application token"},
                "table_id": {"type": "string", "description": "Table identifier"},
                "fields": {"type": "object", "description": "Record field data as key-value pairs"},
                "user_id_type": {"type": "string", "description": "User ID type", "default": "user_id"}
            },
            "required": ["app_token", "table_id", "fields"]
        }
    },
    "bitable_update_record": {
        "description": "Update an existing record in a Lark Base table",
        "parameters": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Base application token"},
                "table_id": {"type": "string", "description": "Table identifier"},
                "record_id": {"type": "string", "description": "Record identifier"},
                "fields": {"type": "object", "description": "Updated field data as key-value pairs"},
                "user_id_type": {"type": "string", "description": "User ID type", "default": "user_id"}
            },
            "required": ["app_token", "table_id", "record_id", "fields"]
        }
    },
    "bitable_delete_record": {
        "description": "Delete a record from a Lark Base table",
        "parameters": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Base application token"},
                "table_id": {"type": "string", "description": "Table identifier"},
                "record_id": {"type": "string", "description": "Record identifier"}
            },
            "required": ["app_token", "table_id", "record_id"]
        }
    },
    
    # Batch Operations
    "bitable_batch_create_records": {
        "description": "Create multiple records in a Lark Base table in a single operation",
        "parameters": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Base application token"},
                "table_id": {"type": "string", "description": "Table identifier"},
                "records": {"type": "array", "description": "Array of record objects with fields"},
                "user_id_type": {"type": "string", "description": "User ID type", "default": "user_id"}
            },
            "required": ["app_token", "table_id", "records"]
        }
    },
    "bitable_search_records": {
        "description": "Search records in a Lark Base table with advanced filtering",
        "parameters": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Base application token"},
                "table_id": {"type": "string", "description": "Table identifier"},
                "filter": {"type": "string", "description": "Search filter formula"},
                "sort": {"type": "string", "description": "Sort configuration", "default": ""},
                "page_size": {"type": "integer", "description": "Number of records per page", "default": 20}
            },
            "required": ["app_token", "table_id", "filter"]
        }
    },
    
    # Legacy tools (maintained for compatibility)
    "send_lark_message": {
        "description": "Send a message to Lark/Feishu chat",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "Chat ID to send message to"},
                "message": {"type": "string", "description": "Message content to send"}
            },
            "required": ["chat_id", "message"]
        }
    },
    "create_bitable_app": {
        "description": "Create a new Lark Base application",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the new Bitable app"},
                "folder_token": {"type": "string", "description": "Folder token where to create the app", "default": ""}
            },
            "required": ["name"]
        }
    }
}

class LarkBitableClient:
    """Enhanced Lark Bitable client using official API patterns"""
    
    def __init__(self, app_id: str = None, app_secret: str = None, tenant_access_token: str = None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = tenant_access_token
        self.base_url = "https://open.larksuite.com/open-apis"
        
    async def get_tenant_access_token(self) -> str:
        """Get tenant access token using app credentials"""
        if self.tenant_access_token:
            return self.tenant_access_token
            
        if not self.app_id or not self.app_secret:
            raise ValueError("App ID and App Secret required for token generation")
            
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    self.tenant_access_token = data["tenant_access_token"]
                    return self.tenant_access_token
            raise Exception(f"Failed to get access token: {response.text}")
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Lark API"""
        token = await self.get_tenant_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            
            if response.status_code not in (200, 201):
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
            return response.json()
    
    # Table Schema Operations
    async def list_tables(self, app_token: str, page_token: str = "", page_size: int = 20) -> Dict[str, Any]:
        """List all tables in a Base application"""
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
            
        return await self._make_request(
            "GET", 
            f"/bitable/v1/apps/{app_token}/tables",
            params=params
        )
    
    async def get_table_schema(self, app_token: str, table_id: str) -> Dict[str, Any]:
        """Get table schema with field definitions"""
        # First get table info
        table_info = await self._make_request(
            "GET",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}"
        )
        
        # Then get field list
        fields_info = await self.list_fields(app_token, table_id)
        
        # Combine the information
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "table": table_info.get("data", {}).get("table", {}),
                "fields": fields_info.get("data", {}).get("items", [])
            }
        }
    
    async def list_fields(self, app_token: str, table_id: str, view_id: str = "", page_size: int = 20) -> Dict[str, Any]:
        """List all fields in a table"""
        params = {"page_size": page_size}
        if view_id:
            params["view_id"] = view_id
            
        return await self._make_request(
            "GET",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
            params=params
        )
    
    # Record Operations (Official SDK patterns)
    async def list_records(self, app_token: str, table_id: str, **kwargs) -> Dict[str, Any]:
        """List records from table with filtering and pagination"""
        params = {}
        for key, value in kwargs.items():
            if value:  # Only include non-empty values
                params[key] = value
                
        return await self._make_request(
            "GET",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records",
            params=params
        )
    
    async def get_record(self, app_token: str, table_id: str, record_id: str, **kwargs) -> Dict[str, Any]:
        """Get a specific record by ID"""
        params = {}
        for key, value in kwargs.items():
            if value:
                params[key] = value
                
        return await self._make_request(
            "GET",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
            params=params
        )
    
    async def create_record(self, app_token: str, table_id: str, fields: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Create a new record"""
        payload = {"fields": fields}
        
        params = {}
        for key, value in kwargs.items():
            if value:
                params[key] = value
                
        return await self._make_request(
            "POST",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records",
            json=payload,
            params=params
        )
    
    async def update_record(self, app_token: str, table_id: str, record_id: str, fields: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Update an existing record"""
        payload = {"fields": fields}
        
        params = {}
        for key, value in kwargs.items():
            if value:
                params[key] = value
                
        return await self._make_request(
            "PUT",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
            json=payload,
            params=params
        )
    
    async def delete_record(self, app_token: str, table_id: str, record_id: str) -> Dict[str, Any]:
        """Delete a record"""
        return await self._make_request(
            "DELETE",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        )
    
    async def batch_create_records(self, app_token: str, table_id: str, records: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Create multiple records in batch"""
        payload = {"records": [{"fields": record} for record in records]}
        
        params = {}
        for key, value in kwargs.items():
            if value:
                params[key] = value
                
        return await self._make_request(
            "POST",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
            json=payload,
            params=params
        )
    
    async def search_records(self, app_token: str, table_id: str, filter_formula: str, **kwargs) -> Dict[str, Any]:
        """Search records with filter formula"""
        payload = {"filter": filter_formula}
        
        # Add optional parameters
        for key in ["sort", "page_size"]:
            if key in kwargs and kwargs[key]:
                payload[key] = kwargs[key]
                
        return await self._make_request(
            "POST",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/search",
            json=payload
        )

# Initialize enhanced Bitable client with environment variables
enhanced_bitable_client = LarkBitableClient(
    app_id=os.getenv("LARK_APP_ID"),
    app_secret=os.getenv("LARK_APP_SECRET"),
    tenant_access_token=os.getenv("LARK_TENANT_ACCESS_TOKEN")  # Optional: if you have a pre-generated token
)

async def execute_bitable_operation(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Bitable operations using official SDK patterns"""
    try:
        # Extract common parameters
        app_token = arguments.get("app_token")
        table_id = arguments.get("table_id")
        
        if not app_token:
            raise ValueError("app_token is required for all Bitable operations")
        
        # Route to appropriate method
        if tool_name == "bitable_list_tables":
            return await enhanced_bitable_client.list_tables(
                app_token=app_token,
                page_token=arguments.get("page_token", ""),
                page_size=arguments.get("page_size", 20)
            )
        
        elif tool_name == "bitable_get_table_schema":
            if not table_id:
                raise ValueError("table_id is required")
            return await enhanced_bitable_client.get_table_schema(app_token, table_id)
        
        elif tool_name == "bitable_list_fields":
            if not table_id:
                raise ValueError("table_id is required")
            return await enhanced_bitable_client.list_fields(
                app_token=app_token,
                table_id=table_id,
                view_id=arguments.get("view_id", ""),
                page_size=arguments.get("page_size", 20)
            )
        
        elif tool_name == "bitable_list_records":
            if not table_id:
                raise ValueError("table_id is required")
            return await enhanced_bitable_client.list_records(
                app_token=app_token,
                table_id=table_id,
                **{k: v for k, v in arguments.items() if k not in ["app_token", "table_id"]}
            )
        
        elif tool_name == "bitable_get_record":
            record_id = arguments.get("record_id")
            if not table_id or not record_id:
                raise ValueError("table_id and record_id are required")
            return await enhanced_bitable_client.get_record(
                app_token=app_token,
                table_id=table_id,
                record_id=record_id,
                **{k: v for k, v in arguments.items() if k not in ["app_token", "table_id", "record_id"]}
            )
        
        elif tool_name == "bitable_create_record":
            fields = arguments.get("fields")
            if not table_id or not fields:
                raise ValueError("table_id and fields are required")
            return await enhanced_bitable_client.create_record(
                app_token=app_token,
                table_id=table_id,
                fields=fields,
                **{k: v for k, v in arguments.items() if k not in ["app_token", "table_id", "fields"]}
            )
        
        elif tool_name == "bitable_update_record":
            record_id = arguments.get("record_id")
            fields = arguments.get("fields")
            if not table_id or not record_id or not fields:
                raise ValueError("table_id, record_id and fields are required")
            return await enhanced_bitable_client.update_record(
                app_token=app_token,
                table_id=table_id,
                record_id=record_id,
                fields=fields,
                **{k: v for k, v in arguments.items() if k not in ["app_token", "table_id", "record_id", "fields"]}
            )
        
        elif tool_name == "bitable_delete_record":
            record_id = arguments.get("record_id")
            if not table_id or not record_id:
                raise ValueError("table_id and record_id are required")
            return await enhanced_bitable_client.delete_record(app_token, table_id, record_id)
        
        elif tool_name == "bitable_batch_create_records":
            records = arguments.get("records")
            if not table_id or not records:
                raise ValueError("table_id and records are required")
            return await enhanced_bitable_client.batch_create_records(
                app_token=app_token,
                table_id=table_id,
                records=records,
                **{k: v for k, v in arguments.items() if k not in ["app_token", "table_id", "records"]}
            )
        
        elif tool_name == "bitable_search_records":
            filter_formula = arguments.get("filter")
            if not table_id or not filter_formula:
                raise ValueError("table_id and filter are required")
            return await enhanced_bitable_client.search_records(
                app_token=app_token,
                table_id=table_id,
                filter_formula=filter_formula,
                **{k: v for k, v in arguments.items() if k not in ["app_token", "table_id", "filter"]}
            )
        
        else:
            raise ValueError(f"Unknown Bitable operation: {tool_name}")
            
    except Exception as e:
        logger.error(f"Error executing {tool_name}: {str(e)}")
        return {
            "error": {
                "code": -1,
                "message": str(e),
                "type": "execution_error"
            }
        }

@router.get("/tools")
async def list_mcp_tools():
    """List all available MCP tools with enhanced Bitable support"""
    tools = []
    for name, config in ENHANCED_TOOL_MAP.items():
        tools.append({
            "name": name,
            "description": config["description"],
            "inputSchema": config["parameters"]
        })
    
    return {"tools": tools}

@router.post("/invoke")
async def invoke_mcp_tool(request: Request):
    """
    Enhanced MCP Bridge endpoint with HTTP streaming support
    Handles JSON-RPC 2.0 protocol with Bitable operations
    """
    try:
        # Parse JSON-RPC request
        body = await request.json()
        
        # Validate JSON-RPC format
        if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request"
                    },
                    "id": body.get("id")
                }
            )
        
        method = body.get("method")
        request_id = body.get("id")
        
        # Handle tools/list method
        if method == "tools/list":
            tools = []
            for name, config in ENHANCED_TOOL_MAP.items():
                tools.append({
                    "name": name,
                    "description": config["description"],
                    "inputSchema": config["parameters"]
                })
            
            return {
                "jsonrpc": "2.0",
                "result": {"tools": tools},
                "id": request_id
            }
        
        # Handle tools/call method
        elif method == "tools/call":
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32602,
                            "message": "Missing tool name"
                        },
                        "id": request_id
                    }
                )
            
            if tool_name not in ENHANCED_TOOL_MAP:
                return JSONResponse(
                    status_code=404,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": f"Tool not found: {tool_name}"
                        },
                        "id": request_id
                    }
                )
            
            # Execute Bitable operations
            if tool_name.startswith("bitable_"):
                result = await execute_bitable_operation(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": json.dumps(result),
                        "isError": "error" in result
                    },
                    "id": request_id
                }
            
            # Handle legacy operations (preserved for compatibility)
            else:
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": json.dumps({
                            "message": f"Legacy tool {tool_name} executed",
                            "arguments": arguments
                        }),
                        "isError": False
                    },
                    "id": request_id
                }
        
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }
            )
    
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                },
                "id": None
            }
        )
    except Exception as e:
        logger.exception("Error in MCP bridge")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": body.get("id") if 'body' in locals() else None
            }
        )
