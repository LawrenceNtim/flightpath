"""
AI-Powered FlightPath System
Production-ready implementation with secure API key handling and comprehensive error management.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FlightRecommendation:
    """Data class for flight recommendations."""
    route: str
    confidence: float
    reasoning: str
    points_value: int
    ai_insights: str
    rule_based_score: float
    ai_score: float
    combined_score: float


@dataclass
class FlightData:
    """Data class for flight information."""
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    passenger_count: int = 1
    class_preference: str = "economy"
    flexible_dates: bool = False
    budget_limit: Optional[int] = None


class PointsOptimizer:
    """Mock PointsOptimizer class for demonstration purposes."""
    
    def __init__(self):
        self.rules = {
            "peak_season_multiplier": 1.5,
            "advance_booking_bonus": 0.2,
            "route_popularity_factor": 1.3,
            "loyalty_tier_multiplier": 1.1
        }
    
    def calculate_points_value(self, flight_data: FlightData) -> Dict[str, Any]:
        """Calculate points value using rule-based logic."""
        base_points = 10000
        
        # Apply rule-based calculations
        if flight_data.class_preference == "business":
            base_points *= 2
        elif flight_data.class_preference == "first":
            base_points *= 3
            
        # Distance-based calculation (mock)
        distance_multiplier = 1.0
        if "international" in flight_data.destination.lower():
            distance_multiplier = 2.0
            
        total_points = int(base_points * distance_multiplier)
        
        return {
            "points_required": total_points,
            "rule_based_score": min(total_points / 50000, 1.0),
            "factors": {
                "class_multiplier": 2 if flight_data.class_preference == "business" else 1,
                "distance_multiplier": distance_multiplier,
                "base_points": base_points
            }
        }
    
    def get_alternative_routes(self, flight_data: FlightData) -> List[Dict[str, Any]]:
        """Get alternative routes for optimization."""
        alternatives = [
            {
                "route": f"{flight_data.origin} -> {flight_data.destination}",
                "points_value": 15000,
                "savings": 5000
            },
            {
                "route": f"{flight_data.origin} -> Hub -> {flight_data.destination}",
                "points_value": 12000,
                "savings": 8000
            }
        ]
        return alternatives


class AIFlightPath:
    """
    AI-powered FlightPath system that combines rule-based optimization 
    with Claude AI strategic analysis.
    """
    
    def __init__(self):
        self.client = None
        self.points_optimizer = PointsOptimizer()
        self.conversation_history = []
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Anthropic client with secure API key handling."""
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not found in environment variables. "
                    "Please set it in your .env file."
                )
            
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("Successfully initialized Anthropic client")
            
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise
    
    @asynccontextmanager
    async def _error_handler(self, operation: str):
        """Context manager for consistent error handling."""
        try:
            yield
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error during {operation}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during {operation}: {e}")
            raise
    
    def _prepare_flight_context(self, flight_data: FlightData) -> str:
        """Prepare flight context for AI analysis."""
        context = f"""
        Flight Analysis Request:
        - Origin: {flight_data.origin}
        - Destination: {flight_data.destination}
        - Departure: {flight_data.departure_date}
        - Return: {flight_data.return_date or 'One-way'}
        - Passengers: {flight_data.passenger_count}
        - Class: {flight_data.class_preference}
        - Flexible dates: {flight_data.flexible_dates}
        - Budget limit: {flight_data.budget_limit or 'None specified'}
        """
        return context
    
    async def analyze_flight_strategy(self, flight_data: FlightData) -> Dict[str, Any]:
        """
        Send flight data to Claude API for strategic analysis.
        """
        async with self._error_handler("flight strategy analysis"):
            context = self._prepare_flight_context(flight_data)
            
            system_prompt = """
            You are an expert travel strategist specializing in points optimization and flight booking strategies. 
            Analyze the provided flight data and provide strategic recommendations focusing on:
            1. Optimal booking timing
            2. Route optimization strategies
            3. Points/miles maximization opportunities
            4. Cost-saving alternatives
            5. Seasonal and demand factors
            
            Provide a confidence score (0-1) and detailed reasoning for your recommendations.
            """
            
            user_prompt = f"""
            {context}
            
            Please analyze this flight request and provide strategic recommendations for optimal booking and points optimization.
            """
            
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                
                ai_analysis = response.content[0].text
                
                # Parse AI confidence (simplified extraction)
                confidence = self._extract_confidence_score(ai_analysis)
                
                return {
                    "ai_analysis": ai_analysis,
                    "confidence": confidence,
                    "ai_score": confidence,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in AI analysis: {e}")
                return {
                    "ai_analysis": "AI analysis temporarily unavailable",
                    "confidence": 0.5,
                    "ai_score": 0.5,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
    
    def _extract_confidence_score(self, ai_text: str) -> float:
        """Extract confidence score from AI response."""
        # Simple confidence extraction logic
        confidence_keywords = {
            "very confident": 0.9,
            "confident": 0.8,
            "moderately confident": 0.7,
            "somewhat confident": 0.6,
            "uncertain": 0.4,
            "low confidence": 0.3
        }
        
        ai_text_lower = ai_text.lower()
        for keyword, score in confidence_keywords.items():
            if keyword in ai_text_lower:
                return score
        
        return 0.7  # Default confidence
    
    def combine_recommendations(self, 
                              flight_data: FlightData,
                              rule_based_result: Dict[str, Any],
                              ai_result: Dict[str, Any]) -> FlightRecommendation:
        """
        Combine rule-based and AI recommendations into a unified suggestion.
        """
        # Weighted combination of scores
        rule_weight = 0.4
        ai_weight = 0.6
        
        combined_score = (
            rule_based_result["rule_based_score"] * rule_weight +
            ai_result["ai_score"] * ai_weight
        )
        
        route = f"{flight_data.origin} → {flight_data.destination}"
        
        recommendation = FlightRecommendation(
            route=route,
            confidence=ai_result["confidence"],
            reasoning=ai_result["ai_analysis"],
            points_value=rule_based_result["points_required"],
            ai_insights=ai_result["ai_analysis"],
            rule_based_score=rule_based_result["rule_based_score"],
            ai_score=ai_result["ai_score"],
            combined_score=combined_score
        )
        
        return recommendation
    
    async def get_flight_recommendations(self, flight_data: FlightData) -> FlightRecommendation:
        """
        Main method to get comprehensive flight recommendations.
        """
        try:
            logger.info(f"Analyzing flight: {flight_data.origin} to {flight_data.destination}")
            
            # Get rule-based analysis
            rule_based_result = self.points_optimizer.calculate_points_value(flight_data)
            
            # Get AI analysis
            ai_result = await self.analyze_flight_strategy(flight_data)
            
            # Combine recommendations
            recommendation = self.combine_recommendations(
                flight_data, rule_based_result, ai_result
            )
            
            logger.info(f"Generated recommendation with combined score: {recommendation.combined_score:.2f}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating flight recommendations: {e}")
            raise
    
    async def interactive_chat(self, user_message: str, flight_context: Optional[FlightData] = None) -> str:
        """
        Interactive chat functionality for flight planning assistance.
        """
        async with self._error_handler("interactive chat"):
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Prepare context
            context = ""
            if flight_context:
                context = self._prepare_flight_context(flight_context)
            
            system_prompt = """
            You are a helpful flight planning assistant. You can help users with:
            - Flight booking strategies
            - Points and miles optimization
            - Route planning
            - Travel timing advice
            - Budget optimization
            
            Be conversational, helpful, and provide actionable advice.
            """
            
            # Prepare messages for the API
            messages = []
            if context:
                messages.append({
                    "role": "user", 
                    "content": f"Flight context: {context}\n\nUser question: {user_message}"
                })
            else:
                messages.append({"role": "user", "content": user_message})
            
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=800,
                    temperature=0.5,
                    system=system_prompt,
                    messages=messages
                )
                
                assistant_response = response.content[0].text
                
                # Add assistant response to conversation history
                self.conversation_history.append({"role": "assistant", "content": assistant_response})
                
                # Keep conversation history manageable
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                
                return assistant_response
                
            except Exception as e:
                logger.error(f"Error in interactive chat: {e}")
                return "I'm sorry, I'm having trouble processing your request right now. Please try again."
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history."""
        return self.conversation_history.copy()
    
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the system."""
        status = {
            "client_initialized": self.client is not None,
            "api_key_configured": bool(os.getenv('ANTHROPIC_API_KEY')),
            "points_optimizer_ready": self.points_optimizer is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        return status


# Example usage and testing
async def main():
    """Example usage of the AIFlightPath system."""
    
    # Initialize the system
    ai_flightpath = AIFlightPath()
    
    # Check system health
    health = ai_flightpath.health_check()
    print(f"System Health: {health}")
    
    # Example flight data
    flight_data = FlightData(
        origin="JFK",
        destination="LAX",
        departure_date="2024-03-15",
        return_date="2024-03-22",
        passenger_count=2,
        class_preference="business",
        flexible_dates=True,
        budget_limit=100000
    )
    
    try:
        # Get flight recommendations
        recommendation = await ai_flightpath.get_flight_recommendations(flight_data)
        
        print("\n=== Flight Recommendation ===")
        print(f"Route: {recommendation.route}")
        print(f"Combined Score: {recommendation.combined_score:.2f}")
        print(f"Points Required: {recommendation.points_value}")
        print(f"AI Confidence: {recommendation.confidence:.2f}")
        print(f"AI Insights: {recommendation.ai_insights[:200]}...")
        
        # Interactive chat example
        chat_response = await ai_flightpath.interactive_chat(
            "What's the best time to book this flight?",
            flight_context=flight_data
        )
        
        print(f"\n=== Chat Response ===")
        print(chat_response)
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())