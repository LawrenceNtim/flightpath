"""
Simple test for FastFlights award search engine
"""

import asyncio
import logging
from datetime import datetime
from fast_flights_engine import test_award_search

# Suppress some logging for cleaner output
logging.getLogger('aiohttp').setLevel(logging.WARNING)

if __name__ == "__main__":
    print("🚀 TESTING FASTFLIGHTS AWARD SEARCH ENGINE")
    print("=" * 60)
    print("Searching for award availability...")
    print()
    
    # Run the award search test
    asyncio.run(test_award_search())