#!/usr/bin/env python3
"""Simple test of Gemini Travel Agent without FlightPath dependencies"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_basic_queries():
    """Test basic travel queries"""
    
    # Import here to ensure env vars are loaded
    from gemini_travel_agent import GeminiTravelAgent
    
    print("✈️ Testing Gemini Travel Agent (Paid Tier)")
    print("=" * 50)
    
    agent = GeminiTravelAgent()
    
    # Test queries
    queries = [
        "Find flights from New York to London next month",
        "I need a hotel in Tokyo near Shibuya",
        "What's the weather like in Barcelona in summer?",
        "Book me the cheapest flight to Miami this weekend"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🧪 Test {i}: {query}")
        print("-" * 40)
        
        try:
            response = await agent.process_request(query, f"test_user_{i}")
            print(f"✅ Response: {response[:300]}...")
            
            # Save conversation
            agent.save_conversation(f"test_user_{i}", query, response)
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Small delay between queries
        await asyncio.sleep(1)
    
    print("\n" + "=" * 50)
    print("✅ Testing complete!")
    
    # Test rate limits
    print("\n🧪 Testing rate limits (10 rapid requests)...")
    print("-" * 40)
    
    rapid_start = asyncio.get_event_loop().time()
    for i in range(10):
        try:
            response = await agent.process_request(
                f"Quick test {i}", 
                "rate_test_user"
            )
            print(f"Request {i+1}: ✅")
        except Exception as e:
            print(f"Request {i+1}: ❌ {str(e)[:50]}...")
    
    rapid_end = asyncio.get_event_loop().time()
    print(f"\nCompleted 10 requests in {rapid_end - rapid_start:.2f} seconds")
    print("(Should be at least 5 seconds with rate limiting)")

async def test_conversation():
    """Test multi-turn conversation"""
    
    from gemini_travel_agent import GeminiTravelAgent
    
    print("\n🧪 Testing Conversation Flow")
    print("=" * 50)
    
    agent = GeminiTravelAgent()
    user_id = "conversation_test"
    
    conversation = [
        "I want to plan a romantic getaway",
        "Somewhere warm with beaches",
        "We prefer all-inclusive resorts",
        "Budget is around $3000 for both of us"
    ]
    
    for message in conversation:
        print(f"\n👤 User: {message}")
        try:
            response = await agent.process_request(message, user_id)
            print(f"🤖 Agent: {response[:250]}...")
            agent.save_conversation(user_id, message, response)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await asyncio.sleep(1)

async def main():
    """Run all tests"""
    
    # Check API key
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not found!")
        return
    
    print(f"🔑 Using API key: {os.getenv('GEMINI_API_KEY')[:10]}...")
    
    # Run tests
    await test_basic_queries()
    await test_conversation()

if __name__ == "__main__":
    asyncio.run(main())