"""
Trip Orchestration Engine for FlightPath
Handles complex multi-component trips with budget optimization and constraint handling
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
from decimal import Decimal, ROUND_HALF_UP
import decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TripType(Enum):
    """Trip type enumeration"""
    FAMILY_VACATION = "family_vacation"
    BUSINESS_TRIP = "business_trip"
    MIXED_BUSINESS_PERSONAL = "mixed_business_personal"
    MULTI_CITY = "multi_city"
    EXTENDED_STAY = "extended_stay"
    EVENT_BASED = "event_based"

class AccommodationType(Enum):
    """Accommodation type enumeration"""
    HOTEL = "hotel"
    AIRBNB = "airbnb"
    FAMILY_HOSTING = "family_hosting"
    BUSINESS_ACCOMMODATION = "business_accommodation"
    PET_FRIENDLY = "pet_friendly"
    MIXED = "mixed"

class RequirementType(Enum):
    """Special requirement types"""
    PET_TRAVEL = "pet_travel"
    BUSINESS_EVENT = "business_event"
    FAMILY_HOSTING = "family_hosting"
    ACCESSIBILITY = "accessibility"
    DIETARY = "dietary"
    CONFERENCE = "conference"
    TAX_DEDUCTION = "tax_deduction"

@dataclass
class TripBudget:
    """Trip budget breakdown"""
    total_budget: Decimal
    flights_budget: Decimal = Decimal('0')
    accommodation_budget: Decimal = Decimal('0')
    activities_budget: Decimal = Decimal('0')
    food_budget: Decimal = Decimal('0')
    transport_budget: Decimal = Decimal('0')
    pet_budget: Decimal = Decimal('0')
    business_budget: Decimal = Decimal('0')
    contingency_budget: Decimal = Decimal('0')
    
    def __post_init__(self):
        """Calculate budget allocations if not specified"""
        if all(getattr(self, field.name) == Decimal('0') for field in self.__dataclass_fields__.values() 
               if field.name != 'total_budget'):
            self._calculate_default_allocations()
    
    def _calculate_default_allocations(self):
        """Calculate default budget allocations"""
        self.flights_budget = self.total_budget * Decimal('0.35')  # 35% for flights
        self.accommodation_budget = self.total_budget * Decimal('0.30')  # 30% for accommodation
        self.activities_budget = self.total_budget * Decimal('0.15')  # 15% for activities
        self.food_budget = self.total_budget * Decimal('0.15')  # 15% for food
        self.transport_budget = self.total_budget * Decimal('0.03')  # 3% for local transport
        self.contingency_budget = self.total_budget * Decimal('0.02')  # 2% contingency

@dataclass
class TripSegment:
    """Individual trip segment"""
    origin: str
    destination: str
    start_date: str
    end_date: str
    accommodation_type: AccommodationType
    purpose: str
    requirements: List[RequirementType]
    budget_allocation: Decimal
    is_business: bool = False
    
@dataclass
class SpecialRequirement:
    """Special requirement for the trip"""
    type: RequirementType
    description: str
    cost_impact: Decimal = Decimal('0')
    logistics: Dict[str, Any] = None
    business_deductible: bool = False

@dataclass
class Activity:
    """Trip activity"""
    name: str
    location: str
    date: str
    cost: Decimal
    duration_hours: int
    category: str
    is_business: bool = False
    booking_required: bool = False

@dataclass
class TripItinerary:
    """Complete trip itinerary"""
    trip_id: str
    trip_type: TripType
    total_duration_days: int
    segments: List[TripSegment]
    budget: TripBudget
    requirements: List[SpecialRequirement]
    activities: List[Activity]
    cost_breakdown: Dict[str, Decimal]
    optimization_score: float
    tax_savings: Decimal = Decimal('0')
    business_percentage: float = 0.0

class TripOrchestrationEngine:
    """
    Main orchestration engine for complex trip planning
    """
    
    def __init__(self):
        # Accommodation cost data (per night)
        self.accommodation_costs = {
            AccommodationType.HOTEL: {
                'budget': Decimal('80'),
                'mid_range': Decimal('150'),
                'luxury': Decimal('300')
            },
            AccommodationType.AIRBNB: {
                'budget': Decimal('60'),
                'mid_range': Decimal('120'),
                'luxury': Decimal('250')
            },
            AccommodationType.FAMILY_HOSTING: {
                'budget': Decimal('0'),
                'mid_range': Decimal('0'),
                'luxury': Decimal('25')  # Host gift
            },
            AccommodationType.PET_FRIENDLY: {
                'budget': Decimal('100'),
                'mid_range': Decimal('180'),
                'luxury': Decimal('350')
            }
        }
        
        # Activity cost data
        self.activity_costs = {
            'theme_park': {'adult': Decimal('120'), 'child': Decimal('100')},
            'museum': {'adult': Decimal('25'), 'child': Decimal('15')},
            'conference': {'adult': Decimal('500'), 'child': Decimal('0')},
            'dining_fine': {'adult': Decimal('80'), 'child': Decimal('40')},
            'dining_casual': {'adult': Decimal('25'), 'child': Decimal('15')},
            'transport_rental': {'daily': Decimal('45')},
            'pet_daycare': {'daily': Decimal('35')}
        }
        
        # Pet travel costs
        self.pet_costs = {
            'airline_fee': Decimal('125'),
            'pet_carrier': Decimal('80'),
            'health_certificate': Decimal('150'),
            'pet_insurance': Decimal('50')
        }
        
        # Business tax deduction rates
        self.tax_rates = {
            'meals': 0.5,  # 50% deductible
            'accommodation': 1.0,  # 100% deductible
            'transport': 1.0,  # 100% deductible
            'conference': 1.0,  # 100% deductible
            'entertainment': 0.5  # 50% deductible
        }
    
    async def orchestrate_trip(self, parsed_request: Dict[str, Any]) -> TripItinerary:
        """
        Main orchestration method
        """
        try:
            logger.info(f"Orchestrating trip: {parsed_request.get('trip_summary', 'Unknown')}")
            
            # Determine trip type
            trip_type = self._determine_trip_type(parsed_request)
            
            # Create budget structure
            budget = self._create_budget(parsed_request)
            
            # Plan trip segments
            segments = self._plan_segments(parsed_request, budget)
            
            # Plan activities
            activities = self._plan_activities(parsed_request, segments, budget)
            
            # Handle special requirements
            requirements = self._handle_requirements(parsed_request)
            
            # Optimize budget allocation
            optimized_budget = await self._optimize_budget(budget, segments, activities, requirements)
            
            # Calculate business deductions
            tax_savings, business_percentage = self._calculate_tax_benefits(
                activities, requirements, optimized_budget
            )
            
            # Generate final cost breakdown
            cost_breakdown = self._generate_cost_breakdown(
                optimized_budget, segments, activities, requirements
            )
            
            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(
                parsed_request, optimized_budget, cost_breakdown
            )
            
            # Create itinerary
            itinerary = TripItinerary(
                trip_id=f"trip_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                trip_type=trip_type,
                total_duration_days=self._calculate_duration(segments),
                segments=segments,
                budget=optimized_budget,
                requirements=requirements,
                activities=activities,
                cost_breakdown=cost_breakdown,
                optimization_score=optimization_score,
                tax_savings=tax_savings,
                business_percentage=business_percentage
            )
            
            logger.info(f"Trip orchestrated successfully: {itinerary.trip_id}")
            return itinerary
            
        except Exception as e:
            logger.error(f"Error orchestrating trip: {e}")
            raise
    
    def _determine_trip_type(self, parsed_request: Dict[str, Any]) -> TripType:
        """Determine the type of trip based on parsed request"""
        purposes = parsed_request.get('purposes', [])
        destinations = parsed_request.get('destinations', [])
        duration = parsed_request.get('duration_days', 0)
        
        # Check for business indicators
        business_indicators = ['conference', 'business', 'work', 'meeting']
        has_business = any(indicator in ' '.join(purposes).lower() for indicator in business_indicators)
        
        # Check for family indicators
        family_indicators = ['family', 'kids', 'children', 'disneyland', 'theme park']
        has_family = any(indicator in ' '.join(purposes).lower() for indicator in family_indicators)
        
        if has_business and has_family:
            return TripType.MIXED_BUSINESS_PERSONAL
        elif has_business:
            return TripType.BUSINESS_TRIP
        elif has_family:
            return TripType.FAMILY_VACATION
        elif len(destinations) > 1:
            return TripType.MULTI_CITY
        elif duration > 14:
            return TripType.EXTENDED_STAY
        else:
            return TripType.FAMILY_VACATION
    
    def _create_budget(self, parsed_request: Dict[str, Any]) -> TripBudget:
        """Create budget structure from parsed request"""
        budget_value = parsed_request.get('budget', 4000)
        if budget_value is None:
            budget_value = 6000  # Default for complex trips without specified budget
        try:
            total_budget = Decimal(str(budget_value))
        except (TypeError, ValueError, decimal.InvalidOperation):
            total_budget = Decimal('6000')  # Safe default
        
        budget = TripBudget(total_budget=total_budget)
        
        # Adjust allocations based on trip characteristics
        if parsed_request.get('has_pets', False):
            budget.pet_budget = total_budget * Decimal('0.05')  # 5% for pet costs
            budget.accommodation_budget = total_budget * Decimal('0.25')  # Reduce accommodation
        
        if parsed_request.get('has_business', False):
            budget.business_budget = total_budget * Decimal('0.20')  # 20% for business
            budget.activities_budget = total_budget * Decimal('0.10')  # Reduce activities
        
        return budget
    
    def _plan_segments(self, parsed_request: Dict[str, Any], budget: TripBudget) -> List[TripSegment]:
        """Plan trip segments"""
        segments = []
        destinations = parsed_request.get('destinations', [])
        origin = parsed_request.get('origin', 'Unknown')
        duration_days = parsed_request.get('duration_days', 7)
        start_date = parsed_request.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        
        if not destinations:
            destinations = [parsed_request.get('destination', 'Unknown')]
        
        # Calculate days per destination
        days_per_destination = duration_days // len(destinations)
        remaining_days = duration_days % len(destinations)
        
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        current_origin = origin
        
        for i, destination in enumerate(destinations):
            segment_days = days_per_destination + (1 if i < remaining_days else 0)
            end_date = current_date + timedelta(days=segment_days - 1)
            
            # Determine accommodation type
            accommodation_type = self._determine_accommodation_type(parsed_request, destination)
            
            # Determine purpose
            purpose = self._determine_segment_purpose(parsed_request, destination)
            
            # Determine requirements
            requirements = self._determine_segment_requirements(parsed_request, destination)
            
            # Calculate budget allocation
            budget_allocation = budget.total_budget / len(destinations)
            
            segment = TripSegment(
                origin=current_origin,
                destination=destination,
                start_date=current_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                accommodation_type=accommodation_type,
                purpose=purpose,
                requirements=requirements,
                budget_allocation=budget_allocation,
                is_business=self._is_business_segment(parsed_request, destination)
            )
            
            segments.append(segment)
            
            # Update for next segment
            current_date = end_date + timedelta(days=1)
            current_origin = destination
        
        return segments
    
    def _determine_accommodation_type(self, parsed_request: Dict[str, Any], destination: str) -> AccommodationType:
        """Determine accommodation type for a destination"""
        hosting_keywords = ['sister hosting', 'family hosting', 'staying with']
        pet_keywords = ['dog', 'pet', 'cat']
        business_keywords = ['conference', 'business', 'work']
        
        request_text = ' '.join([
            parsed_request.get('original_query', ''),
            ' '.join(parsed_request.get('purposes', []))
        ]).lower()
        
        if any(keyword in request_text for keyword in hosting_keywords):
            return AccommodationType.FAMILY_HOSTING
        elif any(keyword in request_text for keyword in pet_keywords):
            return AccommodationType.PET_FRIENDLY
        elif any(keyword in request_text for keyword in business_keywords):
            return AccommodationType.HOTEL
        else:
            return AccommodationType.AIRBNB
    
    def _determine_segment_purpose(self, parsed_request: Dict[str, Any], destination: str) -> str:
        """Determine the purpose of a trip segment"""
        purposes = parsed_request.get('purposes', [])
        
        if 'disneyland' in destination.lower() or 'disney' in destination.lower():
            return 'Family vacation - Theme park'
        elif any('conference' in purpose.lower() for purpose in purposes):
            return 'Business - Conference'
        elif any('family' in purpose.lower() for purpose in purposes):
            return 'Family visit'
        else:
            return 'Leisure travel'
    
    def _determine_segment_requirements(self, parsed_request: Dict[str, Any], destination: str) -> List[RequirementType]:
        """Determine requirements for a segment"""
        requirements = []
        
        if parsed_request.get('has_pets', False):
            requirements.append(RequirementType.PET_TRAVEL)
        
        if parsed_request.get('has_business', False):
            requirements.append(RequirementType.BUSINESS_EVENT)
            requirements.append(RequirementType.TAX_DEDUCTION)
        
        if 'sister hosting' in parsed_request.get('original_query', '').lower():
            requirements.append(RequirementType.FAMILY_HOSTING)
        
        if 'conference' in parsed_request.get('original_query', '').lower():
            requirements.append(RequirementType.CONFERENCE)
        
        return requirements
    
    def _is_business_segment(self, parsed_request: Dict[str, Any], destination: str) -> bool:
        """Determine if a segment is business-related"""
        business_keywords = ['conference', 'business', 'work', 'meeting']
        request_text = parsed_request.get('original_query', '').lower()
        
        return any(keyword in request_text for keyword in business_keywords)
    
    def _plan_activities(self, parsed_request: Dict[str, Any], segments: List[TripSegment], budget: TripBudget) -> List[Activity]:
        """Plan activities for the trip"""
        activities = []
        
        for segment in segments:
            segment_activities = self._plan_segment_activities(segment, parsed_request, budget)
            activities.extend(segment_activities)
        
        return activities
    
    def _plan_segment_activities(self, segment: TripSegment, parsed_request: Dict[str, Any], budget: TripBudget) -> List[Activity]:
        """Plan activities for a specific segment"""
        activities = []
        segment_days = (datetime.strptime(segment.end_date, '%Y-%m-%d') - 
                       datetime.strptime(segment.start_date, '%Y-%m-%d')).days + 1
        
        daily_activity_budget = budget.activities_budget / len(parsed_request.get('destinations', [segment.destination])) / segment_days
        
        # Theme park activities (Disneyland)
        if 'disneyland' in segment.destination.lower():
            activities.extend(self._plan_theme_park_activities(segment, parsed_request, daily_activity_budget))
        
        # Business activities
        if segment.is_business:
            activities.extend(self._plan_business_activities(segment, parsed_request, daily_activity_budget))
        
        # General leisure activities
        activities.extend(self._plan_leisure_activities(segment, parsed_request, daily_activity_budget))
        
        return activities
    
    def _plan_theme_park_activities(self, segment: TripSegment, parsed_request: Dict[str, Any], daily_budget: Decimal) -> List[Activity]:
        """Plan theme park activities"""
        activities = []
        passenger_count = parsed_request.get('passenger_count', 4)
        adult_count = max(2, passenger_count - 2)  # Assume 2 adults minimum
        child_count = passenger_count - adult_count
        
        # Disneyland tickets
        ticket_cost = (adult_count * self.activity_costs['theme_park']['adult'] + 
                      child_count * self.activity_costs['theme_park']['child'])
        
        activities.append(Activity(
            name="Disneyland Park Admission",
            location=segment.destination,
            date=segment.start_date,
            cost=ticket_cost,
            duration_hours=12,
            category="theme_park",
            booking_required=True
        ))
        
        # Character dining
        dining_cost = adult_count * self.activity_costs['dining_fine']['adult'] + child_count * self.activity_costs['dining_fine']['child']
        activities.append(Activity(
            name="Character Dining Experience",
            location=segment.destination,
            date=segment.start_date,
            cost=dining_cost,
            duration_hours=2,
            category="dining",
            booking_required=True
        ))
        
        return activities
    
    def _plan_business_activities(self, segment: TripSegment, parsed_request: Dict[str, Any], daily_budget: Decimal) -> List[Activity]:
        """Plan business activities"""
        activities = []
        
        # Conference registration
        if RequirementType.CONFERENCE in segment.requirements:
            activities.append(Activity(
                name="Music Conference Registration",
                location=segment.destination,
                date=segment.start_date,
                cost=self.activity_costs['conference']['adult'],
                duration_hours=8,
                category="conference",
                is_business=True,
                booking_required=True
            ))
        
        # Business meals
        activities.append(Activity(
            name="Business Networking Dinner",
            location=segment.destination,
            date=segment.start_date,
            cost=self.activity_costs['dining_fine']['adult'],
            duration_hours=3,
            category="business_meal",
            is_business=True
        ))
        
        return activities
    
    def _plan_leisure_activities(self, segment: TripSegment, parsed_request: Dict[str, Any], daily_budget: Decimal) -> List[Activity]:
        """Plan general leisure activities"""
        activities = []
        
        # Local transportation
        segment_days = (datetime.strptime(segment.end_date, '%Y-%m-%d') - 
                       datetime.strptime(segment.start_date, '%Y-%m-%d')).days + 1
        
        if segment.accommodation_type != AccommodationType.FAMILY_HOSTING:
            transport_cost = segment_days * self.activity_costs['transport_rental']['daily']
            activities.append(Activity(
                name="Car Rental",
                location=segment.destination,
                date=segment.start_date,
                cost=transport_cost,
                duration_hours=24 * segment_days,
                category="transport"
            ))
        
        return activities
    
    def _handle_requirements(self, parsed_request: Dict[str, Any]) -> List[SpecialRequirement]:
        """Handle special requirements"""
        requirements = []
        
        # Pet travel requirements
        if parsed_request.get('has_pets', False):
            pet_requirement = SpecialRequirement(
                type=RequirementType.PET_TRAVEL,
                description="Dog travel arrangements and pet-friendly accommodations",
                cost_impact=sum(self.pet_costs.values()),
                logistics={
                    'airline_pet_fee': self.pet_costs['airline_fee'],
                    'pet_carrier_required': True,
                    'health_certificate_needed': True,
                    'pet_insurance_recommended': True
                }
            )
            requirements.append(pet_requirement)
        
        # Business requirements
        if parsed_request.get('has_business', False):
            business_requirement = SpecialRequirement(
                type=RequirementType.TAX_DEDUCTION,
                description="Business trip tax optimization and documentation",
                business_deductible=True,
                logistics={
                    'receipt_tracking': True,
                    'business_purpose_documentation': True,
                    'expense_categorization': True
                }
            )
            requirements.append(business_requirement)
        
        # Family hosting requirements
        if 'hosting' in parsed_request.get('original_query', '').lower():
            hosting_requirement = SpecialRequirement(
                type=RequirementType.FAMILY_HOSTING,
                description="Staying with family - coordinate arrangements and host gifts",
                cost_impact=Decimal('50'),  # Host gift
                logistics={
                    'coordinate_arrival_time': True,
                    'bring_host_gift': True,
                    'respect_house_rules': True
                }
            )
            requirements.append(hosting_requirement)
        
        return requirements
    
    async def _optimize_budget(self, budget: TripBudget, segments: List[TripSegment], 
                             activities: List[Activity], requirements: List[SpecialRequirement]) -> TripBudget:
        """Optimize budget allocation"""
        # Calculate actual costs
        total_activity_cost = sum(activity.cost for activity in activities)
        total_requirement_cost = sum(req.cost_impact for req in requirements)
        
        # Calculate accommodation costs
        total_accommodation_cost = Decimal('0')
        for segment in segments:
            segment_days = (datetime.strptime(segment.end_date, '%Y-%m-%d') - 
                           datetime.strptime(segment.start_date, '%Y-%m-%d')).days + 1
            
            if segment.accommodation_type == AccommodationType.FAMILY_HOSTING:
                cost_per_night = self.accommodation_costs[segment.accommodation_type]['luxury']
            else:
                cost_per_night = self.accommodation_costs[segment.accommodation_type]['mid_range']
            
            total_accommodation_cost += cost_per_night * segment_days
        
        # Adjust budget allocations
        budget.activities_budget = total_activity_cost
        budget.accommodation_budget = total_accommodation_cost
        budget.pet_budget = sum(req.cost_impact for req in requirements if req.type == RequirementType.PET_TRAVEL)
        
        # Ensure we don't exceed total budget
        allocated_budget = (budget.flights_budget + budget.accommodation_budget + 
                           budget.activities_budget + budget.pet_budget + 
                           budget.business_budget + budget.transport_budget)
        
        if allocated_budget > budget.total_budget:
            # Scale down proportionally
            scale_factor = budget.total_budget / allocated_budget
            budget.flights_budget *= scale_factor
            budget.accommodation_budget *= scale_factor
            budget.activities_budget *= scale_factor
            budget.transport_budget *= scale_factor
        
        # Set remaining as contingency
        used_budget = (budget.flights_budget + budget.accommodation_budget + 
                      budget.activities_budget + budget.pet_budget + 
                      budget.business_budget + budget.transport_budget)
        budget.contingency_budget = budget.total_budget - used_budget
        
        return budget
    
    def _calculate_tax_benefits(self, activities: List[Activity], requirements: List[SpecialRequirement], 
                               budget: TripBudget) -> Tuple[Decimal, float]:
        """Calculate tax benefits for business portions"""
        total_business_cost = Decimal('0')
        total_deductible = Decimal('0')
        
        # Business activities
        for activity in activities:
            if activity.is_business:
                if activity.category == 'conference':
                    deductible = activity.cost * Decimal(str(self.tax_rates['conference']))
                elif activity.category == 'business_meal':
                    deductible = activity.cost * Decimal(str(self.tax_rates['meals']))
                else:
                    deductible = activity.cost * Decimal(str(self.tax_rates['transport']))
                
                total_business_cost += activity.cost
                total_deductible += deductible
        
        # Business portion of accommodation and transport
        business_segments = sum(1 for segment in [] if segment.is_business)  # This would be calculated from segments
        if business_segments > 0:
            business_accommodation = budget.accommodation_budget * Decimal('0.5')  # Assume 50% business
            business_transport = budget.transport_budget * Decimal('0.5')
            
            total_business_cost += business_accommodation + business_transport
            total_deductible += (business_accommodation * Decimal(str(self.tax_rates['accommodation'])) + 
                               business_transport * Decimal(str(self.tax_rates['transport'])))
        
        # Calculate tax savings (assuming 25% tax rate)
        tax_savings = total_deductible * Decimal('0.25')
        
        # Calculate business percentage
        business_percentage = float(total_business_cost / budget.total_budget * 100) if budget.total_budget > 0 else 0
        
        return tax_savings, business_percentage
    
    def _generate_cost_breakdown(self, budget: TripBudget, segments: List[TripSegment], 
                                activities: List[Activity], requirements: List[SpecialRequirement]) -> Dict[str, Decimal]:
        """Generate detailed cost breakdown"""
        breakdown = {
            'flights': budget.flights_budget,
            'accommodation': budget.accommodation_budget,
            'activities': budget.activities_budget,
            'food': budget.food_budget,
            'transport': budget.transport_budget,
            'pet_costs': budget.pet_budget,
            'business_expenses': budget.business_budget,
            'contingency': budget.contingency_budget
        }
        
        # Add specific activity costs
        for activity in activities:
            category = f"activity_{activity.category}"
            if category not in breakdown:
                breakdown[category] = Decimal('0')
            breakdown[category] += activity.cost
        
        # Add requirement costs
        for requirement in requirements:
            req_category = f"requirement_{requirement.type.value}"
            breakdown[req_category] = requirement.cost_impact
        
        return breakdown
    
    def _calculate_optimization_score(self, parsed_request: Dict[str, Any], 
                                    budget: TripBudget, cost_breakdown: Dict[str, Decimal]) -> float:
        """Calculate optimization score (0-1)"""
        score = 0.0
        
        # Budget adherence (40% of score)
        total_cost = sum(cost_breakdown.values())
        if total_cost <= budget.total_budget:
            budget_score = 1.0
        else:
            budget_score = float(budget.total_budget / total_cost)
        score += budget_score * 0.4
        
        # Requirement fulfillment (30% of score)
        requirements_met = 0
        total_requirements = 0
        
        if parsed_request.get('has_pets', False):
            total_requirements += 1
            if 'requirement_pet_travel' in cost_breakdown:
                requirements_met += 1
        
        if parsed_request.get('has_business', False):
            total_requirements += 1
            if 'requirement_tax_deduction' in cost_breakdown:
                requirements_met += 1
        
        requirement_score = requirements_met / total_requirements if total_requirements > 0 else 1.0
        score += requirement_score * 0.3
        
        # Value optimization (30% of score)
        # Higher score for better allocation efficiency
        efficiency_score = 0.8  # Default efficiency
        if budget.contingency_budget > Decimal('0'):
            efficiency_score += 0.1
        if budget.pet_budget > Decimal('0') and parsed_request.get('has_pets', False):
            efficiency_score += 0.1
        
        score += min(efficiency_score, 1.0) * 0.3
        
        return min(score, 1.0)
    
    def _calculate_duration(self, segments: List[TripSegment]) -> int:
        """Calculate total trip duration"""
        if not segments:
            return 0
        
        start_date = min(datetime.strptime(segment.start_date, '%Y-%m-%d') for segment in segments)
        end_date = max(datetime.strptime(segment.end_date, '%Y-%m-%d') for segment in segments)
        
        return (end_date - start_date).days + 1


# Example usage and testing
if __name__ == "__main__":
    engine = TripOrchestrationEngine()
    
    # Test scenario 1: Budget-constrained family trip
    scenario1 = {
        'original_query': '$4000 budget, family of 4, SF to Disneyland, flexible dates',
        'budget': 4000,
        'passenger_count': 4,
        'origin': 'SFO',
        'destinations': ['LAX'],
        'destination': 'LAX',
        'purposes': ['family vacation', 'theme park'],
        'duration_days': 5,
        'start_date': '2024-08-15',
        'flexible_dates': True,
        'has_pets': False,
        'has_business': False
    }
    
    # Test scenario 2: Complex multi-week trip
    scenario2 = {
        'original_query': 'LA and SF for 2 weeks, sister hosting, bring dog, music conference',
        'budget': 6000,
        'passenger_count': 1,
        'origin': 'JFK',
        'destinations': ['LAX', 'SFO'],
        'purposes': ['family visit', 'business conference'],
        'duration_days': 14,
        'start_date': '2024-09-01',
        'flexible_dates': True,
        'has_pets': True,
        'has_business': True
    }
    
    async def test_scenarios():
        print("Testing Trip Orchestration Engine")
        print("=" * 50)
        
        # Test Scenario 1
        print("\nScenario 1: Budget-constrained family trip")
        itinerary1 = await engine.orchestrate_trip(scenario1)
        print(f"Trip ID: {itinerary1.trip_id}")
        print(f"Type: {itinerary1.trip_type}")
        print(f"Duration: {itinerary1.total_duration_days} days")
        print(f"Total Budget: ${itinerary1.budget.total_budget}")
        print(f"Optimization Score: {itinerary1.optimization_score:.2f}")
        print(f"Segments: {len(itinerary1.segments)}")
        print(f"Activities: {len(itinerary1.activities)}")
        
        # Test Scenario 2
        print("\nScenario 2: Complex multi-week trip")
        itinerary2 = await engine.orchestrate_trip(scenario2)
        print(f"Trip ID: {itinerary2.trip_id}")
        print(f"Type: {itinerary2.trip_type}")
        print(f"Duration: {itinerary2.total_duration_days} days")
        print(f"Total Budget: ${itinerary2.budget.total_budget}")
        print(f"Tax Savings: ${itinerary2.tax_savings}")
        print(f"Business %: {itinerary2.business_percentage:.1f}%")
        print(f"Optimization Score: {itinerary2.optimization_score:.2f}")
        print(f"Requirements: {len(itinerary2.requirements)}")
    
    asyncio.run(test_scenarios())