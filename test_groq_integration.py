#!/usr/bin/env python3
"""
Test script to verify Groq API integration with the updated system
"""
import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_groq_api():
    """Test basic Groq API functionality"""
    try:
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("❌ GROQ_API_KEY not found in environment")
            return False
        
        print(f"✅ API Key found: {api_key[:10]}...")
        
        # Initialize Groq client
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        print("🧪 Testing Groq API with llama-3.1-8b-instant...")
        
        # Test with a simple query
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond concisely."},
                {"role": "user", "content": "What is 2+2? Respond with just the number."}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ Groq Response: {result}")
        
        if "4" in result:
            print("✅ Groq API integration successful!")
            return True
        else:
            print("⚠️ Unexpected response from Groq API")
            return False
        
    except Exception as e:
        print(f"❌ Groq API test failed: {str(e)}")
        return False

def test_app_integration():
    """Test the app's get_api_key function"""
    try:
        from app import get_api_key
        
        api_key = get_api_key()
        print(f"✅ App get_api_key() works: {api_key[:10]}...")
        return True
        
    except Exception as e:
        print(f"❌ App integration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Groq Integration")
    print("=" * 50)
    
    # Test API directly
    api_success = test_groq_api()
    
    # Test app integration
    app_success = test_app_integration()
    
    print("=" * 50)
    if api_success and app_success:
        print("🎉 All tests passed! Groq integration is working.")
    else:
        print("❌ Some tests failed. Check the errors above.")