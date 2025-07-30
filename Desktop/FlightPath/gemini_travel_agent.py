"""
FlightPath Travel Agent - Gemini 2.0 Flash Edition
Enhanced AI agent that integrates with existing FlightPath system
"""

import os
import google.generativeai as genai
from datetime import datetime, timedelta
import asyncio
import re
from typing import Dict, Optional, List, Tuple
import json
import logging
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import existing FlightPath components
try:
    from flightpath_v2_scraper import FlightPathOrchestrator
    from accommodation_v2_scraper import AccommodationOrchestratorV2
    from fast_flights_engine import FastFlightsEngine, CabinClass
except ImportError:
    logging.warning("FlightPath components not found. Running in standalone mode.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class GeminiTravelAgent:
    """Smart travel agent powered by Gemini 2.0 Flash"""
    
    def __init__(self):
        # Use latest Gemini 2.5 Flash Lite - newer and more efficient
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.conversations = {}
        self.flight_engine = None
        self.accommodation_engine = None
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests
        
        # Initialize FlightPath components if available
        try:
            self.flight_engine = FlightPathOrchestrator()
            self.accommodation_engine = AccommodationOrchestratorV2()
        except:
            logger.info("Running without FlightPath integration")
    
    async def process_request(self, user_message: str, user_id: str = "default") -> str:
        """Main entry point for user requests"""
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
        
        # Get conversation context
        context = self.conversations.get(user_id, {})
        
        # Extract intent
        intent = await self._extract_intent(user_message, context)
        
        # Route to appropriate handler
        if intent['type'] == 'flight_search':
            return await self._handle_flight_search(intent, user_id)
        elif intent['type'] == 'accommodation_search':
            return await self._handle_accommodation_search(intent, user_id)
        elif intent['type'] == 'complete_trip':
            return await self._handle_complete_trip(intent, user_id)
        elif intent['type'] == 'booking_confirmation':
            return await self._handle_booking(intent, user_id)
        else:
            return await self._handle_general_query(user_message, context)
    
    async def _extract_intent(self, message: str, context: Dict) -> Dict:
        """Use Gemini to understand user intent"""
        
        prompt = f"""Analyze this travel request and extract the intent.

User message: "{message}"
Previous context: {json.dumps(context) if context else "None"}

Classify the intent type as one of:
- flight_search: Looking for flights
- accommodation_search: Looking for hotels/stays
- complete_trip: Planning entire trip (flights + hotel)
- booking_confirmation: Confirming a booking
- general_query: General travel questions

Extract all relevant details:
- origin: departure city/airport
- destination: arrival city/airport
- departure_date: when to leave
- return_date: when to return (if round trip)
- travelers: number and type (adults, children)
- cabin_class: economy, business, first
- budget: price range or constraints
- preferences: specific needs or wants

Return as JSON with structure:
{{
    "type": "intent_type",
    "details": {{
        "origin": "...",
        "destination": "...",
        "departure_date": "YYYY-MM-DD",
        "return_date": "YYYY-MM-DD or null",
        "travelers": {{"adults": 1, "children": 0}},
        "cabin_class": "economy",
        "budget": "...",
        "preferences": []
    }}
}}"""
        
        try:
            response = self.model.generate_content(prompt)
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
        
        # Fallback
        return {
            "type": "general_query",
            "details": {}
        }
    
    async def _handle_flight_search(self, intent: Dict, user_id: str) -> str:
        """Handle flight search requests"""
        
        details = intent.get('details', {})
        
        # If we have the flight engine, use it
        if self.flight_engine:
            try:
                # Search for flights
                results = await self.flight_engine.search_flights(
                    origin=details.get('origin', 'LAX'),
                    destination=details.get('destination', 'JFK'),
                    departure_date=details.get('departure_date', 
                                               (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')),
                    return_date=details.get('return_date'),
                    cabin_class=details.get('cabin_class', 'economy')
                )
                
                # Use Gemini to create natural response
                return await self._format_flight_results(results, details)
                
            except Exception as e:
                logger.error(f"Flight search failed: {e}")
        
        # Fallback response
        return await self._generate_flight_recommendation(details)
    
    async def _format_flight_results(self, results: List[Dict], search_params: Dict) -> str:
        """Use Gemini to format flight results naturally"""
        
        prompt = f"""You're a friendly travel agent. Format these flight search results conversationally.

Search parameters: {json.dumps(search_params)}
Flight results: {json.dumps(results[:3])}  # Top 3 results

Create a natural response that:
1. Highlights the best option based on their needs
2. Mentions key details (times, prices, airlines)
3. Explains why you recommend it
4. Asks if they want to book

Keep it conversational and helpful, not like a robot listing options."""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    async def _generate_flight_recommendation(self, details: Dict) -> str:
        """Generate flight recommendation without real data"""
        
        prompt = f"""You're a helpful travel agent. Generate a realistic flight recommendation.

Travel details: {json.dumps(details)}

Create a natural response recommending a specific flight with:
- Realistic departure/arrival times
- Appropriate price for the route and class
- Good reasoning for the recommendation
- Natural, conversational tone

End with asking if they'd like to book it."""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    async def _handle_accommodation_search(self, intent: Dict, user_id: str) -> str:
        """Handle accommodation search requests"""
        
        details = intent.get('details', {})
        
        if self.accommodation_engine:
            try:
                # Search for accommodations
                results = await self.accommodation_engine.search_accommodations(
                    destination=details.get('destination', 'New York'),
                    check_in=details.get('departure_date'),
                    check_out=details.get('return_date'),
                    guests=details.get('travelers', {}).get('adults', 1)
                )
                
                return await self._format_accommodation_results(results, details)
                
            except Exception as e:
                logger.error(f"Accommodation search failed: {e}")
        
        return await self._generate_accommodation_recommendation(details)
    
    async def _generate_accommodation_recommendation(self, details: Dict) -> str:
        """Generate accommodation recommendation without real data"""
        
        prompt = f"""You're a helpful travel agent. Generate a realistic hotel recommendation.

Travel details: {json.dumps(details)}

Create a natural response recommending a specific hotel with:
- Real hotel name appropriate for the destination
- Realistic nightly rate for the location
- Key amenities that match their needs
- Natural, conversational tone

End with asking if they'd like to book it."""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    async def _format_accommodation_results(self, results: List[Dict], search_params: Dict) -> str:
        """Use Gemini to format accommodation results naturally"""
        
        prompt = f"""You're a friendly travel agent. Format these hotel search results conversationally.

Search parameters: {json.dumps(search_params)}
Hotel results: {json.dumps(results[:3])}  # Top 3 results

Create a natural response that:
1. Highlights the best option based on their needs
2. Mentions key details (location, price, amenities)
3. Explains why you recommend it
4. Asks if they want to book

Keep it conversational and helpful."""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    async def _handle_complete_trip(self, intent: Dict, user_id: str) -> str:
        """Handle complete trip planning"""
        
        details = intent.get('details', {})
        
        # Search for both flights and accommodation
        flight_task = self._handle_flight_search(intent, user_id)
        accommodation_task = self._handle_accommodation_search(intent, user_id)
        
        flight_result, accommodation_result = await asyncio.gather(
            flight_task, accommodation_task
        )
        
        # Combine results
        prompt = f"""You're a travel agent who just found great options for a complete trip.

Flight recommendation: {flight_result}
Accommodation recommendation: {accommodation_result}

Create a unified response that:
1. Presents the complete trip package
2. Shows total estimated cost
3. Highlights how well they work together
4. Asks if they want to book the complete package

Keep it natural and enthusiastic."""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    async def _handle_booking(self, intent: Dict, user_id: str) -> str:
        """Handle booking confirmation"""
        
        # Get last conversation context
        context = self.conversations.get(user_id, {})
        
        prompt = f"""The user wants to book their trip. Based on the conversation:

Context: {json.dumps(context)}
Current message: {intent}

Generate a booking confirmation response that:
1. Confirms what's being booked
2. Mentions next steps
3. Asks for any final details needed
4. Ends with enthusiasm about their trip

Be warm and professional."""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    async def _handle_general_query(self, message: str, context: Dict) -> str:
        """Handle general travel questions"""
        
        prompt = f"""You're a knowledgeable travel agent. Answer this question helpfully:

Question: {message}
Context: {json.dumps(context) if context else "None"}

Provide a helpful, conversational response. If it's travel-related, share useful insights.
If it's not travel-related, politely redirect to travel topics."""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def save_conversation(self, user_id: str, message: str, response: str):
        """Save conversation context"""
        
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            'timestamp': datetime.now().isoformat(),
            'user_message': message,
            'agent_response': response
        })
        
        # Keep only last 10 exchanges
        self.conversations[user_id] = self.conversations[user_id][-10:]

# Quick test interface
async def test_gemini_agent():
    """Test the Gemini travel agent"""
    
    print("✈️ FlightPath Gemini Agent Test")
    print("=" * 50)
    
    agent = GeminiTravelAgent()
    
    test_queries = [
        "I need to fly from LA to New York next Friday",
        "Find me a hotel in Manhattan for the same dates",
        "What's the weather like in NYC in December?",
        "Book the flight you recommended"
    ]
    
    user_id = "test_user"
    
    for query in test_queries:
        print(f"\n👤 User: {query}")
        response = await agent.process_request(query, user_id)
        print(f"🤖 Agent: {response}")
        
        # Save conversation
        agent.save_conversation(user_id, query, response)
        print("-" * 50)

# Production API
class FlightPathGeminiAPI:
    """Production API for Gemini agent"""
    
    def __init__(self):
        self.agent = GeminiTravelAgent()
    
    async def chat(self, user_id: str, message: str) -> Dict[str, str]:
        """Main chat endpoint"""
        
        try:
            response = await self.agent.process_request(message, user_id)
            self.agent.save_conversation(user_id, message, response)
            
            return {
                'status': 'success',
                'response': response,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                'status': 'error',
                'response': "I'm having trouble processing that. Could you try again?",
                'error': str(e)
            }

if __name__ == "__main__":
    # Check for API key
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  Please set GEMINI_API_KEY environment variable")
        print("Get your key at: https://makersuite.google.com/app/apikey")
        print("\nExample:")
        print("export GEMINI_API_KEY='your-key-here'")
        exit(1)
    
    # Run test
    asyncio.run(test_gemini_agent())