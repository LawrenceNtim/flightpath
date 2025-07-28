"""
Context Engine for FlightPath
Provides external and internal context for flight recommendations
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass, asdict
import holidays
import pytz
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure requests cache for API calls
requests_cache.install_cache('context_cache', expire_after=3600)  # 1 hour cache

@dataclass
class ContextInsight:
    """Data class for context insights"""
    type: str  # 'warning', 'info', 'suggestion', 'tip'
    category: str  # 'pricing', 'weather', 'events', 'seasonal'
    title: str
    description: str
    impact: str  # 'high', 'medium', 'low'
    source: str
    relevance_score: float  # 0.0 to 1.0

@dataclass
class TravelContext:
    """Complete travel context for a flight request"""
    external_context: Dict[str, Any]
    internal_context: Dict[str, Any]
    insights: List[ContextInsight]
    warnings: List[str]
    suggestions: List[str]
    confidence: float

class ContextEngine:
    """
    Context Engine that provides comprehensive travel context
    """
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="flightpath_context_engine")
        
        # Initialize holiday calendars
        self.us_holidays = holidays.US()
        
        # Peak travel seasons
        self.peak_seasons = {
            'summer': {'start': (6, 15), 'end': (8, 31), 'multiplier': 1.5},
            'winter_holidays': {'start': (12, 20), 'end': (1, 5), 'multiplier': 1.8},
            'spring_break': {'start': (3, 15), 'end': (4, 15), 'multiplier': 1.4},
            'thanksgiving': {'start': (11, 20), 'end': (12, 1), 'multiplier': 1.6}
        }
        
        # Major events data (simplified - would be from external API in production)
        self.major_events = {
            'LAS': [
                {'name': 'CES', 'start': '2024-01-09', 'end': '2024-01-12', 'impact': 'high'},
                {'name': 'NAB Show', 'start': '2024-04-13', 'end': '2024-04-17', 'impact': 'high'}
            ],
            'ATL': [
                {'name': 'Dragon Con', 'start': '2024-08-29', 'end': '2024-09-02', 'impact': 'medium'}
            ],
            'SFO': [
                {'name': 'Dreamforce', 'start': '2024-09-17', 'end': '2024-09-19', 'impact': 'high'}
            ]
        }
        
        # Weather impact data
        self.weather_patterns = {
            'hurricane_season': {
                'regions': ['MIA', 'FLL', 'MCO', 'TPA', 'MSY', 'IAH'],
                'start': (6, 1),
                'end': (11, 30),
                'peak': (8, 15, 10, 15),
                'impact': 'high'
            },
            'winter_storms': {
                'regions': ['BOS', 'JFK', 'LGA', 'EWR', 'PHL', 'DCA', 'ORD', 'DTW'],
                'start': (12, 1),
                'end': (3, 31),
                'peak': (1, 15, 2, 28),
                'impact': 'medium'
            },
            'fog_season': {
                'regions': ['SFO', 'OAK', 'SJC'],
                'start': (6, 1),
                'end': (9, 30),
                'peak': (7, 1, 8, 31),
                'impact': 'medium'
            }
        }
        
        # Airport congestion data
        self.airport_congestion = {
            'JFK': {'peak_hours': [(7, 9), (17, 20)], 'delay_factor': 1.3},
            'LAX': {'peak_hours': [(6, 9), (16, 19)], 'delay_factor': 1.2},
            'ORD': {'peak_hours': [(7, 10), (17, 20)], 'delay_factor': 1.4},
            'ATL': {'peak_hours': [(6, 9), (16, 19)], 'delay_factor': 1.2},
            'DEN': {'peak_hours': [(7, 10), (17, 20)], 'delay_factor': 1.1}
        }
    
    def get_context(self, origin: str, destination: str, departure_date: str, 
                   return_date: Optional[str] = None, 
                   passenger_count: int = 1,
                   class_preference: str = 'economy') -> TravelContext:
        """
        Get comprehensive travel context for a flight request
        """
        try:
            logger.info(f"Getting context for {origin} to {destination} on {departure_date}")
            
            # Parse departure date
            dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
            ret_date = datetime.strptime(return_date, '%Y-%m-%d') if return_date else None
            
            # Get external context
            external_context = self._get_external_context(
                origin, destination, dep_date, ret_date, passenger_count, class_preference
            )
            
            # Get internal context
            internal_context = self._get_internal_context(
                origin, destination, dep_date, ret_date, passenger_count, class_preference
            )
            
            # Generate insights
            insights = self._generate_insights(
                external_context, internal_context, origin, destination, dep_date, ret_date
            )
            
            # Extract warnings and suggestions
            warnings = [insight.description for insight in insights if insight.type == 'warning']
            suggestions = [insight.description for insight in insights if insight.type == 'suggestion']
            
            # Calculate overall confidence
            confidence = self._calculate_context_confidence(external_context, internal_context)
            
            return TravelContext(
                external_context=external_context,
                internal_context=internal_context,
                insights=insights,
                warnings=warnings,
                suggestions=suggestions,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return self._get_default_context()
    
    def _get_external_context(self, origin: str, destination: str, dep_date: datetime,
                            ret_date: Optional[datetime], passenger_count: int,
                            class_preference: str) -> Dict[str, Any]:
        """Get external context data"""
        context = {}
        
        # Holiday context
        context['holidays'] = self._get_holiday_context(dep_date, ret_date)
        
        # Weather context
        context['weather'] = self._get_weather_context(origin, destination, dep_date)
        
        # Events context
        context['events'] = self._get_events_context(origin, destination, dep_date, ret_date)
        
        # Seasonal context
        context['seasonal'] = self._get_seasonal_context(dep_date, ret_date)
        
        # Airport context
        context['airports'] = self._get_airport_context(origin, destination, dep_date)
        
        # Distance and route context
        context['route'] = self._get_route_context(origin, destination)
        
        return context
    
    def _get_internal_context(self, origin: str, destination: str, dep_date: datetime,
                            ret_date: Optional[datetime], passenger_count: int,
                            class_preference: str) -> Dict[str, Any]:
        """Get internal context data"""
        context = {}
        
        # User preferences (simplified - would come from user profile)
        context['user_preferences'] = {
            'preferred_airlines': ['AA', 'UA', 'DL'],
            'loyalty_programs': ['AA AAdvantage', 'UA MileagePlus'],
            'seating_preference': 'aisle',
            'meal_preference': 'vegetarian',
            'notification_preferences': ['email', 'sms']
        }
        
        # Travel history (simplified - would come from database)
        context['travel_history'] = {
            'frequent_routes': [{'route': 'LAX-JFK', 'frequency': 12}],
            'preferred_times': {'departure': 'morning', 'return': 'evening'},
            'average_booking_advance': 21,  # days
            'class_distribution': {'economy': 0.6, 'business': 0.4, 'first': 0.0}
        }
        
        # Calendar conflicts (simplified - would integrate with calendar API)
        context['calendar_conflicts'] = self._check_calendar_conflicts(dep_date, ret_date)
        
        # Budget context
        context['budget'] = self._get_budget_context(passenger_count, class_preference)
        
        return context
    
    def _get_holiday_context(self, dep_date: datetime, ret_date: Optional[datetime]) -> Dict[str, Any]:
        """Get holiday-related context"""
        context = {
            'departure_holiday': None,
            'return_holiday': None,
            'holiday_period': False,
            'impact': 'none'
        }
        
        # Check if departure is on a holiday
        if dep_date.date() in self.us_holidays:
            context['departure_holiday'] = self.us_holidays[dep_date.date()]
            context['impact'] = 'high'
        
        # Check if return is on a holiday
        if ret_date and ret_date.date() in self.us_holidays:
            context['return_holiday'] = self.us_holidays[ret_date.date()]
            context['impact'] = 'high'
        
        # Check for holiday periods
        holiday_periods = [
            ('Christmas/New Year', datetime(dep_date.year, 12, 20), datetime(dep_date.year + 1, 1, 5)),
            ('Thanksgiving', datetime(dep_date.year, 11, 20), datetime(dep_date.year, 12, 1)),
            ('Memorial Day', datetime(dep_date.year, 5, 25), datetime(dep_date.year, 5, 31)),
            ('Labor Day', datetime(dep_date.year, 9, 1), datetime(dep_date.year, 9, 7)),
            ('Independence Day', datetime(dep_date.year, 7, 2), datetime(dep_date.year, 7, 6))
        ]
        
        for period_name, start, end in holiday_periods:
            if start <= dep_date <= end:
                context['holiday_period'] = period_name
                context['impact'] = 'high'
                break
        
        return context
    
    def _get_weather_context(self, origin: str, destination: str, dep_date: datetime) -> Dict[str, Any]:
        """Get weather-related context"""
        context = {
            'origin_weather_risk': 'none',
            'destination_weather_risk': 'none',
            'seasonal_patterns': [],
            'recommendations': []
        }
        
        # Check weather patterns
        for pattern_name, pattern_data in self.weather_patterns.items():
            if origin in pattern_data['regions'] or destination in pattern_data['regions']:
                start_date = datetime(dep_date.year, *pattern_data['start'])
                end_date = datetime(dep_date.year, *pattern_data['end'])
                
                if start_date <= dep_date <= end_date:
                    risk_level = pattern_data['impact']
                    
                    if origin in pattern_data['regions']:
                        context['origin_weather_risk'] = risk_level
                    if destination in pattern_data['regions']:
                        context['destination_weather_risk'] = risk_level
                    
                    context['seasonal_patterns'].append({
                        'pattern': pattern_name,
                        'impact': risk_level,
                        'description': self._get_weather_description(pattern_name)
                    })
        
        return context
    
    def _get_events_context(self, origin: str, destination: str, dep_date: datetime,
                          ret_date: Optional[datetime]) -> Dict[str, Any]:
        """Get events-related context"""
        context = {
            'origin_events': [],
            'destination_events': [],
            'impact': 'none'
        }
        
        # Check for major events
        for airport in [origin, destination]:
            if airport in self.major_events:
                for event in self.major_events[airport]:
                    event_start = datetime.strptime(event['start'], '%Y-%m-%d')
                    event_end = datetime.strptime(event['end'], '%Y-%m-%d')
                    
                    # Check if travel dates overlap with event
                    if (event_start <= dep_date <= event_end) or \
                       (ret_date and event_start <= ret_date <= event_end):
                        
                        event_info = {
                            'name': event['name'],
                            'start': event['start'],
                            'end': event['end'],
                            'impact': event['impact']
                        }
                        
                        if airport == origin:
                            context['origin_events'].append(event_info)
                        else:
                            context['destination_events'].append(event_info)
                        
                        if event['impact'] == 'high':
                            context['impact'] = 'high'
                        elif event['impact'] == 'medium' and context['impact'] != 'high':
                            context['impact'] = 'medium'
        
        return context
    
    def _get_seasonal_context(self, dep_date: datetime, ret_date: Optional[datetime]) -> Dict[str, Any]:
        """Get seasonal context"""
        context = {
            'season': self._get_season(dep_date),
            'peak_travel': False,
            'pricing_multiplier': 1.0,
            'recommendations': []
        }
        
        # Check peak seasons
        for season_name, season_data in self.peak_seasons.items():
            start_date = datetime(dep_date.year, *season_data['start'])
            end_date = datetime(dep_date.year, *season_data['end'])
            
            if start_date <= dep_date <= end_date:
                context['peak_travel'] = True
                context['pricing_multiplier'] = season_data['multiplier']
                context['recommendations'].append(
                    f"Peak {season_name.replace('_', ' ')} season - expect higher prices"
                )
                break
        
        return context
    
    def _get_airport_context(self, origin: str, destination: str, dep_date: datetime) -> Dict[str, Any]:
        """Get airport-specific context"""
        context = {
            'origin_congestion': 'normal',
            'destination_congestion': 'normal',
            'delay_factors': {},
            'recommendations': []
        }
        
        # Check airport congestion
        for airport in [origin, destination]:
            if airport in self.airport_congestion:
                congestion_data = self.airport_congestion[airport]
                
                context['delay_factors'][airport] = congestion_data['delay_factor']
                
                # Check if departure time falls in peak hours
                peak_hours = congestion_data['peak_hours']
                for start_hour, end_hour in peak_hours:
                    context['recommendations'].append(
                        f"Avoid {airport} flights between {start_hour}:00-{end_hour}:00 for less congestion"
                    )
        
        return context
    
    def _get_route_context(self, origin: str, destination: str) -> Dict[str, Any]:
        """Get route-specific context"""
        context = {
            'distance': 0,
            'typical_duration': 0,
            'route_type': 'domestic',
            'time_zone_difference': 0,
            'popular_route': False
        }
        
        try:
            # Get coordinates (simplified - would use airport database)
            origin_coords = self._get_airport_coordinates(origin)
            dest_coords = self._get_airport_coordinates(destination)
            
            if origin_coords and dest_coords:
                # Calculate distance
                distance = geodesic(origin_coords, dest_coords).miles
                context['distance'] = round(distance, 2)
                
                # Estimate flight duration (simplified)
                context['typical_duration'] = self._estimate_flight_duration(distance)
                
                # Determine route type
                if distance > 2500:
                    context['route_type'] = 'transcontinental'
                elif distance > 1000:
                    context['route_type'] = 'long_haul'
                else:
                    context['route_type'] = 'short_haul'
            
        except Exception as e:
            logger.error(f"Error calculating route context: {e}")
        
        return context
    
    def _generate_insights(self, external_context: Dict[str, Any], 
                          internal_context: Dict[str, Any],
                          origin: str, destination: str,
                          dep_date: datetime, ret_date: Optional[datetime]) -> List[ContextInsight]:
        """Generate actionable insights from context data"""
        insights = []
        
        # Holiday insights
        if external_context['holidays']['impact'] == 'high':
            insights.append(ContextInsight(
                type='warning',
                category='pricing',
                title='Holiday Travel Period',
                description='Traveling during a major holiday period - expect higher prices and limited availability',
                impact='high',
                source='holiday_calendar',
                relevance_score=0.9
            ))
        
        # Weather insights
        if external_context['weather']['origin_weather_risk'] == 'high':
            insights.append(ContextInsight(
                type='warning',
                category='weather',
                title='Weather Risk at Origin',
                description='High weather risk at departure airport - consider travel insurance',
                impact='medium',
                source='weather_patterns',
                relevance_score=0.7
            ))
        
        # Event insights
        if external_context['events']['impact'] == 'high':
            insights.append(ContextInsight(
                type='warning',
                category='events',
                title='Major Event Impact',
                description='Major event during travel dates - book early and expect higher prices',
                impact='high',
                source='events_calendar',
                relevance_score=0.8
            ))
        
        # Seasonal insights
        if external_context['seasonal']['peak_travel']:
            insights.append(ContextInsight(
                type='suggestion',
                category='pricing',
                title='Peak Season Pricing',
                description=f"Peak season travel detected - prices may be {external_context['seasonal']['pricing_multiplier']}x higher",
                impact='high',
                source='seasonal_analysis',
                relevance_score=0.8
            ))
        
        # Airport congestion insights
        if origin in self.airport_congestion or destination in self.airport_congestion:
            insights.append(ContextInsight(
                type='tip',
                category='timing',
                title='Airport Congestion',
                description='Consider off-peak flight times to avoid congestion and delays',
                impact='medium',
                source='airport_data',
                relevance_score=0.6
            ))
        
        # Booking timing insights
        days_until_travel = (dep_date - datetime.now()).days
        if days_until_travel < 7:
            insights.append(ContextInsight(
                type='warning',
                category='pricing',
                title='Last-Minute Booking',
                description='Booking less than 7 days in advance - expect premium pricing',
                impact='high',
                source='booking_patterns',
                relevance_score=0.9
            ))
        elif days_until_travel > 90:
            insights.append(ContextInsight(
                type='suggestion',
                category='pricing',
                title='Early Booking Advantage',
                description='Booking well in advance - good opportunity for deals',
                impact='low',
                source='booking_patterns',
                relevance_score=0.6
            ))
        
        return insights
    
    def _check_calendar_conflicts(self, dep_date: datetime, ret_date: Optional[datetime]) -> Dict[str, Any]:
        """Check for calendar conflicts (simplified)"""
        return {
            'conflicts': [],
            'recommendations': [],
            'impact': 'none'
        }
    
    def _get_budget_context(self, passenger_count: int, class_preference: str) -> Dict[str, Any]:
        """Get budget-related context"""
        base_prices = {
            'economy': 300,
            'premium_economy': 600,
            'business': 1200,
            'first': 2400
        }
        
        estimated_cost = base_prices.get(class_preference, 300) * passenger_count
        
        return {
            'estimated_cost': estimated_cost,
            'class_multiplier': {
                'economy': 1.0,
                'premium_economy': 2.0,
                'business': 4.0,
                'first': 8.0
            }.get(class_preference, 1.0),
            'passenger_discount': 0.05 * (passenger_count - 1) if passenger_count > 1 else 0
        }
    
    def _get_season(self, date: datetime) -> str:
        """Get season for a given date"""
        month = date.month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'
    
    def _get_weather_description(self, pattern_name: str) -> str:
        """Get human-readable weather description"""
        descriptions = {
            'hurricane_season': 'Hurricane season in effect - potential for delays and cancellations',
            'winter_storms': 'Winter storm season - increased risk of weather delays',
            'fog_season': 'Fog season at San Francisco area airports - morning delays possible'
        }
        return descriptions.get(pattern_name, 'Weather pattern detected')
    
    def _get_airport_coordinates(self, airport_code: str) -> Optional[Tuple[float, float]]:
        """Get airport coordinates (simplified - would use airport database)"""
        airport_coords = {
            'LAX': (33.9425, -118.4081),
            'JFK': (40.6413, -73.7781),
            'ORD': (41.9742, -87.9073),
            'ATL': (33.6407, -84.4277),
            'DFW': (32.8998, -97.0403),
            'DEN': (39.8561, -104.6737),
            'SFO': (37.6213, -122.3790),
            'SEA': (47.4502, -122.3088),
            'MIA': (25.7959, -80.2870),
            'BOS': (42.3656, -71.0096)
        }
        return airport_coords.get(airport_code)
    
    def _estimate_flight_duration(self, distance: float) -> int:
        """Estimate flight duration in minutes"""
        # Average commercial flight speed: 500 mph
        # Add 30 minutes for taxi, takeoff, landing
        return int((distance / 500) * 60) + 30
    
    def _calculate_context_confidence(self, external_context: Dict[str, Any], 
                                    internal_context: Dict[str, Any]) -> float:
        """Calculate confidence in context data"""
        confidence = 0.0
        
        # External data confidence
        if external_context['holidays']['impact'] != 'none':
            confidence += 0.2
        if external_context['weather']['origin_weather_risk'] != 'none':
            confidence += 0.15
        if external_context['events']['impact'] != 'none':
            confidence += 0.15
        if external_context['seasonal']['peak_travel']:
            confidence += 0.2
        
        # Internal data confidence
        if internal_context['user_preferences']:
            confidence += 0.15
        if internal_context['travel_history']:
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _get_default_context(self) -> TravelContext:
        """Return default context when errors occur"""
        return TravelContext(
            external_context={},
            internal_context={},
            insights=[],
            warnings=[],
            suggestions=[],
            confidence=0.0
        )


# Example usage
if __name__ == "__main__":
    engine = ContextEngine()
    
    # Test context generation
    context = engine.get_context(
        origin='LAX',
        destination='JFK',
        departure_date='2024-08-15',
        return_date='2024-08-22',
        passenger_count=2,
        class_preference='business'
    )
    
    print("Context Analysis Results:")
    print(f"Confidence: {context.confidence:.2f}")
    print(f"Warnings: {len(context.warnings)}")
    print(f"Suggestions: {len(context.suggestions)}")
    print(f"Insights: {len(context.insights)}")
    
    for insight in context.insights:
        print(f"\n{insight.type.upper()}: {insight.title}")
        print(f"  {insight.description}")
        print(f"  Impact: {insight.impact}, Relevance: {insight.relevance_score:.1f}")
    
    print(f"\nExternal Context Keys: {list(context.external_context.keys())}")
    print(f"Internal Context Keys: {list(context.internal_context.keys())}")