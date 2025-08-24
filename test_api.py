#!/usr/bin/env python3
"""
ตัวอย่างการใช้งาน Lark-Telegram Bridge API
"""
import requests
import json

BASE_URL = "https://lark-mcp-telegram-server.onrender.com"

def test_health():
    """ตรวจสอบสถานะเซิร์ฟเวอร์"""
    response = requests.get(f"{BASE_URL}/health")
    return response.json()

def send_lark_message(chat_id, message):
    """ส่งข้อความไป Lark"""
    url = f"{BASE_URL}/api/v1/lark/send"
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(url, json=payload)
    return response.json()

def send_telegram_message(chat_id, message):
    """ส่งข้อความไป Telegram"""
    url = f"{BASE_URL}/api/v1/telegram/send"
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(url, json=payload)
    return response.json()

if __name__ == "__main__":
    print("🧪 ทดสอบ Lark-Telegram Bridge API")
    print("=" * 40)
    
    # ทดสอบสถานะ
    health = test_health()
    print(f"📊 Server Status: {health['status']}")
    print()
    
    # ตัวอย่างการส่งข้อความ (ใส่ chat_id จริงของคุณ)
    # result = send_lark_message("YOUR_LARK_CHAT_ID", "Hello from Python! 🐍")
    # print("📤 Lark Result:", json.dumps(result, indent=2, ensure_ascii=False))
    
    print("💡 แก้ไข chat_id ในไฟล์นี้เพื่อทดสอบส่งข้อความจริง")
