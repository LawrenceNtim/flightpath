"""
FlightPath Travel Agent - Your personal AI travel assistant
Powered by Gemini 2.0 Flash for cost-efficient intelligence
"""

import os
import google.generativeai as genai
from datetime import datetime
import asyncio
import re
from typing import Dict, Optional, Tuple
import json

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class TravelAgent:
    """An AI agent that books trips, not a flight search tool"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.personality = "warm, helpful, and decisive - like a favorite aunt who happens to be a travel expert"
        
    async def chat(self, user_message: str, context: Optional[Dict] = None) -> str:
        """The ONLY interface users need - just chat naturally"""
        
        # Understand what they want
        intent = await self.understand_intent(user_message, context)
        
        # Make a decision (don't show options)
        decision = await self.make_decision(intent)
        
        # Explain simply
        return self.explain_simply(decision)
    
    async def understand_intent(self, message: str, context: Optional[Dict] = None) -> Dict:
        """Extract travel intent without jargon"""
        
        prompt = f"""You are a friendly travel agent AI. A user said: "{message}"
        
        {f"Previous context: {context}" if context else ""}
        
        Extract their travel needs in simple terms:
        1. Where do they want to go? (or describe the type of place)
        2. When do they want to travel? (specific dates or general timeframe)
        3. Why are they traveling? (visit family, vacation, business, etc.)
        4. Who is traveling? (alone, family, kids, etc.)
        5. What matters most? (save money, comfort, quick trip, etc.)
        
        Respond in JSON format:
        {{
            "destination": "location or type of place",
            "when": "timeframe",
            "purpose": "reason for travel",
            "travelers": "who and how many",
            "priorities": "what matters most",
            "flexibility": "how flexible are dates/destination"
        }}
        
        If information is missing, make reasonable assumptions based on context.
        """
        
        response = self.model.generate_content(prompt)
        
        try:
            # Parse JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback to basic extraction
                return {
                    "destination": "not specified",
                    "when": "flexible",
                    "purpose": "leisure",
                    "travelers": "1 adult",
                    "priorities": "balance cost and comfort"
                }
        except:
            return {
                "destination": message,
                "when": "soon",
                "purpose": "general",
                "travelers": "1",
                "priorities": "best value"
            }
    
    async def make_decision(self, intent: Dict) -> Dict:
        """Make THE decision - don't present options"""
        
        # This is where you'd integrate with your flight search
        # For now, we'll simulate a decision
        
        # Example decision logic based on intent
        if "family" in intent.get("purpose", "").lower():
            # Family visits prioritize convenient times, direct flights
            decision = {
                "recommendation": "Thursday morning flight",
                "arrival_time": "2:30 PM",
                "price": "$285",
                "reasoning": "arrives in time for dinner, non-stop flight",
                "booking_method": "points" if intent.get("priorities") == "save money" else "cash"
            }
        elif "business" in intent.get("purpose", "").lower():
            # Business prioritizes schedule and comfort
            decision = {
                "recommendation": "Monday evening flight",
                "arrival_time": "11:30 PM",
                "price": "$420",
                "reasoning": "full work day before travel, better seat available",
                "booking_method": "cash"
            }
        else:
            # Leisure prioritizes value
            decision = {
                "recommendation": "Tuesday afternoon flight",
                "arrival_time": "6:45 PM", 
                "price": "$198",
                "reasoning": "best value this week, good airline",
                "booking_method": "cash"
            }
            
        return decision
    
    def explain_simply(self, decision: Dict) -> str:
        """Explain the decision in human terms - no jargon"""
        
        responses = {
            "points": f"I found a great {decision['recommendation']} that gets you there by {decision['arrival_time']}. I can book it using your credit card points, so you won't pay anything except $12 in taxes. Should I book it?",
            
            "cash": f"Perfect! There's a {decision['recommendation']} arriving at {decision['arrival_time']} for {decision['price']}. {decision['reasoning'].capitalize()}. Want me to book it?"
        }
        
        return responses.get(decision['booking_method'], responses['cash'])
    
    async def book_trip(self, confirmation: str) -> str:
        """Handle booking confirmation"""
        
        if confirmation.lower() in ['yes', 'book it', 'sure', 'ok', 'go ahead', 'book']:
            return "Great! I'm booking that now... ✅ All set! You'll receive a confirmation email shortly. Have a wonderful trip!"
        else:
            return "No problem! Would you like me to look for other options, or is there something specific you'd prefer?"

# Simple test interface
async def test_agent():
    """Test the travel agent with example conversations"""
    
    agent = TravelAgent()
    
    # Test conversations
    test_messages = [
        "I need to visit my mom in Chicago next month",
        "Book something to Vegas this weekend",
        "I want to go somewhere warm",
        "Business meeting in Seattle Tuesday"
    ]
    
    print("✈️ FlightPath Travel Agent Test")
    print("=" * 50)
    
    for message in test_messages:
        print(f"\n👤 User: {message}")
        response = await agent.chat(message)
        print(f"🤖 Agent: {response}")
        print("-" * 50)

# Production interface
class FlightPathAgent:
    """Production-ready travel agent"""
    
    def __init__(self):
        self.agent = TravelAgent()
        self.conversations = {}  # Track conversation context
        
    async def handle_message(self, user_id: str, message: str) -> str:
        """Handle a user message with conversation context"""
        
        # Get conversation context
        context = self.conversations.get(user_id, {})
        
        # Process message
        response = await self.agent.chat(message, context)
        
        # Update context
        self.conversations[user_id] = {
            'last_message': message,
            'last_response': response,
            'timestamp': datetime.now().isoformat()
        }
        
        return response
    
    async def confirm_booking(self, user_id: str, confirmation: str) -> str:
        """Handle booking confirmation"""
        return await self.agent.book_trip(confirmation)

# Quick start for testing
if __name__ == "__main__":
    # Check for API key
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  Please set GEMINI_API_KEY environment variable")
        print("Get your key at: https://makersuite.google.com/app/apikey")
        exit(1)
    
    # Run test
    asyncio.run(test_agent())