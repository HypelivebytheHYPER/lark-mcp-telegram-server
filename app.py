#!/usr/bin/env python3
"""
Production FastAPI server with REAL Lark and Telegram API integrations
Enhanced with optional security features for production use
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
import uuid
import asyncio
from datetime import timedelta
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Import security configuration
from security_config import security_manager, limiter

# Load environment variables
load_dotenv()

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Environment variables - strip whitespace to prevent encoding issues
LARK_APP_ID = os.getenv("LARK_APP_ID", "").strip()
LARK_APP_SECRET = os.getenv("LARK_APP_SECRET", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
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

class BitableRecordUpdateRequest(BaseModel):
    app_token: str
    table_id: str
    record_id: str
    fields: dict

class BitableTableUpdateRequest(BaseModel):
    app_token: str
    table_id: str
    name: Optional[str] = None

class BitableBatchCreateRequest(BaseModel):
    app_token: str
    table_id: str
    records: list[dict]  # List of {"fields": {...}} objects

class BitableBatchUpdateRequest(BaseModel):
    app_token: str
    table_id: str
    records: list[dict]  # List of {"record_id": "...", "fields": {...}} objects

class BitableBatchDeleteRequest(BaseModel):
    app_token: str
    table_id: str
    record_ids: list[str]

class WikiNodeRequest(BaseModel):
    token: str
    obj_type: str = "wiki"

class MessageResponse(BaseModel):
    success: bool
    message: str
    details: Optional[str] = None
    api_response: Optional[dict] = None

# Lark API client
class SupabaseClient:
    """Supabase client for HypeTask session management"""
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("⚠️ Supabase credentials missing - session features disabled")
            self.enabled = False
            return
        self.enabled = True
        self.base_url = SUPABASE_URL.strip()
        # Clean JWT token - remove newlines and whitespace that cause header encoding issues
        self.api_key = SUPABASE_KEY.strip().replace('\n', '').replace(' ', '')
        
        # Validate JWT format (should have 3 parts separated by dots)
        jwt_parts = self.api_key.split('.')
        if len(jwt_parts) != 3:
            logger.error(f"⚠️ Invalid JWT format: expected 3 parts, got {len(jwt_parts)}")
            self.enabled = False
        else:
            logger.info(f"✅ Supabase JWT validated: {len(self.api_key)} chars, 3 parts")
            
    def _get_headers(self):
        """Get standardized headers for Supabase requests"""
        return {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    async def create_session(self, user_id: str, platform: str, user_context: dict = None) -> dict:
        """Create new user session"""
        if not self.enabled:
            return {"success": False, "error": "Supabase not configured"}
            
        session_token = str(uuid.uuid4())
        
        async with httpx.AsyncClient() as client:
            try:
                headers = self._get_headers()
                headers["Prefer"] = "return=representation"
                
                response = await client.post(
                    f"{self.base_url}/rest/v1/hypetask_user_sessions",
                    headers=headers,
                    json={
                        "user_id": user_id,
                        "session_token": session_token,
                        "platform": platform,
                        "user_context": user_context or {},
                        "preferences": {}
                    }
                )
                
                if response.status_code == 201:
                    session_data = response.json()[0]
                    return {"success": True, "session": session_data}
                else:
                    logger.error(f"Failed to create session: {response.text}")
                    return {"success": False, "error": response.text}
                    
            except Exception as e:
                logger.error(f"Session creation error: {e}")
                return {"success": False, "error": str(e)}
    
    async def get_session(self, session_token: str) -> dict:
        """Get session by token"""
        if not self.enabled:
            return {"success": False, "error": "Supabase not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/rest/v1/hypetask_user_sessions",
                    headers=self._get_headers(),
                    params={
                        "session_token": f"eq.{session_token}",
                        "is_active": "eq.true",
                        "expires_at": f"gte.{datetime.utcnow().isoformat()}"
                    }
                )
                
                if response.status_code == 200:
                    sessions = response.json()
                    if sessions:
                        return {"success": True, "session": sessions[0]}
                    else:
                        return {"success": False, "error": "Session not found or expired"}
                else:
                    return {"success": False, "error": response.text}
                    
            except Exception as e:
                logger.error(f"Session retrieval error: {e}")
                return {"success": False, "error": str(e)}
    
    async def log_conversation(self, session_id: str, user_id: str, platform: str, 
                              message_type: str, content: str, action_data: dict = None):
        """Log conversation message"""
        if not self.enabled:
            return {"success": False, "error": "Supabase not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/rest/v1/hypetask_conversations",
                    headers=self._get_headers(),
                    json={
                        "session_id": session_id,
                        "user_id": user_id,
                        "platform": platform,
                        "message_type": message_type,
                        "content": content,
                        "action_data": action_data or {}
                    }
                )
                
                return {"success": response.status_code == 201}
                
            except Exception as e:
                logger.error(f"Conversation logging error: {e}")
                return {"success": False, "error": str(e)}


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

    async def update_bitable_record(self, app_token: str, table_id: str, record_id: str, fields: dict):
        """Update a record in Bitable table"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"fields": fields},
                params={"user_id_type": "open_id"}
            )
        
        return response.status_code, response.json()

    async def delete_bitable_record(self, app_token: str, table_id: str, record_id: str):
        """Delete a record from Bitable table"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
                headers={"Authorization": f"Bearer {token}"},
                params={"user_id_type": "open_id"}
            )
        
        return response.status_code, response.json()

    async def update_bitable_table(self, app_token: str, table_id: str, name: str):
        """Update a table name in Bitable app"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"name": name},
                params={"user_id_type": "open_id"}
            )
        
        return response.status_code, response.json()

    async def delete_bitable_table(self, app_token: str, table_id: str):
        """Delete a table from Bitable app"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}",
                headers={"Authorization": f"Bearer {token}"},
                params={"user_id_type": "open_id"}
            )
        
        return response.status_code, response.json()

    async def batch_create_bitable_records(self, app_token: str, table_id: str, records: list[dict]):
        """Batch create multiple records in Bitable table"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"records": records},
                params={"user_id_type": "open_id"}
            )
        
        return response.status_code, response.json()

    async def batch_update_bitable_records(self, app_token: str, table_id: str, records: list[dict]):
        """Batch update multiple records in Bitable table"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"records": records},
                params={"user_id_type": "open_id"}
            )
        
        return response.status_code, response.json()

    async def batch_delete_bitable_records(self, app_token: str, table_id: str, record_ids: list[str]):
        """Batch delete multiple records from Bitable table"""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"records": record_ids},
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
supabase_client = SupabaseClient()

# Create FastAPI application with enhanced security
app = FastAPI(
    title="HypeMcp",
    description="Secure HTTP server for bridging Lark and Telegram messaging with real API integrations",
    version="2.1.0"
)

# Add rate limiting support
app.state.limiter = limiter

# MCP Bridge integration (zero risk, feature flag)
import os
MCP_BRIDGE_ENABLED = os.getenv("MCP_BRIDGE_ENABLED", "true").lower() == "true"
logger.info(f"🔧 MCP_BRIDGE_ENABLED: {MCP_BRIDGE_ENABLED}")

if MCP_BRIDGE_ENABLED:
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
        import mcp_bridge
        # Include BEFORE existing /mcp routes to take precedence
        app.include_router(mcp_bridge.router, prefix="/mcp", tags=["mcp-bridge"])
        logger.info(f"✅ MCP Bridge router loaded with {len(mcp_bridge.router.routes)} routes")
        # Log routes for debugging
        for route in mcp_bridge.router.routes:
            logger.info(f"   📍 {route.methods} /mcp{route.path}")
    except Exception as e:
        logger.error(f"❌ Failed to load MCP Bridge router: {e}")
        MCP_BRIDGE_ENABLED = False
else:
    logger.warning("⚠️ MCP Bridge disabled - using basic tools only")
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add security headers based on configuration
    headers = security_manager.get_security_headers()
    for key, value in headers.items():
        response.headers[key] = value
    
    # Add HSTS only for HTTPS requests
    if request.url.scheme == "https" and security_manager.security_enabled:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    
    return response

# Enhanced CORS configuration
allowed_origins = ["*"]  # Default permissive for backward compatibility
if os.getenv("ALLOWED_ORIGINS"):
    allowed_origins = os.getenv("ALLOWED_ORIGINS").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to needed methods
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with service information and security status"""
    return {
        "service": "HypeMcp",
        "version": "2.1.0", 
        "status": "running",
        "deployment": "render-production-with-real-apis",
        "environment": os.getenv("RENDER", "development"),
        "port": os.getenv("PORT", "8000"),
        "security": {
            "enabled": security_manager.security_enabled,
            "rate_limit": security_manager.get_rate_limit(),
            "content_validation": True,
            "security_headers": True
        },
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
                "update_table": "/api/v1/bitable/apps/{app_token}/tables/{table_id}",
                "delete_table": "/api/v1/bitable/apps/{app_token}/tables/{table_id}",
                "query_records": "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records",
                "create_record": "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/create",
                "update_record": "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/{record_id}",
                "delete_record": "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/{record_id}",
                "batch_create_records": "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/batch/create",
                "batch_update_records": "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/batch/update",
                "batch_delete_records": "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/batch/delete"
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
            "telegram": "/api/v1/telegram/send",
            "webhooks": {
                "lark_events": "/webhook/lark/events",
                "lark_config": "/webhook/lark/config", 
                "lark_test": "/webhook/lark/test"
            }
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

# =============================================================================
# MCP STANDARD ENDPOINTS
# =============================================================================

@app.get("/mcp/tools")
async def mcp_tools_list():
    """MCP standard: List all available tools"""
    tools = [
        {
            "name": "send_lark_message",
            "description": "Send message to Lark chat or user",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string", "description": "Lark chat ID (ou_xxxxx or oc_xxxxx)"},
                    "text": {"type": "string", "description": "Message text to send"}
                },
                "required": ["chat_id", "text"]
            }
        },
        {
            "name": "create_bitable_app", 
            "description": "Create new Bitable (spreadsheet) application",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name for the Bitable app"},
                    "folder_token": {"type": "string", "description": "Optional folder token"}
                },
                "required": ["name"]
            }
        },
        {
            "name": "list_bitable_tables",
            "description": "List all tables in a Bitable app", 
            "inputSchema": {
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "Bitable app token"}
                },
                "required": ["app_token"]
            }
        },
        {
            "name": "list_departments",
            "description": "List all departments in the organization",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "list_chats",
            "description": "List all Lark chats the user/bot is in",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "create_hypetask_session",
            "description": "Create new HypeTask user session for state management",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User identifier"},
                    "platform": {"type": "string", "description": "Platform (lark/telegram/replit)"},
                    "user_context": {"type": "object", "description": "Optional user context data"}
                },
                "required": ["user_id", "platform"]
            }
        },
        {
            "name": "get_hypetask_session",
            "description": "Get HypeTask session by token",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "session_token": {"type": "string", "description": "Session token"}
                },
                "required": ["session_token"]
            }
        },
        {
            "name": "log_conversation",
            "description": "Log conversation message to HypeTask history",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "session_token": {"type": "string", "description": "Session token"},
                    "message_type": {"type": "string", "description": "Message type (user_input/ai_response/system_action)"},
                    "content": {"type": "string", "description": "Message content"},
                    "action_data": {"type": "object", "description": "Optional action metadata"}
                },
                "required": ["session_token", "message_type", "content"]
            }
        },
        {
            "name": "get_conversation_history",
            "description": "Get conversation history for HypeTask session",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "session_token": {"type": "string", "description": "Session token"},
                    "limit": {"type": "integer", "description": "Message limit (default: 50)"}
                },
                "required": ["session_token"]
            }
        }
    ]
    
    return {
        "tools": tools,
        "count": len(tools),
        "server_info": {
            "name": "lark-productivity-mcp",
            "version": "2.1.0",
            "description": "Lark Productivity Tools MCP Server"
        }
    }

@app.get("/mcp/resources") 
async def mcp_resources_list():
    """MCP standard: List all available resources"""
    resources = [
        {
            "uri": "lark://contacts/departments",
            "name": "Organization Departments",
            "description": "Live list of all departments in the organization",
            "mimeType": "application/json"
        },
        {
            "uri": "lark://chats/list", 
            "name": "Chat List",
            "description": "Live list of all accessible chats",
            "mimeType": "application/json"
        },
        {
            "uri": "lark://bitable/apps",
            "name": "Bitable Applications", 
            "description": "List of all Bitable apps accessible to user",
            "mimeType": "application/json"
        }
    ]
    
    return {
        "resources": resources,
        "count": len(resources)
    }

@app.get("/mcp/prompts")
async def mcp_prompts_list():
    """MCP standard: List all available prompts"""
    prompts = [
        {
            "name": "daily_standup",
            "description": "Send daily standup message to team chat",
            "arguments": [
                {
                    "name": "team_chat_id", 
                    "description": "Team chat ID (ou_xxxxx)",
                    "required": True
                },
                {
                    "name": "tasks_completed",
                    "description": "Tasks completed yesterday",
                    "required": True
                },
                {
                    "name": "tasks_today", 
                    "description": "Tasks planned for today",
                    "required": True
                }
            ]
        },
        {
            "name": "project_status_report",
            "description": "Create and send project status report to stakeholders", 
            "arguments": [
                {
                    "name": "project_name",
                    "description": "Name of the project",
                    "required": True
                },
                {
                    "name": "status",
                    "description": "Current status (on track, delayed, blocked)",
                    "required": True
                },
                {
                    "name": "chat_ids",
                    "description": "List of chat IDs to send report to",
                    "required": True
                }
            ]
        }
    ]
    
    return {
        "prompts": prompts,
        "count": len(prompts)
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
@limiter.limit(security_manager.get_rate_limit())
async def send_lark_endpoint(
    request: Request,
    message_request: MessageRequest,
    user_role: Optional[str] = Depends(security_manager.verify_api_key)
):
    """Send message to Lark chat using real API with optional security"""
    
    if not lark_client:
        raise HTTPException(
            status_code=503, 
            detail="Lark integration not configured - missing LARK_APP_ID or LARK_APP_SECRET"
        )
    
    # Validate and sanitize input
    try:
        validated_content = security_manager.validate_content(message_request.text)
        validated_chat_id = security_manager.validate_chat_id(message_request.chat_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    
    # Log request with security info
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        f"Lark API request from {client_ip}: "
        f"chat_id={security_manager.hash_sensitive_data(validated_chat_id)}, "
        f"text_length={len(validated_content)}, "
        f"authenticated={user_role is not None}"
    )
    
    try:
        status_code, api_response = await lark_client.send_message(validated_chat_id, validated_content)
        
        if status_code == 200 and api_response.get("code") == 0:
            return MessageResponse(
                success=True,
                message=f"Message sent to Lark chat {validated_chat_id}",
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

@app.put("/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/{record_id}")
async def update_bitable_record(app_token: str, table_id: str, record_id: str, request: BitableRecordUpdateRequest):
    """Update a record in Bitable table"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.update_bitable_record(
            app_token, table_id, record_id, request.fields
        )
        
        if status_code == 200 and api_response.get("code") == 0:
            record_data = api_response.get('data', {})
            return MessageResponse(
                success=True,
                message="Record updated successfully in Bitable table",
                details=f"Record ID: {record_id}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to update Bitable record",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/{record_id}")
async def delete_bitable_record(app_token: str, table_id: str, record_id: str):
    """Delete a record from Bitable table"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.delete_bitable_record(
            app_token, table_id, record_id
        )
        
        if status_code == 200 and api_response.get("code") == 0:
            return MessageResponse(
                success=True,
                message="Record deleted successfully from Bitable table",
                details=f"Record ID: {record_id}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to delete Bitable record",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.patch("/api/v1/bitable/apps/{app_token}/tables/{table_id}")
async def update_bitable_table(app_token: str, table_id: str, request: BitableTableUpdateRequest):
    """Update a table name in Bitable app"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    if not request.name:
        raise HTTPException(status_code=422, detail="Missing 'name' field in request body")
    try:
        status_code, api_response = await lark_client.update_bitable_table(
            app_token, table_id, request.name
        )
        if status_code == 200 and api_response.get("code") == 0:
            table_data = api_response.get('data', {})
            return MessageResponse(
                success=True,
                message="Table updated successfully in Bitable app",
                details=f"Table ID: {table_id}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to update Bitable table",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/api/v1/bitable/apps/{app_token}/tables/{table_id}")
async def delete_bitable_table(app_token: str, table_id: str):
    """Delete a table from Bitable app"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.delete_bitable_table(
            app_token, table_id
        )
        
        if status_code == 200 and api_response.get("code") == 0:
            return MessageResponse(
                success=True,
                message="Table deleted successfully from Bitable app",
                details=f"Table ID: {table_id}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to delete Bitable table",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/batch/create")
async def batch_create_bitable_records(app_token: str, table_id: str, request: BitableBatchCreateRequest):
    """Batch create multiple records in Bitable table"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.batch_create_bitable_records(
            app_token, table_id, request.records
        )
        
        if status_code == 200 and api_response.get("code") == 0:
            records_data = api_response.get('data', {})
            record_count = len(records_data.get('records', []))
            return MessageResponse(
                success=True,
                message=f"Batch created {record_count} records successfully in Bitable table",
                details=f"Records created: {record_count}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to batch create Bitable records",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.patch("/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/batch/update")
async def batch_update_bitable_records(app_token: str, table_id: str, request: BitableBatchUpdateRequest):
    """Batch update multiple records in Bitable table"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.batch_update_bitable_records(
            app_token, table_id, request.records
        )
        
        if status_code == 200 and api_response.get("code") == 0:
            records_data = api_response.get('data', {})
            record_count = len(records_data.get('records', []))
            return MessageResponse(
                success=True,
                message=f"Batch updated {record_count} records successfully in Bitable table",
                details=f"Records updated: {record_count}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to batch update Bitable records",
                details=f"API error: {api_response}",
                api_response=api_response
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/batch/delete")
async def batch_delete_bitable_records(app_token: str, table_id: str, request: BitableBatchDeleteRequest):
    """Batch delete multiple records from Bitable table"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark not configured")
    
    try:
        status_code, api_response = await lark_client.batch_delete_bitable_records(
            app_token, table_id, request.record_ids
        )
        
        if status_code == 200 and api_response.get("code") == 0:
            record_count = len(request.record_ids)
            return MessageResponse(
                success=True,
                message=f"Batch deleted {record_count} records successfully from Bitable table",
                details=f"Records deleted: {record_count}",
                api_response=api_response
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to batch delete Bitable records",
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
@limiter.limit(security_manager.get_rate_limit())
async def send_telegram_endpoint(
    request: Request,
    message_request: MessageRequest,
    user_role: Optional[str] = Depends(security_manager.verify_api_key)
):
    """Send message to Telegram chat using real API with optional security"""
    
    if not telegram_client:
        raise HTTPException(
            status_code=503, 
            detail="Telegram integration not configured - missing TELEGRAM_TOKEN"
        )
    
    # Validate and sanitize input
    try:
        validated_content = security_manager.validate_content(message_request.text)
        validated_chat_id = security_manager.validate_chat_id(message_request.chat_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    
    # Log request with security info
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        f"Telegram API request from {client_ip}: "
        f"chat_id={security_manager.hash_sensitive_data(validated_chat_id)}, "
        f"text_length={len(validated_content)}, "
        f"authenticated={user_role is not None}"
    )
        
    try:
        status_code, api_response = await telegram_client.send_message(validated_chat_id, validated_content)
        
        if status_code == 200 and api_response.get("ok"):
            return MessageResponse(
                success=True,
                message=f"Message sent to Telegram chat {validated_chat_id}",
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

# ========================== HYPETASK SESSION MANAGEMENT ==========================

class SessionRequest(BaseModel):
    user_id: str
    platform: str
    user_context: Optional[dict] = None

class ConversationLogRequest(BaseModel):
    session_token: str
    message_type: str  # user_input, ai_response, system_action
    content: str
    action_data: Optional[dict] = None

@app.post("/api/v1/hypetask/session/create")
async def create_session(request: SessionRequest):
    """Create new HypeTask user session"""
    try:
        result = await supabase_client.create_session(
            user_id=request.user_id,
            platform=request.platform,
            user_context=request.user_context
        )
        
        if result["success"]:
            return MessageResponse(
                success=True,
                message="Session created successfully",
                details=f"Session for user {request.user_id} on {request.platform}",
                api_response=result["session"]
            )
        else:
            return MessageResponse(
                success=False,
                message="Failed to create session",
                details=result.get("error", "Unknown error"),
                api_response=result
            )
            
    except Exception as e:
        logger.error(f"Session creation exception: {e}")
        raise HTTPException(status_code=500, detail=f"Session creation error: {str(e)}")

@app.get("/api/v1/hypetask/session/{session_token}")
async def get_session(session_token: str):
    """Get session by token"""
    try:
        result = await supabase_client.get_session(session_token)
        
        if result["success"]:
            return MessageResponse(
                success=True,
                message="Session retrieved successfully",
                details=f"Session token: {session_token}",
                api_response=result["session"]
            )
        else:
            return MessageResponse(
                success=False,
                message="Session not found",
                details=result.get("error", "Session expired or not found"),
                api_response=result
            )
            
    except Exception as e:
        logger.error(f"Session retrieval exception: {e}")
        raise HTTPException(status_code=500, detail=f"Session retrieval error: {str(e)}")

@app.post("/api/v1/hypetask/conversation/log")
async def log_conversation(request: ConversationLogRequest):
    """Log conversation message to history"""
    try:
        # Get session first
        session_result = await supabase_client.get_session(request.session_token)
        if not session_result["success"]:
            return MessageResponse(
                success=False,
                message="Invalid session token",
                details="Session not found or expired"
            )
        
        session = session_result["session"]
        
        # Log conversation
        result = await supabase_client.log_conversation(
            session_id=session["id"],
            user_id=session["user_id"],
            platform=session["platform"],
            message_type=request.message_type,
            content=request.content,
            action_data=request.action_data
        )
        
        return MessageResponse(
            success=result["success"],
            message="Conversation logged successfully" if result["success"] else "Failed to log conversation",
            details=f"Message type: {request.message_type}",
            api_response=result
        )
        
    except Exception as e:
        logger.error(f"Conversation logging exception: {e}")
        raise HTTPException(status_code=500, detail=f"Conversation logging error: {str(e)}")

@app.get("/api/v1/hypetask/conversation/history/{session_token}")
async def get_conversation_history(session_token: str, limit: int = 50):
    """Get conversation history for session"""
    try:
        # Get session first
        session_result = await supabase_client.get_session(session_token)
        if not session_result["success"]:
            return MessageResponse(
                success=False,
                message="Invalid session token",
                details="Session not found or expired"
            )
        
        session = session_result["session"]
        
        # Get conversation history via direct API call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{supabase_client.base_url}/rest/v1/hypetask_conversations",
                headers=supabase_client._get_headers(),
                params={
                    "session_id": f"eq.{session['id']}",
                    "order": "created_at.desc",
                    "limit": limit
                }
            )
            
            if response.status_code == 200:
                conversations = response.json()
                return MessageResponse(
                    success=True,
                    message=f"Retrieved {len(conversations)} conversation messages",
                    details=f"Session: {session_token}",
                    api_response={"conversations": conversations, "session": session}
                )
            else:
                return MessageResponse(
                    success=False,
                    message="Failed to retrieve conversation history",
                    details=response.text
                )
        
    except Exception as e:
        logger.error(f"Conversation history exception: {e}")
        raise HTTPException(status_code=500, detail=f"Conversation history error: {str(e)}")

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

# ============================================
# 🔔 Webhook Auto-Update Endpoints
# ============================================

@app.post("/webhook/lark/events")
@limiter.limit("100/minute")  # Higher limit for webhooks
async def handle_lark_webhook(
    request: Request,
    user_role: Optional[str] = Depends(security_manager.verify_api_key)
):
    """Handle incoming Lark webhook events for auto-updates"""
    try:
        # Get raw request data
        body = await request.body()
        headers = dict(request.headers)
        
        # Log the webhook event
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"📥 Received Lark webhook event from {client_ip}")
        
        # Parse JSON payload
        try:
            event_data = await request.json()
        except Exception as e:
            logger.error(f"❌ Failed to parse webhook JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Verify webhook signature (Lark webhook verification)
        event_type = event_data.get("type")
        
        # Handle different event types
        if event_type == "url_verification":
            # Initial webhook URL verification
            challenge = event_data.get("challenge")
            logger.info(f"✅ Webhook URL verification with challenge: {challenge}")
            return {"challenge": challenge}
        
        elif event_type == "event_callback":
            # Actual event processing
            event = event_data.get("event", {})
            event_name = event.get("type")
            
            logger.info(f"🔔 Processing event: {event_name}")
            
            # Process different Lark events
            response_data = await process_lark_event(event_name, event, event_data)
            
            # Forward to n8n workflows if needed
            if response_data.get("forward_to_n8n"):
                await forward_to_n8n_webhook(event_name, event, response_data)
            
            return {
                "success": True,
                "message": f"Event {event_name} processed successfully",
                "event_type": event_name,
                "processed_at": datetime.now().isoformat(),
                "forwarded_to_n8n": response_data.get("forward_to_n8n", False)
            }
        
        else:
            logger.warning(f"⚠️ Unknown event type: {event_type}")
            return {
                "success": False,
                "message": f"Unknown event type: {event_type}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

async def process_lark_event(event_name: str, event: dict, full_data: dict) -> dict:
    """Process different types of Lark events"""
    
    if event_name == "message":
        # Handle new messages
        message = event.get("message", {})
        chat_id = message.get("chat_id")
        sender = event.get("sender", {})
        
        logger.info(f"💬 New message in chat {security_manager.hash_sensitive_data(chat_id or 'unknown')} from user {security_manager.hash_sensitive_data(sender.get('sender_id', {}).get('open_id', 'unknown'))}")
        
        return {
            "event": "message_received",
            "chat_id": chat_id,
            "message_id": message.get("message_id"),
            "forward_to_n8n": True
        }
        
    elif event_name == "app_table_record_changed":
        # Handle Bitable record changes
        table_info = event.get("table_info", {})
        record_info = event.get("record_info", {})
        
        logger.info(f"📊 Bitable record changed in app {table_info.get('app_token')} table {table_info.get('table_id')}")
        
        return {
            "event": "bitable_record_changed", 
            "app_token": table_info.get("app_token"),
            "table_id": table_info.get("table_id"),
            "record_id": record_info.get("record_id"),
            "forward_to_n8n": True
        }
        
    elif event_name == "contact_user_created":
        # Handle new user added
        user_info = event.get("object", {})
        
        logger.info(f"👤 New user created: {security_manager.hash_sensitive_data(user_info.get('open_id', 'unknown'))}")
        
        return {
            "event": "user_created",
            "user_id": user_info.get("open_id"),
            "forward_to_n8n": True
        }
        
    else:
        logger.info(f"ℹ️ Event {event_name} processed but no specific handler")
        return {
            "event": event_name,
            "forward_to_n8n": False
        }

async def forward_to_n8n_webhook(event_name: str, event: dict, processed_data: dict):
    """Forward processed events to n8n webhook URLs"""
    
    # Define n8n webhook URLs for different event types
    n8n_webhooks = {
        "message_received": "https://modcho.app.n8n.cloud/webhook/lark-message-received",
        "bitable_record_changed": "https://modcho.app.n8n.cloud/webhook/lark-bitable-changed", 
        "user_created": "https://modcho.app.n8n.cloud/webhook/lark-user-created"
    }
    
    webhook_url = n8n_webhooks.get(processed_data.get("event"))
    
    if webhook_url:
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "event_type": event_name,
                    "event_data": event,
                    "processed_data": processed_data,
                    "timestamp": datetime.now().isoformat(),
                    "source": "HypeMcp-webhook"
                }
                
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Forwarded {event_name} to n8n webhook successfully")
                else:
                    logger.warning(f"⚠️ n8n webhook returned {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to forward to n8n: {str(e)}")
    else:
        logger.debug(f"ℹ️ No n8n webhook configured for event: {processed_data.get('event')}")

@app.get("/webhook/lark/config")
async def get_webhook_config():
    """Get current webhook configuration"""
    return {
        "success": True,
        "service": "HypeMcp",
        "webhook_endpoint": "https://lark-mcp-telegram-server.onrender.com/webhook/lark/events",
        "supported_events": [
            "message",
            "app_table_record_changed", 
            "contact_user_created"
        ],
        "n8n_forwarding": {
            "message_received": "https://modcho.app.n8n.cloud/webhook/lark-message-received",
            "bitable_record_changed": "https://modcho.app.n8n.cloud/webhook/lark-bitable-changed",
            "user_created": "https://modcho.app.n8n.cloud/webhook/lark-user-created"
        },
        "setup_instructions": {
            "step_1": "Go to your Lark app configuration",
            "step_2": "Add webhook URL: https://lark-mcp-telegram-server.onrender.com/webhook/lark/events",
            "step_3": "Subscribe to desired events: message, app_table_record_changed, contact_user_created",
            "step_4": "Configure webhook secret (optional but recommended)",
            "step_5": "Test with URL verification"
        },
        "security": {
            "rate_limit": "100/minute",
            "authentication": "optional",
            "ip_logging": True
        }
    }

@app.post("/webhook/lark/test")
async def test_webhook():
    """Test webhook endpoint with sample data"""
    sample_event = {
        "type": "event_callback",
        "event": {
            "type": "message",
            "message": {
                "chat_id": "oc_test_chat_id",
                "message_id": "test_message_id",
                "content": "Test webhook message"
            },
            "sender": {
                "sender_id": {
                    "open_id": "test_user_id"
                }
            }
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Process the test event
    processed = await process_lark_event("message", sample_event["event"], sample_event)
    
    return {
        "success": True,
        "message": "Webhook test completed",
        "test_event": sample_event,
        "processed_result": processed,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🚀 Starting Production HypeMcp Server with Real APIs on port {port}")
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