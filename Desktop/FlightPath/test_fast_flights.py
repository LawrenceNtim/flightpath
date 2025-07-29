"""
FastFlights Engine Tests - Comprehensive test suite
Ensures commercial-grade reliability for September 1st launch
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fast_flights_engine import (
    FastFlightsEngine, AwardAvailability, CabinClass, 
    AwardType, AwardCache, UnitedAwardSearcher
)

# ===== UNIT TESTS =====
class TestAwardAvailability:
    """Test AwardAvailability model"""
    
    def test_cache_key_generation(self):
        """Test unique cache key generation"""
        award = AwardAvailability(
            airline='United',
            flight_number='UA123',
            origin='LAX',
            destination='JFK',
            departure_time=datetime(2025, 8, 15, 8, 0),
            arrival_time=datetime(2025, 8, 15, 16, 30),
            cabin_class=CabinClass.ECONOMY,
            award_type=AwardType.SAVER,
            miles_required=12500,
            seats_available=4
        )
        
        expected_key = "award:United:UA123:2025-08-15"
        assert award.cache_key == expected_key
    
    def test_value_score_calculation(self):
        """Test value score calculation"""
        # Saver award, direct flight, 4 seats
        award1 = AwardAvailability(
            airline='United',
            flight_number='UA123',
            origin='LAX',
            destination='JFK',
            departure_time=datetime(2025, 8, 15, 8, 0),
            arrival_time=datetime(2025, 8, 15, 16, 30),
            cabin_class=CabinClass.ECONOMY,
            award_type=AwardType.SAVER,
            miles_required=12500,
            seats_available=4
        )
        
        # Standard award, connecting flight
        award2 = AwardAvailability(
            airline='United',
            flight_number='UA456',
            origin='LAX',
            destination='JFK',
            departure_time=datetime(2025, 8, 15, 10, 0),
            arrival_time=datetime(2025, 8, 15, 20, 30),
            cabin_class=CabinClass.ECONOMY,
            award_type=AwardType.STANDARD,
            miles_required=25000,
            seats_available=9,
            connection_info=[{'airport': 'DEN'}]
        )
        
        # Saver should score higher
        assert award1.value_score > award2.value_score
    
    def test_partner_award_penalty(self):
        """Test partner award scoring penalty"""
        regular_award = AwardAvailability(
            airline='United',
            flight_number='UA123',
            origin='LAX',
            destination='JFK',
            departure_time=datetime(2025, 8, 15, 8, 0),
            arrival_time=datetime(2025, 8, 15, 16, 30),
            cabin_class=CabinClass.ECONOMY,
            award_type=AwardType.SAVER,
            miles_required=12500,
            seats_available=4,
            partner_award=False
        )
        
        partner_award = AwardAvailability(
            airline='United',
            flight_number='LH123',
            origin='LAX',
            destination='JFK',
            departure_time=datetime(2025, 8, 15, 8, 0),
            arrival_time=datetime(2025, 8, 15, 16, 30),
            cabin_class=CabinClass.ECONOMY,
            award_type=AwardType.SAVER,
            miles_required=12500,
            seats_available=4,
            partner_award=True
        )
        
        assert regular_award.value_score > partner_award.value_score

# ===== ASYNC TESTS =====
@pytest.mark.asyncio
class TestFastFlightsEngine:
    """Test main search engine"""
    
    async def test_search_all_airlines(self):
        """Test searching across all airlines"""
        engine = FastFlightsEngine()
        
        awards = await engine.search_all_airlines('LAX', 'JFK', '2025-08-15')
        
        assert len(awards) > 0
        assert all(isinstance(award, AwardAvailability) for award in awards)
        # Should be sorted by value score
        scores = [award.value_score for award in awards]
        assert scores == sorted(scores, reverse=True)
    
    async def test_cache_functionality(self):
        """Test caching works correctly"""
        engine = FastFlightsEngine()
        
        # First search - should hit APIs
        start = datetime.now()
        awards1 = await engine.search_all_airlines('LAX', 'JFK', '2025-08-15')
        duration1 = (datetime.now() - start).total_seconds()
        
        # Second search - should hit cache
        start = datetime.now()
        awards2 = await engine.search_all_airlines('LAX', 'JFK', '2025-08-15')
        duration2 = (datetime.now() - start).total_seconds()
        
        # Cache should be faster
        assert duration2 < duration1
        # Results should be identical
        assert len(awards1) == len(awards2)
    
    async def test_calendar_view(self):
        """Test calendar view functionality"""
        engine = FastFlightsEngine()
        
        calendar = await engine.get_calendar_view(
            'LAX', 'JFK', '2025-08-15', days=7
        )
        
        assert len(calendar) == 7
        # Each date should have results
        for date, awards in calendar.items():
            assert isinstance(awards, list)
    
    async def test_timeout_handling(self):
        """Test timeout handling"""
        engine = FastFlightsEngine()
        
        # Mock a slow searcher
        with patch.object(UnitedAwardSearcher, 'search_awards') as mock_search:
            async def slow_search(*args):
                await asyncio.sleep(60)  # Longer than timeout
                return []
            
            mock_search.side_effect = slow_search
            
            # Should not raise exception
            awards = await engine.search_all_airlines('LAX', 'JFK', '2025-08-15')
            # May have partial results or empty
            assert isinstance(awards, list)

# ===== INTEGRATION TESTS =====
@pytest.mark.asyncio
class TestFastFlightsIntegration:
    """Test integration with FlightPath"""
    
    async def test_enhance_with_awards(self):
        """Test enhancing flight recommendations with awards"""
        from fast_flights_engine import FastFlightsIntegration
        
        integrator = FastFlightsIntegration()
        
        # Mock flight recommendations
        recommendations = [
            {
                'flight': {
                    'name': 'United Airlines - UA123',
                    'price': 'USD 250',
                    'departure': '08:00 AM',
                    'arrival': '04:30 PM'
                },
                'airline': 'United',
                'cash_price_usd': 250
            },
            {
                'flight': {
                    'name': 'American Airlines - AA456',
                    'price': 'USD 185',
                    'departure': '10:15 AM',
                    'arrival': '06:45 PM'
                },
                'airline': 'American',
                'cash_price_usd': 185
            }
        ]
        
        enhanced = await integrator.enhance_with_awards(recommendations)
        
        # Should have award availability info
        for rec in enhanced:
            assert 'award_availability' in rec
            if rec['award_availability']['available']:
                assert 'miles_required' in rec['award_availability']
                assert 'seats_available' in rec['award_availability']

# ===== PERFORMANCE TESTS =====
@pytest.mark.asyncio
class TestPerformance:
    """Performance and load tests"""
    
    async def test_concurrent_searches(self):
        """Test handling multiple concurrent searches"""
        engine = FastFlightsEngine()
        
        # Create 20 concurrent searches
        routes = [
            ('LAX', 'JFK'), ('SFO', 'ORD'), ('DFW', 'BOS'),
            ('SEA', 'MIA'), ('DEN', 'LGA'), ('PHX', 'EWR'),
            ('LAS', 'DCA'), ('ATL', 'LAX'), ('MSP', 'SAN'),
            ('DTW', 'PDX')
        ]
        
        tasks = []
        for origin, dest in routes:
            task = engine.search_all_airlines(origin, dest, '2025-08-15')
            tasks.append(task)
        
        start = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = (datetime.now() - start).total_seconds()
        
        # Should complete within reasonable time
        assert duration < 10  # 10 seconds for 10 routes
        
        # Count successful results
        successful = sum(1 for r in results if isinstance(r, list))
        assert successful >= 8  # At least 80% success rate
    
    async def test_cache_performance(self):
        """Test cache performance under load"""
        cache = AwardCache()
        
        # Write 1000 entries
        write_start = datetime.now()
        for i in range(1000):
            await cache.set(f"test_key_{i}", {"data": f"value_{i}"})
        write_duration = (datetime.now() - write_start).total_seconds()
        
        # Read 1000 entries
        read_start = datetime.now()
        for i in range(1000):
            value = await cache.get(f"test_key_{i}")
            assert value is not None
        read_duration = (datetime.now() - read_start).total_seconds()
        
        # Should be fast
        assert write_duration < 1.0  # Less than 1ms per write
        assert read_duration < 0.5   # Less than 0.5ms per read

# ===== ERROR HANDLING TESTS =====
@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and recovery"""
    
    async def test_invalid_airport_codes(self):
        """Test handling of invalid airport codes"""
        engine = FastFlightsEngine()
        
        # Should handle gracefully
        awards = await engine.search_all_airlines('XXX', 'YYY', '2025-08-15')
        assert isinstance(awards, list)  # Should return empty list or mock data
    
    async def test_invalid_dates(self):
        """Test handling of invalid dates"""
        engine = FastFlightsEngine()
        
        # Past date
        awards = await engine.search_all_airlines('LAX', 'JFK', '2020-01-01')
        assert isinstance(awards, list)
        
        # Invalid format
        awards = await engine.search_all_airlines('LAX', 'JFK', 'not-a-date')
        assert isinstance(awards, list)
    
    async def test_network_failure_recovery(self):
        """Test recovery from network failures"""
        engine = FastFlightsEngine()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Simulate network error
            mock_get.side_effect = aiohttp.ClientError("Network error")
            
            # Should not crash
            awards = await engine.search_all_airlines('LAX', 'JFK', '2025-08-15')
            assert isinstance(awards, list)

# ===== MONITORING TESTS =====
def test_monitoring_metrics():
    """Test monitoring functionality"""
    from fast_flights_engine import AwardSearchMonitor
    
    monitor = AwardSearchMonitor()
    
    # Simulate searches
    asyncio.run(monitor.log_search('LAX', 'JFK', 1.5, 10))
    asyncio.run(monitor.log_search('SFO', 'ORD', 2.0, 8))
    asyncio.run(monitor.log_search('DFW', 'BOS', 1.0, 12))
    
    metrics = monitor.get_metrics()
    
    assert metrics['searches'] == 3
    assert metrics['avg_response_time'] == 1.5

# ===== TEST RUNNER =====
def run_all_tests():
    """Run all tests"""
    print("🧪 Running FastFlights Engine Tests")
    print("=" * 50)
    
    # Run pytest
    pytest.main([__file__, '-v'])

if __name__ == "__main__":
    # Quick test
    print("Running quick functionality test...")
    
    async def quick_test():
        engine = FastFlightsEngine()
        awards = await engine.search_all_airlines('LAX', 'JFK', '2025-08-15')
        print(f"✅ Found {len(awards)} awards")
        
        if awards:
            best = awards[0]
            print(f"Best option: {best.airline} {best.flight_number} - {best.miles_required:,} miles")
    
    asyncio.run(quick_test())
    
    print("\nRun 'pytest test_fast_flights.py -v' for full test suite")