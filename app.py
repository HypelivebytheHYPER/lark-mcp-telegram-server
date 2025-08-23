#!/usr/bin/env python3
"""
HTTP-compatible FastMCP server for Render deployment
"""
from fastmcp import FastMCP
from lark_oapi.api.im.v1 import *
import lark_oapi as lark
from telegram import Bot
import os
import asyncio
import logging
from typing import Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Lark Telegram Tools HTTP")

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
def send_lark(chat_id: str, text: str) -> str:
    """Send text to a Lark chat."""
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
async def send_telegram(chat_id: str, text: str) -> str:
    """Send text to a Telegram chat."""
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
def health_check() -> str:
    """Health check endpoint with system status."""
    status = {
        "server": "✅ FastMCP HTTP Server Running",
        "lark_client": "✅ Connected" if lark_client else "❌ Not available",
        "telegram_client": "✅ Connected" if telegram_bot else "❌ Not available",
        "deployment": "✅ Render HTTP deployment"
    }
    
    logger.info("Health check requested")
    return f"🏥 Health Status:\n" + "\n".join([f"{k}: {v}" for k, v in status.items()])

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting FastMCP HTTP server on port {port}")
    
    try:
        # Run with HTTP transport for Render deployment
        mcp.run(
            transport="http",
            host="0.0.0.0",  # Bind to all interfaces for Render
            port=port,
            path="/mcp"
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise