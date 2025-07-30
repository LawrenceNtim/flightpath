#!/usr/bin/env python3
"""Minimal test to verify Gemini is working"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key loaded: {api_key[:10] if api_key else 'NOT FOUND'}...")

if not api_key:
    print("ERROR: No API key found!")
    exit(1)

# Configure Gemini
genai.configure(api_key=api_key)

# Test with stable model
print("\nTesting Gemini 1.5 Flash...")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say hello in 5 words or less")
    print(f"Response: {response.text}")
    print("✅ Gemini 1.5 Flash works!")
except Exception as e:
    print(f"❌ Error: {e}")

# Test paid tier limits
print("\nTesting multiple requests (paid tier)...")
for i in range(5):
    try:
        response = model.generate_content(f"Count to {i+1}")
        print(f"Request {i+1}: {response.text.strip()}")
    except Exception as e:
        print(f"Request {i+1} failed: {e}")

print("\n✅ All tests complete!")