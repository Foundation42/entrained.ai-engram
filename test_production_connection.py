#!/usr/bin/env python3
"""
Test connection to production Engram server
"""
import httpx
import asyncio
import sys

# Production server details
PROD_SERVER = "engram-fi-1.entrained.ai"
PROD_PORT = 8443


async def test_production_api():
    """Test connection to production API"""
    print(f"🔍 Testing connection to {PROD_SERVER}:{PROD_PORT}...\n")
    
    async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
        try:
            # Test health endpoint
            print("1. Testing /health endpoint...")
            response = await client.get(f"http://{PROD_SERVER}:{PROD_PORT}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Health: {data['status']}")
                print(f"   ✅ Redis: {data['redis']}")
                print(f"   ✅ Vector Index: {data['vector_index']}\n")
            else:
                print(f"   ❌ Error: {response.status_code}\n")
                return False
            
            # Test root endpoint
            print("2. Testing / endpoint...")
            response = await client.get(f"http://{PROD_SERVER}:{PROD_PORT}/")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Name: {data['name']}")
                print(f"   ✅ Version: {data['version']}")
                print(f"   ✅ Features: {', '.join(data['features'][:3])}...\n")
            else:
                print(f"   ❌ Error: {response.status_code}\n")
                return False
            
            print("✨ Production server is accessible and healthy!")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False


if __name__ == "__main__":
    result = asyncio.run(test_production_api())
    sys.exit(0 if result else 1)
