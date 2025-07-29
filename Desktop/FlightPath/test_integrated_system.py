"""
Integrated System Test - FlightPath with Accommodation
Shows the complete system working together
"""

import asyncio
from datetime import datetime

class MockFlightResult:
    """Mock flight search result"""
    def __init__(self, airline, price, award_miles=None):
        self.airline = airline
        self.price_usd = price
        self.award_miles = award_miles
        self.available_seats = 4 if award_miles else 0

class MockAccommodation:
    """Mock accommodation result"""
    def __init__(self, name, price, points=None, amenities=None):
        self.name = name
        self.price = price
        self.points = points
        self.amenities = amenities or []

class IntegratedTripOptimizer:
    """Integrated trip optimizer with mock data"""
    
    def search_flights(self, route):
        """Mock flight search"""
        return [
            MockFlightResult("United", 400, 30000),  # Award available
            MockFlightResult("American", 350, 30000),  # Award available
            MockFlightResult("Delta", 380),  # Cash only
            MockFlightResult("Southwest", 320)  # Cash only
        ]
    
    def search_accommodations(self, destination):
        """Mock accommodation search"""
        return [
            MockAccommodation("Disney Area Home (Airbnb)", 900, amenities=["Kitchen", "Pool", "4BR"]),
            MockAccommodation("Marriott Swan", 175, points=250000, amenities=["Resort", "Extra Magic Hours"]),
            MockAccommodation("Contemporary Resort", 2250, amenities=["Monorail", "Magic Kingdom View"]),
            MockAccommodation("Hilton Orlando", 945, amenities=["Pool", "Shuttle"])
        ]
    
    def optimize_trip(self, budget, user_points):
        """Find optimal trip combinations"""
        
        flights = self.search_flights("LAX-MCO")
        hotels = self.search_accommodations("Disney World")
        
        print("✈️  FLIGHT OPTIONS FOUND:")
        for i, flight in enumerate(flights, 1):
            if flight.award_miles:
                print(f"   {i}. {flight.airline}: ${flight.price_usd} OR {flight.award_miles:,} miles")
            else:
                print(f"   {i}. {flight.airline}: ${flight.price_usd} (cash only)")
        
        print("\n🏨 ACCOMMODATION OPTIONS FOUND:")
        for i, hotel in enumerate(hotels, 1):
            amenity_str = f" ({', '.join(hotel.amenities[:3])})" if hotel.amenities else ""
            if hotel.points:
                print(f"   {i}. {hotel.name}: ${hotel.price} + {hotel.points:,} points{amenity_str}")
            else:
                print(f"   {i}. {hotel.name}: ${hotel.price}{amenity_str}")
        
        # Find best combinations
        print(f"\n🎯 OPTIMIZING FOR ${budget:,} BUDGET:")
        print("="*50)
        
        best_combos = []
        
        # Strategy 1: Maximize points usage
        united_flight = flights[0]  # United with award
        marriott_hotel = hotels[1]  # Marriott with points
        
        if (user_points.get('United', 0) >= united_flight.award_miles * 4 and 
            user_points.get('Marriott', 0) >= marriott_hotel.points):
            
            cash_needed = (united_flight.price_usd * 0.1 * 4) + marriott_hotel.price  # 10% for taxes
            points_used = (united_flight.award_miles * 4) + marriott_hotel.points
            
            best_combos.append({
                'name': 'POINTS MAXIMIZER',
                'flight': f"United Awards x4 people",
                'hotel': marriott_hotel.name,
                'cash': cash_needed,
                'points': points_used,
                'remaining': budget - cash_needed,
                'score': 95
            })
        
        # Strategy 2: Cash optimization
        southwest_flight = flights[3]  # Southwest cash
        airbnb_hotel = hotels[0]  # Airbnb
        
        cash_needed = (southwest_flight.price_usd * 4) + airbnb_hotel.price
        if cash_needed <= budget:
            best_combos.append({
                'name': 'BUDGET OPTIMIZER',
                'flight': f"Southwest Cash x4 people",
                'hotel': airbnb_hotel.name,
                'cash': cash_needed,
                'points': 0,
                'remaining': budget - cash_needed,
                'score': 85
            })
        
        # Strategy 3: Mixed approach
        united_award = flights[0]
        disney_home = hotels[0]
        
        if user_points.get('United', 0) >= united_award.award_miles * 4:
            cash_needed = (united_award.price_usd * 0.1 * 4) + disney_home.price
            points_used = united_award.award_miles * 4
            
            best_combos.append({
                'name': 'MIXED STRATEGY',
                'flight': f"United Awards x4 people",
                'hotel': disney_home.name,
                'cash': cash_needed,
                'points': points_used,
                'remaining': budget - cash_needed,
                'score': 90
            })
        
        # Sort by score
        best_combos.sort(key=lambda x: x['score'], reverse=True)
        
        return best_combos

def run_test():
    """Run the integrated system test"""
    
    print("🏰 FLIGHTPATH INTEGRATED SYSTEM TEST")
    print("Disney World Family Trip | 4 people | 5 nights")
    print("="*60)
    
    # User's points portfolio
    user_points = {
        'United': 250000,
        'Marriott': 300000,
        'Chase UR': 120000,  # Can transfer to United
        'Amex MR': 85000
    }
    
    print("\n💳 USER POINTS BALANCE:")
    for program, points in user_points.items():
        print(f"   {program}: {points:,}")
    
    # Run optimization
    optimizer = IntegratedTripOptimizer()
    results = optimizer.optimize_trip(4000, user_points)
    
    print(f"\n🏆 TOP RECOMMENDATIONS:")
    print("="*50)
    
    for i, combo in enumerate(results, 1):
        print(f"\n{i}. {combo['name']}:")
        print(f"   ✈️  {combo['flight']}")
        print(f"   🏨 {combo['hotel']}")
        print(f"   💰 Cash needed: ${combo['cash']:,.0f}")
        if combo['points']:
            print(f"   💳 Points used: {combo['points']:,}")
        print(f"   💵 Budget remaining: ${combo['remaining']:,.0f}")
        print(f"   📊 Value score: {combo['score']}")
    
    # Final recommendation
    if results:
        best = results[0]
        print(f"\n💡 RECOMMENDATION:")
        print(f"Go with the {best['name']}!")
        print(f"You'll have ${best['remaining']:,.0f} left for:")
        print("   • Disney park tickets (~$2,000 for family)")
        print("   • Meals and snacks")
        print("   • Souvenirs and magical experiences!")
        
        if best['remaining'] >= 2000:
            print("\n✅ Perfect! You have enough for tickets and more!")
        else:
            print(f"\n⚠️  Tight on park tickets. Consider saving ${2000 - best['remaining']:.0f} more.")

if __name__ == "__main__":
    run_test()