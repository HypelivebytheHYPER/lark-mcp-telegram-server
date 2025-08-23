# FastMCP Lark-Telegram Server

A FastMCP server that bridges Lark (Feishu) and Telegram messaging platforms.

## Features

- Send messages to Lark and Telegram
- Authentication and rate limiting
- Comprehensive error handling
- Ready for Render deployment

## Setup

1. Copy .env.example to .env and fill in your credentials
2. Run: uv run python server_enhanced.py
3. Test: uv run pytest test_server.py

## Deploy to Render

Connect this repository to Render and set environment variables.
