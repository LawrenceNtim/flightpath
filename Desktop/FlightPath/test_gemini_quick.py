#!/usr/bin/env python3
"""Quick test of Gemini API connection"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv('GEMINI_API_KEY')
print(f"🔑 Using API key: {api_key[:10]}...")

genai.configure(api_key=api_key)

try:
    # Try Gemini 2.0 Flash experimental
    print("\n🧪 Testing Gemini 2.0 Flash Experimental...")
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content("Say 'FlightPath is ready to fly with Gemini!'")
    print(f"✅ Gemini 2.0 Flash says: {response.text.strip()}")
except Exception as e:
    print(f"⚠️  Gemini 2.0 Flash experimental not available: {e}")
    
    # Fallback to stable version
    print("\n🧪 Testing Gemini 1.5 Flash...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'FlightPath is ready to fly with Gemini!'")
        print(f"✅ Gemini 1.5 Flash says: {response.text.strip()}")
    except Exception as e:
        print(f"❌ Error: {e}")

# Test travel query
print("\n🧪 Testing travel query...")
try:
    prompt = """You are a helpful travel agent. A user asks: 
    "I want to fly from LA to New York next week"
    
    Provide a brief, friendly response with a flight recommendation."""
    
    response = model.generate_content(prompt)
    print(f"✈️ Travel response: {response.text.strip()[:200]}...")
    print("\n✅ All tests passed! Gemini is ready for FlightPath!")
except Exception as e:
    print(f"❌ Travel query failed: {e}")