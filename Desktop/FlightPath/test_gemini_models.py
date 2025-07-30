#!/usr/bin/env python3
"""Test available Gemini models"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

print("🔍 Testing Gemini Models")
print("=" * 50)

# Models to test
models_to_test = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest"
]

# Test each model
for model_name in models_to_test:
    print(f"\n📦 Testing: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'Hello' in exactly one word")
        print(f"✅ {model_name} works! Response: {response.text.strip()}")
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "404" in error_msg:
            print(f"❌ {model_name} - Not available")
        else:
            print(f"⚠️  {model_name} - Error: {error_msg[:100]}...")

# List all available models
print("\n" + "=" * 50)
print("📋 All Available Models:")
print("-" * 50)

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"• {model.name}")
            if hasattr(model, 'description'):
                print(f"  Description: {model.description[:80]}...")
except Exception as e:
    print(f"Error listing models: {e}")