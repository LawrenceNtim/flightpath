#!/usr/bin/env python3
"""
Test script for enhanced FlightPath system
"""

import asyncio
from nlp_parser import FlightQueryParser
from context_engine import ContextEngine
from ai_flightpath import AIFlightPath, FlightData

async def test_enhanced_system():
    """Test all enhanced components"""
    print("🚀 Testing Enhanced FlightPath System")
    print("=" * 50)
    
    # Test 1: NLP Parser
    print("\n1. Testing Natural Language Parser")
    parser = FlightQueryParser()
    
    test_queries = [
        "wedding by 12pm August 15th, leave Sunday from LA to NY",
        "business trip from Miami to Denver next Tuesday, first class",
        "family vacation to Orlando, 4 passengers, flexible dates",
        "cheap flight from Vegas to Phoenix this weekend"
    ]
    
    for query in test_queries:
        result = parser.parse_query(query)
        print(f"   Query: {query}")
        print(f"   → {result['origin']} to {result['destination']}")
        print(f"   → Date: {result['departure_date']}, Class: {result['class_preference']}")
        print(f"   → Confidence: {result['confidence']:.2f}")
        print()
    
    # Test 2: Context Engine
    print("\n2. Testing Context Engine")
    context_engine = ContextEngine()
    
    context = context_engine.get_context(
        origin='LAX',
        destination='JFK',
        departure_date='2024-08-15',
        return_date='2024-08-22',
        passenger_count=2,
        class_preference='business'
    )
    
    print(f"   Context Analysis:")
    print(f"   → Insights: {len(context.insights)}")
    print(f"   → Warnings: {len(context.warnings)}")
    print(f"   → Suggestions: {len(context.suggestions)}")
    print(f"   → Confidence: {context.confidence:.2f}")
    
    if context.insights:
        print(f"   → Sample insight: {context.insights[0].title}")
    
    # Test 3: AI FlightPath Integration
    print("\n3. Testing AI FlightPath Integration")
    ai_flightpath = AIFlightPath()
    
    flight_data = FlightData(
        origin='LAX',
        destination='JFK',
        departure_date='2024-08-15',
        return_date='2024-08-22',
        passenger_count=2,
        class_preference='business',
        flexible_dates=True,
        budget_limit=100000
    )
    
    recommendation = await ai_flightpath.get_flight_recommendations(flight_data)
    
    print(f"   Flight Recommendation:")
    print(f"   → Route: {recommendation.route}")
    print(f"   → Combined Score: {recommendation.combined_score:.3f}")
    print(f"   → Points Required: {recommendation.points_value:,}")
    print(f"   → AI Confidence: {recommendation.confidence:.3f}")
    
    # Test 4: Enhanced Chat with Context
    print("\n4. Testing Enhanced Chat")
    
    chat_response = await ai_flightpath.interactive_chat(
        "What's the best strategy for this LAX to JFK flight?",
        flight_context=flight_data
    )
    
    print(f"   Chat Response Length: {len(chat_response)} characters")
    print(f"   Sample: {chat_response[:200]}...")
    
    print("\n" + "=" * 50)
    print("✅ All enhanced components working successfully!")
    print("\n🌐 Access the enhanced web interface at: http://localhost:5002")
    print("\n📋 Features available:")
    print("   • Natural language search: 'wedding by 12pm August 15th, leave Sunday from LA to NY'")
    print("   • Voice input (Chrome/Edge browsers)")
    print("   • Context-aware insights about weather, events, pricing")
    print("   • Enhanced AI chat with flight context")
    print("   • Traditional form search as fallback")

if __name__ == "__main__":
    asyncio.run(test_enhanced_system())