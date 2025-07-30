#!/usr/bin/env python3
"""
Simple OpenAI test to verify the API key and model work
"""

import os
from openai import OpenAI

def test_openai_basic():
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set in environment")
        return None, None
    
    try:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client created successfully")
        
        # Test with a simple model first (gpt-4o-mini is usually available)
        models_to_try = [
            "gpt-4.1-nano-2025-04-14",
            "gpt-4o-mini", 
            "gpt-3.5-turbo"
        ]
        
        for model in models_to_try:
            try:
                print(f"\n🧪 Testing model: {model}")
                
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant. Respond with valid JSON only."},
                        {"role": "user", "content": "Analyze this: user says 'My name is John', assistant says 'Nice to meet you John'. Should this be stored as memory? Respond with JSON: {\"should_store\": true/false, \"reasoning\": \"explanation\"}"}
                    ],
                    temperature=0.1,
                    max_tokens=200,
                    response_format={"type": "json_object"}
                )
                
                result = response.choices[0].message.content
                print(f"✅ Model {model} works!")
                print(f"📝 Response: {result}")
                return model, result
                
            except Exception as e:
                print(f"❌ Model {model} failed: {str(e)}")
                continue
        
        print("❌ No models worked")
        return None, None
        
    except Exception as e:
        print(f"❌ OpenAI client creation failed: {e}")
        return None, None

if __name__ == "__main__":
    print("🔑 Testing OpenAI Integration")
    print("=" * 50)
    
    working_model, response = test_openai_basic()
    
    if working_model:
        print(f"\n🎉 SUCCESS! Working model: {working_model}")
    else:
        print(f"\n💥 FAILED! No models worked")