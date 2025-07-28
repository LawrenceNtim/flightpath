"""
Natural Language Parser for FlightPath
Processes natural language flight queries and extracts structured search parameters
"""

import re
import spacy
from datetime import datetime, timedelta
from dateutil.parser import parse as date_parse
from typing import Dict, List, Optional, Tuple, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlightQueryParser:
    """
    Natural Language Parser for flight queries
    Handles queries like "wedding by 12pm August 15th, leave Sunday from LA to NY"
    """
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Successfully loaded spaCy English model")
        except OSError:
            logger.error("spaCy English model not found. Run: python -m spacy download en_core_web_sm")
            raise
        
        # Airport code mappings
        self.airport_codes = {
            # Major US airports
            'los angeles': 'LAX', 'la': 'LAX', 'lax': 'LAX',
            'new york': 'JFK', 'ny': 'JFK', 'nyc': 'JFK', 'jfk': 'JFK',
            'newark': 'EWR', 'ewr': 'EWR',
            'laguardia': 'LGA', 'lga': 'LGA',
            'chicago': 'ORD', 'ord': 'ORD',
            'san francisco': 'SFO', 'sf': 'SFO', 'sfo': 'SFO',
            'miami': 'MIA', 'mia': 'MIA',
            'dallas': 'DFW', 'dfw': 'DFW',
            'denver': 'DEN', 'den': 'DEN',
            'seattle': 'SEA', 'sea': 'SEA',
            'boston': 'BOS', 'bos': 'BOS',
            'atlanta': 'ATL', 'atl': 'ATL',
            'phoenix': 'PHX', 'phx': 'PHX',
            'las vegas': 'LAS', 'vegas': 'LAS', 'las': 'LAS',
            'orlando': 'MCO', 'mco': 'MCO',
            'washington': 'DCA', 'dc': 'DCA', 'dca': 'DCA',
            'houston': 'IAH', 'iah': 'IAH',
            'philadelphia': 'PHL', 'philly': 'PHL', 'phl': 'PHL',
            'detroit': 'DTW', 'dtw': 'DTW',
            'minneapolis': 'MSP', 'msp': 'MSP',
            'salt lake city': 'SLC', 'slc': 'SLC',
            'portland': 'PDX', 'pdx': 'PDX',
            'san diego': 'SAN', 'san': 'SAN',
            'sacramento': 'SMF', 'smf': 'SMF',
            'oakland': 'OAK', 'oak': 'OAK',
            'san jose': 'SJC', 'sjc': 'SJC',
            'santa barbara': 'SBA', 'sba': 'SBA',
            'burbank': 'BUR', 'bur': 'BUR',
            'long beach': 'LGB', 'lgb': 'LGB',
            'orange county': 'SNA', 'sna': 'SNA',
            'ontario': 'ONT', 'ont': 'ONT',
            'palm springs': 'PSP', 'psp': 'PSP',
            'reno': 'RNO', 'rno': 'RNO',
            'fresno': 'FAT', 'fat': 'FAT',
            'bakersfield': 'BFL', 'bfl': 'BFL',
            'monterey': 'MRY', 'mry': 'MRY',
            'santa maria': 'SMX', 'smx': 'SMX',
            'santa rosa': 'STS', 'sts': 'STS',
            'redding': 'RDD', 'rdd': 'RDD',
            'stockton': 'SCK', 'sck': 'SCK',
            'modesto': 'MOD', 'mod': 'MOD',
            'visalia': 'VIS', 'vis': 'VIS',
            'eureka': 'ACV', 'acv': 'ACV',
            'chico': 'CIC', 'cic': 'CIC',
            'lake tahoe': 'TVL', 'tvl': 'TVL',
            'mammoth': 'MMH', 'mmh': 'MMH',
            'bishop': 'BIH', 'bih': 'BIH',
            'inyokern': 'IYK', 'iyk': 'IYK',
            'imperial': 'IPL', 'ipl': 'IPL',
            'san luis obispo': 'SBP', 'slo': 'SBP', 'sbp': 'SBP'
        }
        
        # Time-related patterns
        self.time_patterns = {
            'by': r'by\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            'at': r'at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            'before': r'before\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            'after': r'after\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            'around': r'around\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)'
        }
        
        # Flexibility indicators
        self.flexibility_patterns = {
            'flexible': r'flexible|any\s+time|doesn\'t\s+matter|open',
            'exact': r'exact|precise|specific|must\s+be',
            'prefer': r'prefer|would\s+like|ideally',
            'avoid': r'avoid|not|don\'t\s+want'
        }
        
        # Event types that might affect pricing/availability
        self.event_types = {
            'wedding': 'special_event',
            'conference': 'business_event',
            'vacation': 'leisure',
            'business': 'business_event',
            'funeral': 'emergency',
            'emergency': 'emergency',
            'holiday': 'holiday',
            'graduation': 'special_event',
            'anniversary': 'special_event',
            'birthday': 'special_event'
        }
        
        # Travel class preferences
        self.class_keywords = {
            'first': 'first',
            'business': 'business',
            'premium': 'premium_economy',
            'economy': 'economy',
            'coach': 'economy',
            'cheap': 'economy',
            'luxury': 'first',
            'comfortable': 'business'
        }
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Main parsing function that converts natural language to structured data
        """
        try:
            logger.info(f"Parsing query: {query}")
            
            # Clean and normalize the query
            normalized_query = self._normalize_query(query)
            
            # Process with spaCy
            doc = self.nlp(normalized_query)
            
            # Extract structured components
            result = {
                'origin': self._extract_origin(doc, normalized_query),
                'destination': self._extract_destination(doc, normalized_query),
                'departure_date': self._extract_departure_date(doc, normalized_query),
                'return_date': self._extract_return_date(doc, normalized_query),
                'time_constraints': self._extract_time_constraints(normalized_query),
                'flexibility': self._extract_flexibility(normalized_query),
                'passenger_count': self._extract_passenger_count(doc, normalized_query),
                'class_preference': self._extract_class_preference(normalized_query),
                'event_type': self._extract_event_type(normalized_query),
                'budget_indicators': self._extract_budget_indicators(normalized_query),
                'urgency': self._extract_urgency(normalized_query),
                'parsed_entities': self._extract_entities(doc),
                'confidence': self._calculate_confidence(doc, normalized_query)
            }
            
            logger.info(f"Parsed result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            return self._get_default_result()
    
    def _normalize_query(self, query: str) -> str:
        """Normalize the query for better parsing"""
        # Convert to lowercase
        query = query.lower()
        
        # Replace common abbreviations
        replacements = {
            'tmrw': 'tomorrow',
            'asap': 'as soon as possible',
            'biz': 'business',
            'econ': 'economy',
            'redeye': 'red eye',
            'nonstop': 'non stop',
            'layover': 'connection'
        }
        
        for old, new in replacements.items():
            query = query.replace(old, new)
        
        return query
    
    def _extract_origin(self, doc, query: str) -> Optional[str]:
        """Extract departure city/airport"""
        # Look for patterns like "from X", "leaving X", "departing X"
        from_patterns = [
            r'from\s+([a-zA-Z\s]+?)(?:\s+to|\s+airport|\s+on|\s+at|$)',
            r'leaving\s+([a-zA-Z\s]+?)(?:\s+to|\s+airport|\s+on|\s+at|$)',
            r'departing\s+([a-zA-Z\s]+?)(?:\s+to|\s+airport|\s+on|\s+at|$)',
            r'out\s+of\s+([a-zA-Z\s]+?)(?:\s+to|\s+airport|\s+on|\s+at|$)'
        ]
        
        for pattern in from_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                return self._resolve_airport_code(location)
        
        return None
    
    def _extract_destination(self, doc, query: str) -> Optional[str]:
        """Extract arrival city/airport"""
        # Look for patterns like "to X", "going to X", "arriving at X"
        to_patterns = [
            r'to\s+([a-zA-Z\s]+?)(?:\s+on|\s+at|\s+by|\s+for|\s+airport|$)',
            r'going\s+to\s+([a-zA-Z\s]+?)(?:\s+on|\s+at|\s+by|\s+for|\s+airport|$)',
            r'arriving\s+(?:at|in)\s+([a-zA-Z\s]+?)(?:\s+on|\s+at|\s+by|\s+for|\s+airport|$)',
            r'destination\s+([a-zA-Z\s]+?)(?:\s+on|\s+at|\s+by|\s+for|\s+airport|$)'
        ]
        
        for pattern in to_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                return self._resolve_airport_code(location)
        
        return None
    
    def _extract_departure_date(self, doc, query: str) -> Optional[str]:
        """Extract departure date"""
        # Look for date entities first
        for ent in doc.ents:
            if ent.label_ == "DATE":
                try:
                    # Try to parse the date
                    parsed_date = date_parse(ent.text, fuzzy=True)
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
        
        # Look for day of week patterns
        day_patterns = [
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))',
            r'(this\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))'
        ]
        
        for pattern in day_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return self._resolve_day_to_date(match.group(1))
        
        # Look for relative dates
        relative_patterns = [
            r'(tomorrow|tmrw)',
            r'(today)',
            r'(next\s+week)',
            r'(this\s+week)',
            r'in\s+(\d+)\s+days?'
        ]
        
        for pattern in relative_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return self._resolve_relative_date(match.group(1))
        
        return None
    
    def _extract_return_date(self, doc, query: str) -> Optional[str]:
        """Extract return date if mentioned"""
        return_patterns = [
            r'return(?:ing)?\s+(?:on\s+)?([a-zA-Z0-9\s,]+)',
            r'coming\s+back\s+(?:on\s+)?([a-zA-Z0-9\s,]+)',
            r'back\s+(?:on\s+)?([a-zA-Z0-9\s,]+)'
        ]
        
        for pattern in return_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    parsed_date = date_parse(match.group(1), fuzzy=True)
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
        
        return None
    
    def _extract_time_constraints(self, query: str) -> Dict[str, Any]:
        """Extract time-related constraints"""
        constraints = {}
        
        for constraint_type, pattern in self.time_patterns.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                constraints[constraint_type] = match.group(1)
        
        return constraints
    
    def _extract_flexibility(self, query: str) -> Dict[str, Any]:
        """Extract flexibility indicators"""
        flexibility = {
            'dates_flexible': False,
            'times_flexible': False,
            'airports_flexible': False,
            'class_flexible': False
        }
        
        # Check for flexibility keywords
        if re.search(self.flexibility_patterns['flexible'], query, re.IGNORECASE):
            flexibility['dates_flexible'] = True
            flexibility['times_flexible'] = True
        
        # Check for specific flexibility mentions
        if re.search(r'flexible\s+dates?', query, re.IGNORECASE):
            flexibility['dates_flexible'] = True
        
        if re.search(r'flexible\s+times?', query, re.IGNORECASE):
            flexibility['times_flexible'] = True
        
        if re.search(r'any\s+airport', query, re.IGNORECASE):
            flexibility['airports_flexible'] = True
        
        return flexibility
    
    def _extract_passenger_count(self, doc, query: str) -> int:
        """Extract number of passengers"""
        # Look for number patterns
        number_patterns = [
            r'(\d+)\s+(?:passengers?|people|persons?|travelers?)',
            r'(?:for\s+)?(\d+)(?:\s+people)?',
            r'party\s+of\s+(\d+)',
            r'(\d+)\s+tickets?'
        ]
        
        for pattern in number_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Look for word numbers
        word_numbers = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        
        for word, num in word_numbers.items():
            if re.search(rf'\b{word}\s+(?:passengers?|people|persons?)', query, re.IGNORECASE):
                return num
        
        return 1  # Default to 1 passenger
    
    def _extract_class_preference(self, query: str) -> str:
        """Extract travel class preference"""
        for keyword, class_type in self.class_keywords.items():
            if re.search(rf'\b{keyword}\b', query, re.IGNORECASE):
                return class_type
        
        return 'economy'  # Default to economy
    
    def _extract_event_type(self, query: str) -> Optional[str]:
        """Extract event type if mentioned"""
        for event, category in self.event_types.items():
            if re.search(rf'\b{event}\b', query, re.IGNORECASE):
                return category
        
        return None
    
    def _extract_budget_indicators(self, query: str) -> Dict[str, Any]:
        """Extract budget-related information"""
        budget_info = {
            'budget_conscious': False,
            'luxury_preferred': False,
            'points_mentioned': False,
            'cash_mentioned': False
        }
        
        # Budget conscious keywords
        if re.search(r'cheap|budget|affordable|economical|save\s+money', query, re.IGNORECASE):
            budget_info['budget_conscious'] = True
        
        # Luxury keywords
        if re.search(r'luxury|premium|expensive|splurge|treat', query, re.IGNORECASE):
            budget_info['luxury_preferred'] = True
        
        # Points/miles keywords
        if re.search(r'points|miles|reward|redeem', query, re.IGNORECASE):
            budget_info['points_mentioned'] = True
        
        # Cash keywords
        if re.search(r'cash|money|dollars?|\$', query, re.IGNORECASE):
            budget_info['cash_mentioned'] = True
        
        return budget_info
    
    def _extract_urgency(self, query: str) -> str:
        """Extract urgency level"""
        if re.search(r'urgent|emergency|asap|immediately|rush', query, re.IGNORECASE):
            return 'high'
        elif re.search(r'soon|quickly|fast', query, re.IGNORECASE):
            return 'medium'
        else:
            return 'low'
    
    def _extract_entities(self, doc) -> List[Dict[str, str]]:
        """Extract named entities"""
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
        return entities
    
    def _calculate_confidence(self, doc, query: str) -> float:
        """Calculate parsing confidence score"""
        score = 0.0
        
        # Check if we found origin and destination
        if self._extract_origin(doc, query):
            score += 0.3
        if self._extract_destination(doc, query):
            score += 0.3
        if self._extract_departure_date(doc, query):
            score += 0.2
        
        # Check for time constraints
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.time_patterns.values()):
            score += 0.1
        
        # Check for class preference
        if any(re.search(rf'\b{keyword}\b', query, re.IGNORECASE) for keyword in self.class_keywords.keys()):
            score += 0.1
        
        return min(score, 1.0)
    
    def _resolve_airport_code(self, location: str) -> Optional[str]:
        """Resolve location name to airport code"""
        location = location.lower().strip()
        
        # Direct lookup
        if location in self.airport_codes:
            return self.airport_codes[location]
        
        # Fuzzy matching for partial matches
        for key, code in self.airport_codes.items():
            if key in location or location in key:
                return code
        
        # If it's already a 3-letter code, return as-is
        if len(location) == 3 and location.isalpha():
            return location.upper()
        
        return None
    
    def _resolve_day_to_date(self, day_text: str) -> str:
        """Convert day of week to actual date"""
        # This is a simplified implementation
        # In production, you'd want more sophisticated date resolution
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        today = datetime.now()
        
        if day_text.lower() in days:
            target_day = days[day_text.lower()]
            days_ahead = target_day - today.weekday()
            
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            target_date = today + timedelta(days=days_ahead)
            return target_date.strftime('%Y-%m-%d')
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _resolve_relative_date(self, relative_text: str) -> str:
        """Convert relative date to actual date"""
        today = datetime.now()
        
        if relative_text.lower() in ['tomorrow', 'tmrw']:
            return (today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif relative_text.lower() == 'today':
            return today.strftime('%Y-%m-%d')
        elif 'next week' in relative_text.lower():
            return (today + timedelta(days=7)).strftime('%Y-%m-%d')
        elif 'this week' in relative_text.lower():
            return (today + timedelta(days=3)).strftime('%Y-%m-%d')
        
        return today.strftime('%Y-%m-%d')
    
    def _get_default_result(self) -> Dict[str, Any]:
        """Return default result structure"""
        return {
            'origin': None,
            'destination': None,
            'departure_date': None,
            'return_date': None,
            'time_constraints': {},
            'flexibility': {
                'dates_flexible': False,
                'times_flexible': False,
                'airports_flexible': False,
                'class_flexible': False
            },
            'passenger_count': 1,
            'class_preference': 'economy',
            'event_type': None,
            'budget_indicators': {
                'budget_conscious': False,
                'luxury_preferred': False,
                'points_mentioned': False,
                'cash_mentioned': False
            },
            'urgency': 'low',
            'parsed_entities': [],
            'confidence': 0.0
        }
    
    def convert_to_flight_data(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Convert parsed query to FlightData format"""
        return {
            'origin': parsed_query.get('origin', ''),
            'destination': parsed_query.get('destination', ''),
            'departure_date': parsed_query.get('departure_date', ''),
            'return_date': parsed_query.get('return_date'),
            'passenger_count': parsed_query.get('passenger_count', 1),
            'class_preference': parsed_query.get('class_preference', 'economy'),
            'flexible_dates': parsed_query.get('flexibility', {}).get('dates_flexible', False),
            'budget_limit': None  # This would need to be extracted from budget indicators
        }


# Example usage and testing
if __name__ == "__main__":
    parser = FlightQueryParser()
    
    # Test queries
    test_queries = [
        "wedding by 12pm August 15th, leave Sunday from LA to NY",
        "need to get from San Francisco to Chicago tomorrow morning",
        "business trip from Miami to Denver next Tuesday, first class",
        "family vacation to Orlando from Boston, 4 passengers, flexible dates",
        "emergency flight from Seattle to Atlanta ASAP",
        "cheap flight from Vegas to Phoenix this weekend",
        "going to conference in Dallas from Portland Monday, return Friday"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = parser.parse_query(query)
        print(f"Result: {result}")
        print(f"FlightData: {parser.convert_to_flight_data(result)}")
        print("-" * 50)