#!/usr/bin/env python3
"""
Set OpenAI API key for memory curation system
This script should be run before starting the server
"""

import os

# The OpenAI API key for memory curation - SET THIS BEFORE RUNNING
OPENAI_API_KEY = "your-openai-api-key-here"

def set_environment():
    """Set the OpenAI API key as environment variable"""
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    print("✅ OpenAI API key set for memory curation")
    print(f"Model: gpt-4.1-nano-2025-04-14")
    print("Memory curation system ready!")

def create_env_file():
    """Create .env file with the API key"""
    env_content = f"""# Engram Configuration
ENGRAM_DEBUG=false
ENGRAM_REDIS_HOST=localhost
ENGRAM_REDIS_PORT=6379

# OpenAI for memory curation
OPENAI_API_KEY={OPENAI_API_KEY}
ENGRAM_OPENAI_CURATION_MODEL=gpt-4.1-nano-2025-04-14
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Created .env file with OpenAI API key")
    print("🔒 WARNING: .env file contains sensitive API key - do not commit to Git!")

if __name__ == "__main__":
    print("🔑 Setting up OpenAI API key for Engram memory curation")
    print("=" * 60)
    
    # Set environment variable for current session
    set_environment()
    
    # Create .env file for persistent configuration
    create_env_file()
    
    print("\n🚀 Ready to start Engram with AI-powered memory curation!")
    print("Run: python main.py")