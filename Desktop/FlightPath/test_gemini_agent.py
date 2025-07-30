#!/usr/bin/env python3
"""
Test script for Gemini Travel Agent
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_basic_functionality():
    """Test basic agent functionality"""
    from gemini_travel_agent import GeminiTravelAgent
    
    print("🧪 Testing Gemini Travel Agent")
    print("=" * 50)
    
    agent = GeminiTravelAgent()
    
    # Test queries
    test_cases = [
        {
            "query": "I need to fly from Los Angeles to New York next month",
            "expected": "flight recommendation"
        },
        {
            "query": "Find me a nice hotel in Manhattan for 3 nights",
            "expected": "accommodation recommendation"
        },
        {
            "query": "Plan a complete trip to Tokyo for Golden Week",
            "expected": "complete trip package"
        },
        {
            "query": "What's the best time to visit Iceland?",
            "expected": "general travel advice"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['query']}")
        print("-" * 40)
        
        try:
            response = await agent.process_request(test['query'], f"test_user_{i}")
            print(f"✅ Response: {response[:200]}...")
            print(f"Expected: {test['expected']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Testing complete!")

async def test_conversation_flow():
    """Test multi-turn conversation"""
    from gemini_travel_agent import GeminiTravelAgent
    
    print("\n🧪 Testing Conversation Flow")
    print("=" * 50)
    
    agent = GeminiTravelAgent()
    user_id = "conversation_test"
    
    conversation = [
        "I want to visit Paris",
        "I'm thinking late spring, maybe May",
        "It's for our anniversary, so somewhere romantic",
        "Yes, book the trip you suggested"
    ]
    
    for message in conversation:
        print(f"\n👤 User: {message}")
        response = await agent.process_request(message, user_id)
        print(f"🤖 Agent: {response[:300]}...")
        agent.save_conversation(user_id, message, response)
        await asyncio.sleep(1)  # Brief pause between messages

def check_api_key():
    """Check if API key is configured"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your-gemini-api-key-here':
        print("❌ GEMINI_API_KEY not configured")
        print("Please set your API key in the .env file")
        print("Get your key at: https://makersuite.google.com/app/apikey")
        return False
    print("✅ GEMINI_API_KEY configured")
    return True

async def main():
    """Run all tests"""
    print("🚀 FlightPath Gemini Agent Test Suite")
    print("=" * 50)
    
    if not check_api_key():
        return
    
    try:
        # Test basic functionality
        await test_basic_functionality()
        
        # Test conversation flow
        await test_conversation_flow()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())