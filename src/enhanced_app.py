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

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_flightpath import AIFlightPath, FlightData
from nlp_parser import FlightQueryParser
from context_engine import ContextEngine

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize systems
ai_flightpath = None
nlp_parser = None
context_engine = None

def initialize_systems():
    """Initialize all AI systems."""
    global ai_flightpath, nlp_parser, context_engine
    
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
        health_status['context_engine']
    ])
    
    return jsonify({
        'success': all_healthy,
        'health': health_status
    })

@app.route('/api/examples')
def get_examples():
    """Get example queries for the interface."""
    examples = [
        {
            'query': 'Wedding by 12pm August 15th, leave Sunday from LA to NY',
            'description': 'Event-based travel with time constraints'
        },
        {
            'query': 'Business trip from Miami to Denver next Tuesday, first class',
            'description': 'Business travel with class preference'
        },
        {
            'query': 'Family vacation to Orlando from Boston, 4 passengers, flexible dates',
            'description': 'Family travel with flexibility'
        },
        {
            'query': 'Emergency flight from Seattle to Atlanta ASAP',
            'description': 'Urgent travel requirement'
        },
        {
            'query': 'Cheap flight from Vegas to Phoenix this weekend',
            'description': 'Budget-conscious travel'
        },
        {
            'query': 'Conference in Dallas from Portland Monday, return Friday',
            'description': 'Round-trip business travel'
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
        print("✨ Features: Natural Language Processing, Context Awareness, Voice Input")
        print("📍 Access the application at: http://localhost:5003")
        app.run(debug=True, host='0.0.0.0', port=5003)
    else:
        print("❌ Failed to initialize enhanced systems")
        print("Please check your dependencies and configuration")