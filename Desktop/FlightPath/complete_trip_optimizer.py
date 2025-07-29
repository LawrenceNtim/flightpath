"""
Complete Trip Optimizer - FlightPath + Accommodation
Optimizes entire trip budget across flights and stays
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Import our engines
from integrated_flightpath import EnhancedFlightPathApp, EnhancedPointsOptimizer
from accommodation_engine import TripOptimizer, AccommodationOrchestrator
from fast_flights_engine import FastFlightsEngine, CabinClass

# ===== COMPLETE TRIP OPTIMIZER =====
@dataclass
class TripComponent:
    """Individual trip component (flight or accommodation)"""
    type: str  # 'flight' or 'accommodation'
    description: str
    cash_cost: float
    points_cost: Optional[int] = None
    points_program: Optional[str] = None
    value_score: float = 0.0
    details: Dict = None

class CompleteTripOptimizer:
    """Optimizes complete trip including flights and accommodation"""
    
    def __init__(self):
        self.flight_app = EnhancedFlightPathApp()
        self.flight_engine = FastFlightsEngine()
        self.trip_optimizer = TripOptimizer()
        self.accommodation_engine = AccommodationOrchestrator()
    
    async def optimize_complete_trip(self, 
                                   origin: str,
                                   destination: str,
                                   departure_date: str,
                                   return_date: str,
                                   travelers: int,
                                   total_budget: float,
                                   user_points: Optional[Dict] = None,
                                   preferences: Optional[Dict] = None) -> Dict:
        """Optimize complete trip within budget constraints"""
        
        print(f"\n🌟 COMPLETE TRIP OPTIMIZATION")
        print("=" * 50)
        print(f"Route: {origin} → {destination}")
        print(f"Dates: {departure_date} to {return_date}")
        print(f"Travelers: {travelers}")
        print(f"Budget: ${total_budget:,.0f}")
        print("=" * 50)
        
        # Calculate trip duration
        nights = (datetime.fromisoformat(return_date) - datetime.fromisoformat(departure_date)).days
        
        # Step 1: Get flight options
        print("\n✈️  Searching flights...")
        flight_options = await self._get_flight_options(
            origin, destination, departure_date, return_date, travelers
        )
        
        # Step 2: Get accommodation options
        print("\n🏨 Searching accommodations...")
        accommodation_options = await self._get_accommodation_options(
            destination, departure_date, return_date, travelers, preferences
        )
        
        # Step 3: Find optimal combinations
        print("\n🔄 Finding optimal combinations...")
        optimal_combos = self._find_optimal_combinations(
            flight_options, accommodation_options, total_budget, user_points
        )
        
        # Step 4: Generate recommendations
        recommendations = self._generate_recommendations(
            optimal_combos, total_budget, nights, travelers
        )
        
        return recommendations
    
    async def _get_flight_options(self, origin: str, destination: str, 
                                 departure_date: str, return_date: str, 
                                 travelers: int) -> List[TripComponent]:
        """Get flight options with pricing"""
        
        # Search outbound flights
        outbound_result = await self.flight_app.ai_analyzer.analyze_with_ai_and_awards(
            origin, destination, departure_date
        )
        
        # Search return flights
        return_result = await self.flight_app.ai_analyzer.analyze_with_ai_and_awards(
            destination, origin, return_date
        )
        
        # Combine best options
        flight_options = []
        
        # Get top 3 combinations
        for out_rec in outbound_result['recommendations'][:3]:
            for ret_rec in return_result['recommendations'][:3]:
                # Calculate total cost
                total_cash = (out_rec['cash_price_usd'] + ret_rec['cash_price_usd']) * travelers
                
                # Check if awards available for both
                out_award = out_rec.get('award_availability', {})
                ret_award = ret_rec.get('award_availability', {})
                
                if out_award.get('available') and ret_award.get('available'):
                    total_points = (out_award['miles_required'] + ret_award['miles_required']) * travelers
                    total_taxes = (out_award['taxes_fees'] + ret_award['taxes_fees']) * travelers
                    
                    # Create points option
                    flight_options.append(TripComponent(
                        type='flight',
                        description=f"{out_rec['airline']} (out) + {ret_rec['airline']} (return)",
                        cash_cost=total_taxes,  # Just taxes for award flights
                        points_cost=total_points,
                        points_program=out_rec['transfer_options'][0] if out_rec.get('transfer_options') else 'Airline',
                        value_score=85,  # High score for award availability
                        details={
                            'outbound': out_rec['flight'],
                            'return': ret_rec['flight'],
                            'award_type': out_award['award_type']
                        }
                    ))
                
                # Always add cash option
                flight_options.append(TripComponent(
                    type='flight',
                    description=f"{out_rec['airline']} (out) + {ret_rec['airline']} (return)",
                    cash_cost=total_cash,
                    value_score=70,
                    details={
                        'outbound': out_rec['flight'],
                        'return': ret_rec['flight']
                    }
                ))
        
        return flight_options[:6]  # Return top 6 options
    
    async def _get_accommodation_options(self, destination: str, checkin: str, 
                                       checkout: str, travelers: int,
                                       preferences: Optional[Dict]) -> List[TripComponent]:
        """Get accommodation options"""
        
        # Search all sources
        accommodations = await self.accommodation_engine.search_all(
            destination, checkin, checkout, travelers, preferences=preferences
        )
        
        # Convert to trip components
        acc_options = []
        
        # Get best from each category
        for source, listings in accommodations.items():
            for acc in listings[:3]:  # Top 3 from each source
                if acc.price_type.value == 'cash':
                    acc_options.append(TripComponent(
                        type='accommodation',
                        description=f"{acc.name} ({source})",
                        cash_cost=acc.cash_price + acc.taxes_fees,
                        value_score=acc.value_score,
                        details={
                            'property': acc,
                            'nights': acc.total_nights,
                            'amenities': acc.amenities[:5]
                        }
                    ))
                else:  # Points option
                    acc_options.append(TripComponent(
                        type='accommodation',
                        description=f"{acc.name} ({source})",
                        cash_cost=acc.taxes_fees,  # Just taxes/fees
                        points_cost=acc.points_required,
                        points_program='Marriott',
                        value_score=acc.value_score + 10,  # Bonus for points
                        details={
                            'property': acc,
                            'nights': acc.total_nights,
                            'category': acc.award_category
                        }
                    ))
        
        return sorted(acc_options, key=lambda x: x.value_score, reverse=True)[:8]
    
    def _find_optimal_combinations(self, flight_options: List[TripComponent],
                                 acc_options: List[TripComponent],
                                 budget: float,
                                 user_points: Optional[Dict]) -> List[Dict]:
        """Find optimal flight + accommodation combinations"""
        
        combinations = []
        
        for flight in flight_options:
            for acc in acc_options:
                # Calculate total cost
                total_cash = flight.cash_cost + acc.cash_cost
                
                # Skip if over budget
                if total_cash > budget:
                    continue
                
                # Calculate points needed
                points_needed = {}
                if flight.points_cost:
                    program = flight.points_program
                    points_needed[program] = points_needed.get(program, 0) + flight.points_cost
                
                if acc.points_cost:
                    program = acc.points_program
                    points_needed[program] = points_needed.get(program, 0) + acc.points_cost
                
                # Check if user has enough points
                can_afford_points = True
                if user_points:
                    for program, needed in points_needed.items():
                        if user_points.get(program, 0) < needed:
                            can_afford_points = False
                            break
                
                # Calculate combo score
                combo_score = flight.value_score + acc.value_score
                
                # Bonus for using points effectively
                if points_needed and can_afford_points:
                    combo_score += 20
                
                # Bonus for staying under budget
                budget_utilization = total_cash / budget
                if 0.7 <= budget_utilization <= 0.9:
                    combo_score += 15  # Good budget usage
                
                combinations.append({
                    'flight': flight,
                    'accommodation': acc,
                    'total_cash': total_cash,
                    'points_needed': points_needed,
                    'can_afford': can_afford_points,
                    'score': combo_score,
                    'budget_remaining': budget - total_cash
                })
        
        # Sort by score
        return sorted(combinations, key=lambda x: x['score'], reverse=True)
    
    def _generate_recommendations(self, combinations: List[Dict], 
                                budget: float, nights: int, 
                                travelers: int) -> Dict:
        """Generate final recommendations"""
        
        recommendations = {
            'trip_summary': {
                'total_budget': budget,
                'nights': nights,
                'travelers': travelers
            },
            'top_recommendations': [],
            'points_maximizer': None,
            'budget_maximizer': None,
            'value_maximizer': None
        }
        
        # Find special recommendations
        points_combos = [c for c in combinations if c['points_needed']]
        cash_combos = [c for c in combinations if not c['points_needed']]
        
        # Points maximizer (most points usage)
        if points_combos:
            points_max = max(points_combos, 
                           key=lambda x: sum(x['points_needed'].values()))
            recommendations['points_maximizer'] = self._format_combo(points_max)
        
        # Budget maximizer (lowest cash cost)
        if cash_combos:
            budget_max = min(cash_combos, key=lambda x: x['total_cash'])
            recommendations['budget_maximizer'] = self._format_combo(budget_max)
        
        # Value maximizer (highest score)
        if combinations:
            value_max = combinations[0]  # Already sorted by score
            recommendations['value_maximizer'] = self._format_combo(value_max)
        
        # Top 3 overall recommendations
        for combo in combinations[:3]:
            recommendations['top_recommendations'].append(
                self._format_combo(combo)
            )
        
        return recommendations
    
    def _format_combo(self, combo: Dict) -> Dict:
        """Format combination for display"""
        return {
            'flights': {
                'description': combo['flight'].description,
                'cost': f"${combo['flight'].cash_cost:,.0f}",
                'points': f"{combo['flight'].points_cost:,} {combo['flight'].points_program}" 
                         if combo['flight'].points_cost else None
            },
            'accommodation': {
                'description': combo['accommodation'].description,
                'cost': f"${combo['accommodation'].cash_cost:,.0f}",
                'points': f"{combo['accommodation'].points_cost:,} {combo['accommodation'].points_program}"
                         if combo['accommodation'].points_cost else None
            },
            'total_cost': f"${combo['total_cash']:,.0f}",
            'points_required': combo['points_needed'],
            'budget_remaining': f"${combo['budget_remaining']:,.0f}",
            'value_score': combo['score']
        }

# ===== DISNEY TRIP COMPLETE TEST =====
async def test_complete_disney_trip():
    """Test complete Disney trip optimization"""
    
    optimizer = CompleteTripOptimizer()
    
    # User's points balances
    user_points = {
        'Chase UR': 150000,
        'Amex MR': 80000,
        'Marriott': 250000,
        'United': 75000,
        'American': 60000
    }
    
    # Family preferences
    preferences = {
        'family_friendly': True,
        'kitchen': True,
        'pool': True,
        'min_bedrooms': 2
    }
    
    # Run optimization
    results = await optimizer.optimize_complete_trip(
        origin='LAX',
        destination='MCO',  # Orlando
        departure_date='2025-08-15',
        return_date='2025-08-20',
        travelers=4,  # Family of 4
        total_budget=4000,
        user_points=user_points,
        preferences=preferences
    )
    
    # Display results
    print("\n" + "="*60)
    print("🎯 OPTIMIZATION RESULTS")
    print("="*60)
    
    # Value Maximizer
    if results['value_maximizer']:
        print("\n⭐ BEST OVERALL VALUE:")
        _display_recommendation(results['value_maximizer'])
    
    # Points Maximizer
    if results['points_maximizer']:
        print("\n💳 BEST POINTS USAGE:")
        _display_recommendation(results['points_maximizer'])
    
    # Budget Maximizer
    if results['budget_maximizer']:
        print("\n💰 MOST BUDGET-FRIENDLY:")
        _display_recommendation(results['budget_maximizer'])
    
    print("\n" + "="*60)
    print("💡 RECOMMENDATION:")
    print("For a Disney family trip, the BEST OVERALL VALUE option maximizes")
    print("your points while keeping cash costs low for park tickets and dining.")
    print(f"You'll have ${results['value_maximizer']['budget_remaining']} left for")
    print("Disney tickets ($500/person) and meals!")

def _display_recommendation(rec: Dict):
    """Display a recommendation nicely"""
    print(f"\nFlights: {rec['flights']['description']}")
    if rec['flights']['points']:
        print(f"  → {rec['flights']['points']} + {rec['flights']['cost']} taxes")
    else:
        print(f"  → {rec['flights']['cost']}")
    
    print(f"\nStay: {rec['accommodation']['description']}")
    if rec['accommodation']['points']:
        print(f"  → {rec['accommodation']['points']}")
        if rec['accommodation']['cost'] != '$0':
            print(f"     + {rec['accommodation']['cost']} fees")
    else:
        print(f"  → {rec['accommodation']['cost']}")
    
    print(f"\nTotal Cash Needed: {rec['total_cost']}")
    print(f"Budget Remaining: {rec['budget_remaining']}")
    
    if rec['points_required']:
        print("\nPoints Required:")
        for program, points in rec['points_required'].items():
            print(f"  • {program}: {points:,}")

# ===== MAIN ENTRY POINT =====
if __name__ == "__main__":
    print("🚀 FlightPath Complete Trip Optimizer")
    print("Optimizing flights + accommodation together!\n")
    
    # Run Disney trip test
    asyncio.run(test_complete_disney_trip())