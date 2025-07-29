"""
Accommodation Search Engine for FlightPath
Integrates Airbnb, Booking.com, and Hotel Loyalty Programs
"""

import os
import json
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from bs4 import BeautifulSoup
import re
from functools import lru_cache

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== CONFIGURATION =====
class AccommodationConfig:
    """Accommodation search configuration"""
    
    # API Keys
    BOOKING_API_KEY = os.getenv('BOOKING_API_KEY', '')
    BOOKING_API_URL = 'https://api.booking.com/v1'
    
    # Marriott scraper settings
    MARRIOTT_BASE_URL = 'https://www.marriott.com'
    MARRIOTT_SEARCH_TIMEOUT = 30
    
    # OpenBNB MCP settings
    OPENBNB_SERVER_URL = os.getenv('OPENBNB_SERVER_URL', 'http://localhost:3000')
    
    # Search defaults
    DEFAULT_RADIUS_MILES = 10
    MAX_RESULTS_PER_SOURCE = 20
    CACHE_TTL_MINUTES = 60

# ===== DATA MODELS =====
class AccommodationType(Enum):
    HOTEL = "hotel"
    AIRBNB = "airbnb"
    VACATION_RENTAL = "vacation_rental"
    RESORT = "resort"

class PriceType(Enum):
    CASH = "cash"
    POINTS = "points"
    MIXED = "mixed"

@dataclass
class Accommodation:
    """Unified accommodation data structure"""
    source: str  # booking, airbnb, marriott
    property_id: str
    name: str
    type: AccommodationType
    location: Dict[str, float]  # lat, lng
    address: str
    distance_to_destination: float  # miles
    
    # Pricing
    price_type: PriceType
    cash_price: Optional[float] = None
    points_required: Optional[int] = None
    taxes_fees: float = 0.0
    total_nights: int = 1
    
    # Details
    rating: Optional[float] = None
    review_count: Optional[int] = None
    room_type: Optional[str] = None
    max_guests: int = 2
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    
    # Amenities
    amenities: List[str] = field(default_factory=list)
    pet_friendly: bool = False
    family_friendly: bool = False
    has_kitchen: bool = False
    has_parking: bool = False
    has_pool: bool = False
    has_wifi: bool = True
    
    # Award specific
    award_category: Optional[int] = None
    award_type: Optional[str] = None  # standard, peak, off-peak
    
    @property
    def price_per_night(self) -> float:
        """Calculate price per night"""
        if self.cash_price:
            return (self.cash_price + self.taxes_fees) / self.total_nights
        return 0
    
    @property
    def points_per_night(self) -> int:
        """Calculate points per night"""
        if self.points_required:
            return self.points_required // self.total_nights
        return 0
    
    @property
    def value_score(self) -> float:
        """Calculate value score for ranking"""
        score = 100.0
        
        # Rating bonus
        if self.rating:
            score += (self.rating - 4.0) * 20  # +20 for 5.0, -20 for 3.0
        
        # Distance penalty (closer is better)
        score -= min(self.distance_to_destination * 2, 30)
        
        # Amenity bonuses
        if self.has_kitchen:
            score += 15  # Can save on dining
        if self.has_parking:
            score += 10
        if self.family_friendly:
            score += 10
        
        # Price factor (lower is better)
        if self.price_per_night > 0:
            # Normalize around $150/night as baseline
            price_factor = 150 / self.price_per_night
            score *= price_factor
        
        return score

# ===== AIRBNB SEARCHER (via OpenBNB MCP) =====
class AirbnbSearcher:
    """Search Airbnb listings via OpenBNB MCP server"""
    
    def __init__(self):
        self.server_url = AccommodationConfig.OPENBNB_SERVER_URL
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search(self, location: str, checkin: str, checkout: str, 
                    guests: int = 2, filters: Optional[Dict] = None) -> List[Accommodation]:
        """Search Airbnb listings"""
        try:
            # Call OpenBNB MCP server
            endpoint = f"{self.server_url}/search"
            params = {
                'location': location,
                'checkin': checkin,
                'checkout': checkout,
                'guests': guests,
                'limit': AccommodationConfig.MAX_RESULTS_PER_SOURCE
            }
            
            if filters:
                params.update(filters)
            
            async with self.session.get(endpoint, params=params) as response:
                if response.status != 200:
                    logger.error(f"Airbnb search failed: {response.status}")
                    return []
                
                data = await response.json()
                return self._parse_airbnb_results(data, checkin, checkout)
        
        except Exception as e:
            logger.error(f"Airbnb search error: {e}")
            # Return mock data for testing
            return self._get_mock_airbnb_results(location, checkin, checkout)
    
    def _parse_airbnb_results(self, data: Dict, checkin: str, checkout: str) -> List[Accommodation]:
        """Parse Airbnb API response"""
        accommodations = []
        
        nights = (datetime.fromisoformat(checkout) - datetime.fromisoformat(checkin)).days
        
        for listing in data.get('listings', []):
            try:
                acc = Accommodation(
                    source='airbnb',
                    property_id=listing['id'],
                    name=listing['name'],
                    type=AccommodationType.AIRBNB,
                    location={'lat': listing['lat'], 'lng': listing['lng']},
                    address=listing.get('address', ''),
                    distance_to_destination=listing.get('distance', 0),
                    price_type=PriceType.CASH,
                    cash_price=listing['price'] * nights,
                    taxes_fees=listing.get('cleaning_fee', 0) + listing.get('service_fee', 0),
                    total_nights=nights,
                    rating=listing.get('rating'),
                    review_count=listing.get('reviews_count'),
                    room_type=listing.get('room_type'),
                    max_guests=listing.get('guests', 2),
                    bedrooms=listing.get('bedrooms'),
                    bathrooms=listing.get('bathrooms'),
                    amenities=listing.get('amenities', []),
                    pet_friendly='pets allowed' in listing.get('house_rules', '').lower(),
                    has_kitchen='kitchen' in [a.lower() for a in listing.get('amenities', [])],
                    has_parking='parking' in [a.lower() for a in listing.get('amenities', [])]
                )
                accommodations.append(acc)
            except Exception as e:
                logger.error(f"Error parsing Airbnb listing: {e}")
        
        return accommodations
    
    def _get_mock_airbnb_results(self, location: str, checkin: str, checkout: str) -> List[Accommodation]:
        """Return mock Airbnb results for testing"""
        nights = (datetime.fromisoformat(checkout) - datetime.fromisoformat(checkin)).days
        
        return [
            Accommodation(
                source='airbnb',
                property_id='mock-1',
                name='Cozy Disney Area Home - Pool & Game Room',
                type=AccommodationType.AIRBNB,
                location={'lat': 28.3852, 'lng': -81.5639},
                address='Kissimmee, FL',
                distance_to_destination=5.2,
                price_type=PriceType.CASH,
                cash_price=180 * nights,
                taxes_fees=75,
                total_nights=nights,
                rating=4.9,
                review_count=127,
                room_type='Entire home',
                max_guests=8,
                bedrooms=4,
                bathrooms=2.5,
                amenities=['Pool', 'Kitchen', 'WiFi', 'Parking', 'Game room', 'BBQ'],
                pet_friendly=True,
                family_friendly=True,
                has_kitchen=True,
                has_parking=True,
                has_pool=True
            ),
            Accommodation(
                source='airbnb',
                property_id='mock-2',
                name='Modern Condo Near Theme Parks',
                type=AccommodationType.AIRBNB,
                location={'lat': 28.3772, 'lng': -81.5707},
                address='Orlando, FL',
                distance_to_destination=7.8,
                price_type=PriceType.CASH,
                cash_price=120 * nights,
                taxes_fees=50,
                total_nights=nights,
                rating=4.7,
                review_count=89,
                room_type='Entire condo',
                max_guests=6,
                bedrooms=2,
                bathrooms=2,
                amenities=['Pool', 'Kitchen', 'WiFi', 'Parking', 'Gym'],
                family_friendly=True,
                has_kitchen=True,
                has_parking=True,
                has_pool=True
            )
        ]

# ===== BOOKING.COM SEARCHER =====
class BookingSearcher:
    """Search hotels via Booking.com API"""
    
    def __init__(self):
        self.api_key = AccommodationConfig.BOOKING_API_KEY
        self.base_url = AccommodationConfig.BOOKING_API_URL
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search(self, location: str, checkin: str, checkout: str, 
                    guests: int = 2, filters: Optional[Dict] = None) -> List[Accommodation]:
        """Search hotels on Booking.com"""
        try:
            if not self.api_key:
                logger.warning("Booking.com API key not set, using mock data")
                return self._get_mock_booking_results(location, checkin, checkout)
            
            # Booking.com API call would go here
            # For now, return mock data
            return self._get_mock_booking_results(location, checkin, checkout)
        
        except Exception as e:
            logger.error(f"Booking search error: {e}")
            return []
    
    def _get_mock_booking_results(self, location: str, checkin: str, checkout: str) -> List[Accommodation]:
        """Return mock Booking.com results"""
        nights = (datetime.fromisoformat(checkout) - datetime.fromisoformat(checkin)).days
        
        return [
            Accommodation(
                source='booking',
                property_id='booking-1',
                name='Disney\'s Contemporary Resort',
                type=AccommodationType.RESORT,
                location={'lat': 28.4149, 'lng': -81.5736},
                address='Bay Lake, FL',
                distance_to_destination=0.5,
                price_type=PriceType.CASH,
                cash_price=450 * nights,
                taxes_fees=67.50 * nights,
                total_nights=nights,
                rating=4.5,
                review_count=2341,
                room_type='Theme Park View Room',
                max_guests=4,
                amenities=['Pool', 'Restaurant', 'Monorail', 'Concierge', 'Spa'],
                family_friendly=True,
                has_parking=True,
                has_pool=True
            ),
            Accommodation(
                source='booking',
                property_id='booking-2',
                name='Hilton Orlando',
                type=AccommodationType.HOTEL,
                location={'lat': 28.4159, 'lng': -81.4669},
                address='Orlando, FL',
                distance_to_destination=8.2,
                price_type=PriceType.CASH,
                cash_price=189 * nights,
                taxes_fees=28.35 * nights,
                total_nights=nights,
                rating=4.2,
                review_count=1876,
                room_type='Two Queen Beds',
                max_guests=4,
                amenities=['Pool', 'Restaurant', 'Gym', 'Business Center'],
                family_friendly=True,
                has_parking=True,
                has_pool=True
            )
        ]

# ===== MARRIOTT AWARD SCRAPER =====
class MarriottAwardSearcher:
    """Scrape Marriott award availability"""
    
    def __init__(self):
        self.base_url = AccommodationConfig.MARRIOTT_BASE_URL
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search(self, location: str, checkin: str, checkout: str, 
                    flexible_dates: bool = True) -> List[Accommodation]:
        """Search Marriott award availability"""
        try:
            # For production, this would scrape Marriott's website
            # For now, return mock award data
            return self._get_mock_marriott_awards(location, checkin, checkout)
        
        except Exception as e:
            logger.error(f"Marriott search error: {e}")
            return []
    
    def _get_mock_marriott_awards(self, location: str, checkin: str, checkout: str) -> List[Accommodation]:
        """Return mock Marriott award availability"""
        nights = (datetime.fromisoformat(checkout) - datetime.fromisoformat(checkin)).days
        
        return [
            Accommodation(
                source='marriott',
                property_id='marriott-1',
                name='Walt Disney World Swan',
                type=AccommodationType.HOTEL,
                location={'lat': 28.3669, 'lng': -81.5541},
                address='Lake Buena Vista, FL',
                distance_to_destination=2.1,
                price_type=PriceType.POINTS,
                points_required=50000 * nights,
                taxes_fees=35 * nights,  # Resort fee
                total_nights=nights,
                rating=4.4,
                review_count=1562,
                room_type='Traditional Room',
                max_guests=4,
                amenities=['Pool', 'Restaurant', 'Extra Magic Hours', 'Spa'],
                family_friendly=True,
                has_parking=True,
                has_pool=True,
                award_category=6,
                award_type='standard'
            ),
            Accommodation(
                source='marriott',
                property_id='marriott-2',
                name='Residence Inn Orlando at SeaWorld',
                type=AccommodationType.HOTEL,
                location={'lat': 28.4494, 'lng': -81.4697},
                address='Orlando, FL',
                distance_to_destination=10.5,
                price_type=PriceType.POINTS,
                points_required=35000 * nights,
                taxes_fees=0,  # No resort fee
                total_nights=nights,
                rating=4.3,
                review_count=876,
                room_type='Studio Suite',
                max_guests=4,
                amenities=['Pool', 'Kitchen', 'Breakfast', 'Parking'],
                family_friendly=True,
                has_kitchen=True,
                has_parking=True,
                has_pool=True,
                award_category=5,
                award_type='standard'
            )
        ]

# ===== UNIFIED ACCOMMODATION ORCHESTRATOR =====
class AccommodationOrchestrator:
    """Orchestrates search across all accommodation sources"""
    
    def __init__(self):
        self.airbnb = AirbnbSearcher()
        self.booking = BookingSearcher()
        self.marriott = MarriottAwardSearcher()
        self._cache = {}
    
    async def search_all(self, location: str, checkin: str, checkout: str,
                        guests: int = 2, budget: Optional[float] = None,
                        preferences: Optional[Dict] = None) -> Dict[str, List[Accommodation]]:
        """Search all accommodation sources"""
        
        # Check cache
        cache_key = f"{location}:{checkin}:{checkout}:{guests}"
        if cache_key in self._cache:
            logger.info(f"Cache hit for accommodation search: {cache_key}")
            return self._cache[cache_key]
        
        # Search all sources concurrently
        tasks = [
            self._search_airbnb(location, checkin, checkout, guests, preferences),
            self._search_booking(location, checkin, checkout, guests, preferences),
            self._search_marriott(location, checkin, checkout)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results
        all_accommodations = {
            'airbnb': results[0] if isinstance(results[0], list) else [],
            'hotels': results[1] if isinstance(results[1], list) else [],
            'marriott_awards': results[2] if isinstance(results[2], list) else []
        }
        
        # Apply budget filter if specified
        if budget:
            all_accommodations = self._filter_by_budget(all_accommodations, budget)
        
        # Cache results
        self._cache[cache_key] = all_accommodations
        
        return all_accommodations
    
    async def _search_airbnb(self, location: str, checkin: str, checkout: str,
                           guests: int, preferences: Optional[Dict]) -> List[Accommodation]:
        """Search Airbnb with preferences"""
        filters = {}
        if preferences:
            if preferences.get('pet_friendly'):
                filters['pets_allowed'] = True
            if preferences.get('min_bedrooms'):
                filters['min_bedrooms'] = preferences['min_bedrooms']
        
        async with self.airbnb as searcher:
            return await searcher.search(location, checkin, checkout, guests, filters)
    
    async def _search_booking(self, location: str, checkin: str, checkout: str,
                            guests: int, preferences: Optional[Dict]) -> List[Accommodation]:
        """Search Booking.com with preferences"""
        async with self.booking as searcher:
            return await searcher.search(location, checkin, checkout, guests, preferences)
    
    async def _search_marriott(self, location: str, checkin: str, checkout: str) -> List[Accommodation]:
        """Search Marriott awards"""
        async with self.marriott as searcher:
            return await searcher.search(location, checkin, checkout)
    
    def _filter_by_budget(self, accommodations: Dict, budget: float) -> Dict:
        """Filter accommodations by budget"""
        filtered = {}
        
        for source, listings in accommodations.items():
            filtered[source] = [
                acc for acc in listings 
                if acc.price_type == PriceType.POINTS or 
                   (acc.cash_price and acc.cash_price + acc.taxes_fees <= budget)
            ]
        
        return filtered
    
    def optimize_for_value(self, accommodations: Dict[str, List[Accommodation]], 
                          user_points: Optional[Dict] = None,
                          preferences: Optional[Dict] = None) -> List[Tuple[Accommodation, str]]:
        """Optimize accommodation selection for best value"""
        
        # Flatten all accommodations
        all_options = []
        for source, listings in accommodations.items():
            for acc in listings:
                all_options.append((acc, source))
        
        # Score each option
        scored_options = []
        for acc, source in all_options:
            score = acc.value_score
            
            # Bonus for points redemption if user has points
            if user_points and acc.price_type == PriceType.POINTS:
                if acc.source == 'marriott' and user_points.get('marriott', 0) >= acc.points_required:
                    score += 30  # Bonus for using points
            
            # Apply preference adjustments
            if preferences:
                if preferences.get('pet_friendly') and acc.pet_friendly:
                    score += 20
                if preferences.get('family_friendly') and acc.family_friendly:
                    score += 15
                if preferences.get('kitchen') and acc.has_kitchen:
                    score += 25
            
            scored_options.append((acc, source, score))
        
        # Sort by score
        scored_options.sort(key=lambda x: x[2], reverse=True)
        
        return [(acc, source) for acc, source, _ in scored_options]

# ===== INTEGRATED TRIP OPTIMIZER =====
class TripOptimizer:
    """Optimizes complete trip including flights and accommodation"""
    
    def __init__(self):
        self.accommodation_orchestrator = AccommodationOrchestrator()
    
    async def optimize_trip(self, origin: str, destination: str, 
                          checkin: str, checkout: str,
                          total_budget: float, travelers: int = 2,
                          preferences: Optional[Dict] = None,
                          user_points: Optional[Dict] = None) -> Dict:
        """Optimize complete trip within budget"""
        
        # Calculate nights
        nights = (datetime.fromisoformat(checkout) - datetime.fromisoformat(checkin)).days
        
        # Search accommodations
        accommodations = await self.accommodation_orchestrator.search_all(
            destination, checkin, checkout, travelers, 
            budget=total_budget * 0.6,  # Allocate 60% to accommodation initially
            preferences=preferences
        )
        
        # Optimize selection
        best_options = self.accommodation_orchestrator.optimize_for_value(
            accommodations, user_points, preferences
        )
        
        # Build recommendations
        recommendations = {
            'trip_summary': {
                'destination': destination,
                'dates': f"{checkin} to {checkout}",
                'nights': nights,
                'travelers': travelers,
                'total_budget': total_budget
            },
            'accommodation_options': []
        }
        
        # Add top 5 accommodation options
        for acc, source in best_options[:5]:
            option = {
                'source': source,
                'name': acc.name,
                'type': acc.type.value,
                'total_cost': acc.cash_price + acc.taxes_fees if acc.cash_price else 0,
                'points_cost': acc.points_required if acc.points_required else 0,
                'per_night': acc.price_per_night if acc.cash_price else acc.points_per_night,
                'distance': f"{acc.distance_to_destination} miles",
                'rating': acc.rating,
                'key_amenities': [a for a in ['Kitchen', 'Pool', 'Parking'] if a in acc.amenities],
                'family_friendly': acc.family_friendly,
                'recommendation': self._get_recommendation_reason(acc, preferences)
            }
            recommendations['accommodation_options'].append(option)
        
        # Calculate budget allocation
        if best_options:
            best_acc = best_options[0][0]
            acc_cost = best_acc.cash_price + best_acc.taxes_fees if best_acc.cash_price else 0
            flight_budget = total_budget - acc_cost
            
            recommendations['budget_allocation'] = {
                'accommodation': acc_cost,
                'flights': flight_budget,
                'remaining': total_budget - acc_cost if acc_cost < total_budget else 0
            }
        
        return recommendations
    
    def _get_recommendation_reason(self, acc: Accommodation, preferences: Optional[Dict]) -> str:
        """Generate recommendation reason"""
        reasons = []
        
        if acc.rating and acc.rating >= 4.5:
            reasons.append("Highly rated")
        
        if acc.has_kitchen:
            reasons.append("Kitchen saves on dining")
        
        if acc.price_type == PriceType.POINTS:
            reasons.append("Great points redemption")
        
        if acc.distance_to_destination < 5:
            reasons.append(f"Only {acc.distance_to_destination:.1f} miles away")
        
        if preferences and preferences.get('family_friendly') and acc.family_friendly:
            reasons.append("Perfect for families")
        
        return " • ".join(reasons[:3]) if reasons else "Good value option"

# ===== DISNEY TRIP TEST SCENARIO =====
async def test_disney_trip():
    """Test $4000 Disney family trip scenario"""
    print("🏰 DISNEY FAMILY TRIP OPTIMIZER")
    print("=" * 50)
    print("Budget: $4,000 | Family of 4 | 5 nights")
    print("=" * 50)
    
    optimizer = TripOptimizer()
    
    # User preferences
    preferences = {
        'family_friendly': True,
        'kitchen': True,  # Save money on meals
        'min_bedrooms': 2,
        'pool': True  # Kids love pools
    }
    
    # User points balances
    user_points = {
        'marriott': 250000,
        'chase_ur': 100000,
        'amex_mr': 80000
    }
    
    # Search and optimize
    results = await optimizer.optimize_trip(
        origin='LAX',
        destination='Disney World Orlando',
        checkin='2025-08-15',
        checkout='2025-08-20',
        total_budget=4000,
        travelers=4,
        preferences=preferences,
        user_points=user_points
    )
    
    # Display results
    print("\n📍 ACCOMMODATION RECOMMENDATIONS:\n")
    
    for i, opt in enumerate(results['accommodation_options'], 1):
        print(f"{i}. {opt['name']}")
        print(f"   Type: {opt['type']} | Source: {opt['source']}")
        
        if opt['points_cost']:
            print(f"   💳 Points: {opt['points_cost']:,} points")
        else:
            print(f"   💰 Cost: ${opt['total_cost']:.0f} (${opt['per_night']:.0f}/night)")
        
        print(f"   📍 Distance: {opt['distance']}")
        print(f"   ⭐ Rating: {opt['rating']}")
        
        if opt['key_amenities']:
            print(f"   🏠 Amenities: {', '.join(opt['key_amenities'])}")
        
        print(f"   💡 Why: {opt['recommendation']}")
        print()
    
    # Budget breakdown
    if 'budget_allocation' in results:
        alloc = results['budget_allocation']
        print("\n💰 RECOMMENDED BUDGET ALLOCATION:")
        print(f"   Accommodation: ${alloc['accommodation']:.0f}")
        print(f"   Flights (4 people): ${alloc['flights']:.0f}")
        print(f"   Remaining for park tickets/food: ${alloc['remaining']:.0f}")

# ===== MAIN ENTRY POINT =====
if __name__ == "__main__":
    # Run Disney trip test
    asyncio.run(test_disney_trip())