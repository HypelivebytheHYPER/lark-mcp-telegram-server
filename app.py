#!/usr/bin/env python3
"""
Production FastAPI server with REAL Lark and Telegram API integrations
"""
import os
import logging
import sys
import json
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Environment variables
LARK_APP_ID = os.getenv("LARK_APP_ID")
LARK_APP_SECRET = os.getenv("LARK_APP_SECRET") 
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", "8000"))

# Validate required environment variables
if not all([LARK_APP_ID, LARK_APP_SECRET, TELEGRAM_TOKEN]):
    logger.warning("⚠️ Missing API credentials - some endpoints may not work")
    logger.warning(f"LARK_APP_ID: {'✓' if LARK_APP_ID else '❌'}")
    logger.warning(f"LARK_APP_SECRET: {'✓' if LARK_APP_SECRET else '❌'}")
    logger.warning(f"TELEGRAM_TOKEN: {'✓' if TELEGRAM_TOKEN else '❌'}")

# Request/Response models
class MessageRequest(BaseModel):
    chat_id: str
    text: str

class ChatListRequest(BaseModel):
    limit: int = 10

class ChatMembersRequest(BaseModel):
    chat_id: str

class CreateGroupRequest(BaseModel):
    name: str
    description: str = ""
    user_ids: list = []

class BitableAppRequest(BaseModel):
    name: str
    folder_token: Optional[str] = None

class BitableTableRequest(BaseModel):
    app_token: str
    table_name: str
    fields: Optional[list] = []

class BitableRecordRequest(BaseModel):
    app_token: str
    table_id: str
    fields: dict

class WikiNodeRequest(BaseModel):
    token: str
    obj_type: str = "wiki"

class MessageResponse(BaseModel):
    success: bool
    message: str
    details: Optional[str] = None
    api_response: Optional[dict] = None

# Lark API client
class LarkClient:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.larksuite.com/open-apis"
        self._access_token = None
        
    async def get_access_token(self):
        """Get Lark access token"""
        if self._access_token:
            return self._access_token
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/v3/tenant_access_token/internal",
                headers={"Content-Type": "application/json"},
                json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret
                }
            )
            
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                self._access_token = data["tenant_access_token"]
                return self._access_token
            else:
                raise HTTPException(status_code=400, detail=f"Lark auth failed: {data}")
        else:
            raise HTTPException(status_code=response.status_code, detail="Lark auth request failed")
    
    async def send_message(self, chat_id: str, text: str):
        """Send message to Lark chat"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/im/v1/messages",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "receive_id": chat_id,
                    "msg_type": "text",
                    "content": json.dumps({"text": text})
                },
                params={"receive_id_type": "chat_id"}
            )
            
        return response.status_code, response.json()
    
    async def get_chat_list(self, limit: int = 10):
        """Get list of chats"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/im/v1/chats",
                headers={"Authorization": f"Bearer {token}"},
                params={"page_size": limit, "user_id_type": "open_id"}
            )
        
        return response.status_code, response.json()
    
    async def get_chat_members(self, chat_id: str):
        """Get members of a specific chat"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/im/v1/chats/{chat_id}/members",
                headers={"Authorization": f"Bearer {token}"},
                params={"member_id_type": "open_id", "page_size": 100}
            )
        
        return response.status_code, response.json()
    
    async def create_group(self, name: str, description: str = "", user_ids: list = None):
        """Create a new group chat"""
        token = await self.get_access_token()
        
        group_data = {
            "name": name,
            "description": description,
            "chat_type": "group"
        }
        
        if user_ids:
            group_data["user_id_list"] = user_ids
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/im/v1/chats",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=group_data,
                params={"user_id_type": "open_id"}
            )
        
        return response.status_code, response.json()
    
    async def create_bitable_app(self, name: str, folder_token: str = None):
        """Create a new Bitable app"""
        token = await self.get_access_token()
        
        app_data = {"name": name}
        if folder_token:
            app_data["folder_token"] = folder_token
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bitable/v1/apps",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=app_data
            )
        
        return response.status_code, response.json()
    
    async def list_bitable_tables(self, app_token: str):
        """List tables in a Bitable app"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/bitable/v1/apps/{app_token}/tables",
                headers={"Authorization": f"Bearer {token}"},
                params={"page_size": 100}
            )
        
        return response.status_code, response.json()
    
    async def create_bitable_table(self, app_token: str, table_name: str, fields: list = None):
        """Create a new table in Bitable app"""
        token = await self.get_access_token()
        
        table_data = {"table": {"name": table_name}}
        if fields:
            table_data["table"]["fields"] = fields
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bitable/v1/apps/{app_token}/tables",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=table_data
            )
        
        return response.status_code, response.json()
    
    async def query_bitable_records(self, app_token: str, table_id: str, page_size: int = 100):
        """Query records from a Bitable table"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/search",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={},
                params={
                    "page_size": page_size,
                    "user_id_type": "open_id"
                }
            )
        
        return response.status_code, response.json()
    
    async def create_bitable_record(self, app_token: str, table_id: str, fields: dict):
        """Create a new record in Bitable table"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"fields": fields},
                params={"user_id_type": "open_id"}
            )
        
        return response.status_code, response.json()
    
    async def get_wiki_node(self, token: str, obj_type: str = "wiki"):
        """Get Wiki node information"""
        access_token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/wiki/v2/spaces/get_node",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"token": token, "obj_type": obj_type}
            )
        
        return response.status_code, response.json()
    
    async def get_document_content(self, document_id: str):
        """Get document raw content"""
        access_token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/docx/v1/documents/{document_id}/raw_content",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"lang": 0}
            )
        
        return response.status_code, response.json()
    
    async def get_user_info(self, user_id: str):
        """Get user information"""
        access_token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/contact/v3/users/{user_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "user_id_type": "open_id",
                    "department_id_type": "open_department_id"
                }
            )
        
        return response.status_code, response.json()
    
    async def list_departments(self, parent_department_id: str = None):
        """List departments"""
        access_token = await self.get_access_token()
        
        params = {
            "department_id_type": "open_department_id", 
            "user_id_type": "open_id",
            "fetch_child": True,
            "page_size": 50
        }
        
        if parent_department_id:
            params["parent_department_id"] = parent_department_id
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/contact/v3/departments",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params
            )
        
        return response.status_code, response.json()

# Telegram API client  
class TelegramClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        
    async def send_message(self, chat_id: str, text: str):
        """Send message to Telegram chat"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
            )
            
        return response.status_code, response.json()

# Initialize API clients
lark_client = LarkClient(LARK_APP_ID, LARK_APP_SECRET) if LARK_APP_ID and LARK_APP_SECRET else None
telegram_client = TelegramClient(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

# Create FastAPI application
app = FastAPI(
    title="Lark-Telegram Bridge Server",
    description="HTTP server for bridging Lark and Telegram messaging with real API integrations",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Lark-Telegram Bridge Server",
        "version": "2.0.0", 
        "status": "running",
        "deployment": "render-production-with-real-apis",
        "environment": os.getenv("RENDER", "development"),
        "port": os.getenv("PORT", "8000"),
        "integrations": {
            "lark": "✓ configured" if lark_client else "❌ missing credentials",
            "telegram": "✓ configured" if telegram_client else "❌ missing credentials"
        },
        "endpoints": {
            "health": "/health",
            "ready": "/ready", 
            "lark": {
                "send": "/api/v1/lark/send",
                "chats": "/api/v1/lark/chats",
                "members": "/api/v1/lark/chats/{chat_id}/members",
                "create_group": "/api/v1/lark/groups/create",
                "test_auth": "/api/v1/lark/test-auth"
            },
            "bitable": {
                "create_app": "/api/v1/bitable/apps/create",
                "list_tables": "/api/v1/bitable/apps/{app_token}/tables",
                "create_table": "/api/v1/bitable/apps/{app_token}/tables/create",
                "query_records": "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records",
                "create_record": "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/create"
            },
            "wiki": {
                "get_node": "/api/v1/wiki/nodes/{token}"
            },
            "documents": {
                "get_content": "/api/v1/documents/{document_id}/content"
            },
            "contacts": {
                "get_user": "/api/v1/contacts/users/{user_id}",
                "list_departments": "/api/v1/contacts/departments"
            },
            "telegram": "/api/v1/telegram/send"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "lark-telegram-bridge",
        "deployment_status": "production-ready-with-real-apis",
        "integrations": {
            "lark_configured": lark_client is not None,
            "telegram_configured": telegram_client is not None
        }
    }

@app.get("/ready") 
async def readiness_check():
    """Readiness check endpoint"""    
    return {
        "ready": True,
        "services": {
            "server": True,
            "lark_client": lark_client is not None,
            "telegram_client": telegram_client is not None
        },
        "deployment": "fastapi-server-with-real-apis",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/v1/lark/test-auth")
async def test_lark_auth():
    """Test Lark authentication only"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        token = await lark_client.get_access_token()
        return {"success": True, "message": "Authentication successful", "token_length": len(token)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/v1/lark/send")
async def send_lark_endpoint(request: MessageRequest):
    """Send message to Lark chat using real API"""
    
    if not lark_client:
        raise HTTPException(
            status_code=503, 
            detail="Lark integration not configured - missing LARK_APP_ID or LARK_APP_SECRET"
        )
    
    logger.info(f"Lark API request: chat_id={request.chat_id}, text_length={len(request.text)}")
    
    try:
        status_code, api_response = await lark_client.send_message(request.chat_id, request.text)
        
        if status_code == 200 and api_response.get("code") == 0:
            return MessageResponse(
                success=True,
                message=f"Message sent to Lark chat {request.chat_id}",
                details="Lark API call successful",
                api_response=api_response
            )
        else:
            logger.error(f"Lark API error: {api_response}")
            return MessageResponse(
                success=False,
                message="Failed to send message to Lark",
                details=f"API error: {api_response}",
                api_response=api_response
            )
            
    except Exception as e:
        logger.error(f"Lark API exception: {e}")
        raise HTTPException(status_code=500, detail=f"Lark API error: {str(e)}")

@app.get("/api/v1/lark/chats")
async def get_lark_chats():
    """Get list of Lark chats"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.get_chat_list()
        
        if status_code == 200 and api_response.get("code") == 0:
            return MessageResponse(
                success=True,
                message="Chat list retrieved successfully",
                details=f"Found {len(api_response.get('data', {}).get('items', []))} chats",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to get chat list",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/v1/lark/chats/{chat_id}/members")
async def get_chat_members(chat_id: str):
    """Get members of a specific Lark chat"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.get_chat_members(chat_id)
        
        if status_code == 200 and api_response.get("code") == 0:
            return MessageResponse(
                success=True,
                message=f"Members retrieved for chat {chat_id}",
                details=f"Found {len(api_response.get('data', {}).get('items', []))} members",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to get chat members",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/v1/lark/groups/create")
async def create_lark_group(request: CreateGroupRequest):
    """Create a new Lark group chat"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.create_group(
            request.name, 
            request.description, 
            request.user_ids if request.user_ids else None
        )
        
        if status_code == 200 and api_response.get("code") == 0:
            return MessageResponse(
                success=True,
                message=f"Group '{request.name}' created successfully",
                details=f"Group ID: {api_response.get('data', {}).get('chat_id')}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to create group",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/v1/bitable/apps/create")
async def create_bitable_app(request: BitableAppRequest):
    """Create a new Bitable app"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.create_bitable_app(
            request.name, request.folder_token
        )
        
        if status_code == 200 and api_response.get("code") == 0:
            app_data = api_response.get('data', {})
            return MessageResponse(
                success=True,
                message=f"Bitable app '{request.name}' created successfully",
                details=f"App Token: {app_data.get('app_token')}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to create Bitable app",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/v1/bitable/apps/{app_token}/tables")
async def list_bitable_tables(app_token: str):
    """List tables in a Bitable app"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.list_bitable_tables(app_token)
        
        if status_code == 200 and api_response.get("code") == 0:
            tables_data = api_response.get('data', {}).get('items', [])
            return MessageResponse(
                success=True,
                message=f"Retrieved {len(tables_data)} tables from Bitable app",
                details=f"App Token: {app_token}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to list Bitable tables",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/v1/bitable/apps/{app_token}/tables/create")
async def create_bitable_table(app_token: str, request: BitableTableRequest):
    """Create a new table in Bitable app"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.create_bitable_table(
            app_token, request.table_name, request.fields
        )
        
        if status_code == 200 and api_response.get("code") == 0:
            table_data = api_response.get('data', {})
            return MessageResponse(
                success=True,
                message=f"Table '{request.table_name}' created successfully",
                details=f"Table ID: {table_data.get('table_id')}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to create Bitable table",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/v1/bitable/apps/{app_token}/tables/{table_id}/records")
async def query_bitable_records(app_token: str, table_id: str, page_size: int = 100):
    """Query records from a Bitable table"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.query_bitable_records(
            app_token, table_id, page_size
        )
        
        if status_code == 200 and api_response.get("code") == 0:
            records_data = api_response.get('data', {}).get('items', [])
            return MessageResponse(
                success=True,
                message=f"Retrieved {len(records_data)} records from Bitable table",
                details=f"Table ID: {table_id}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to query Bitable records",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/create")
async def create_bitable_record(app_token: str, table_id: str, request: BitableRecordRequest):
    """Create a new record in Bitable table"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.create_bitable_record(
            app_token, table_id, request.fields
        )
        
        if status_code == 200 and api_response.get("code") == 0:
            record_data = api_response.get('data', {})
            return MessageResponse(
                success=True,
                message="Record created successfully in Bitable table",
                details=f"Record ID: {record_data.get('record_id')}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to create Bitable record",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/v1/wiki/nodes/{token}")
async def get_wiki_node(token: str, obj_type: str = "wiki"):
    """Get Wiki node information"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.get_wiki_node(token, obj_type)
        
        if status_code == 200 and api_response.get("code") == 0:
            node_data = api_response.get('data', {})
            return MessageResponse(
                success=True,
                message=f"Wiki node information retrieved successfully",
                details=f"Node Type: {node_data.get('obj_type')}, Title: {node_data.get('title', 'N/A')}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to get Wiki node",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/v1/documents/{document_id}/content")
async def get_document_content(document_id: str):
    """Get document raw content"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.get_document_content(document_id)
        
        if status_code == 200 and api_response.get("code") == 0:
            content_data = api_response.get('data', {})
            content_text = content_data.get('content', '')
            return MessageResponse(
                success=True,
                message=f"Document content retrieved successfully",
                details=f"Content length: {len(content_text)} characters",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to get document content",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/v1/contacts/users/{user_id}")
async def get_user_info(user_id: str):
    """Get user information"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.get_user_info(user_id)
        
        if status_code == 200 and api_response.get("code") == 0:
            user_data = api_response.get('data', {}).get('user', {})
            return MessageResponse(
                success=True,
                message=f"User information retrieved successfully",
                details=f"Name: {user_data.get('name', 'N/A')}, Email: {user_data.get('email', 'N/A')}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to get user information",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/v1/contacts/departments")
async def list_departments(parent_department_id: str = None):
    """List departments"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.list_departments(parent_department_id)
        
        if status_code == 200 and api_response.get("code") == 0:
            dept_data = api_response.get('data', {}).get('items', [])
            return MessageResponse(
                success=True,
                message=f"Retrieved {len(dept_data)} departments",
                details=f"Parent ID: {parent_department_id or 'Root'}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to list departments",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/v1/telegram/send") 
async def send_telegram_endpoint(request: MessageRequest):
    """Send message to Telegram chat using real API"""
    
    if not telegram_client:
        raise HTTPException(
            status_code=503, 
            detail="Telegram integration not configured - missing TELEGRAM_TOKEN"
        )
    
    logger.info(f"Telegram API request: chat_id={request.chat_id}, text_length={len(request.text)}")
        
    try:
        status_code, api_response = await telegram_client.send_message(request.chat_id, request.text)
        
        if status_code == 200 and api_response.get("ok"):
            return MessageResponse(
                success=True,
                message=f"Message sent to Telegram chat {request.chat_id}",
                details="Telegram API call successful",
                api_response=api_response
            )
        else:
            logger.error(f"Telegram API error: {api_response}")
            return MessageResponse(
                success=False,
                message="Failed to send message to Telegram", 
                details=f"API error: {api_response}",
                api_response=api_response
            )
            
    except Exception as e:
        logger.error(f"Telegram API exception: {e}")
        raise HTTPException(status_code=500, detail=f"Telegram API error: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error", 
            "path": str(request.url),
            "service": "lark-telegram-bridge",
            "deployment": "production-with-real-apis"
        }
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🚀 Starting Production Lark-Telegram Bridge Server with Real APIs on port {port}")
    logger.info(f"📊 Environment: {os.getenv('RENDER', 'development')}")
    logger.info(f"🔧 Deployment: FastAPI production server with real API integrations")
    logger.info(f"🔗 Lark integration: {'✓ configured' if lark_client else '❌ missing credentials'}")
    logger.info(f"🔗 Telegram integration: {'✓ configured' if telegram_client else '❌ missing credentials'}")
    
    # Production-optimized uvicorn configuration
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        server_header=False,
        workers=1
    )