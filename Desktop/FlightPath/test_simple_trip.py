"""
Simple trip optimization test - no external dependencies
Shows the core functionality working
"""

import asyncio
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

# Simulate trip components
@dataclass
class TripComponent:
    type: str
    description: str
    cash_cost: float
    points_cost: int = 0
    points_program: str = ""
    value_score: float = 0.0

class SimpleTripOptimizer:
    """Simplified trip optimizer for testing"""
    
    def optimize_trip(self, budget: float, user_points: Dict) -> Dict:
        """Optimize a Disney trip with mock data"""
        
        print(f"💰 Budget: ${budget:,.0f}")
        print(f"👨‍👩‍👧‍👦 Family of 4 | 5 nights at Disney World")
        print("=" * 50)
        
        # Mock flight options
        flight_options = [
            TripComponent(
                type="flight",
                description="United Awards (LAX-MCO roundtrip x4)",
                cash_cost=180,  # Just taxes/fees
                points_cost=240000,  # 60k x 4 people
                points_program="United",
                value_score=95
            ),
            TripComponent(
                type="flight",
                description="American Cash (LAX-MCO roundtrip x4)",
                cash_cost=1600,  # $400 per person
                value_score=70
            ),
            TripComponent(
                type="flight",
                description="Southwest Cash (LAX-MCO roundtrip x4)",
                cash_cost=1200,  # $300 per person
                value_score=80
            )
        ]
        
        # Mock accommodation options
        accommodation_options = [
            TripComponent(
                type="accommodation",
                description="Disney Area Home (Airbnb) - 4BR, Pool, Kitchen",
                cash_cost=950,  # $190/night x 5 nights
                value_score=90
            ),
            TripComponent(
                type="accommodation",
                description="Marriott Swan (Award Redemption)",
                cash_cost=175,  # Resort fees only
                points_cost=250000,
                points_program="Marriott",
                value_score=85
            ),
            TripComponent(
                type="accommodation",
                description="Disney Contemporary Resort (Cash)",
                cash_cost=2250,  # $450/night x 5 nights
                value_score=75
            ),
            TripComponent(
                type="accommodation",
                description="Hilton Orlando (Cash)",
                cash_cost=950,  # $190/night x 5 nights
                value_score=70
            )
        ]
        
        # Find optimal combinations
        combinations = []
        
        for flight in flight_options:
            for hotel in accommodation_options:
                total_cash = flight.cash_cost + hotel.cash_cost
                
                # Skip if over budget
                if total_cash > budget:
                    continue
                
                # Check points availability
                points_ok = True
                if flight.points_cost and user_points.get(flight.points_program, 0) < flight.points_cost:
                    points_ok = False
                if hotel.points_cost and user_points.get(hotel.points_program, 0) < hotel.points_cost:
                    points_ok = False
                
                if not points_ok and (flight.points_cost or hotel.points_cost):
                    continue  # Skip if not enough points
                
                combo_score = flight.value_score + hotel.value_score
                
                # Bonus for good budget utilization
                budget_util = total_cash / budget
                if 0.3 <= budget_util <= 0.7:  # Good range for Disney trip
                    combo_score += 20
                
                combinations.append({
                    'flight': flight,
                    'hotel': hotel,
                    'total_cash': total_cash,
                    'budget_remaining': budget - total_cash,
                    'score': combo_score,
                    'points_used': (flight.points_cost or 0) + (hotel.points_cost or 0)
                })
        
        # Sort by score
        combinations.sort(key=lambda x: x['score'], reverse=True)
        
        return combinations

def test_disney_optimization():
    """Test Disney trip optimization"""
    
    # User's points balances
    user_points = {
        'United': 300000,
        'Marriott': 400000,
        'Chase UR': 150000,  # Can transfer to United
        'Amex MR': 80000
    }
    
    optimizer = SimpleTripOptimizer()
    results = optimizer.optimize_trip(4000, user_points)
    
    print("\n🎯 TOP RECOMMENDATIONS:\n")
    
    for i, combo in enumerate(results[:3], 1):
        print(f"{i}. OPTION {i}:")
        print(f"   ✈️  {combo['flight'].description}")
        if combo['flight'].points_cost:
            print(f"      → {combo['flight'].points_cost:,} {combo['flight'].points_program} points + ${combo['flight'].cash_cost}")
        else:
            print(f"      → ${combo['flight'].cash_cost}")
        
        print(f"   🏨 {combo['hotel'].description}")
        if combo['hotel'].points_cost:
            print(f"      → {combo['hotel'].points_cost:,} {combo['hotel'].points_program} points + ${combo['hotel'].cash_cost}")
        else:
            print(f"      → ${combo['hotel'].cash_cost}")
        
        print(f"   💰 Total Cash: ${combo['total_cash']}")
        print(f"   🎫 Remaining for Disney tickets/food: ${combo['budget_remaining']}")
        print(f"   📊 Value Score: {combo['score']:.0f}")
        
        if combo['points_used']:
            print(f"   💳 Total Points Used: {combo['points_used']:,}")
        
        print()
    
    # Analysis
    best = results[0]
    print("💡 RECOMMENDATION:")
    if best['points_used'] > 0:
        print(f"Use your points for maximum value! You'll save approximately")
        cash_equivalent = best['points_used'] * 0.015  # Assume 1.5 cents per point
        print(f"${cash_equivalent:,.0f} by using points instead of cash.")
    
    print(f"\nWith ${best['budget_remaining']} remaining, you can cover:")
    print("• Disney park tickets: ~$500 per person ($2,000 total)")
    print("• Meals and snacks: ~$100 per person per day")
    print("• Souvenirs and extras")
    
    if best['budget_remaining'] >= 2000:
        print("\n✅ Perfect! You have enough for tickets and dining!")
    else:
        print("\n⚠️  Consider the budget option to have more for park expenses.")

if __name__ == "__main__":
    print("🏰 FLIGHTPATH DISNEY TRIP OPTIMIZER")
    print("Testing complete trip optimization...")
    print()
    
    test_disney_optimization()