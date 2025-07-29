"""
Flight API Integration Examples for FlightPath
Replace the mock data with real API calls
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import os

class FlightAPIService:
    """Base class for flight API integrations"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

class AmadeusFlightAPI(FlightAPIService):
    """Amadeus API integration for flight search"""
    
    def __init__(self):
        super().__init__()
        self.client_id = os.getenv('AMADEUS_CLIENT_ID')
        self.client_secret = os.getenv('AMADEUS_CLIENT_SECRET')
        self.base_url = 'https://api.amadeus.com/v2'
        self.token = None
    
    async def authenticate(self):
        """Get OAuth token from Amadeus"""
        auth_url = 'https://api.amadeus.com/v1/security/oauth2/token'
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        async with self.session.post(auth_url, data=data) as response:
            result = await response.json()
            self.token = result['access_token']
    
    async def search_flights(self, origin: str, destination: str, date: str, 
                           return_date: Optional[str] = None) -> List[Dict]:
        """Search flights using Amadeus API"""
        if not self.token:
            await self.authenticate()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': date,
            'adults': 1,
            'max': 10
        }
        
        if return_date:
            params['returnDate'] = return_date
        
        url = f"{self.base_url}/shopping/flight-offers"
        async with self.session.get(url, headers=headers, params=params) as response:
            data = await response.json()
            
            # Transform Amadeus response to our format
            flights = []
            for offer in data.get('data', []):
                for itinerary in offer['itineraries']:
                    segment = itinerary['segments'][0]
                    flights.append({
                        'name': f"{segment['carrierCode']} - {segment['number']}",
                        'price': f"USD {offer['price']['total']}",
                        'departure': segment['departure']['at'],
                        'arrival': segment['arrival']['at'],
                        'duration': itinerary['duration'],
                        'stops': len(itinerary['segments']) - 1,
                        'cabin': offer['travelerPricings'][0]['fareDetailsBySegment'][0]['cabin']
                    })
            
            return flights

class SkyscannerAPI(FlightAPIService):
    """Skyscanner API integration"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('SKYSCANNER_API_KEY')
        self.base_url = 'https://partners.api.skyscanner.net/apiservices/v3'
    
    async def search_flights(self, origin: str, destination: str, date: str) -> List[Dict]:
        """Search flights using Skyscanner API"""
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Create search session
        search_data = {
            'query': {
                'market': 'US',
                'locale': 'en-US',
                'currency': 'USD',
                'queryLegs': [{
                    'originPlaceId': {'iata': origin},
                    'destinationPlaceId': {'iata': destination},
                    'date': {'year': int(date[:4]), 'month': int(date[5:7]), 'day': int(date[8:10])}
                }],
                'adults': 1,
                'cabinClass': 'CABIN_CLASS_ECONOMY'
            }
        }
        
        # Poll for results
        create_url = f"{self.base_url}/flights/live/search/create"
        async with self.session.post(create_url, headers=headers, json=search_data) as response:
            result = await response.json()
            session_token = result['sessionToken']
        
        # Get results
        poll_url = f"{self.base_url}/flights/live/search/poll/{session_token}"
        async with self.session.get(poll_url, headers=headers) as response:
            data = await response.json()
            
            # Transform response
            flights = []
            for itinerary in data.get('content', {}).get('results', {}).get('itineraries', []):
                leg = itinerary['legs'][0]
                flights.append({
                    'name': f"{leg['carriers'][0]['name']} - {leg['segments'][0]['flightNumber']}",
                    'price': f"USD {itinerary['pricing']['price']['amount']}",
                    'departure': leg['departure'],
                    'arrival': leg['arrival'],
                    'duration': f"{leg['durationInMinutes']//60}h {leg['durationInMinutes']%60}m",
                    'stops': leg['stopCount']
                })
            
            return flights

class KiwiAPI(FlightAPIService):
    """Kiwi.com (formerly Skypicker) API integration"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('KIWI_API_KEY')
        self.base_url = 'https://api.tequila.kiwi.com/v2'
    
    async def search_flights(self, origin: str, destination: str, date: str) -> List[Dict]:
        """Search flights using Kiwi API"""
        headers = {'apikey': self.api_key}
        params = {
            'fly_from': origin,
            'fly_to': destination,
            'date_from': date,
            'date_to': date,
            'adults': 1,
            'limit': 10,
            'curr': 'USD',
            'sort': 'price'
        }
        
        url = f"{self.base_url}/search"
        async with self.session.get(url, headers=headers, params=params) as response:
            data = await response.json()
            
            flights = []
            for flight in data.get('data', []):
                route = flight['route'][0]
                flights.append({
                    'name': f"{route['airline']} - {route['flight_no']}",
                    'price': f"USD {flight['price']}",
                    'departure': datetime.fromtimestamp(route['dTimeUTC']).strftime('%I:%M %p'),
                    'arrival': datetime.fromtimestamp(route['aTimeUTC']).strftime('%I:%M %p'),
                    'duration': flight['fly_duration'],
                    'stops': len(flight['route']) - 1
                })
            
            return flights

class FlightAggregator:
    """Aggregates results from multiple flight APIs"""
    
    def __init__(self):
        self.apis = {
            'amadeus': AmadeusFlightAPI(),
            'skyscanner': SkyscannerAPI(),
            'kiwi': KiwiAPI()
        }
    
    async def search_all(self, origin: str, destination: str, date: str) -> Dict[str, List[Dict]]:
        """Search flights across all available APIs"""
        results = {}
        
        # Run all API searches concurrently
        tasks = []
        for name, api in self.apis.items():
            if self._is_api_configured(name):
                tasks.append(self._search_with_api(name, api, origin, destination, date))
        
        # Gather results
        api_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, result in api_results:
            if isinstance(result, Exception):
                print(f"Error with {name} API: {result}")
            else:
                results[name] = result
        
        return results
    
    async def _search_with_api(self, name: str, api: FlightAPIService, 
                              origin: str, destination: str, date: str) -> tuple:
        """Search with a specific API"""
        try:
            async with api:
                flights = await api.search_flights(origin, destination, date)
                return (name, flights)
        except Exception as e:
            return (name, e)
    
    def _is_api_configured(self, api_name: str) -> bool:
        """Check if API credentials are configured"""
        if api_name == 'amadeus':
            return bool(os.getenv('AMADEUS_CLIENT_ID') and os.getenv('AMADEUS_CLIENT_SECRET'))
        elif api_name == 'skyscanner':
            return bool(os.getenv('SKYSCANNER_API_KEY'))
        elif api_name == 'kiwi':
            return bool(os.getenv('KIWI_API_KEY'))
        return False

# ===== INTEGRATION WITH FLIGHTPATH =====
def integrate_with_flightpath():
    """
    To integrate real APIs with FlightPath:
    
    1. Sign up for API keys:
       - Amadeus: https://developers.amadeus.com/
       - Skyscanner: https://developers.skyscanner.net/
       - Kiwi: https://tequila.kiwi.com/
    
    2. Set environment variables:
       export AMADEUS_CLIENT_ID='your-client-id'
       export AMADEUS_CLIENT_SECRET='your-client-secret'
       export SKYSCANNER_API_KEY='your-api-key'
       export KIWI_API_KEY='your-api-key'
    
    3. Replace the mock data method in SecurePointsOptimizer:
    """
    
    example_code = '''
    # In SecurePointsOptimizer class, replace _get_mock_flights with:
    
    async def _get_real_flights(self, origin: str, destination: str, date: str) -> List[Dict]:
        """Get real flight data from APIs"""
        aggregator = FlightAggregator()
        results = await aggregator.search_all(origin, destination, date)
        
        # Combine and deduplicate results
        all_flights = []
        seen = set()
        
        for api_name, flights in results.items():
            for flight in flights:
                # Create unique key
                key = f"{flight['name']}-{flight['departure']}"
                if key not in seen:
                    seen.add(key)
                    flight['source_api'] = api_name
                    all_flights.append(flight)
        
        # Sort by price
        all_flights.sort(key=lambda x: float(x['price'].replace('USD ', '')))
        
        return all_flights[:20]  # Return top 20 results
    '''
    
    return example_code

# ===== EXAMPLE USAGE =====
async def main():
    """Example of using the flight APIs"""
    
    # Test individual APIs
    print("Testing Amadeus API...")
    amadeus = AmadeusFlightAPI()
    if os.getenv('AMADEUS_CLIENT_ID'):
        async with amadeus:
            flights = await amadeus.search_flights('LAX', 'JFK', '2025-08-15')
            print(f"Found {len(flights)} flights")
    
    # Test aggregator
    print("\nTesting Flight Aggregator...")
    aggregator = FlightAggregator()
    results = await aggregator.search_all('LAX', 'JFK', '2025-08-15')
    
    for api_name, flights in results.items():
        print(f"{api_name}: {len(flights)} flights found")

if __name__ == "__main__":
    # Run example
    asyncio.run(main())
    
    # Show integration instructions
    print("\n" + "="*50)
    print("INTEGRATION INSTRUCTIONS:")
    print("="*50)
    print(integrate_with_flightpath())