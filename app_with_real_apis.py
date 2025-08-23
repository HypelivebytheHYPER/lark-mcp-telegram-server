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
        self.base_url = "https://open.feishu.cn/open-apis"
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
            "lark": "/api/v1/lark/send",
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