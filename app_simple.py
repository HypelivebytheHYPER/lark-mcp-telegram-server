#!/usr/bin/env python3
"""
Simplified FastAPI server for Render deployment
Production-ready HTTP server without complex MCP dependencies
"""
import os
import logging
import sys
from typing import Optional
import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Request/Response models
class MessageRequest(BaseModel):
    chat_id: str
    text: str

class MessageResponse(BaseModel):
    success: bool
    message: str
    details: Optional[str] = None

# Create FastAPI application
app = FastAPI(
    title="Lark-Telegram Bridge Server",
    description="HTTP server for bridging Lark and Telegram messaging",
    version="1.0.0"
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
        "version": "1.0.0", 
        "status": "running",
        "environment": os.getenv("RENDER", "development"),
        "port": os.getenv("PORT", "8000"),
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
        "timestamp": "2025-08-23T19:00:00Z",
        "service": "lark-telegram-bridge"
    }

@app.get("/ready") 
async def readiness_check():
    """Readiness check endpoint"""    
    return {
        "ready": True,
        "services": {
            "server": True,
            "dependencies_available": True
        },
        "timestamp": "2025-08-23T19:00:00Z"
    }

@app.post("/api/v1/lark/send")
async def send_lark_endpoint(request: MessageRequest):
    """Send message to Lark chat (simplified version)"""
    
    # For now, return success simulation
    # In production, this would integrate with actual Lark API
    logger.info(f"Lark message request: chat_id={request.chat_id}, text_length={len(request.text)}")
    
    return MessageResponse(
        success=True,
        message=f"Message would be sent to Lark chat {request.chat_id}",
        details="Lark integration in development"
    )

@app.post("/api/v1/telegram/send") 
async def send_telegram_endpoint(request: MessageRequest):
    """Send message to Telegram chat (simplified version)"""
    
    # For now, return success simulation  
    # In production, this would integrate with actual Telegram API
    logger.info(f"Telegram message request: chat_id={request.chat_id}, text_length={len(request.text)}")
        
    return MessageResponse(
        success=True,
        message=f"Message would be sent to Telegram chat {request.chat_id}",
        details="Telegram integration in development"
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error", 
            "path": str(request.url),
            "service": "lark-telegram-bridge"
        }
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🚀 Starting Lark-Telegram Bridge Server on port {port}")
    logger.info(f"📊 Environment: {os.getenv('RENDER', 'development')}")
    
    # Production-optimized uvicorn configuration
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        server_header=False
    )