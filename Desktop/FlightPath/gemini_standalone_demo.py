#!/usr/bin/env python3
"""
Standalone Gemini Travel Agent Demo
Works without FlightPath components
"""

import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
import json
import re
from datetime import datetime
from typing import Dict, Optional

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class SimpleTravelAgent:
    """Simplified travel agent using only Gemini"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.conversations = {}
    
    async def chat(self, message: str, user_id: str = "default") -> str:
        """Process user message and return response"""
        
        # Get conversation history
        context = self.conversations.get(user_id, [])
        
        # Create prompt with context
        prompt = self._build_prompt(message, context)
        
        # Get response from Gemini
        try:
            response = self.model.generate_content(prompt)
            result = response.text
            
            # Save to conversation history
            self._save_conversation(user_id, message, result)
            
            return result
            
        except Exception as e:
            return f"I'm having trouble processing that. Could you try again? ({str(e)})"
    
    def _build_prompt(self, message: str, context: list) -> str:
        """Build prompt with conversation context"""
        
        prompt = """You are a friendly and knowledgeable travel agent AI assistant. 
You help users plan trips, find flights, book hotels, and answer travel questions.

Be conversational, helpful, and specific in your recommendations.
When suggesting flights or hotels, use realistic prices and times.
If the user wants to book something, ask for confirmation and act as if you can process it.

"""
        
        # Add conversation history
        if context:
            prompt += "Previous conversation:\n"
            for item in context[-3:]:  # Last 3 exchanges
                prompt += f"User: {item['user']}\n"
                prompt += f"Agent: {item['agent']}\n"
            prompt += "\n"
        
        prompt += f"Current user message: {message}\n"
        prompt += "Your response:"
        
        return prompt
    
    def _save_conversation(self, user_id: str, user_message: str, agent_response: str):
        """Save conversation to history"""
        
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            'user': user_message,
            'agent': agent_response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 10 exchanges
        self.conversations[user_id] = self.conversations[user_id][-10:]

async def demo():
    """Run interactive demo"""
    
    print("✈️  FlightPath Travel Agent (Gemini Powered)")
    print("=" * 50)
    print("Your AI travel assistant is ready!")
    print("Type 'quit' to exit\n")
    
    agent = SimpleTravelAgent()
    user_id = "demo_user"
    
    # Show example queries
    print("Try asking me:")
    print("• Book a flight from NYC to Paris next week")
    print("• Find a romantic hotel in Rome")
    print("• Plan a 5-day trip to Japan")
    print("• What's the best time to visit Iceland?")
    print("-" * 50)
    
    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n✈️ Safe travels! Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Get response
            print("\n🤖 Agent: ", end="", flush=True)
            response = await agent.chat(user_input, user_id)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n✈️ Safe travels! Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

async def test_queries():
    """Test with sample queries"""
    
    print("🧪 Running automated test queries...")
    print("=" * 50)
    
    agent = SimpleTravelAgent()
    
    test_queries = [
        "I need to fly from Los Angeles to New York next Friday",
        "What's the weather like in Tokyo in April?",
        "Find me a luxury hotel in Dubai for next month",
        "Book the flight you recommended",
        "How much would that cost in total?"
    ]
    
    user_id = "test_user"
    
    for query in test_queries:
        print(f"\n👤 User: {query}")
        response = await agent.chat(query, user_id)
        print(f"🤖 Agent: {response[:300]}{'...' if len(response) > 300 else ''}")
        await asyncio.sleep(0.5)  # Small delay
    
    print("\n✅ Test complete!")

async def main():
    """Main entry point"""
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        await test_queries()
    else:
        await demo()

if __name__ == "__main__":
    # Check API key
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not found!")
        print("Please check your .env file")
        exit(1)
    
    # Run
    asyncio.run(main())