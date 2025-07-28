#!/usr/bin/env python3
"""
Test script for AI FlightPath system
Demonstrates advanced travel hacker optimization for LAX to JFK route
"""

import asyncio
import json
from datetime import datetime
from ai_flightpath import AIFlightPath, FlightData

def print_divider(title):
    """Print a formatted divider with title."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_technical_analysis(rule_based_result, points_optimizer):
    """Display detailed technical analysis."""
    print_divider("TECHNICAL ANALYSIS - RULE-BASED OPTIMIZATION")
    
    print(f"Points Required: {rule_based_result['points_required']:,}")
    print(f"Rule-based Score: {rule_based_result['rule_based_score']:.3f}")
    
    print(f"\nFactors Applied:")
    for factor, value in rule_based_result['factors'].items():
        print(f"  • {factor.replace('_', ' ').title()}: {value}")
    
    # Get alternative routes
    flight_data = FlightData(
        origin="LAX",
        destination="JFK", 
        departure_date="2024-08-15",
        class_preference="business",
        flexible_dates=True
    )
    
    alternatives = points_optimizer.get_alternative_routes(flight_data)
    print(f"\nAlternative Routes:")
    for alt in alternatives:
        print(f"  • {alt['route']}: {alt['points_value']:,} points (saves {alt['savings']:,})")

def print_ai_analysis(ai_result):
    """Display AI strategic analysis."""
    print_divider("AI STRATEGIC ANALYSIS - CLAUDE RECOMMENDATIONS")
    
    print(f"AI Confidence Score: {ai_result['confidence']:.3f}")
    print(f"Analysis Timestamp: {ai_result['timestamp']}")
    
    if 'error' in ai_result:
        print(f"⚠️  Error: {ai_result['error']}")
    
    print(f"\nClaude's Strategic Insights:")
    print("-" * 40)
    print(ai_result['ai_analysis'])

def print_combined_recommendation(recommendation):
    """Display the combined recommendation."""
    print_divider("COMBINED RECOMMENDATION")
    
    print(f"Route: {recommendation.route}")
    print(f"Combined Score: {recommendation.combined_score:.3f}")
    print(f"Points Value: {recommendation.points_value:,}")
    
    print(f"\nScore Breakdown:")
    print(f"  • Rule-based Score: {recommendation.rule_based_score:.3f}")
    print(f"  • AI Score: {recommendation.ai_score:.3f}")
    print(f"  • Combined Score: {recommendation.combined_score:.3f}")
    print(f"  • AI Confidence: {recommendation.confidence:.3f}")

async def test_interactive_chat(ai_flightpath, flight_data):
    """Test interactive chat with travel hacker profile."""
    print_divider("INTERACTIVE CHAT - TRAVEL HACKER CONSULTATION")
    
    # Travel hacker specific questions
    questions = [
        "As an advanced travel hacker, what's the optimal booking strategy for this LAX-JFK route?",
        "Should I consider positioning flights or stopovers to maximize points earning?",
        "What are the best credit card strategies for this booking?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n🔸 Question {i}: {question}")
        response = await ai_flightpath.interactive_chat(question, flight_context=flight_data)
        print(f"💬 Claude: {response}")
        print("-" * 50)

async def main():
    """Main test function."""
    print_divider("AI FLIGHTPATH SYSTEM TEST")
    print("Testing LAX → JFK route optimization for advanced travel hacker")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize the system
    try:
        ai_flightpath = AIFlightPath()
        print("✅ AI FlightPath system initialized successfully")
        
        # Health check
        health = ai_flightpath.health_check()
        print(f"✅ System health check: {health}")
        
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return
    
    # Define flight data for advanced travel hacker
    flight_data = FlightData(
        origin="LAX",
        destination="JFK",
        departure_date="2024-08-15",
        return_date=None,  # One-way for flexibility
        passenger_count=1,
        class_preference="business",  # Advanced hacker optimizing for premium redemptions
        flexible_dates=True,
        budget_limit=150000  # High points budget for optimization
    )
    
    print(f"\n🎯 Target Flight Details:")
    print(f"  Route: {flight_data.origin} → {flight_data.destination}")
    print(f"  Date: {flight_data.departure_date}")
    print(f"  Class: {flight_data.class_preference}")
    print(f"  Flexible: {flight_data.flexible_dates}")
    print(f"  Budget: {flight_data.budget_limit:,} points")
    
    try:
        # Get comprehensive analysis
        recommendation = await ai_flightpath.get_flight_recommendations(flight_data)
        
        # Display technical analysis
        rule_based_result = ai_flightpath.points_optimizer.calculate_points_value(flight_data)
        print_technical_analysis(rule_based_result, ai_flightpath.points_optimizer)
        
        # Display AI analysis
        ai_result = await ai_flightpath.analyze_flight_strategy(flight_data)
        print_ai_analysis(ai_result)
        
        # Display combined recommendation
        print_combined_recommendation(recommendation)
        
        # Interactive chat testing
        await test_interactive_chat(ai_flightpath, flight_data)
        
        print_divider("TEST SUMMARY")
        print("✅ All tests completed successfully!")
        print(f"Final Recommendation Score: {recommendation.combined_score:.3f}")
        print(f"System performed {len(ai_flightpath.get_conversation_history())} chat interactions")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())