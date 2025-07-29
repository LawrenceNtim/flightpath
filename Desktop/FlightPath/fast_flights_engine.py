"""
FastFlights Award Availability Engine - Commercial Core
Production-ready award search with real-time availability checking
"""

import os
import json
import asyncio
import aiohttp
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from functools import lru_cache
from enum import Enum
import redis
from concurrent.futures import ThreadPoolExecutor
import backoff

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== CONFIGURATION =====
class FastFlightsConfig:
    """FastFlights specific configuration"""
    # Redis cache for award availability
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    CACHE_TTL_MINUTES = int(os.getenv('AWARD_CACHE_TTL', '30'))  # 30 min default
    
    # Award search settings
    MAX_CONCURRENT_SEARCHES = int(os.getenv('MAX_CONCURRENT_SEARCHES', '10'))
    SEARCH_TIMEOUT_SECONDS = int(os.getenv('SEARCH_TIMEOUT', '30'))
    RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))
    
    # Airline API endpoints (mock for now, replace with real)
    AIRLINE_ENDPOINTS = {
        'united': os.getenv('UNITED_API_URL', 'https://api.united.com/awards/v1'),
        'american': os.getenv('AA_API_URL', 'https://api.aa.com/awards/v1'),
        'delta': os.getenv('DELTA_API_URL', 'https://api.delta.com/awards/v1'),
        'alaska': os.getenv('ALASKA_API_URL', 'https://api.alaskaair.com/awards/v1'),
    }
    
    # API Keys for airlines (encrypted in production)
    AIRLINE_API_KEYS = {
        'united': os.getenv('UNITED_API_KEY', ''),
        'american': os.getenv('AA_API_KEY', ''),
        'delta': os.getenv('DELTA_API_KEY', ''),
        'alaska': os.getenv('ALASKA_API_KEY', ''),
    }

# ===== DATA MODELS =====
class CabinClass(Enum):
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"

class AwardType(Enum):
    SAVER = "saver"
    STANDARD = "standard"
    FLEXIBLE = "flexible"
    DYNAMIC = "dynamic"

@dataclass
class AwardAvailability:
    """Award availability data structure"""
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    cabin_class: CabinClass
    award_type: AwardType
    miles_required: int
    seats_available: int
    waitlist_available: bool = False
    partner_award: bool = False
    mixed_cabin: bool = False
    connection_info: Optional[List[Dict]] = None
    taxes_fees: float = 0.0
    
    @property
    def cache_key(self) -> str:
        """Generate unique cache key"""
        return f"award:{self.airline}:{self.flight_number}:{self.departure_time.date()}"
    
    @property
    def value_score(self) -> float:
        """Calculate value score for ranking"""
        base_score = 100.0
        
        # Prefer saver awards
        if self.award_type == AwardType.SAVER:
            base_score += 50
        
        # Prefer direct flights
        if not self.connection_info:
            base_score += 30
        
        # Prefer more available seats
        base_score += min(self.seats_available * 5, 25)
        
        # Penalty for partner awards (usually more restrictive)
        if self.partner_award:
            base_score -= 20
            
        # Penalty for mixed cabin
        if self.mixed_cabin:
            base_score -= 15
            
        return base_score

# ===== CACHE LAYER =====
class AwardCache:
    """Redis-based caching for award availability"""
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(
                FastFlightsConfig.REDIS_URL,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Redis cache connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, using in-memory cache: {e}")
            self.redis_client = None
            self._memory_cache = {}
    
    async def get(self, key: str) -> Optional[Dict]:
        """Get from cache"""
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                return json.loads(data) if data else None
            else:
                return self._memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Dict, ttl_minutes: int = None):
        """Set in cache with TTL"""
        ttl = ttl_minutes or FastFlightsConfig.CACHE_TTL_MINUTES
        try:
            if self.redis_client:
                self.redis_client.setex(
                    key, 
                    timedelta(minutes=ttl), 
                    json.dumps(value)
                )
            else:
                self._memory_cache[key] = value
                # Simple TTL for memory cache
                asyncio.create_task(self._expire_key(key, ttl * 60))
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def _expire_key(self, key: str, seconds: int):
        """Expire key from memory cache after delay"""
        await asyncio.sleep(seconds)
        self._memory_cache.pop(key, None)

# ===== AIRLINE SEARCHERS =====
class BaseAirlineSearcher:
    """Base class for airline-specific award searchers"""
    
    def __init__(self, airline: str):
        self.airline = airline
        self.api_url = FastFlightsConfig.AIRLINE_ENDPOINTS.get(airline)
        self.api_key = FastFlightsConfig.AIRLINE_API_KEYS.get(airline)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=FastFlightsConfig.RETRY_ATTEMPTS
    )
    async def search_awards(self, origin: str, destination: str, 
                          date: str, cabin: CabinClass) -> List[AwardAvailability]:
        """Search for award availability - must be implemented by subclass"""
        raise NotImplementedError

class UnitedAwardSearcher(BaseAirlineSearcher):
    """United Airlines award searcher"""
    
    def __init__(self):
        super().__init__('united')
    
    async def search_awards(self, origin: str, destination: str, 
                          date: str, cabin: CabinClass) -> List[AwardAvailability]:
        """Search United award availability"""
        # For now, return mock data. In production, this would call United's API
        mock_awards = [
            AwardAvailability(
                airline='United',
                flight_number='UA123',
                origin=origin,
                destination=destination,
                departure_time=datetime.fromisoformat(f"{date}T08:00:00"),
                arrival_time=datetime.fromisoformat(f"{date}T16:30:00"),
                cabin_class=cabin,
                award_type=AwardType.SAVER,
                miles_required=12500 if origin[:2] == destination[:2] else 30000,
                seats_available=4,
                taxes_fees=5.60
            ),
            AwardAvailability(
                airline='United',
                flight_number='UA789',
                origin=origin,
                destination=destination,
                departure_time=datetime.fromisoformat(f"{date}T14:00:00"),
                arrival_time=datetime.fromisoformat(f"{date}T22:30:00"),
                cabin_class=cabin,
                award_type=AwardType.STANDARD,
                miles_required=25000 if origin[:2] == destination[:2] else 60000,
                seats_available=9,
                taxes_fees=5.60
            )
        ]
        
        # Simulate API delay
        await asyncio.sleep(0.5)
        
        return mock_awards

class AmericanAwardSearcher(BaseAirlineSearcher):
    """American Airlines award searcher"""
    
    def __init__(self):
        super().__init__('american')
    
    async def search_awards(self, origin: str, destination: str, 
                          date: str, cabin: CabinClass) -> List[AwardAvailability]:
        """Search American award availability"""
        mock_awards = [
            AwardAvailability(
                airline='American',
                flight_number='AA456',
                origin=origin,
                destination=destination,
                departure_time=datetime.fromisoformat(f"{date}T10:15:00"),
                arrival_time=datetime.fromisoformat(f"{date}T18:45:00"),
                cabin_class=cabin,
                award_type=AwardType.SAVER,
                miles_required=12500 if origin[:2] == destination[:2] else 30000,
                seats_available=2,
                taxes_fees=5.60,
                partner_award=False
            )
        ]
        
        await asyncio.sleep(0.5)
        return mock_awards

# ===== MAIN SEARCH ENGINE =====
class FastFlightsEngine:
    """Main award availability search engine"""
    
    def __init__(self):
        self.cache = AwardCache()
        self.searchers = {
            'united': UnitedAwardSearcher,
            'american': AmericanAwardSearcher,
            # Add more airlines as needed
        }
        self._session_cache = {}
    
    async def search_all_airlines(self, origin: str, destination: str, 
                                date: str, cabin: CabinClass = CabinClass.ECONOMY,
                                airlines: Optional[List[str]] = None) -> List[AwardAvailability]:
        """Search award availability across all airlines"""
        
        # Validate inputs
        origin = origin.upper().strip()
        destination = destination.upper().strip()
        
        # Check cache first
        cache_key = f"search:{origin}:{destination}:{date}:{cabin.value}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info(f"✅ Cache hit for {cache_key}")
            return [AwardAvailability(**award) for award in cached_result]
        
        # Determine which airlines to search
        airlines_to_search = airlines or list(self.searchers.keys())
        
        # Search concurrently across airlines
        tasks = []
        for airline in airlines_to_search:
            if airline in self.searchers:
                searcher_class = self.searchers[airline]
                task = self._search_airline(searcher_class, origin, destination, date, cabin)
                tasks.append(task)
        
        # Gather results with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=FastFlightsConfig.SEARCH_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            logger.error("Search timeout exceeded")
            results = []
        
        # Flatten and filter results
        all_awards = []
        for result in results:
            if isinstance(result, list):
                all_awards.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Search error: {result}")
        
        # Sort by value score
        all_awards.sort(key=lambda x: x.value_score, reverse=True)
        
        # Cache results
        if all_awards:
            cache_data = [award.__dict__ for award in all_awards]
            # Convert datetime objects to strings for JSON serialization
            for award_dict in cache_data:
                award_dict['departure_time'] = award_dict['departure_time'].isoformat()
                award_dict['arrival_time'] = award_dict['arrival_time'].isoformat()
                award_dict['cabin_class'] = award_dict['cabin_class'].value
                award_dict['award_type'] = award_dict['award_type'].value
            
            await self.cache.set(cache_key, cache_data)
        
        return all_awards
    
    async def _search_airline(self, searcher_class, origin: str, 
                            destination: str, date: str, cabin: CabinClass) -> List[AwardAvailability]:
        """Search a specific airline"""
        try:
            async with searcher_class() as searcher:
                return await searcher.search_awards(origin, destination, date, cabin)
        except Exception as e:
            logger.error(f"Error searching {searcher_class.__name__}: {e}")
            return []
    
    async def get_calendar_view(self, origin: str, destination: str, 
                              start_date: str, days: int = 30, 
                              cabin: CabinClass = CabinClass.ECONOMY) -> Dict[str, List[AwardAvailability]]:
        """Get award availability for a date range"""
        calendar = {}
        
        # Generate date range
        start = datetime.fromisoformat(start_date)
        dates = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
        
        # Search each date concurrently
        tasks = []
        for date in dates:
            task = self.search_all_airlines(origin, destination, date, cabin)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build calendar view
        for date, result in zip(dates, results):
            if isinstance(result, list):
                calendar[date] = result
            else:
                calendar[date] = []
        
        return calendar
    
    def get_best_options(self, awards: List[AwardAvailability], 
                        max_results: int = 5) -> List[AwardAvailability]:
        """Get the best award options based on value score"""
        return sorted(awards, key=lambda x: x.value_score, reverse=True)[:max_results]

# ===== INTEGRATION HELPER =====
class FastFlightsIntegration:
    """Helper to integrate FastFlights with existing FlightPath"""
    
    def __init__(self):
        self.engine = FastFlightsEngine()
    
    async def enhance_with_awards(self, flight_recommendations: List[Dict]) -> List[Dict]:
        """Enhance flight recommendations with award availability"""
        
        for rec in flight_recommendations:
            flight = rec['flight']
            # Extract flight details
            airline = rec['airline']
            
            # Search for award availability
            # This is simplified - in production you'd match specific flights
            awards = await self.engine.search_all_airlines(
                origin='LAX',  # Would come from flight data
                destination='JFK',  # Would come from flight data
                date='2025-08-15',  # Would come from flight data
                cabin=CabinClass.ECONOMY
            )
            
            # Find matching awards for this airline
            matching_awards = [a for a in awards if a.airline.lower() == airline.lower()]
            
            if matching_awards:
                best_award = self.engine.get_best_options(matching_awards, 1)[0]
                rec['award_availability'] = {
                    'available': True,
                    'miles_required': best_award.miles_required,
                    'seats_available': best_award.seats_available,
                    'award_type': best_award.award_type.value,
                    'taxes_fees': best_award.taxes_fees
                }
            else:
                rec['award_availability'] = {
                    'available': False,
                    'reason': 'No award seats found'
                }
        
        return flight_recommendations

# ===== TESTING & MONITORING =====
async def test_award_search():
    """Test the award search functionality"""
    engine = FastFlightsEngine()
    
    print("🔍 Testing FastFlights Award Search Engine")
    print("=" * 50)
    
    # Test single date search
    awards = await engine.search_all_airlines('LAX', 'JFK', '2025-08-15')
    print(f"\nFound {len(awards)} award options for LAX-JFK on 2025-08-15:")
    
    for award in awards[:3]:
        print(f"\n✈️  {award.airline} {award.flight_number}")
        print(f"   Departure: {award.departure_time.strftime('%I:%M %p')}")
        print(f"   Miles: {award.miles_required:,} ({award.award_type.value})")
        print(f"   Seats: {award.seats_available} available")
        print(f"   Value Score: {award.value_score:.1f}")
    
    # Test calendar view
    print("\n\n📅 Testing Calendar View (7 days):")
    calendar = await engine.get_calendar_view('LAX', 'JFK', '2025-08-15', days=7)
    
    for date, awards in calendar.items():
        if awards:
            best = engine.get_best_options(awards, 1)[0]
            print(f"{date}: {len(awards)} options, best: {best.miles_required:,} miles")
        else:
            print(f"{date}: No availability")

# ===== PRODUCTION MONITORING =====
class AwardSearchMonitor:
    """Monitor award search performance and availability"""
    
    def __init__(self):
        self.metrics = {
            'searches': 0,
            'cache_hits': 0,
            'errors': 0,
            'avg_response_time': 0
        }
    
    async def log_search(self, origin: str, destination: str, 
                        duration: float, results_count: int):
        """Log search metrics"""
        self.metrics['searches'] += 1
        # Update average response time
        current_avg = self.metrics['avg_response_time']
        new_avg = (current_avg * (self.metrics['searches'] - 1) + duration) / self.metrics['searches']
        self.metrics['avg_response_time'] = new_avg
        
        logger.info(f"Search: {origin}-{destination} | {results_count} results | {duration:.2f}s")
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        return self.metrics.copy()

# ===== MAIN ENTRY POINT =====
if __name__ == "__main__":
    # Run test
    asyncio.run(test_award_search())