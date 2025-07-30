#!/usr/bin/env python3
"""
FlightPath Gemini Demo - Simple interactive demo
"""

import asyncio
import os
from dotenv import load_dotenv
from gemini_travel_agent import GeminiTravelAgent
import time

# Load environment variables
load_dotenv()

async def main():
    """Interactive demo of the Gemini travel agent"""
    
    print("✈️  FlightPath powered by Gemini 2.0 Flash")
    print("=" * 50)
    print("Your AI travel assistant is ready!")
    print("Type 'quit' to exit\n")
    
    agent = GeminiTravelAgent()
    user_id = "demo_user"
    
    # Example queries to try
    print("Try asking me things like:")
    print("• I need to fly from LA to New York next week")
    print("• Find me a hotel in Paris")
    print("• Plan a trip to Tokyo for cherry blossom season")
    print("• What's the best time to visit Iceland?")
    print("-" * 50)
    
    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n🤖 Agent: Safe travels! Goodbye! ✈️")
                break
            
            if not user_input:
                continue
            
            # Process with agent
            print("\n🤖 Agent: ", end="", flush=True)
            
            response = await agent.process_request(user_input, user_id)
            
            # Print response
            print(response)
            
            # Save conversation
            agent.save_conversation(user_id, user_input, response)
            
            # Small delay to respect rate limits
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\n🤖 Agent: Safe travels! Goodbye! ✈️")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Let me try again...")
            time.sleep(2)  # Wait before retry

if __name__ == "__main__":
    # Check API key
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not found in environment")
        print("Please check your .env file")
        exit(1)
    
    # Run demo
    asyncio.run(main())