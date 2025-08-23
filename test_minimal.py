#!/usr/bin/env python3
"""
Minimal FastAPI test to isolate deployment issues
"""
import os
import logging
import sys

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info("🧪 Starting minimal FastAPI test...")

try:
    from fastapi import FastAPI
    logger.info("✅ FastAPI import successful")
    
    import uvicorn
    logger.info("✅ Uvicorn import successful")
    
    # Test basic FastAPI app
    app = FastAPI(title="Minimal Test")
    
    @app.get("/")
    async def root():
        return {"status": "minimal test running", "port": os.getenv("PORT", "8000")}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    logger.info("✅ FastAPI app created successfully")
    
    # Test server startup
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"🚀 Starting server on port {port}")
    
    if __name__ == "__main__":
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Unexpected error: {e}")
    sys.exit(1)