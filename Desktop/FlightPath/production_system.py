"""
FlightPath Production System - September 1st Launch Ready
Complete travel optimization with scraping, estimation, and AI intelligence
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional

# Import our production modules
from flightpath_v2_scraper import FlightPathOrchestrator
from accommodation_v2_scraper import AccommodationOrchestratorV2

class FlightPathProductionSystem:
    """Main production system orchestrator"""
    
    def __init__(self):
        self.flight_orchestrator = FlightPathOrchestrator()
        self.accommodation_orchestrator = AccommodationOrchestratorV2()
        
        # Comprehensive transfer partner database
        self.transfer_partners = {
            'Chase UR': {
                'airlines': ['United', 'Southwest', 'British Airways', 'Air France', 'Virgin Atlantic'],
                'hotels': ['Hyatt', 'IHG', 'Marriott'],
                'ratio': 1.0  # 1:1 transfer
            },
            'Amex MR': {
                'airlines': ['Delta', 'British Airways', 'Air France', 'Virgin Atlantic', 'ANA'],
                'hotels': ['Hilton', 'Marriott'],
                'ratio': 1.0  # Most are 1:1
            },
            'Citi TYP': {
                'airlines': ['Turkish', 'Virgin Atlantic', 'Air France', 'Singapore'],
                'hotels': [],
                'ratio': 1.0
            },
            'Bilt': {
                'airlines': ['United', 'American', 'Alaska', 'British Airways', 'Air France'],
                'hotels': ['Hyatt', 'IHG', 'Marriott'],
                'ratio': 1.0
            },
            'Capital One': {
                'airlines': ['Turkish', 'Air France', 'British Airways', 'Virgin Atlantic'],
                'hotels': ['Wyndham'],
                'ratio': 1.0
            }
        }
    
    async def optimize_complete_trip(self, trip_request: Dict) -> Dict:
        """Optimize a complete trip with flights and accommodation"""
        
        print("\n🌟 FLIGHTPATH PRODUCTION SYSTEM")
        print("=" * 60)
        print(f"📅 Trip: {trip_request['origin']} → {trip_request['destination']}")
        print(f"📆 Dates: {trip_request['departure']} to {trip_request['return']}")
        print(f"👥 Travelers: {trip_request['travelers']}")
        print(f"💰 Budget: ${trip_request.get('budget', 'Flexible')}")
        print("=" * 60)
        
        # Step 1: Search flights
        print("\n✈️  ANALYZING FLIGHTS...")
        outbound_flights = await self.flight_orchestrator.search_and_optimize(
            trip_request['origin'],
            trip_request['destination'],
            trip_request['departure'],
            trip_request.get('user_context', {})
        )
        
        return_flights = await self.flight_orchestrator.search_and_optimize(
            trip_request['destination'],
            trip_request['origin'],
            trip_request['return'],
            trip_request.get('user_context', {})
        )
        
        # Step 2: Search accommodation
        print("\n🏨 ANALYZING ACCOMMODATION...")
        accommodation = await self.accommodation_orchestrator.search_all(
            trip_request['destination'],
            trip_request['departure'],
            trip_request['return'],
            trip_request['travelers'],
            trip_request.get('preferences', {})
        )
        
        # Step 3: Generate comprehensive strategy
        strategy = self._generate_comprehensive_strategy(
            outbound_flights,
            return_flights,
            accommodation,
            trip_request
        )
        
        return strategy
    
    def _generate_comprehensive_strategy(self, outbound: Dict, return_flight: Dict, 
                                       accommodation: Dict, request: Dict) -> Dict:
        """Generate comprehensive optimization strategy"""
        
        # Extract best options
        best_out_cash = outbound['cash_flights'][0] if outbound['cash_flights'] else None
        best_ret_cash = return_flight['cash_flights'][0] if return_flight['cash_flights'] else None
        
        best_out_award = next((a for a in outbound['award_estimates'] if a['likely']), None)
        best_ret_award = next((a for a in return_flight['award_estimates'] if a['likely']), None)
        
        best_accommodation = accommodation['analysis']['recommendations'][0]['accommodation']
        
        # Calculate total costs
        travelers = request['travelers']
        
        # Cash option
        flight_cash = (best_out_cash['price'] + best_ret_cash['price']) * travelers if best_out_cash and best_ret_cash else 0
        
        # Award option
        if best_out_award and best_ret_award:
            flight_miles = (best_out_award['miles'] + best_ret_award['miles']) * travelers
            flight_taxes = 100 * travelers  # Estimate
        else:
            flight_miles = 0
            flight_taxes = 0
        
        # Build strategies
        strategies = []
        
        # Strategy 1: All Cash
        if flight_cash > 0:
            cash_total = flight_cash + best_accommodation.total_price
            strategies.append({
                'name': 'BUDGET OPTIMIZER',
                'description': 'Minimize points usage, pay cash',
                'flights': f"Cash flights: ${flight_cash}",
                'accommodation': f"{best_accommodation.name}: ${best_accommodation.total_price}",
                'total_cash': cash_total,
                'points_used': 0,
                'pros': ['Preserve points for future', 'Simple booking'],
                'cons': ['Higher out-of-pocket cost']
            })
        
        # Strategy 2: Points Maximizer
        if flight_miles > 0 and self._can_transfer_points(best_out_award['airline'], request.get('user_context', {}).get('points', {})):
            points_acc = next((a for a in accommodation['all_options'] if a.points_price), None)
            
            if points_acc:
                strategies.append({
                    'name': 'POINTS MAXIMIZER',
                    'description': 'Use maximum points for flights and hotel',
                    'flights': f"{best_out_award['airline']} awards: {flight_miles:,} miles + ${flight_taxes} taxes",
                    'accommodation': f"{points_acc.name}: {points_acc.points_price:,} points",
                    'total_cash': flight_taxes + (points_acc.total_price or 0),
                    'points_used': {'flights': flight_miles, 'hotel': points_acc.points_price},
                    'pros': ['Minimal cash outlay', 'High value redemptions'],
                    'cons': ['Depletes point balances', 'Award availability risk']
                })
        
        # Strategy 3: Hybrid
        if flight_miles > 0:
            cash_acc = accommodation['analysis']['best_value']
            strategies.append({
                'name': 'SMART HYBRID',
                'description': 'Use points for flights, cash for accommodation',
                'flights': f"Award flights: {flight_miles:,} miles + ${flight_taxes}",
                'accommodation': f"{cash_acc.name}: ${cash_acc.total_price}",
                'total_cash': flight_taxes + cash_acc.total_price,
                'points_used': {'flights': flight_miles},
                'pros': ['Balanced approach', 'Good value', 'Flexibility'],
                'cons': ['Still uses significant points']
            })
        
        # Add AI recommendation
        ai_rec = outbound.get('recommendation', 'Book the most flexible option given uncertain award availability.')
        
        return {
            'trip_summary': {
                'route': f"{request['origin']} → {request['destination']}",
                'dates': f"{request['departure']} to {request['return']}",
                'travelers': request['travelers'],
                'nights': (datetime.fromisoformat(request['return']) - datetime.fromisoformat(request['departure'])).days
            },
            'strategies': strategies,
            'ai_recommendation': ai_rec,
            'best_flight_options': {
                'cash': {'outbound': best_out_cash, 'return': best_ret_cash},
                'awards': {'outbound': best_out_award, 'return': best_ret_award}
            },
            'best_accommodation': {
                'overall': best_accommodation,
                'value': accommodation['analysis']['best_value'],
                'points': accommodation['analysis']['best_points']
            },
            'data_quality': {
                'flights': 'Scraped from Google Flights patterns',
                'awards': 'Estimated using historical patterns',
                'accommodation': 'Simulated based on market data',
                'confidence': 'Medium-High'
            }
        }
    
    def _can_transfer_points(self, airline: str, user_points: Dict) -> bool:
        """Check if user can transfer points to airline"""
        for program, balance in user_points.items():
            if program in self.transfer_partners:
                if airline in self.transfer_partners[program]['airlines']:
                    return True
        return False

# ===== PRODUCTION TEST =====
async def test_production_system():
    """Test the complete production system"""
    
    system = FlightPathProductionSystem()
    
    # Disney trip request
    trip_request = {
        'origin': 'LAX',
        'destination': 'MCO',  # Orlando
        'departure': '2025-08-15',
        'return': '2025-08-20',
        'travelers': 4,
        'budget': 4000,
        'user_context': {
            'points': {
                'Chase UR': 200000,
                'Amex MR': 150000,
                'United': 100000,
                'Marriott': 300000
            }
        },
        'preferences': {
            'family': True,
            'kitchen': True,
            'entire_place': True
        }
    }
    
    # Run optimization
    results = await system.optimize_complete_trip(trip_request)
    
    # Display results
    print("\n" + "=" * 60)
    print("🎯 OPTIMIZATION COMPLETE")
    print("=" * 60)
    
    print(f"\n📋 TRIP SUMMARY:")
    summary = results['trip_summary']
    print(f"   Route: {summary['route']}")
    print(f"   Dates: {summary['dates']} ({summary['nights']} nights)")
    print(f"   Travelers: {summary['travelers']}")
    
    print("\n💡 RECOMMENDED STRATEGIES:")
    for i, strategy in enumerate(results['strategies'], 1):
        print(f"\n{i}. {strategy['name']} - {strategy['description']}")
        print(f"   ✈️  {strategy['flights']}")
        print(f"   🏨 {strategy['accommodation']}")
        print(f"   💰 Total Cash Needed: ${strategy['total_cash']:,}")
        if strategy['points_used']:
            print(f"   💳 Points Used: {strategy['points_used']}")
        print(f"   ✅ Pros: {', '.join(strategy['pros'])}")
        print(f"   ⚠️  Cons: {', '.join(strategy['cons'])}")
    
    print(f"\n🤖 AI RECOMMENDATION:")
    print(f"   {results['ai_recommendation']}")
    
    print(f"\n📊 DATA SOURCES & CONFIDENCE:")
    for source, quality in results['data_quality'].items():
        print(f"   • {source}: {quality}")

# ===== MAIN ENTRY =====
if __name__ == "__main__":
    print("🚀 FLIGHTPATH PRODUCTION SYSTEM V2")
    print("Ready for September 1st Launch!")
    print("Using: Scraping + Estimation + AI Intelligence")
    print("=" * 60)
    
    # Ensure cache directories exist
    os.makedirs('.flightpath_cache', exist_ok=True)
    os.makedirs('.flightpath_cache/airbnb', exist_ok=True)
    os.makedirs('.flightpath_cache/hotels', exist_ok=True)
    
    # Run test
    asyncio.run(test_production_system())