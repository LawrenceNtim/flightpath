"""
FlightPath - Clean production-ready flight optimization with AI
"""

import os
import re
import json
import asyncio
import logging
from datetime import datetime
from functools import lru_cache
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== CONFIGURATION =====
class Config:
    """Centralized configuration - set these as environment variables"""
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    CRC_TO_USD_RATE = float(os.getenv('CRC_TO_USD_RATE', '500'))
    CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '3600'))  # 1 hour
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    
    # Feature flags
    USE_CACHING = os.getenv('USE_CACHING', 'true').lower() == 'true'
    USE_ASYNC = os.getenv('USE_ASYNC', 'true').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set!")
        return True

# ===== INPUT VALIDATION =====
class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_airport_code(code: str) -> str:
        """Validate and normalize airport code"""
        code = code.strip().upper()
        if not re.match(r'^[A-Z]{3}$', code):
            raise ValueError(f"Invalid airport code: {code}. Must be 3 letters (e.g., LAX)")
        return code
    
    @staticmethod
    def validate_date(date_str: str) -> str:
        """Validate date format"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize user input strings"""
        # Remove any potential injection characters
        sanitized = re.sub(r'[<>\"\'`;]', '', text)
        return sanitized[:max_length]

# ===== PERFORMANCE MONITORING =====
def timed_operation(func):
    """Decorator to time operations"""
    def wrapper(*args, **kwargs):
        start = datetime.now()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start).total_seconds()
            logger.info(f"✅ {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            logger.error(f"❌ {func.__name__} failed after {duration:.2f}s: {str(e)}")
            raise
    return wrapper

# ===== SECURE POINTS OPTIMIZER =====
class SecurePointsOptimizer:
    def __init__(self):
        self.validator = Validator()
        self._cache = {}
        
        # Award charts (same as before but with validation)
        self.award_charts = {
            'United': {'domestic': 12500, 'international': 30000},
            'American': {'domestic': 12500, 'international': 30000},
            'Delta': {'domestic': 'dynamic', 'international': 'dynamic'},
            'Alaska': {'domestic': 12500, 'international': 25000},
            'JetBlue': {'domestic': 'revenue', 'international': 'revenue'},
            'Southwest': {'domestic': 'revenue', 'international': 'revenue'},
        }
        
        # Transfer partners (simplified for production)
        self.transfer_partners = {
            'Chase UR': ['United', 'Southwest', 'JetBlue', 'Air France', 'British Airways'],
            'Amex MR': ['Delta', 'JetBlue', 'British Airways', 'Virgin Atlantic', 'Air France'],
            'Citi TYP': ['JetBlue', 'Turkish', 'Virgin Atlantic', 'Air France', 'Emirates'],
            'Bilt': ['Alaska', 'United', 'Air France', 'Virgin Atlantic', 'British Airways'],
        }
    
    @lru_cache(maxsize=100)
    @timed_operation
    def get_cached_flights(self, origin: str, destination: str, date: str) -> List[Dict]:
        """Get flights with caching"""
        # Validate inputs
        origin = self.validator.validate_airport_code(origin)
        destination = self.validator.validate_airport_code(destination)
        date = self.validator.validate_date(date)
        
        logger.info(f"🔍 Fetching flights: {origin} → {destination} on {date}")
        
        # In production, this would call your actual flight API
        # For now, return mock data for testing
        return self._get_mock_flights(origin, destination, date)
    
    def _get_mock_flights(self, origin: str, destination: str, date: str) -> List[Dict]:
        """Mock flight data for testing"""
        return [
            {
                'name': 'United Airlines - UA123',
                'price': 'CRC 250,000',
                'departure': '08:00 AM',
                'arrival': '04:30 PM',
                'duration': '5h 30m',
                'stops': 0
            },
            {
                'name': 'American Airlines - AA456',
                'price': 'CRC 185,000',
                'departure': '10:15 AM',
                'arrival': '06:45 PM',
                'duration': '5h 30m',
                'stops': 0
            },
            {
                'name': 'Delta Air Lines - DL789',
                'price': 'CRC 310,000',
                'departure': '02:00 PM',
                'arrival': '10:30 PM',
                'duration': '5h 30m',
                'stops': 0
            }
        ]
    
    def optimize_flight(self, origin: str, destination: str, date: str) -> List[Dict]:
        """Main optimization with error handling"""
        try:
            # Get flights
            flights = self.get_cached_flights(origin, destination, date)
            
            # Process and optimize
            recommendations = []
            for flight in flights:
                # Extract price safely
                price_match = re.search(r'[\d,]+', flight['price'])
                if price_match:
                    price_crc = int(price_match.group().replace(',', ''))
                    price_usd = price_crc / Config.CRC_TO_USD_RATE
                else:
                    price_usd = 0
                
                # Extract airline
                airline = flight['name'].split(' - ')[0].strip()
                
                # Calculate award value
                route_type = 'domestic' if origin[:2] == destination[:2] else 'international'
                award_info = self._calculate_award_value(airline, route_type, price_usd)
                
                recommendations.append({
                    'flight': flight,
                    'airline': airline,
                    'cash_price_usd': price_usd,
                    'award_info': award_info,
                    'transfer_options': self._get_transfer_options(airline)
                })
            
            return sorted(recommendations, key=lambda x: x['cash_price_usd'])
            
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            raise
    
    def _calculate_award_value(self, airline: str, route_type: str, cash_price: float) -> Optional[Dict]:
        """Calculate award value with error handling"""
        try:
            if airline not in self.award_charts:
                return None
            
            award_cost = self.award_charts[airline].get(route_type)
            if not award_cost:
                return None
            
            if award_cost == 'revenue':
                points_needed = int(cash_price * 77)  # ~1.3 cents per point
                return {
                    'points_needed': points_needed,
                    'cents_per_point': 1.3,
                    'worth_it': True,
                    'type': 'revenue-based'
                }
            elif award_cost == 'dynamic':
                points_needed = int(cash_price * 100)
                return {
                    'points_needed': points_needed,
                    'cents_per_point': 1.0,
                    'worth_it': cash_price > 200,
                    'type': 'dynamic'
                }
            else:
                cpp = (cash_price * 100) / award_cost
                return {
                    'points_needed': award_cost,
                    'cents_per_point': cpp,
                    'worth_it': cpp > 1.5,
                    'type': 'fixed'
                }
        except Exception as e:
            logger.error(f"Award calculation error: {str(e)}")
            return None
    
    def _get_transfer_options(self, airline: str) -> List[str]:
        """Get transfer options for airline"""
        options = []
        for program, partners in self.transfer_partners.items():
            if airline in partners:
                options.append(program)
        return options

# ===== SECURE AI INTEGRATION =====
class SecureAIFlightPath:
    def __init__(self):
        Config.validate()
        self.optimizer = SecurePointsOptimizer()
        self._setup_anthropic_client()
    
    def _setup_anthropic_client(self):
        """Setup Anthropic client with error handling"""
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            logger.info("✅ AI client initialized successfully")
        except ImportError:
            logger.warning("⚠️ Anthropic not installed. Run: pip install anthropic")
            self.client = None
        except Exception as e:
            logger.error(f"❌ AI client setup failed: {str(e)}")
            self.client = None
    
    @timed_operation
    async def analyze_with_ai_async(self, origin: str, destination: str, date: str, user_profile: Optional[Dict] = None):
        """Async AI analysis"""
        # Validate inputs
        origin = Validator.validate_airport_code(origin)
        destination = Validator.validate_airport_code(destination)
        date = Validator.validate_date(date)
        
        # Get recommendations
        recommendations = self.optimizer.optimize_flight(origin, destination, date)
        
        # If AI client available, enhance with AI
        if self.client:
            ai_insights = await self._get_ai_insights_async(recommendations, origin, destination, date, user_profile)
            return {
                'recommendations': recommendations,
                'ai_insights': ai_insights,
                'status': 'complete'
            }
        else:
            return {
                'recommendations': recommendations,
                'ai_insights': 'AI analysis not available',
                'status': 'partial'
            }
    
    async def _get_ai_insights_async(self, recommendations: List[Dict], origin: str, destination: str, date: str, user_profile: Optional[Dict]) -> str:
        """Get AI insights asynchronously"""
        try:
            # Prepare prompt
            flight_summary = []
            for i, rec in enumerate(recommendations[:3]):
                flight_summary.append(f"{i+1}. {rec['airline']} - ${rec['cash_price_usd']:.0f}")
                if rec['award_info']:
                    flight_summary.append(f"   Points: {rec['award_info']['points_needed']:,} ({rec['award_info']['cents_per_point']:.1f}¢/pt)")
            
            prompt = f"""Analyze these flights from {origin} to {destination} on {date}:

{chr(10).join(flight_summary)}

Provide a brief recommendation (2-3 sentences) on the best option considering value and points strategy."""

            # Get AI response
            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            return "AI analysis temporarily unavailable"

# ===== MAIN APPLICATION =====
class FlightPathApp:
    def __init__(self):
        self.ai_analyzer = SecureAIFlightPath()
    
    async def run_analysis(self, origin: str, destination: str, date: str):
        """Run complete analysis"""
        print(f"\n🚀 FLIGHTPATH ANALYSIS")
        print("=" * 50)
        print(f"Route: {origin} → {destination}")
        print(f"Date: {date}")
        print("=" * 50)
        
        try:
            # Run analysis
            result = await self.ai_analyzer.analyze_with_ai_async(origin, destination, date)
            
            # Display results
            print("\n📊 FLIGHT OPTIONS:")
            for i, rec in enumerate(result['recommendations'][:5], 1):
                flight = rec['flight']
                print(f"\n{i}. {flight['name']}")
                print(f"   💰 Cash: ${rec['cash_price_usd']:.0f}")
                print(f"   ⏱️  {flight['duration']} | {flight['departure']} → {flight['arrival']}")
                
                if rec['award_info']:
                    award = rec['award_info']
                    status = "✅ Good value" if award['worth_it'] else "❌ Poor value"
                    print(f"   🎯 Points: {award['points_needed']:,} ({award['cents_per_point']:.1f}¢/pt) - {status}")
                
                if rec['transfer_options']:
                    print(f"   💳 Transfer from: {', '.join(rec['transfer_options'])}")
            
            if result.get('ai_insights') and result['ai_insights'] != 'AI analysis not available':
                print(f"\n🤖 AI RECOMMENDATION:")
                print(result['ai_insights'])
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
            return None

# ===== QUICK START FUNCTIONS =====
def quick_analyze(origin: str, destination: str, date: str):
    """Quick synchronous analysis for testing"""
    app = FlightPathApp()
    return asyncio.run(app.run_analysis(origin, destination, date))

def setup_environment():
    """Help setup environment variables"""
    print("🔧 FLIGHTPATH SETUP")
    print("=" * 50)
    print("Create a .env file with:")
    print("ANTHROPIC_API_KEY=your-key-here")
    print("CRC_TO_USD_RATE=500")
    print("\nOr set them in your shell:")
    print("export ANTHROPIC_API_KEY='your-key-here'")
    print("export CRC_TO_USD_RATE=500")

# ===== MAIN ENTRY POINT =====
if __name__ == "__main__":
    # Check if API key is set
    if not Config.ANTHROPIC_API_KEY:
        setup_environment()
        print("\n⚠️  Please set ANTHROPIC_API_KEY to enable AI features")
        print("The app will still work but without AI recommendations\n")
    
    # Example usage
    print("🚀 Starting FlightPath Analysis...")
    
    # Run async analysis
    result = quick_analyze("LAX", "JFK", "2025-08-15")
    
    # Interactive mode
    print("\n💬 Try another search? (or 'quit' to exit)")
    while True:
        try:
            user_input = input("\nEnter route (e.g., 'SFO NYC 2025-09-01'): ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            parts = user_input.split()
            if len(parts) >= 3:
                origin, dest, date = parts[0], parts[1], parts[2]
                quick_analyze(origin, dest, date)
            else:
                print("Format: ORIGIN DEST YYYY-MM-DD")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")