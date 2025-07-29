"""
Simplified test for accommodation engine only
"""

import asyncio
from accommodation_engine import test_disney_trip

if __name__ == "__main__":
    print("🧪 Testing Accommodation Engine Only")
    print("=" * 50)
    
    # Run the Disney trip test
    asyncio.run(test_disney_trip())