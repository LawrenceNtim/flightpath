from fast_flights import FlightData, Passengers, get_flights
from datetime import datetime
import re

class PointsOptimizer:
    def __init__(self):
        # Comprehensive award charts database
        self.award_charts = {
            'United': {'domestic': 12500, 'international': 30000},
            'American': {'domestic': 12500, 'international': 30000},
            'Delta': {'domestic': 'dynamic', 'international': 'dynamic'},
            'Alaska': {'domestic': 12500, 'international': 25000},
            'Virgin Atlantic': {'domestic': None, 'international': 25000},
            'JetBlue': {'domestic': 'revenue', 'international': 'revenue'},  # ~1.4 cents per point
            'Southwest': {'domestic': 'revenue', 'international': 'revenue'}, # ~1.3 cents per point
            'Air France': {'domestic': 'dynamic', 'international': 15000},
            'British Airways': {'domestic': 'dynamic', 'international': 13000},
            'Turkish': {'domestic': 'dynamic', 'international': 15000},
            'Emirates': {'domestic': 'dynamic', 'international': 62500},
            'Singapore': {'domestic': 'dynamic', 'international': 35000},
            'Cathay Pacific': {'domestic': 'dynamic', 'international': 30000},
            'Qatar Airways': {'domestic': 'dynamic', 'international': 42500}
        }
        
        # COMPLETE transfer partners database
        self.transfer_partners = {
            'Chase UR': [
                'United', 'Southwest', 'JetBlue', 'Air France', 'British Airways',
                'Virgin Atlantic', 'Singapore', 'Aer Lingus', 'Emirates', 'Iberia',
                'Air Canada', 'IHG', 'Marriott', 'Hyatt'
            ],
            'Amex MR': [
                'Delta', 'JetBlue', 'British Airways', 'Virgin Atlantic', 'Air France',
                'Avianca', 'Singapore', 'Cathay Pacific', 'Emirates', 'Turkish',
                'Air Canada', 'ANA', 'Etihad', 'Flying Blue', 'Aer Lingus',
                'Choice Hotels', 'Hilton', 'Marriott'
            ],
            'Citi TYP': [
                'JetBlue', 'Turkish', 'Virgin Atlantic', 'Air France', 'Emirates',
                'Singapore', 'Cathay Pacific', 'Qatar Airways', 'Avianca',
                'Aer Lingus', 'Thai Airways', 'EVA Air', 'Etihad',
                'Choice Hotels', 'Accor', 'Wyndham', 'Leading Hotels'
            ],
            'Bilt': [
                'Alaska', 'United', 'Air France', 'Virgin Atlantic', 'British Airways',
                'Emirates', 'Turkish', 'Cathay Pacific', 'Southwest', 'JetBlue',
                'Japan Airlines', 'Qatar Airways', 'Avianca', 'Air Canada',
                'Aer Lingus', 'TAP Portugal', 'Iberia',
                'Hilton', 'Marriott', 'Hyatt', 'IHG', 'Accor'
            ],
            'Wells Fargo': [
                'Choice Hotels', 'Virgin Atlantic', 'Air France'  # Limited but growing
            ]
        }
        
        # Transfer ratios (most are 1:1, but some exceptions)
        self.transfer_ratios = {
            'Chase UR': {
                'default': 1.0,  # Most are 1:1
            },
            'Amex MR': {
                'default': 1.0,
                'Choice Hotels': 2.0,  # 1:2 bonus
            },
            'Citi TYP': {
                'default': 1.0,
                'Choice Hotels': 2.0,  # 1:2 for premium cards
                'JetBlue': 0.8,  # For non-premium cards
                'Wyndham': 0.8,  # For non-premium cards
            },
            'Bilt': {
                'default': 1.0,
                'Accor': 0.67,  # 3:2 ratio (worse)
            },
            'Wells Fargo': {
                'default': 1.0,
                'Choice Hotels': 2.0,
            }
        }

    def get_cash_flights(self, origin, destination, date):
        """Get cash flights using our existing fast-flights"""
        result = get_flights(
            flight_data=[
                FlightData(date=date, from_airport=origin, to_airport=destination)
            ],
            trip="one-way", 
            seat="economy",
            passengers=Passengers(adults=1)
        )
        return result.flights
    
    def estimate_award_value(self, airline, route_type, cash_price_usd):
        """Estimate if using points is worth it"""
        if airline not in self.award_charts:
            return None
            
        award_cost = self.award_charts[airline][route_type]
        
        if award_cost == 'revenue':
            # Revenue-based programs (JetBlue, Southwest)
            point_values = {
                'JetBlue': 1.4,  # TrueBlue points worth ~1.4 cents
                'Southwest': 1.3  # Rapid Rewards ~1.3 cents
            }
            
            point_value = point_values.get(airline, 1.0)
            estimated_points = (cash_price_usd * 100) / point_value
            
            return {
                'points_needed': int(estimated_points),
                'cents_per_point': point_value,
                'worth_it': True,  # Revenue-based is always "fair"
                'type': 'revenue-based'
            }
        
        elif award_cost == 'dynamic':
            # Dynamic pricing (Delta, Emirates, etc.)
            estimated_points = cash_price_usd * 100  # rough estimate
            return {
                'points_needed': int(estimated_points),
                'cents_per_point': 1.0,  # Dynamic usually around 1cpp
                'worth_it': estimated_points < cash_price_usd * 80,
                'type': 'dynamic'
            }
        
        # Fixed award charts
        cpp = (cash_price_usd * 100) / award_cost if award_cost else 0
        
        return {
            'points_needed': award_cost,
            'cents_per_point': cpp,
            'worth_it': cpp > 1.5,  # Generally good value above 1.5cpp
            'type': 'fixed'
        }
    
    def get_transfer_options(self, airline):
        """Find which credit cards can transfer to this airline"""
        transfer_options = []
        for program, partners in self.transfer_partners.items():
            if airline in partners:
                # Get the transfer ratio
                ratio = self.transfer_ratios[program].get(airline, 
                       self.transfer_ratios[program]['default'])
                transfer_options.append({
                    'program': program,
                    'ratio': ratio,
                    'display': f"{program} ({ratio}:1)" if ratio != 1.0 else program
                })
        return transfer_options
    
    def get_best_transfer_strategy(self, airline, points_needed):
        """Recommend the best credit card program for this redemption"""
        transfer_options = self.get_transfer_options(airline)
        
        if not transfer_options:
            return None
        
        # Calculate actual points needed from each program
        strategies = []
        for option in transfer_options:
            actual_points_needed = int(points_needed / option['ratio'])
            strategies.append({
                'program': option['program'],
                'points_from_program': actual_points_needed,
                'ratio': option['ratio'],
                'efficiency': option['ratio']  # Higher ratio = more efficient
            })
        
        # Sort by efficiency (highest ratio first)
        strategies.sort(key=lambda x: x['efficiency'], reverse=True)
        return strategies[0]
    
    def optimize_flight(self, origin, destination, date):
        """Main optimization function"""
        print(f"🔍 Optimizing {origin} → {destination} on {date}")
        
        # Get cash flights
        cash_flights = self.get_cash_flights(origin, destination, date)
        
        # Convert CRC to USD (you can make this dynamic later)
        crc_to_usd = 500
        
        recommendations = []
        
        for flight in cash_flights[:5]:
            # Extract numeric value from price string
            price_crc_str = flight.price
            price_crc_num = int(re.sub(r"[^0-9]", "", price_crc_str))
            cash_price_usd = price_crc_num / crc_to_usd
            
            # Determine route type
            route_type = 'domestic' if origin[:2] == destination[:2] else 'international'
            
            # Get airline name (clean it up)
            airline = flight.name.split(' - ')[0] if ' - ' in flight.name else flight.name
            
            # Estimate award value
            award_info = self.estimate_award_value(airline, route_type, cash_price_usd)
            
            # Get transfer options
            transfer_options = self.get_transfer_options(airline)
            
            # Get best transfer strategy
            best_strategy = None
            if award_info and transfer_options:
                best_strategy = self.get_best_transfer_strategy(airline, award_info['points_needed'])
            
            recommendation = {
                'flight': flight,
                'cash_price_usd': cash_price_usd,
                'award_info': award_info,
                'airline': airline,
                'transfer_options': transfer_options,
                'best_strategy': best_strategy
            }
            
            recommendations.append(recommendation)
        
        return recommendations

# Test the enhanced optimizer
if __name__ == "__main__":
    optimizer = PointsOptimizer()
    
    recommendations = optimizer.optimize_flight("LAX", "JFK", "2025-08-15")
    
    print("\n💎 FLIGHTPATH COMPREHENSIVE RECOMMENDATIONS:")
    print("=" * 70)
    
    for i, rec in enumerate(recommendations, 1):
        flight = rec['flight']
        cash_price = rec['cash_price_usd']
        award_info = rec['award_info']
        best_strategy = rec['best_strategy']
        
        print(f"\n{i}. {flight.name}")
        print(f"   💰 Cash: ${cash_price:.0f} USD")
        print(f"   ⏱️  Duration: {flight.duration}")
        print(f"   🔄 Departure: {flight.departure}")
        print(f"   🛬 Arrival: {flight.arrival}")
        
        if award_info:
            points = award_info['points_needed']
            cpp = award_info['cents_per_point']
            worth_it = "✅ GOOD VALUE" if award_info['worth_it'] else "❌ Poor value"
            award_type = f"({award_info['type']} pricing)"
            
            print(f"   🎯 Award: {points:,} points ({cpp:.1f}¢/point) {award_type} - {worth_it}")
            
            if best_strategy:
                prog = best_strategy['program']
                pts_needed = best_strategy['points_from_program']
                efficiency = best_strategy['ratio']
                
                print(f"   💳 BEST STRATEGY: Transfer {pts_needed:,} {prog} points")
                if efficiency != 1.0:
                    print(f"      (Transfer ratio: {efficiency}:1 - BONUS!)")
        else:
            print(f"   🎯 Award: No award program available")


class ComplexTripOptimizer:
    def __init__(self):
        self.points_optimizer = PointsOptimizer()
    
    def optimize_trip_sequence(self, trips, user_profile=None):
        """
        Optimize a sequence of flights considering:
        - Overall points strategy
        - Status earning potential
        - Positioning for future trips
        """
        print("🌍 OPTIMIZING COMPLEX TRIP SEQUENCE")
        print("=" * 50)
        
        total_recommendations = []
        running_status_miles = 0
        
        for i, trip in enumerate(trips, 1):
            print(f"\n🛫 LEG {i}: {trip['origin']} → {trip['destination']} on {trip['date']}")
            
            # Get recommendations for this leg
            leg_recommendations = self.points_optimizer.optimize_flight(
                trip['origin'], 
                trip['destination'], 
                trip['date']
            )
            
            # Add status earning potential
            for rec in leg_recommendations:
                distance = self.estimate_distance(trip['origin'], trip['destination'])
                rec['status_miles'] = distance
                rec['total_status_miles'] = running_status_miles + distance
            
            total_recommendations.append({
                'leg': i,
                'route': f"{trip['origin']} → {trip['destination']}",
                'date': trip['date'],
                'options': leg_recommendations
            })
        
        return self.generate_trip_strategy(total_recommendations, user_profile)
    
    def estimate_distance(self, origin, destination):
        """Rough distance estimation for status miles"""
        # This is a simplified version - you'd use real distance calculation
        domestic_routes = ['LAX-JFK', 'JFK-LAX', 'LAX-SFO', 'JFK-BOS']
        route = f"{origin}-{destination}"
        
        if route in domestic_routes or route[::-1] in domestic_routes:
            return 2500  # Average domestic distance
        else:
            return 5500  # Average international distance
    
    def generate_trip_strategy(self, recommendations, user_profile):
        """Generate overall trip strategy"""
        print("\n💎 FLIGHTPATH TRIP STRATEGY:")
        print("=" * 60)
        
        # Calculate total cost in points vs cash
        total_cash = 0
        total_points = 0
        best_strategy = []
        
        for leg in recommendations:
            best_option = min(leg['options'], 
                            key=lambda x: x['cash_price_usd'] if not x['award_info'] 
                            else x['award_info']['points_needed'] * 0.015)  # 1.5cpp value
            
            best_strategy.append({
                'leg': leg['leg'],
                'route': leg['route'],
                'date': leg['date'],
                'recommendation': best_option
            })
            
            total_cash += best_option['cash_price_usd']
            if best_option['award_info']:
                total_points += best_option['award_info']['points_needed']
        
        print(f"\n📊 TRIP SUMMARY:")
        print(f"   💰 Total Cash Cost: ${total_cash:.0f}")
        print(f"   🎯 Total Points Cost: {total_points:,} points")
        print(f"   🏆 Status Miles Earned: {sum(s['recommendation']['status_miles'] for s in best_strategy):,}")
        
        print(f"\n🎯 OPTIMAL STRATEGY:")
        for strategy in best_strategy:
            rec = strategy['recommendation']
            flight = rec['flight']
            
            print(f"\n   {strategy['leg']}. {strategy['route']} - {strategy['date']}")
            print(f"      ✈️  {flight.name} - {flight.duration}")
            
            if rec['award_info'] and rec['best_strategy']:
                points = rec['best_strategy']['points_from_program']
                program = rec['best_strategy']['program']
                print(f"      🎯 USE POINTS: {points:,} {program}")
            else:
                print(f"      💰 PAY CASH: ${rec['cash_price_usd']:.0f}")
        
        return best_strategy

# Test with a complex trip
if __name__ == "__main__":
    optimizer = ComplexTripOptimizer()
    
    # Example: Your upcoming trips from the spreadsheet
    trips = [
        {'origin': 'LAX', 'destination': 'JFK', 'date': '2025-08-15'},
        {'origin': 'JFK', 'destination': 'LHR', 'date': '2025-08-20'},
        {'origin': 'LHR', 'destination': 'LAX', 'date': '2025-08-25'}
    ]
    
    strategy = optimizer.optimize_trip_sequence(trips)


class AwardAvailabilityChecker:
    def check_award_space(self, airline, route, date, cabin_class):
        """Check if award seats actually exist"""
        # This is where we'd connect to:
        # - United API
        # - American API  
        # - Partner airline websites
        pass
    

class UserProfile:
    def __init__(self):
        self.credit_cards = ['Chase Sapphire Reserve', 'Amex Platinum']
        self.points_balances = {'Chase UR': 150000, 'Amex MR': 75000}
        self.status_goals = {'United': 'Premier Gold', 'Hyatt': 'Globalist'}
        self.home_airports = ['LAX', 'SFO']
        self.future_trips = [
            {'destination': 'NRT', 'date': '2026-01-15', 'cabin': 'business'}
        ] 