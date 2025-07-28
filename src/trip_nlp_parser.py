"""
Enhanced NLP Parser for Trip Orchestration
Handles complex trip scenarios with budget constraints, multi-destinations, and special requirements
"""

import re
import spacy
from datetime import datetime, timedelta
from dateutil.parser import parse as date_parse
from typing import Dict, List, Optional, Tuple, Any
import logging
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TripNLPParser:
    """
    Enhanced NLP Parser for complex trip orchestration scenarios
    """
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Successfully loaded spaCy English model for trip parsing")
        except OSError:
            logger.error("spaCy English model not found. Run: python -m spacy download en_core_web_sm")
            raise
        
        # Extended airport and location mappings
        self.location_mappings = {
            # Major cities and airports
            'san francisco': 'SFO', 'sf': 'SFO', 'sfo': 'SFO',
            'los angeles': 'LAX', 'la': 'LAX', 'lax': 'LAX', 'hollywood': 'LAX',
            'disneyland': 'LAX', 'disney': 'LAX', 'anaheim': 'LAX',
            'new york': 'JFK', 'ny': 'JFK', 'nyc': 'JFK', 'manhattan': 'JFK',
            'chicago': 'ORD', 'denver': 'DEN', 'seattle': 'SEA', 'miami': 'MIA',
            'dallas': 'DFW', 'atlanta': 'ATL', 'boston': 'BOS', 'vegas': 'LAS',
            'las vegas': 'LAS', 'phoenix': 'PHX', 'orlando': 'MCO'
        }
        
        # Budget extraction patterns
        self.budget_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $4,000.00 or $4000
            r'(\d{1,3}(?:,\d{3})*)\s*(?:dollars?|bucks?)',  # 4000 dollars
            r'budget\s+(?:of\s+)?(?:\$)?(\d{1,3}(?:,\d{3})*)',  # budget of $4000
            r'(\d{1,3}(?:,\d{3})*)\s+budget',  # 4000 budget
        ]
        
        # Family and group patterns
        self.group_patterns = {
            'family_of': r'family\s+of\s+(\d+)',
            'group_of': r'group\s+of\s+(\d+)',
            'party_of': r'party\s+of\s+(\d+)',
            'travelers': r'(\d+)\s+(?:travelers?|people|persons?)',
            'adults_children': r'(\d+)\s+adults?\s+(?:and\s+)?(\d+)\s+(?:children?|kids?)',
            'couple': r'couple',  # 2 people
            'solo': r'solo|alone|by\s+myself',  # 1 person
        }
        
        # Duration patterns
        self.duration_patterns = [
            r'(\d+)\s+(?:weeks?)',
            r'(\d+)\s+(?:days?)',
            r'(\d+)\s+(?:nights?)',
            r'for\s+(\d+)\s+(?:weeks?|days?|nights?)',
            r'(\d+)(?:-|\s+to\s+)(\d+)\s+(?:days?|weeks?)',  # 7-10 days
        ]
        
        # Special requirement patterns
        self.requirement_patterns = {
            'pets': r'(?:bring|bringing|with)\s+(?:my\s+)?(?:dog|cat|pet)',
            'business': r'(?:business|conference|work|meeting|corporate)',
            'hosting': r'(?:sister|family|friend|relative)\s+hosting',
            'accessibility': r'(?:wheelchair|accessibility|disabled|mobility)',
            'dietary': r'(?:vegetarian|vegan|gluten.free|kosher|halal)',
            'flexible_dates': r'flexible\s+(?:dates?|timing?)',
            'direct_flights': r'(?:direct|nonstop|non.stop)\s+flights?',
            'budget_conscious': r'(?:cheap|budget|affordable|economical)',
            'luxury': r'(?:luxury|premium|upscale|high.end)',
        }
        
        # Accommodation indicators
        self.accommodation_patterns = {
            'hotel': r'(?:hotel|resort|inn)',
            'airbnb': r'(?:airbnb|vacation\s+rental|rental)',
            'family_hosting': r'(?:staying\s+with|hosted\s+by|sister\s+hosting)',
            'camping': r'(?:camping|campground|rv)',
            'mixed': r'(?:mix\s+of|different\s+types)',
        }
        
        # Activity and purpose patterns
        self.activity_patterns = {
            'theme_park': r'(?:disneyland|disney|theme\s+park|amusement\s+park)',
            'conference': r'(?:conference|convention|summit|expo)',
            'wedding': r'(?:wedding|marriage|ceremony)',
            'vacation': r'(?:vacation|holiday|getaway|leisure)',
            'business': r'(?:business|work|corporate|meeting)',
            'family_visit': r'(?:visit\s+family|family\s+visit|see\s+relatives)',
            'sightseeing': r'(?:sightseeing|tourist|tourism|attractions)',
        }
        
        # Date flexibility patterns
        self.flexibility_patterns = {
            'very_flexible': r'(?:very\s+flexible|completely\s+flexible|any\s+time)',
            'somewhat_flexible': r'(?:somewhat\s+flexible|±\s*\d+\s+days?)',
            'specific_dates': r'(?:exact|specific|must\s+be|fixed)\s+dates?',
        }
    
    def parse_trip_request(self, query: str) -> Dict[str, Any]:
        """
        Main parsing function for complex trip requests
        """
        try:
            logger.info(f"Parsing trip request: {query}")
            
            # Clean and normalize the query
            normalized_query = self._normalize_query(query)
            
            # Process with spaCy
            doc = self.nlp(normalized_query)
            
            # Extract all components
            result = {
                'original_query': query,
                'trip_summary': self._extract_trip_summary(normalized_query),
                'budget': self._extract_budget(normalized_query),
                'passenger_count': self._extract_passenger_count(normalized_query),
                'group_composition': self._extract_group_composition(normalized_query),
                'origin': self._extract_origin(doc, normalized_query),
                'destinations': self._extract_destinations(doc, normalized_query),
                'destination': None,  # For compatibility
                'duration_days': self._extract_duration(normalized_query),
                'start_date': self._extract_start_date(doc, normalized_query),
                'end_date': None,  # Calculated from duration
                'flexible_dates': self._extract_flexibility(normalized_query),
                'accommodation_preferences': self._extract_accommodation_preferences(normalized_query),
                'special_requirements': self._extract_special_requirements(normalized_query),
                'activities': self._extract_activities(normalized_query),
                'purposes': self._extract_purposes(normalized_query),
                'business_portion': self._extract_business_portion(normalized_query),
                'tax_optimization': self._check_tax_optimization(normalized_query),
                'has_pets': self._has_pets(normalized_query),
                'has_business': self._has_business(normalized_query),
                'budget_constraints': self._extract_budget_constraints(normalized_query),
                'confidence': 0.0,
                'parsed_entities': self._extract_entities(doc)
            }
            
            # Post-process and validate
            result = self._post_process_results(result)
            result['confidence'] = self._calculate_confidence(result)
            
            # Set destination for compatibility
            if result['destinations']:
                result['destination'] = result['destinations'][0]
            
            logger.info(f"Trip parsing complete. Confidence: {result['confidence']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing trip request: {e}")
            return self._get_default_trip_result()
    
    def _normalize_query(self, query: str) -> str:
        """Normalize the query for better parsing"""
        query = query.lower()
        
        # Expand common abbreviations
        replacements = {
            'w/': 'with',
            '&': 'and',
            'biz': 'business',
            'conf': 'conference',
            'fam': 'family',
            'wks': 'weeks',
            'nts': 'nights',
            'incl': 'including',
            'excl': 'excluding',
        }
        
        for old, new in replacements.items():
            query = query.replace(old, new)
        
        return query
    
    def _extract_trip_summary(self, query: str) -> str:
        """Extract a brief summary of the trip"""
        # Find key elements for summary
        budget_match = re.search(r'\$\d+', query)
        duration_match = re.search(r'\d+\s+(?:weeks?|days?)', query)
        group_match = re.search(r'family\s+of\s+\d+|group\s+of\s+\d+|\d+\s+people', query)
        
        summary_parts = []
        
        if budget_match:
            summary_parts.append(budget_match.group())
        if group_match:
            summary_parts.append(group_match.group())
        if duration_match:
            summary_parts.append(duration_match.group())
        
        # Add purpose if clear
        if 'disneyland' in query:
            summary_parts.append('Disneyland trip')
        elif 'conference' in query:
            summary_parts.append('business conference')
        elif 'family' in query:
            summary_parts.append('family trip')
        
        return ', '.join(summary_parts) if summary_parts else 'Trip planning request'
    
    def _extract_budget(self, query: str) -> Optional[int]:
        """Extract budget from the query"""
        for pattern in self.budget_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                budget_str = match.group(1).replace(',', '')
                try:
                    return int(float(budget_str))
                except ValueError:
                    continue
        return None
    
    def _extract_passenger_count(self, query: str) -> int:
        """Extract number of passengers"""
        # Check for specific group patterns
        for pattern_name, pattern in self.group_patterns.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if pattern_name == 'couple':
                    return 2
                elif pattern_name == 'solo':
                    return 1
                elif pattern_name == 'adults_children':
                    adults = int(match.group(1))
                    children = int(match.group(2))
                    return adults + children
                else:
                    return int(match.group(1))
        
        # Default to 1
        return 1
    
    def _extract_group_composition(self, query: str) -> Dict[str, int]:
        """Extract detailed group composition"""
        composition = {'adults': 0, 'children': 0, 'infants': 0}
        
        # Look for adults and children breakdown
        adults_children_match = re.search(r'(\d+)\s+adults?\s+(?:and\s+)?(\d+)\s+(?:children?|kids?)', query)
        if adults_children_match:
            composition['adults'] = int(adults_children_match.group(1))
            composition['children'] = int(adults_children_match.group(2))
        else:
            # Assume composition based on total count
            total_count = self._extract_passenger_count(query)
            if total_count <= 2:
                composition['adults'] = total_count
            else:
                # Assume 2 adults minimum for families
                composition['adults'] = 2
                composition['children'] = max(0, total_count - 2)
        
        return composition
    
    def _extract_destinations(self, doc, query: str) -> List[str]:
        """Extract all destinations from the query"""
        destinations = []
        
        # Look for specific location patterns
        for location, code in self.location_mappings.items():
            if location in query and code not in destinations:
                destinations.append(code)
        
        # Look for "and" patterns like "LA and SF"
        and_pattern = r'(\w+(?:\s+\w+)?)\s+and\s+(\w+(?:\s+\w+)?)'
        and_matches = re.findall(and_pattern, query)
        for match in and_matches:
            for location_part in match:
                location_part = location_part.strip().lower()
                if location_part in self.location_mappings:
                    code = self.location_mappings[location_part]
                    if code not in destinations:
                        destinations.append(code)
        
        # Use spaCy to find geographic entities
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:  # Geographic entities
                location = ent.text.lower()
                if location in self.location_mappings:
                    code = self.location_mappings[location]
                    if code not in destinations:
                        destinations.append(code)
        
        return destinations
    
    def _extract_origin(self, doc, query: str) -> Optional[str]:
        """Extract origin location"""
        # Look for "from X" patterns
        from_patterns = [
            r'from\s+([a-zA-Z\s]+?)(?:\s+to|\s+for|\s+in|$)',
            r'leaving\s+([a-zA-Z\s]+?)(?:\s+to|\s+for|\s+in|$)',
            r'departing\s+([a-zA-Z\s]+?)(?:\s+to|\s+for|\s+in|$)',
        ]
        
        for pattern in from_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                location = match.group(1).strip().lower()
                if location in self.location_mappings:
                    return self.location_mappings[location]
        
        # Default based on common patterns
        if 'sf' in query or 'san francisco' in query:
            return 'SFO'
        elif 'ny' in query or 'new york' in query:
            return 'JFK'
        
        return None
    
    def _extract_duration(self, query: str) -> int:
        """Extract trip duration in days"""
        for pattern in self.duration_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if 'week' in match.group():
                    weeks = int(re.search(r'(\d+)', match.group()).group(1))
                    return weeks * 7
                elif 'day' in match.group() or 'night' in match.group():
                    return int(re.search(r'(\d+)', match.group()).group(1))
        
        # Default duration based on trip type
        if 'weekend' in query:
            return 3
        elif 'week' in query:
            return 7
        else:
            return 5  # Default 5 days
    
    def _extract_start_date(self, doc, query: str) -> Optional[str]:
        """Extract start date from query"""
        # Look for date entities
        for ent in doc.ents:
            if ent.label_ == "DATE":
                try:
                    parsed_date = date_parse(ent.text, fuzzy=True)
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
        
        # Look for relative dates
        if 'next month' in query:
            next_month = datetime.now() + timedelta(days=30)
            return next_month.strftime('%Y-%m-%d')
        elif 'next week' in query:
            next_week = datetime.now() + timedelta(days=7)
            return next_week.strftime('%Y-%m-%d')
        
        # Default to 30 days from now
        default_date = datetime.now() + timedelta(days=30)
        return default_date.strftime('%Y-%m-%d')
    
    def _extract_flexibility(self, query: str) -> bool:
        """Check if dates are flexible"""
        return bool(re.search(self.flexibility_patterns['very_flexible'] + '|' + 
                             self.flexibility_patterns['somewhat_flexible'], query, re.IGNORECASE))
    
    def _extract_accommodation_preferences(self, query: str) -> List[str]:
        """Extract accommodation preferences"""
        preferences = []
        
        for accom_type, pattern in self.accommodation_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                preferences.append(accom_type)
        
        return preferences if preferences else ['mixed']
    
    def _extract_special_requirements(self, query: str) -> List[str]:
        """Extract special requirements"""
        requirements = []
        
        for req_type, pattern in self.requirement_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                requirements.append(req_type)
        
        return requirements
    
    def _extract_activities(self, query: str) -> List[str]:
        """Extract desired activities"""
        activities = []
        
        for activity_type, pattern in self.activity_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                activities.append(activity_type)
        
        return activities
    
    def _extract_purposes(self, query: str) -> List[str]:
        """Extract trip purposes"""
        purposes = []
        
        # Map activities to purposes
        activity_to_purpose = {
            'theme_park': 'family entertainment',
            'conference': 'business conference',
            'wedding': 'special event',
            'vacation': 'leisure travel',
            'business': 'business travel',
            'family_visit': 'family visit',
            'sightseeing': 'tourism'
        }
        
        activities = self._extract_activities(query)
        for activity in activities:
            if activity in activity_to_purpose:
                purpose = activity_to_purpose[activity]
                if purpose not in purposes:
                    purposes.append(purpose)
        
        return purposes if purposes else ['leisure travel']
    
    def _extract_business_portion(self, query: str) -> float:
        """Extract what percentage is business-related"""
        if not self._has_business(query):
            return 0.0
        
        # If mixed business/personal
        if re.search(r'(?:and|with|plus).*(?:family|personal|vacation)', query, re.IGNORECASE):
            return 0.5  # 50% business
        
        # Pure business trip
        if re.search(r'(?:business|conference|work)\s+(?:trip|travel)', query, re.IGNORECASE):
            return 1.0  # 100% business
        
        return 0.3  # Default partial business
    
    def _check_tax_optimization(self, query: str) -> bool:
        """Check if tax optimization is relevant"""
        return self._has_business(query) or 'tax' in query or 'deduction' in query
    
    def _has_pets(self, query: str) -> bool:
        """Check if pets are involved"""
        return bool(re.search(self.requirement_patterns['pets'], query, re.IGNORECASE))
    
    def _has_business(self, query: str) -> bool:
        """Check if business component exists"""
        return bool(re.search(self.requirement_patterns['business'], query, re.IGNORECASE))
    
    def _extract_budget_constraints(self, query: str) -> Dict[str, Any]:
        """Extract budget-related constraints"""
        constraints = {
            'strict_budget': False,
            'budget_conscious': False,
            'luxury_preferred': False,
            'specific_allocations': {}
        }
        
        if re.search(r'(?:strict|exact|must\s+be)\s+budget', query, re.IGNORECASE):
            constraints['strict_budget'] = True
        
        if re.search(self.requirement_patterns['budget_conscious'], query, re.IGNORECASE):
            constraints['budget_conscious'] = True
        
        if re.search(self.requirement_patterns['luxury'], query, re.IGNORECASE):
            constraints['luxury_preferred'] = True
        
        return constraints
    
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
    
    def _post_process_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process and validate results"""
        # Ensure destinations list is not empty
        if not result['destinations'] and result.get('destination'):
            result['destinations'] = [result['destination']]
        
        # Set end date based on start date and duration
        if result['start_date'] and result['duration_days']:
            start_date = datetime.strptime(result['start_date'], '%Y-%m-%d')
            end_date = start_date + timedelta(days=result['duration_days'] - 1)
            result['end_date'] = end_date.strftime('%Y-%m-%d')
        
        # Validate passenger count
        if result['passenger_count'] <= 0:
            result['passenger_count'] = 1
        
        # Ensure budget is reasonable
        if result['budget'] and result['budget'] < 100:
            result['budget'] = None  # Likely parsing error
        
        return result
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate parsing confidence"""
        score = 0.0
        
        # Budget extraction (20%)
        if result['budget']:
            score += 0.2
        
        # Destinations (25%)
        if result['destinations']:
            score += 0.25
        
        # Duration (15%)
        if result['duration_days']:
            score += 0.15
        
        # Passenger count (10%)
        if result['passenger_count'] > 0:
            score += 0.1
        
        # Special requirements (15%)
        if result['special_requirements']:
            score += 0.15
        
        # Activities/purposes (15%)
        if result['activities'] or result['purposes']:
            score += 0.15
        
        return min(score, 1.0)
    
    def _get_default_trip_result(self) -> Dict[str, Any]:
        """Return default result structure for trip parsing"""
        return {
            'original_query': '',
            'trip_summary': 'Trip parsing failed',
            'budget': None,
            'passenger_count': 1,
            'group_composition': {'adults': 1, 'children': 0, 'infants': 0},
            'origin': None,
            'destinations': [],
            'destination': None,
            'duration_days': 7,
            'start_date': None,
            'end_date': None,
            'flexible_dates': False,
            'accommodation_preferences': ['mixed'],
            'special_requirements': [],
            'activities': [],
            'purposes': ['leisure travel'],
            'business_portion': 0.0,
            'tax_optimization': False,
            'has_pets': False,
            'has_business': False,
            'budget_constraints': {
                'strict_budget': False,
                'budget_conscious': False,
                'luxury_preferred': False,
                'specific_allocations': {}
            },
            'confidence': 0.0,
            'parsed_entities': []
        }


# Example usage and testing
if __name__ == "__main__":
    parser = TripNLPParser()
    
    # Test scenarios
    test_queries = [
        "$4000 budget, family of 4, SF to Disneyland, flexible dates",
        "LA and SF for 2 weeks, sister hosting, bring dog, music conference",
        "Business trip to NYC for 5 days, luxury hotel, conference attendance",
        "Weekend getaway to Vegas with my wife, budget conscious",
        "Family vacation to Orlando for 7 days, 2 adults and 3 children"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = parser.parse_trip_request(query)
        print(f"Summary: {result['trip_summary']}")
        print(f"Budget: ${result['budget']}" if result['budget'] else "Budget: Not specified")
        print(f"Passengers: {result['passenger_count']}")
        print(f"Destinations: {result['destinations']}")
        print(f"Duration: {result['duration_days']} days")
        print(f"Requirements: {result['special_requirements']}")
        print(f"Business: {result['has_business']}, Pets: {result['has_pets']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print("-" * 60)