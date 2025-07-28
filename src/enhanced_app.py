#!/usr/bin/env python3
"""
Enhanced FlightPath Web Application
Features natural language parsing, context awareness, and voice input
"""

import asyncio
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sys
import os

# Add current and parent directory to path to import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(current_dir)
sys.path.append(parent_dir)

from ai_flightpath import AIFlightPath, FlightData
from nlp_parser import FlightQueryParser
from context_engine import ContextEngine
from trip_orchestration_integration import TripOrchestrationIntegration

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize systems
ai_flightpath = None
nlp_parser = None
context_engine = None
trip_orchestration = None

def initialize_systems():
    """Initialize all AI systems."""
    global ai_flightpath, nlp_parser, context_engine, trip_orchestration
    
    try:
        # Initialize AI FlightPath
        ai_flightpath = AIFlightPath()
        logger.info("✅ AI FlightPath system initialized")
        
        # Initialize NLP Parser
        nlp_parser = FlightQueryParser()
        logger.info("✅ NLP Parser initialized")
        
        # Initialize Context Engine
        context_engine = ContextEngine()
        logger.info("✅ Context Engine initialized")
        
        # Initialize Trip Orchestration
        trip_orchestration = TripOrchestrationIntegration()
        logger.info("✅ Trip Orchestration system initialized")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize systems: {e}")
        return False

@app.route('/')
def index():
    """Enhanced main page with NLP and voice input."""
    return render_template('enhanced_index.html')

@app.route('/api/parse', methods=['POST'])
def parse_natural_language():
    """API endpoint for natural language parsing."""
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'No query provided'
            }), 400
        
        # Parse the natural language query
        parsed_query = nlp_parser.parse_query(query)
        
        # Convert to FlightData format
        flight_data = nlp_parser.convert_to_flight_data(parsed_query)
        
        return jsonify({
            'success': True,
            'parsed_query': parsed_query,
            'flight_data': flight_data
        })
        
    except Exception as e:
        logger.error(f"Error parsing natural language: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/context', methods=['POST'])
def get_context():
    """API endpoint for travel context insights."""
    try:
        data = request.json
        
        # Extract flight data
        origin = data.get('origin', '')
        destination = data.get('destination', '')
        departure_date = data.get('departure_date', '')
        return_date = data.get('return_date')
        passenger_count = int(data.get('passenger_count', 1))
        class_preference = data.get('class_preference', 'economy')
        
        if not all([origin, destination, departure_date]):
            return jsonify({
                'success': False,
                'error': 'Origin, destination, and departure date are required'
            }), 400
        
        # Get context
        context = context_engine.get_context(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            passenger_count=passenger_count,
            class_preference=class_preference
        )
        
        # Convert context to JSON-serializable format
        context_dict = {
            'external_context': context.external_context,
            'internal_context': context.internal_context,
            'insights': [
                {
                    'type': insight.type,
                    'category': insight.category,
                    'title': insight.title,
                    'description': insight.description,
                    'impact': insight.impact,
                    'source': insight.source,
                    'relevance_score': insight.relevance_score
                }
                for insight in context.insights
            ],
            'warnings': context.warnings,
            'suggestions': context.suggestions,
            'confidence': context.confidence
        }
        
        return jsonify({
            'success': True,
            'context': context_dict
        })
        
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search_flights():
    """Enhanced API endpoint for flight search with context integration."""
    try:
        data = request.json
        
        # Create FlightData object
        flight_data = FlightData(
            origin=data.get('origin', '').upper(),
            destination=data.get('destination', '').upper(),
            departure_date=data.get('departure_date'),
            return_date=data.get('return_date'),
            passenger_count=int(data.get('passenger_count', 1)),
            class_preference=data.get('class_preference', 'economy'),
            flexible_dates=data.get('flexible_dates', False),
            budget_limit=int(data.get('budget_limit', 0)) if data.get('budget_limit') else None
        )
        
        # Get recommendations asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            recommendation = loop.run_until_complete(
                ai_flightpath.get_flight_recommendations(flight_data)
            )
            
            # Get context insights
            context = context_engine.get_context(
                origin=flight_data.origin,
                destination=flight_data.destination,
                departure_date=flight_data.departure_date,
                return_date=flight_data.return_date,
                passenger_count=flight_data.passenger_count,
                class_preference=flight_data.class_preference
            )
            
            # Enhanced recommendation with context
            enhanced_recommendation = {
                'route': recommendation.route,
                'combined_score': round(recommendation.combined_score, 3),
                'confidence': round(recommendation.confidence, 3),
                'points_value': recommendation.points_value,
                'ai_insights': recommendation.ai_insights,
                'rule_based_score': round(recommendation.rule_based_score, 3),
                'ai_score': round(recommendation.ai_score, 3),
                'context_insights': len(context.insights),
                'context_warnings': len(context.warnings),
                'context_confidence': round(context.confidence, 3)
            }
            
            # Format response
            response = {
                'success': True,
                'recommendation': enhanced_recommendation,
                'flight_data': {
                    'origin': flight_data.origin,
                    'destination': flight_data.destination,
                    'departure_date': flight_data.departure_date,
                    'return_date': flight_data.return_date,
                    'class_preference': flight_data.class_preference,
                    'passenger_count': flight_data.passenger_count
                }
            }
            
            return jsonify(response)
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in flight search: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Enhanced API endpoint for interactive chat with context awareness."""
    try:
        data = request.json
        message = data.get('message', '')
        
        # Create flight context if provided
        flight_context = None
        if data.get('flight_context'):
            ctx = data['flight_context']
            flight_context = FlightData(
                origin=ctx.get('origin', ''),
                destination=ctx.get('destination', ''),
                departure_date=ctx.get('departure_date', ''),
                return_date=ctx.get('return_date'),
                passenger_count=ctx.get('passenger_count', 1),
                class_preference=ctx.get('class_preference', 'economy'),
                flexible_dates=ctx.get('flexible_dates', False),
                budget_limit=ctx.get('budget_limit')
            )
        
        # Get enhanced context if flight context is provided
        context_info = ""
        if flight_context and flight_context.origin and flight_context.destination:
            try:
                context = context_engine.get_context(
                    origin=flight_context.origin,
                    destination=flight_context.destination,
                    departure_date=flight_context.departure_date,
                    return_date=flight_context.return_date,
                    passenger_count=flight_context.passenger_count,
                    class_preference=flight_context.class_preference
                )
                
                # Add context insights to the message
                if context.insights:
                    context_info = f"\n\nRelevant Context:\n"
                    for insight in context.insights[:3]:  # Top 3 insights
                        context_info += f"- {insight.title}: {insight.description}\n"
                
                if context.warnings:
                    context_info += f"\nWarnings: {'; '.join(context.warnings[:2])}\n"
                
                if context.suggestions:
                    context_info += f"\nSuggestions: {'; '.join(context.suggestions[:2])}\n"
                    
            except Exception as e:
                logger.error(f"Error getting context for chat: {e}")
        
        # Enhance the message with context
        enhanced_message = message + context_info
        
        # Get chat response asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(
                ai_flightpath.interactive_chat(enhanced_message, flight_context)
            )
            
            return jsonify({
                'success': True,
                'response': response,
                'context_provided': bool(context_info)
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/voice-test', methods=['POST'])
def voice_test():
    """Test endpoint for voice input processing."""
    try:
        data = request.json
        transcript = data.get('transcript', '')
        
        if not transcript:
            return jsonify({
                'success': False,
                'error': 'No transcript provided'
            }), 400
        
        # Process with NLP parser
        parsed_query = nlp_parser.parse_query(transcript)
        
        return jsonify({
            'success': True,
            'transcript': transcript,
            'parsed_query': parsed_query
        })
        
    except Exception as e:
        logger.error(f"Error processing voice input: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health')
def health_check():
    """Enhanced health check endpoint."""
    health_status = {
        'ai_flightpath': ai_flightpath is not None,
        'nlp_parser': nlp_parser is not None,
        'context_engine': context_engine is not None,
        'trip_orchestration': trip_orchestration is not None,
        'timestamp': datetime.now().isoformat()
    }
    
    if ai_flightpath:
        try:
            ai_health = ai_flightpath.health_check()
            health_status.update(ai_health)
        except Exception as e:
            health_status['ai_error'] = str(e)
    
    all_healthy = all([
        health_status['ai_flightpath'],
        health_status['nlp_parser'],
        health_status['context_engine'],
        health_status['trip_orchestration']
    ])
    
    return jsonify({
        'success': all_healthy,
        'health': health_status
    })

@app.route('/api/orchestrate-trip', methods=['POST'])
def orchestrate_trip():
    """API endpoint for complete trip orchestration."""
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'No query provided'
            }), 400
        
        # Run trip orchestration asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                trip_orchestration.orchestrate_complete_trip(query)
            )
            
            # Convert result to JSON-serializable format
            orchestration_result = {
                'trip_id': result.trip_id,
                'original_query': result.original_query,
                'parsed_request': result.parsed_request,
                'budget_optimization': {
                    'optimized_budget': {k: float(v) for k, v in result.budget_optimization['optimized_budget'].items()},
                    'total_cost': result.budget_optimization['total_cost'],
                    'savings': result.budget_optimization['savings'],
                    'efficiency_score': result.budget_optimization['efficiency_score'],
                    'recommendations': result.budget_optimization['recommendations'],
                    'warnings': result.budget_optimization['warnings']
                },
                'orchestration_result': {
                    'trip_id': result.orchestration_result.trip_id,
                    'segments': [
                        {
                            'origin': seg.origin,
                            'destination': seg.destination,
                            'start_date': seg.start_date,
                            'end_date': seg.end_date,
                            'accommodation_type': seg.accommodation_type.value,
                            'transportation_mode': seg.transportation_mode.value
                        }
                        for seg in result.orchestration_result.segments
                    ],
                    'activities': [
                        {
                            'name': act.name,
                            'date': act.date,
                            'duration_hours': act.duration_hours,
                            'cost': float(act.cost),
                            'category': act.category,
                            'booking_required': act.booking_required
                        }
                        for act in result.orchestration_result.activities
                    ],
                    'special_requirements': [
                        {
                            'type': req.type.value,
                            'description': req.description,
                            'cost_impact': float(req.cost_impact),
                            'handled': req.handled
                        }
                        for req in result.orchestration_result.special_requirements
                    ],
                    'cost_breakdown': {k: float(v) for k, v in result.orchestration_result.cost_breakdown.items()},
                    'optimization_score': result.orchestration_result.optimization_score,
                    'tax_savings': float(result.orchestration_result.tax_savings)
                },
                'daily_schedule': result.daily_schedule,
                'booking_checklist': result.booking_checklist,
                'total_cost': float(result.total_cost),
                'tax_savings': float(result.tax_savings),
                'efficiency_score': result.efficiency_score,
                'confidence_score': result.confidence_score
            }
            
            return jsonify({
                'success': True,
                'result': orchestration_result
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in trip orchestration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/examples')
def get_examples():
    """Get example queries for the interface."""
    examples = [
        {
            'query': 'Wedding by 12pm August 15th, leave Sunday from LA to NY',
            'description': 'Event-based travel with time constraints',
            'type': 'flight'
        },
        {
            'query': 'Business trip from Miami to Denver next Tuesday, first class',
            'description': 'Business travel with class preference',
            'type': 'flight'
        },
        {
            'query': 'Family vacation to Orlando from Boston, 4 passengers, flexible dates',
            'description': 'Family travel with flexibility',
            'type': 'flight'
        },
        {
            'query': '$4000 budget, family of 4, SF to Disneyland, flexible dates',
            'description': 'Complete family trip orchestration with budget constraints',
            'type': 'trip'
        },
        {
            'query': 'LA and SF for 2 weeks, sister hosting, bring dog, music conference',
            'description': 'Complex multi-city trip with pet and business requirements',
            'type': 'trip'
        },
        {
            'query': 'Martha\'s Vineyard weekend from NYC, $5000 budget, 5-bedroom house in Oak Bluffs',
            'description': 'Luxury weekend getaway with specific accommodation needs',
            'type': 'trip'
        },
        {
            'query': 'Japan trip $1500 budget, United flights only, 40,000 points available from SF',
            'description': 'International trip with airline and points constraints',
            'type': 'trip'
        }
    ]
    
    return jsonify({
        'success': True,
        'examples': examples
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Initialize all systems on startup
    if initialize_systems():
        print("🚀 Enhanced FlightPath Web Interface starting...")
        print("✨ Features: Natural Language Processing, Context Awareness, Voice Input, Trip Orchestration")
        print("🎯 New: Complete trip planning with budget optimization, accommodation booking, and activity planning")
        print("📍 Access the application at: http://localhost:5003")
        app.run(debug=True, host='0.0.0.0', port=5003)
    else:
        print("❌ Failed to initialize enhanced systems")
        print("Please check your dependencies and configuration")