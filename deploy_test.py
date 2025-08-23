#!/usr/bin/env python3
"""
Simple deployment test to verify Python environment
"""
import sys
import os

print("=== Deployment Test ===")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"PORT environment: {os.getenv('PORT', 'not set')}")
print(f"RENDER environment: {os.getenv('RENDER', 'not set')}")

# List files in current directory
print("\nFiles in current directory:")
for file in os.listdir('.'):
    print(f"  {file}")

# Test FastAPI import
try:
    from fastapi import FastAPI
    print("\n✅ FastAPI import successful")
except ImportError as e:
    print(f"\n❌ FastAPI import failed: {e}")

# Test uvicorn import
try:
    import uvicorn
    print("✅ Uvicorn import successful")
except ImportError as e:
    print(f"❌ Uvicorn import failed: {e}")

print("\n=== Test Complete ===")