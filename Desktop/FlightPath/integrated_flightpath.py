"""
Integrated FlightPath with FastFlights Engine
Production-ready for September 1st launch
"""

import os
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from flightpath_clean import (
    Config, Validator, SecurePointsOptimizer, 
    SecureAIFlightPath, FlightPathApp
)
from fast_flights_engine import (
    FastFlightsEngine, FastFlightsIntegration,
    CabinClass, AwardSearchMonitor
)

# ===== ENHANCED POINTS OPTIMIZER =====
class EnhancedPointsOptimizer(SecurePointsOptimizer):
    """Enhanced optimizer with FastFlights integration"""
    
    def __init__(self):
        super().__init__()
        self.award_engine = FastFlightsEngine()
        self.monitor = AwardSearchMonitor()
    
    async def optimize_flight_with_awards(self, origin: str, destination: str, date: str) -> List[Dict]:
        """Optimize flights with real-time award availability"""
        
        # Get base flight recommendations
        recommendations = self.optimize_flight(origin, destination, date)
        
        # Search for award availability
        start_time = datetime.now()
        awards = await self.award_engine.search_all_airlines(
            origin, destination, date, CabinClass.ECONOMY
        )
        search_duration = (datetime.now() - start_time).total_seconds()
        
        # Log metrics
        await self.monitor.log_search(origin, destination, search_duration, len(awards))
        
        # Match awards to flights
        for rec in recommendations:
            airline = rec['airline']
            
            # Find matching awards
            matching_awards = [a for a in awards if a.airline == airline]
            
            if matching_awards:
                # Get best award option
                best_award = self.award_engine.get_best_options(matching_awards, 1)[0]
                
                rec['award_availability'] = {
                    'available': True,
                    'miles_required': best_award.miles_required,
                    'seats_available': best_award.seats_available,
                    'award_type': best_award.award_type.value,
                    'taxes_fees': best_award.taxes_fees,
                    'value_score': best_award.value_score,
                    'flight_number': best_award.flight_number,
                    'departure_time': best_award.departure_time.strftime('%I:%M %p')
                }
                
                # Recalculate award value with real data
                cash_price = rec['cash_price_usd']
                miles = best_award.miles_required
                taxes = best_award.taxes_fees
                
                # Calculate true cents per point including taxes
                true_cpp = ((cash_price - taxes) * 100) / miles if miles > 0 else 0
                
                rec['award_info'] = {
                    'points_needed': miles,
                    'cents_per_point': true_cpp,
                    'worth_it': true_cpp > 1.5,
                    'type': best_award.award_type.value,
                    'availability': best_award.seats_available
                }
            else:
                rec['award_availability'] = {
                    'available': False,
                    'reason': 'No award seats available'
                }
        
        return recommendations

# ===== ENHANCED AI FLIGHTPATH =====
class EnhancedAIFlightPath(SecureAIFlightPath):
    """Enhanced AI analysis with award availability"""
    
    def __init__(self):
        super().__init__()
        self.optimizer = EnhancedPointsOptimizer()
    
    async def analyze_with_ai_and_awards(self, origin: str, destination: str, 
                                       date: str, user_profile: Optional[Dict] = None):
        """AI analysis with real-time award data"""
        
        # Validate inputs
        origin = Validator.validate_airport_code(origin)
        destination = Validator.validate_airport_code(destination)
        date = Validator.validate_date(date)
        
        # Get recommendations with awards
        recommendations = await self.optimizer.optimize_flight_with_awards(
            origin, destination, date
        )
        
        # Enhance with AI if available
        if self.client:
            ai_insights = await self._get_enhanced_ai_insights(
                recommendations, origin, destination, date, user_profile
            )
            return {
                'recommendations': recommendations,
                'ai_insights': ai_insights,
                'status': 'complete',
                'metrics': self.optimizer.monitor.get_metrics()
            }
        else:
            return {
                'recommendations': recommendations,
                'ai_insights': 'AI analysis not available',
                'status': 'partial',
                'metrics': self.optimizer.monitor.get_metrics()
            }
    
    async def _get_enhanced_ai_insights(self, recommendations: List[Dict], 
                                      origin: str, destination: str, 
                                      date: str, user_profile: Optional[Dict]) -> str:
        """Get AI insights with award availability context"""
        try:
            # Prepare enhanced prompt with award data
            flight_summary = []
            for i, rec in enumerate(recommendations[:3]):
                summary = f"{i+1}. {rec['airline']} - ${rec['cash_price_usd']:.0f}"
                
                if rec.get('award_availability', {}).get('available'):
                    award = rec['award_availability']
                    summary += f"\n   ✅ Award available: {award['miles_required']:,} miles + ${award['taxes_fees']:.0f}"
                    summary += f"\n   Seats: {award['seats_available']} ({award['award_type']})"
                else:
                    summary += "\n   ❌ No award availability"
                
                flight_summary.append(summary)
            
            prompt = f"""Analyze these flights from {origin} to {destination} on {date} with real-time award availability:

{chr(10).join(flight_summary)}

Provide a brief recommendation (2-3 sentences) considering both cash prices and award availability. 
Focus on the best value option and mention if awards are worth it."""

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

# ===== ENHANCED MAIN APP =====
class EnhancedFlightPathApp(FlightPathApp):
    """Enhanced app with full integration"""
    
    def __init__(self):
        self.ai_analyzer = EnhancedAIFlightPath()
    
    async def run_enhanced_analysis(self, origin: str, destination: str, date: str):
        """Run enhanced analysis with awards"""
        print(f"\n🚀 FLIGHTPATH ENHANCED ANALYSIS")
        print("=" * 50)
        print(f"Route: {origin} → {destination}")
        print(f"Date: {date}")
        print("=" * 50)
        
        try:
            # Run enhanced analysis
            result = await self.ai_analyzer.analyze_with_ai_and_awards(
                origin, destination, date
            )
            
            # Display results
            print("\n📊 FLIGHT OPTIONS WITH AWARD AVAILABILITY:")
            for i, rec in enumerate(result['recommendations'][:5], 1):
                flight = rec['flight']
                print(f"\n{i}. {flight['name']}")
                print(f"   💰 Cash: ${rec['cash_price_usd']:.0f}")
                print(f"   ⏱️  {flight['duration']} | {flight['departure']} → {flight['arrival']}")
                
                # Show award availability
                if rec.get('award_availability', {}).get('available'):
                    award = rec['award_availability']
                    print(f"   ✅ AWARD AVAILABLE: {award['miles_required']:,} miles + ${award['taxes_fees']:.0f}")
                    print(f"   📊 {award['seats_available']} seats | {award['award_type']} | Score: {award['value_score']:.0f}")
                else:
                    print(f"   ❌ No award seats available")
                
                # Show award value analysis
                if rec.get('award_info'):
                    award_info = rec['award_info']
                    status = "✅ Good value" if award_info['worth_it'] else "⚠️  Poor value"
                    print(f"   💎 Value: {award_info['cents_per_point']:.1f}¢/pt - {status}")
                
                if rec['transfer_options']:
                    print(f"   💳 Transfer from: {', '.join(rec['transfer_options'])}")
            
            # Show AI insights
            if result.get('ai_insights') and result['ai_insights'] != 'AI analysis not available':
                print(f"\n🤖 AI RECOMMENDATION:")
                print(result['ai_insights'])
            
            # Show metrics
            if result.get('metrics'):
                metrics = result['metrics']
                print(f"\n📈 PERFORMANCE METRICS:")
                print(f"   Total searches: {metrics['searches']}")
                print(f"   Avg response time: {metrics['avg_response_time']:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
            return None
    
    async def run_calendar_analysis(self, origin: str, destination: str, 
                                  start_date: str, days: int = 7):
        """Run calendar view analysis"""
        print(f"\n📅 CALENDAR VIEW: {origin} → {destination}")
        print("=" * 50)
        
        engine = FastFlightsEngine()
        calendar = await engine.get_calendar_view(
            origin, destination, start_date, days
        )
        
        for date, awards in calendar.items():
            if awards:
                best = engine.get_best_options(awards, 1)[0]
                print(f"{date}: {len(awards):2d} options | Best: {best.airline} {best.miles_required:,} miles")
            else:
                print(f"{date}: No availability")

# ===== PRODUCTION HELPERS =====
def check_production_readiness():
    """Check if system is ready for production"""
    print("🔍 Production Readiness Check")
    print("=" * 50)
    
    checks = {
        "Anthropic API": bool(Config.ANTHROPIC_API_KEY),
        "Redis Cache": bool(os.getenv('REDIS_URL')),
        "Error Handling": True,  # Always enabled
        "Performance Monitoring": True,  # Always enabled
        "Caching Enabled": Config.USE_CACHING,
        "Async Enabled": Config.USE_ASYNC
    }
    
    for check, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check}: {'Ready' if status else 'Not configured'}")
    
    ready = all(checks.values())
    print(f"\n{'✅ READY FOR PRODUCTION' if ready else '⚠️  Some items need configuration'}")
    
    return ready

# ===== QUICK START FUNCTIONS =====
async def quick_enhanced_analyze(origin: str, destination: str, date: str):
    """Quick enhanced analysis"""
    app = EnhancedFlightPathApp()
    return await app.run_enhanced_analysis(origin, destination, date)

async def quick_calendar_view(origin: str, destination: str, start_date: str):
    """Quick calendar view"""
    app = EnhancedFlightPathApp()
    return await app.run_calendar_analysis(origin, destination, start_date)

# ===== MAIN ENTRY POINT =====
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Check production readiness
    if not check_production_readiness():
        print("\n⚠️  Please configure missing items before launch")
    
    print("\n🚀 Starting Enhanced FlightPath with FastFlights...")
    
    # Demo with real award search
    asyncio.run(quick_enhanced_analyze("LAX", "JFK", "2025-08-15"))
    
    # Demo calendar view
    print("\n" + "="*50)
    asyncio.run(quick_calendar_view("LAX", "JFK", "2025-08-15"))
    
    # Interactive mode
    print("\n💬 Interactive Mode (type 'help' for commands)")
    while True:
        try:
            user_input = input("\nCommand: ").strip().lower()
            
            if user_input in ['quit', 'exit', 'q']:
                break
            elif user_input == 'help':
                print("Commands:")
                print("  search LAX JFK 2025-08-15  - Search specific date")
                print("  calendar LAX JFK 2025-08-15 - Show 7-day calendar")
                print("  metrics                     - Show performance metrics")
                print("  quit                        - Exit")
            elif user_input.startswith('search '):
                parts = user_input.split()[1:]
                if len(parts) >= 3:
                    asyncio.run(quick_enhanced_analyze(parts[0], parts[1], parts[2]))
            elif user_input.startswith('calendar '):
                parts = user_input.split()[1:]
                if len(parts) >= 3:
                    asyncio.run(quick_calendar_view(parts[0], parts[1], parts[2]))
            elif user_input == 'metrics':
                monitor = AwardSearchMonitor()
                print(f"Metrics: {monitor.get_metrics()}")
            else:
                print("Unknown command. Type 'help' for options.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")