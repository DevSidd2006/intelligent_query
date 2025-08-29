#!/usr/bin/env python3
"""
Quick test script to verify Groq API integration
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_groq_connection():
    try:
        # Get Groq API key
        api_key = os.getenv('GROQ_API_KEY')
        
        # Initialize Groq client
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        print("🧪 Testing Groq connection...")
        
        # Test with a simple query
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond in JSON format."},
                {"role": "user", "content": 'Please respond with: {"status": "success", "message": "Groq is working!"}'}
            ]
        )
        
        result = response.choices[0].message.content
        print(f"✅ Groq Response: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Groq test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Groq API Integration")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ No API key found (GROQ_API_KEY)")
        print("Please check your .env file")
    elif api_key == "your_groq_api_key_here":
        print("❌ Please update your .env file with a real Groq API key")
        print("Get one from: https://console.groq.com/keys")
    else:
        print(f"✅ API Key found: {api_key[:10]}...")
        test_groq_connection()
    
    print("=" * 50)
