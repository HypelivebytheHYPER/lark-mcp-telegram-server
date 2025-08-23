#!/usr/bin/env python3
"""
Enhanced FastMCP server with authentication, logging, and robust error handling
"""
from fastmcp import FastMCP
from lark_oapi.api.im.v1 import *
import lark_oapi as lark
from telegram import Bot
import os
import asyncio
import logging
import hashlib
import time
from typing import Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Lark Telegram Tools Enhanced")

# Configuration
API_KEY = os.getenv("MCP_API_KEY")  # Optional API key for authentication
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

# Rate limiting storage (in production, use Redis or similar)
rate_limit_storage = {}

def authenticate_request(api_key: Optional[str] = None) -> bool:
    """Simple API key authentication"""
    if not API_KEY:
        return True  # No auth required if API_KEY not set
    return api_key == API_KEY

def check_rate_limit(identifier: str) -> bool:
    """Check if request is within rate limits"""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    
    # Clean old entries
    if identifier in rate_limit_storage:
        rate_limit_storage[identifier] = [
            req_time for req_time in rate_limit_storage[identifier] 
            if req_time > window_start
        ]
    else:
        rate_limit_storage[identifier] = []
    
    # Check limit
    if len(rate_limit_storage[identifier]) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    rate_limit_storage[identifier].append(now)
    return True

# Initialize clients with error handling
try:
    lark_client = lark.Client.builder() \
        .app_id(os.getenv("LARK_APP_ID")) \
        .app_secret(os.getenv("LARK_APP_SECRET")) \
        .log_level(lark.LogLevel.INFO) \
        .build()
    logger.info("Lark client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Lark client: {e}")
    lark_client = None

try:
    telegram_bot = Bot(os.getenv("TELEGRAM_TOKEN"))
    logger.info("Telegram bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Telegram bot: {e}")
    telegram_bot = None

@mcp.tool
def send_lark(chat_id: str, text: str, api_key: Optional[str] = None) -> str:
    """Send text to a Lark chat with authentication and error handling."""
    
    # Authentication
    if not authenticate_request(api_key):
        logger.warning(f"Unauthorized Lark message attempt for chat {chat_id}")
        return "❌ Authentication failed: Invalid API key"
    
    # Rate limiting
    rate_key = f"lark_{hashlib.md5(chat_id.encode()).hexdigest()}"
    if not check_rate_limit(rate_key):
        logger.warning(f"Rate limit exceeded for Lark chat {chat_id}")
        return "❌ Rate limit exceeded: Please try again later"
    
    # Validate inputs
    if not chat_id or not chat_id.strip():
        return "❌ Error: chat_id cannot be empty"
    
    if not text or not text.strip():
        return "❌ Error: text cannot be empty"
    
    if len(text) > 4000:  # Lark message limit
        return "❌ Error: Message too long (max 4000 characters)"
    
    # Check if client is available
    if lark_client is None:
        logger.error("Lark client not available")
        return "❌ Error: Lark client not configured properly"
    
    try:
        # Sanitize text (basic)
        text = text.replace('"', '\\"')  # Escape quotes for JSON
        
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
            logger.info(f"Message sent to Lark chat {chat_id}: {text[:50]}...")
            return f"✅ Message sent to Lark chat {chat_id}: {text}"
        else:
            logger.error(f"Lark API error for chat {chat_id}: {response.msg}")
            return f"❌ Lark API error: {response.msg}"
            
    except Exception as e:
        logger.error(f"Exception sending to Lark chat {chat_id}: {str(e)}")
        return f"❌ Error sending to Lark: {str(e)}"

@mcp.tool
async def send_telegram(chat_id: str, text: str, api_key: Optional[str] = None) -> str:
    """Send text to a Telegram chat with authentication and error handling."""
    
    # Authentication
    if not authenticate_request(api_key):
        logger.warning(f"Unauthorized Telegram message attempt for chat {chat_id}")
        return "❌ Authentication failed: Invalid API key"
    
    # Rate limiting
    rate_key = f"telegram_{hashlib.md5(chat_id.encode()).hexdigest()}"
    if not check_rate_limit(rate_key):
        logger.warning(f"Rate limit exceeded for Telegram chat {chat_id}")
        return "❌ Rate limit exceeded: Please try again later"
    
    # Validate inputs
    if not chat_id or not chat_id.strip():
        return "❌ Error: chat_id cannot be empty"
    
    if not text or not text.strip():
        return "❌ Error: text cannot be empty"
    
    if len(text) > 4096:  # Telegram message limit
        return "❌ Error: Message too long (max 4096 characters)"
    
    # Check if client is available
    if telegram_bot is None:
        logger.error("Telegram bot not available")
        return "❌ Error: Telegram bot not configured properly"
    
    try:
        await telegram_bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"Message sent to Telegram chat {chat_id}: {text[:50]}...")
        return f"✅ Message sent to Telegram chat {chat_id}: {text}"
        
    except Exception as e:
        logger.error(f"Exception sending to Telegram chat {chat_id}: {str(e)}")
        return f"❌ Error sending to Telegram: {str(e)}"

@mcp.tool
def health_check(api_key: Optional[str] = None) -> str:
    """Health check endpoint with system status."""
    
    # Authentication for detailed health info
    if not authenticate_request(api_key):
        return "❌ Authentication required for detailed health check"
    
    status = {
        "server": "✅ FastMCP Server Running",
        "lark_client": "✅ Connected" if lark_client else "❌ Not available",
        "telegram_client": "✅ Connected" if telegram_bot else "❌ Not available",
        "authentication": "✅ Enabled" if API_KEY else "⚠️ Disabled",
        "rate_limiting": f"✅ {RATE_LIMIT_REQUESTS} requests/{RATE_LIMIT_WINDOW}s"
    }
    
    logger.info("Health check requested")
    return f"🏥 Health Status:\n" + "\n".join([f"{k}: {v}" for k, v in status.items()])

@mcp.tool
def get_server_info() -> str:
    """Get server information and capabilities."""
    info = {
        "name": "Lark Telegram FastMCP Server",
        "version": "1.0.0",
        "capabilities": ["lark_messaging", "telegram_messaging", "rate_limiting", "authentication"],
        "tools": ["send_lark", "send_telegram", "health_check", "get_server_info"],
        "authentication": "API Key" if API_KEY else "None",
        "rate_limit": f"{RATE_LIMIT_REQUESTS}/{RATE_LIMIT_WINDOW}s"
    }
    
    return f"📋 Server Info:\n" + "\n".join([f"{k}: {v}" for k, v in info.items()])

if __name__ == "__main__":
    logger.info("Starting Enhanced FastMCP server")
    logger.info(f"Authentication: {'Enabled' if API_KEY else 'Disabled'}")
    logger.info(f"Rate limiting: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds")
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise