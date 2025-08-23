#!/usr/bin/env python3
"""
Production FastAPI server for Lark-Telegram MCP bridge
Optimized for Render deployment with proper health checks and error handling
"""
import os
import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastmcp import FastMCP
from lark_oapi.api.im.v1 import *
import lark_oapi as lark
from telegram import Bot
from dotenv import load_dotenv
import uvicorn

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global state for clients
lark_client = None
telegram_bot = None
mcp_server = None

# Request/Response models
class MessageRequest(BaseModel):
    chat_id: str
    text: str
    api_key: Optional[str] = None

class MessageResponse(BaseModel):
    success: bool
    message: str
    details: Optional[str] = None

# Initialize clients with comprehensive error handling
def initialize_clients():
    """Initialize Lark and Telegram clients with proper error handling"""
    global lark_client, telegram_bot
    
    # Lark client initialization
    lark_app_id = os.getenv("LARK_APP_ID")
    lark_app_secret = os.getenv("LARK_APP_SECRET")
    
    if lark_app_id and lark_app_secret:
        try:
            lark_client = lark.Client.builder() \
                .app_id(lark_app_id) \
                .app_secret(lark_app_secret) \
                .log_level(lark.LogLevel.INFO) \
                .build()
            logger.info("✅ Lark client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Lark client: {e}")
            lark_client = None
    else:
        logger.warning("⚠️  Lark credentials not found - Lark messaging disabled")
    
    # Telegram client initialization  
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    
    if telegram_token:
        try:
            telegram_bot = Bot(telegram_token)
            logger.info("✅ Telegram bot initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram bot: {e}")
            telegram_bot = None
    else:
        logger.warning("⚠️  Telegram token not found - Telegram messaging disabled")

def initialize_mcp_server():
    """Initialize FastMCP server with tools"""
    global mcp_server
    
    try:
        mcp_server = FastMCP("Lark Telegram Bridge")
        
        @mcp_server.tool
        def send_lark_message(chat_id: str, text: str) -> str:
            """Send text message to Lark chat"""
            if not lark_client:
                return "❌ Lark client not available"
            
            try:
                request = CreateMessageRequest.builder() \
                    .receive_id_type("chat_id") \
                    .request_body(CreateMessageRequestBody.builder()
                        .receive_id(chat_id)
                        .msg_type("text")
                        .content(f'{{"text":"{text}"}}')
                        .build()) \
                    .build()
                
                response = lark_client.im.v1.message.create(request)
                
                if response.success():
                    return f"✅ Message sent to Lark chat {chat_id}"
                else:
                    return f"❌ Lark API error: {response.msg}"
                    
            except Exception as e:
                return f"❌ Error sending to Lark: {str(e)}"
        
        @mcp_server.tool
        async def send_telegram_message(chat_id: str, text: str) -> str:
            """Send text message to Telegram chat"""
            if not telegram_bot:
                return "❌ Telegram bot not available"
            
            try:
                await telegram_bot.send_message(chat_id=chat_id, text=text)
                return f"✅ Message sent to Telegram chat {chat_id}"
            except Exception as e:
                return f"❌ Error sending to Telegram: {str(e)}"
        
        logger.info("✅ MCP server initialized with tools")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize MCP server: {e}")
        return False

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    logger.info("🚀 Starting Lark-Telegram MCP Bridge...")
    
    # Startup
    initialize_clients()
    mcp_initialized = initialize_mcp_server()
    
    if not mcp_initialized:
        logger.error("❌ MCP server initialization failed")
    
    # Log startup status
    startup_status = {
        "lark_client": "✅ Ready" if lark_client else "❌ Unavailable",
        "telegram_bot": "✅ Ready" if telegram_bot else "❌ Unavailable", 
        "mcp_server": "✅ Ready" if mcp_initialized else "❌ Failed"
    }
    
    logger.info("📋 Service Status:")
    for service, status in startup_status.items():
        logger.info(f"  {service}: {status}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Lark-Telegram MCP Bridge...")

# Create FastAPI application
app = FastAPI(
    title="Lark-Telegram MCP Bridge",
    description="FastMCP server bridging Lark and Telegram messaging platforms",
    version="1.0.0",
    lifespan=lifespan
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
        "service": "Lark-Telegram MCP Bridge",
        "version": "1.0.0", 
        "status": "running",
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
        "timestamp": "2025-08-23T18:00:00Z"
    }

@app.get("/ready") 
async def readiness_check():
    """Readiness check with detailed service status"""
    services_ready = {
        "lark_client": lark_client is not None,
        "telegram_bot": telegram_bot is not None,
        "mcp_server": mcp_server is not None
    }
    
    all_ready = all(services_ready.values())
    status_code = 200 if all_ready else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_ready,
            "services": services_ready,
            "timestamp": "2025-08-23T18:00:00Z"
        }
    )

@app.post("/api/v1/lark/send")
async def send_lark_endpoint(request: MessageRequest):
    """Send message to Lark chat"""
    if not lark_client:
        raise HTTPException(status_code=503, detail="Lark client not available")
    
    try:
        # Direct Lark API call without MCP dependency
        text = request.text.replace('"', '\\"')  # Escape quotes
        
        req = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(CreateMessageRequestBody.builder()
                .receive_id(request.chat_id)
                .msg_type("text")
                .content(f'{{"text":"{text}"}}')
                .build()) \
            .build()
        
        response = lark_client.im.v1.message.create(req)
        
        if response.success():
            logger.info(f"Message sent to Lark chat {request.chat_id}")
            return MessageResponse(
                success=True,
                message=f"Message sent to Lark chat {request.chat_id}",
                details="Lark API success"
            )
        else:
            logger.error(f"Lark API error: {response.msg}")
            raise HTTPException(status_code=400, detail=f"Lark API error: {response.msg}")
        
    except Exception as e:
        logger.error(f"Error in Lark endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/telegram/send") 
async def send_telegram_endpoint(request: MessageRequest):
    """Send message to Telegram chat"""
    if not telegram_bot:
        raise HTTPException(status_code=503, detail="Telegram bot not available")
    
    try:
        # Direct Telegram API call
        await telegram_bot.send_message(chat_id=request.chat_id, text=request.text)
        
        logger.info(f"Message sent to Telegram chat {request.chat_id}")
        return MessageResponse(
            success=True,
            message=f"Message sent to Telegram chat {request.chat_id}",
            details="Telegram API success"
        )
        
    except Exception as e:
        logger.error(f"Error in Telegram endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": str(request.url)}
    )

# Graceful shutdown handler
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🚀 Starting FastAPI server on port {port}")
    logger.info(f"📊 Environment: {os.getenv('RENDER', 'development')}")
    
    # Production-optimized uvicorn configuration
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,  # Single worker for Render starter plan
        log_level="info",
        access_log=True,
        server_header=False,  # Security: hide server header
        date_header=False     # Performance: disable date header
    )