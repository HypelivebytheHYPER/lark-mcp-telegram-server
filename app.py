#!/usr/bin/env python3
"""
Production FastMCP server for Render deployment
"""
from server_enhanced import mcp
import os
import logging

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting FastMCP server on port {port}")
    mcp.run()