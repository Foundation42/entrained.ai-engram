#!/usr/bin/env python3
"""
Test the serialization fix for various data types
"""

import httpx
import asyncio
from datetime import datetime
import random


async def test_serialization_fix():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Serialization Fix")
    print("=" * 50)
    
    # Create test vector
    test_vector = [random.gauss(0, 1) for _ in range(768)]
    norm = sum(x**2 for x in test_vector) ** 0.5
    test_vector = [x/norm for x in test_vector]
    
    # Test cases with various problematic data types
    test_cases = [
        {
            "name": "None values",
            "memory": {
                "content": {
                    "text": "Test with None values",
                    "media": None,  # None value
                    "extra": None
                },
                "primary_vector": test_vector,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "agent_id": "test-agent",
                    "memory_type": None,  # None value
                    "domain": None,
                    "confidence": None
                },
                "tags": None  # None value
            }
        },
        {
            "name": "Boolean values",
            "memory": {
                "content": {
                    "text": "Test with boolean values",
                    "is_important": True,  # Boolean
                    "verified": False
                },
                "primary_vector": test_vector,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "agent_id": "test-agent",
                    "memory_type": "test",
                    "active": True,  # Boolean
                    "published": False
                },
                "tags": ["test", "boolean"]
            }
        },
        {
            "name": "Nested objects",
            "memory": {
                "content": {
                    "text": "Test with nested objects",
                    "media": [
                        {"type": "image", "url": "http://example.com/img.jpg"},
                        {"type": "video", "data": {"source": "youtube", "id": "123"}}
                    ]
                },
                "primary_vector": test_vector,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "agent_id": "test-agent",
                    "memory_type": "complex",
                    "extra_data": {
                        "nested": {
                            "deeply": {
                                "value": 42,
                                "flag": True
                            }
                        }
                    }
                },
                "tags": ["nested", "complex"]
            }
        },
        {
            "name": "Mixed problematic types",
            "memory": {
                "content": {
                    "text": "Mixed types test",
                    "number": 3.14159,
                    "integer": 42,
                    "null_value": None,
                    "bool_value": True,
                    "list_value": [1, 2, None, True, "string"]
                },
                "primary_vector": test_vector,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "agent_id": "test-agent",
                    "memory_type": "mixed",
                    "tags_in_metadata": [None, "tag1", True, 123]
                },
                "tags": [None, "valid_tag", ""]  # Mixed with None and empty
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test each case
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test_case['name']}")
            
            try:
                response = await client.post(
                    f"{base_url}/cam/store",
                    json=test_case['memory']
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Success! Memory ID: {result['memory_id']}")
                else:
                    print(f"   ❌ Failed with status {response.status_code}")
                    print(f"   Response: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Serialization test completed!")


if __name__ == "__main__":
    asyncio.run(test_serialization_fix())