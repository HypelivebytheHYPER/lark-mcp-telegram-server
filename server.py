from fastmcp import FastMCP
from lark_oapi.api.im.v1 import *
import lark_oapi as lark
from telegram import Bot
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Lark Telegram Tools")

# Lark client
lark_client = lark.Client.builder() \
    .app_id(os.getenv("LARK_APP_ID")) \
    .app_secret(os.getenv("LARK_APP_SECRET")) \
    .log_level(lark.LogLevel.INFO) \
    .build()

# Telegram
telegram_bot = Bot(os.getenv("TELEGRAM_TOKEN"))

@mcp.tool
def send_lark(chat_id: str, text: str) -> str:
    """Send text to a Lark chat."""
    try:
        request = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(CreateMessageRequestBody.builder()
                .receive_id(chat_id)
                .msg_type("text")
                .content("{\"text\":\"" + text + "\"}")
                .build()) \
            .build()
        
        response = lark_client.im.v1.message.create(request)
        
        if response.success():
            return f"Message sent to Lark chat {chat_id}: {text}"
        else:
            return f"Error sending to Lark: {response.msg}"
    except Exception as e:
        return f"Error sending to Lark: {str(e)}"

@mcp.tool
async def send_telegram(chat_id: str, text: str) -> str:
    """Send text to a Telegram chat."""
    try:
        await telegram_bot.send_message(chat_id=chat_id, text=text)
        return f"Message sent to Telegram chat {chat_id}: {text}"
    except Exception as e:
        return f"Error sending to Telegram: {str(e)}"

if __name__ == "__main__":
    mcp.run()