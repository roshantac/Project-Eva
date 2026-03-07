#!/usr/bin/env python3
"""
Eva AI - Run Script
Simple script to start the Eva AI server
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main entry point"""
    port = int(os.getenv("PORT", 3001))
    host = os.getenv("HOST", "0.0.0.0")
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("❌ .env file not found. Please copy .env.example to .env and configure it.")
        sys.exit(1)
    
    print("🚀 Starting Eva AI Server...")
    print(f"   Environment: {environment}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   LLM Provider: {os.getenv('LLM_PROVIDER', 'ollama')}")
    print(f"   Audio Provider: {os.getenv('AUDIO_PROVIDER', 'local')}")
    print("")
    
    # Import here to ensure environment is loaded
    from app.main import socket_app
    
    # Run server
    uvicorn.run(
        socket_app,
        host=host,
        port=port,
        log_level="info" if environment == "production" else "debug",
        access_log=True,
        reload=environment == "development"
    )


if __name__ == "__main__":
    main()
