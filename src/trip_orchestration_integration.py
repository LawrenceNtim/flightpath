"""
Trip Orchestration Integration Module
Integrates all components: NLP parsing, budget optimization, and itinerary generation
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
import decimal

# Import our modules
from trip_nlp_parser import TripNLPParser
from trip_budget_optimizer import TripBudgetOptimizer, OptimizationStrategy, BudgetConstraint, BudgetCategory
from trip_orchestration_engine import TripOrchestrationEngine, TripItinerary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CompleteItinerary:
    """Complete trip itinerary with all components"""
    trip_id: str
    original_query: str
    parsed_request: Dict[str, Any]
    budget_optimization: Dict[str, Any]
    orchestration_result: TripItinerary
    daily_schedule: List[Dict[str, Any]]
    booking_checklist: List[str]
    total_cost: Decimal
    tax_savings: Decimal
    efficiency_score: float
    confidence_score: float

class TripOrchestrationIntegration:
    """
    Main integration class that coordinates all trip orchestration components
    """
    
    def __init__(self):
        self.nlp_parser = TripNLPParser()
        self.budget_optimizer = TripBudgetOptimizer()
        self.orchestration_engine = TripOrchestrationEngine()
        
        # Accommodation booking platforms and their features
        self.accommodation_platforms = {
            'airbnb': {
                'best_for': ['families', 'extended_stays', 'kitchen_access'],
                'avg_savings': 0.25,
                'pet_friendly_filter': True,
                'cancellation_flexible': True
            },
            'hotels.com': {
                'best_for': ['business', 'loyalty_points', 'consistency'],
                'avg_savings': 0.10,
                'pet_friendly_filter': True,
                'cancellation_flexible': False
            },
            'booking.com': {
                'best_for': ['variety', 'international', 'last_minute'],
                'avg_savings': 0.15,
                'pet_friendly_filter': True,
                'cancellation_flexible': True
            }
        }
        
        # Activity booking platforms
        self.activity_platforms = {
            'viator': {'best_for': ['tours', 'experiences'], 'discount_rate': 0.05},
            'getyourguide': {'best_for': ['attractions', 'skip_the_line'], 'discount_rate': 0.08},
            'klook': {'best_for': ['asia_pacific', 'theme_parks'], 'discount_rate': 0.12},
            'direct_booking': {'best_for': ['theme_parks', 'museums'], 'discount_rate': 0.00}
        }
    
    async def orchestrate_complete_trip(self, natural_language_query: str) -> CompleteItinerary:
        """
        Main orchestration method that processes a natural language query into a complete itinerary
        """
        try:
            logger.info(f"Starting complete trip orchestration for: {natural_language_query}")
            
            # Step 1: Parse natural language query
            parsed_request = self.nlp_parser.parse_trip_request(natural_language_query)
            logger.info(f"NLP parsing complete. Confidence: {parsed_request['confidence']:.2f}")
            
            # Step 2: Optimize budget
            budget_optimization = await self._optimize_trip_budget(parsed_request)
            logger.info(f"Budget optimization complete. Efficiency: {budget_optimization['efficiency_score']:.2f}")
            
            # Step 3: Orchestrate trip components
            orchestration_result = await self.orchestration_engine.orchestrate_trip(parsed_request)
            logger.info(f"Trip orchestration complete. Score: {orchestration_result.optimization_score:.2f}")
            
            # Step 4: Generate daily schedule
            daily_schedule = self._generate_daily_schedule(orchestration_result, parsed_request)
            
            # Step 5: Create booking checklist
            booking_checklist = self._generate_booking_checklist(orchestration_result, parsed_request)
            
            # Step 6: Calculate final metrics
            total_cost = sum(orchestration_result.cost_breakdown.values())
            efficiency_score = (budget_optimization['efficiency_score'] + orchestration_result.optimization_score) / 2
            confidence_score = parsed_request['confidence']
            
            # Create complete itinerary
            complete_itinerary = CompleteItinerary(
                trip_id=orchestration_result.trip_id,
                original_query=natural_language_query,
                parsed_request=parsed_request,
                budget_optimization=budget_optimization,
                orchestration_result=orchestration_result,
                daily_schedule=daily_schedule,
                booking_checklist=booking_checklist,
                total_cost=total_cost,
                tax_savings=orchestration_result.tax_savings,
                efficiency_score=efficiency_score,
                confidence_score=confidence_score
            )
            
            logger.info(f"Complete trip orchestration finished. Trip ID: {complete_itinerary.trip_id}")
            return complete_itinerary
            
        except Exception as e:
            logger.error(f"Error in complete trip orchestration: {e}")
            raise
    
    async def _optimize_trip_budget(self, parsed_request: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize budget based on parsed request"""
        budget_value = parsed_request.get('budget', 4000)
        # Handle case where budget might be parsed incorrectly or None
        if budget_value is None:
            budget_value = 4000  # Default budget
        elif budget_value and budget_value < 1000:
            budget_value = budget_value * 10  # Likely parsing error, multiply by 10
        
        # Ensure budget_value is a valid number
        try:
            total_budget = Decimal(str(budget_value))
        except (TypeError, ValueError, decimal.InvalidOperation):
            logger.warning(f"Invalid budget value: {budget_value}, using default $6000")
            total_budget = Decimal('6000')  # Default for complex trips
        
        # Create trip parameters for budget optimizer
        trip_params = {
            'duration_days': parsed_request.get('duration_days', 7),
            'passenger_count': parsed_request.get('passenger_count', 1),
            'destinations': parsed_request.get('destinations', []),
            'accommodation_preferences': parsed_request.get('accommodation_preferences', ['mid_range']),
            'has_pets': parsed_request.get('has_pets', False),
            'business_portion': parsed_request.get('business_portion', 0.0),
            'budget_constraints': parsed_request.get('budget_constraints', {})
        }
        
        # Determine optimization strategy
        strategy = OptimizationStrategy.MAXIMIZE_VALUE
        budget_constraints = parsed_request.get('budget_constraints', {})
        
        if budget_constraints.get('strict_budget', False):
            strategy = OptimizationStrategy.STRICT_BUDGET
        elif budget_constraints.get('budget_conscious', False):
            strategy = OptimizationStrategy.MINIMIZE_COST
        elif budget_constraints.get('luxury_preferred', False):
            strategy = OptimizationStrategy.LUXURY_FOCUS
        
        # Create constraints based on special requirements
        constraints = []
        
        # Pet travel constraint
        if parsed_request.get('has_pets', False):
            constraints.append(BudgetConstraint(
                category=BudgetCategory.PET_COSTS,
                min_amount=Decimal('300'),
                priority=1,
                flexible=False
            ))
        
        # Business travel constraint
        if parsed_request.get('business_portion', 0) > 0:
            constraints.append(BudgetConstraint(
                category=BudgetCategory.BUSINESS,
                min_amount=Decimal('200'),
                priority=2,
                flexible=True
            ))
        
        # Activity constraint for theme parks
        if 'theme_park' in parsed_request.get('activities', []):
            constraints.append(BudgetConstraint(
                category=BudgetCategory.ACTIVITIES,
                min_amount=Decimal('400'),
                priority=1,
                flexible=False
            ))
        
        # Optimize budget
        optimization_result = await self.budget_optimizer.optimize_budget(
            total_budget, trip_params, constraints, strategy
        )
        
        return {
            'optimized_budget': optimization_result.optimized_budget,
            'total_cost': float(optimization_result.total_cost),
            'savings': float(optimization_result.savings),
            'efficiency_score': optimization_result.efficiency_score,
            'recommendations': optimization_result.recommendations,
            'warnings': optimization_result.warnings,
            'constraints_met': optimization_result.constraints_met,
            'total_constraints': optimization_result.total_constraints,
            'alternatives': optimization_result.alternative_allocations
        }
    
    def _generate_daily_schedule(self, orchestration_result: TripItinerary, 
                                parsed_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed daily schedule"""
        daily_schedule = []
        
        # Group activities by date
        activities_by_date = {}
        for activity in orchestration_result.activities:
            date = activity.date
            if date not in activities_by_date:
                activities_by_date[date] = []
            activities_by_date[date].append(activity)
        
        # Create daily schedule for each segment
        for segment in orchestration_result.segments:
            current_date = datetime.strptime(segment.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(segment.end_date, '%Y-%m-%d')
            
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                
                # Create daily schedule
                day_schedule = {
                    'date': date_str,
                    'day_of_week': current_date.strftime('%A'),
                    'location': segment.destination,
                    'accommodation': {
                        'type': segment.accommodation_type.value,
                        'estimated_cost': self._estimate_daily_accommodation_cost(segment)
                    },
                    'activities': [],
                    'meals': self._plan_daily_meals(segment, parsed_request),
                    'transport': self._plan_daily_transport(segment, parsed_request),
                    'estimated_daily_cost': Decimal('0'),
                    'notes': []
                }
                
                # Add scheduled activities for this date
                if date_str in activities_by_date:
                    for activity in activities_by_date[date_str]:
                        day_schedule['activities'].append({
                            'name': activity.name,
                            'time': self._estimate_activity_time(activity),
                            'duration': f"{activity.duration_hours} hours",
                            'cost': float(activity.cost),
                            'booking_required': activity.booking_required,
                            'category': activity.category
                        })
                
                # Calculate daily cost
                day_schedule['estimated_daily_cost'] = float(
                    self._calculate_daily_cost(day_schedule, segment, parsed_request)
                )
                
                # Add special notes
                day_schedule['notes'] = self._generate_daily_notes(segment, current_date, parsed_request)
                
                daily_schedule.append(day_schedule)
                current_date += timedelta(days=1)
        
        return daily_schedule
    
    def _generate_booking_checklist(self, orchestration_result: TripItinerary,
                                   parsed_request: Dict[str, Any]) -> List[str]:
        """Generate comprehensive booking checklist"""
        checklist = []
        
        # Flight bookings
        for segment in orchestration_result.segments:
            checklist.append(f"✈️ Book flight: {segment.origin} → {segment.destination} on {segment.start_date}")
        
        # Return flight
        if len(orchestration_result.segments) > 0:
            last_segment = orchestration_result.segments[-1]
            first_segment = orchestration_result.segments[0]
            checklist.append(f"✈️ Book return flight: {last_segment.destination} → {first_segment.origin}")
        
        # Accommodation bookings
        for segment in orchestration_result.segments:
            if segment.accommodation_type.value != 'family_hosting':
                platform = self._recommend_accommodation_platform(segment, parsed_request)
                checklist.append(f"🏨 Book accommodation in {segment.destination} via {platform}")
        
        # Activity bookings
        for activity in orchestration_result.activities:
            if activity.booking_required:
                platform = self._recommend_activity_platform(activity)
                checklist.append(f"🎯 Book {activity.name} via {platform}")
        
        # Pet-related bookings
        if parsed_request.get('has_pets', False):
            checklist.extend([
                "🐕 Schedule vet visit for health certificate (2-3 weeks before travel)",
                "🐕 Purchase airline-approved pet carrier",
                "🐕 Book pet-friendly accommodations",
                "🐕 Research pet daycare options at destination",
                "🐕 Purchase pet travel insurance"
            ])
        
        # Business-related tasks
        if parsed_request.get('business_portion', 0) > 0:
            checklist.extend([
                "💼 Set up expense tracking app/spreadsheet",
                "💼 Confirm business meeting/conference details",
                "💼 Download receipt scanning app",
                "💼 Review company travel policy"
            ])
        
        # General travel preparation
        checklist.extend([
            "📱 Download airline apps",
            "📱 Download accommodation apps",
            "💳 Notify credit card companies of travel",
            "🧳 Check baggage allowances",
            "📋 Create packing checklist",
            "🌐 Check international roaming/SIM options",
            "💉 Check vaccination requirements (if international)"
        ])
        
        # Family-specific items
        if parsed_request.get('passenger_count', 1) > 2:
            checklist.extend([
                "👨‍👩‍👧‍👦 Prepare travel entertainment for family",
                "👨‍👩‍👧‍👦 Pack snacks and travel essentials",
                "👨‍👩‍👧‍👦 Confirm child policies for activities"
            ])
        
        return checklist
    
    def _estimate_daily_accommodation_cost(self, segment) -> float:
        """Estimate daily accommodation cost"""
        base_costs = {
            'hotel': 150,
            'airbnb': 120,
            'family_hosting': 25,  # Host gift
            'pet_friendly': 180,
            'business_accommodation': 200
        }
        
        return base_costs.get(segment.accommodation_type.value, 120)
    
    def _plan_daily_meals(self, segment, parsed_request: Dict[str, Any]) -> List[Dict[str, str]]:
        """Plan daily meals"""
        meals = []
        
        # Breakfast
        if segment.accommodation_type.value in ['airbnb', 'family_hosting']:
            meals.append({'meal': 'Breakfast', 'plan': 'Cook at accommodation', 'estimated_cost': '15'})
        else:
            meals.append({'meal': 'Breakfast', 'plan': 'Hotel breakfast or local cafe', 'estimated_cost': '25'})
        
        # Lunch
        if 'theme_park' in parsed_request.get('activities', []):
            meals.append({'meal': 'Lunch', 'plan': 'Theme park dining', 'estimated_cost': '45'})
        else:
            meals.append({'meal': 'Lunch', 'plan': 'Local restaurant', 'estimated_cost': '35'})
        
        # Dinner
        if parsed_request.get('business_portion', 0) > 0:
            meals.append({'meal': 'Dinner', 'plan': 'Business dinner', 'estimated_cost': '80'})
        else:
            meals.append({'meal': 'Dinner', 'plan': 'Family restaurant', 'estimated_cost': '60'})
        
        return meals
    
    def _plan_daily_transport(self, segment, parsed_request: Dict[str, Any]) -> Dict[str, str]:
        """Plan daily transportation"""
        if segment.accommodation_type.value == 'family_hosting':
            return {'method': 'Family transport/rideshare', 'estimated_cost': '25'}
        elif parsed_request.get('budget_constraints', {}).get('budget_conscious', False):
            return {'method': 'Public transport', 'estimated_cost': '15'}
        else:
            return {'method': 'Rental car/rideshare', 'estimated_cost': '45'}
    
    def _estimate_activity_time(self, activity) -> str:
        """Estimate activity start time"""
        # Simple time estimation based on activity type
        time_mapping = {
            'theme_park': '9:00 AM',
            'conference': '9:00 AM',
            'museum': '10:00 AM',
            'dining': '7:00 PM',
            'transport': '8:00 AM',
            'business_meal': '7:30 PM'
        }
        
        return time_mapping.get(activity.category, '10:00 AM')
    
    def _calculate_daily_cost(self, day_schedule: Dict[str, Any], segment, parsed_request: Dict[str, Any]) -> Decimal:
        """Calculate estimated daily cost"""
        total_cost = Decimal('0')
        
        # Accommodation cost
        total_cost += Decimal(str(day_schedule['accommodation']['estimated_cost']))
        
        # Activity costs
        for activity in day_schedule['activities']:
            total_cost += Decimal(str(activity['cost']))
        
        # Meal costs
        for meal in day_schedule['meals']:
            total_cost += Decimal(str(meal['estimated_cost']))
        
        # Transport cost
        total_cost += Decimal(str(day_schedule['transport']['estimated_cost']))
        
        # Pet costs (if applicable)
        if parsed_request.get('has_pets', False):
            total_cost += Decimal('20')  # Daily pet costs
        
        return total_cost
    
    def _generate_daily_notes(self, segment, current_date: datetime, parsed_request: Dict[str, Any]) -> List[str]:
        """Generate helpful daily notes"""
        notes = []
        
        # Weekend notes
        if current_date.weekday() >= 5:  # Saturday or Sunday
            notes.append("Weekend - expect higher prices and crowds")
        
        # Pet notes
        if parsed_request.get('has_pets', False):
            notes.append("Remember to plan for pet needs and restrictions")
        
        # Business notes
        if parsed_request.get('business_portion', 0) > 0:
            notes.append("Keep all receipts for business expense tracking")
        
        # First day notes
        if current_date.strftime('%Y-%m-%d') == segment.start_date:
            notes.append("Arrival day - plan for potential travel fatigue")
        
        # Destination-specific notes
        if segment.destination == 'LAX' and 'theme_park' in parsed_request.get('activities', []):
            notes.append("Download Disneyland app for wait times and mobile ordering")
        
        return notes
    
    def _recommend_accommodation_platform(self, segment, parsed_request: Dict[str, Any]) -> str:
        """Recommend best accommodation booking platform"""
        requirements = []
        
        if parsed_request.get('has_pets', False):
            requirements.append('pet_friendly_filter')
        
        if parsed_request.get('business_portion', 0) > 0:
            requirements.append('business')
        
        if parsed_request.get('passenger_count', 1) > 2:
            requirements.append('families')
        
        if parsed_request.get('duration_days', 0) > 7:
            requirements.append('extended_stays')
        
        # Score platforms based on requirements
        platform_scores = {}
        for platform, features in self.accommodation_platforms.items():
            score = 0
            for req in requirements:
                if req in features.get('best_for', []):
                    score += 2
                if req == 'pet_friendly_filter' and features.get('pet_friendly_filter', False):
                    score += 3
            
            # Add savings bonus
            score += features.get('avg_savings', 0) * 10
            
            platform_scores[platform] = score
        
        # Return highest scoring platform
        best_platform = max(platform_scores, key=platform_scores.get)
        return best_platform
    
    def _recommend_activity_platform(self, activity) -> str:
        """Recommend best activity booking platform"""
        category_mapping = {
            'theme_park': 'direct_booking',
            'conference': 'direct_booking',
            'museum': 'getyourguide',
            'tours': 'viator',
            'attractions': 'getyourguide'
        }
        
        return category_mapping.get(activity.category, 'viator')


# Test the integration
async def test_integration():
    """Test the complete integration"""
    integration = TripOrchestrationIntegration()
    
    # Test scenarios
    test_scenarios = [
        "$4000 budget, family of 4, SF to Disneyland, flexible dates",
        "LA and SF for 2 weeks, sister hosting, bring dog, music conference"
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"TESTING SCENARIO {i}: {scenario}")
        print(f"{'='*60}")
        
        try:
            result = await integration.orchestrate_complete_trip(scenario)
            
            print(f"\n🎯 TRIP OVERVIEW")
            print(f"Trip ID: {result.trip_id}")
            print(f"Total Cost: ${result.total_cost}")
            print(f"Tax Savings: ${result.tax_savings}")
            print(f"Efficiency Score: {result.efficiency_score:.2f}")
            print(f"Confidence Score: {result.confidence_score:.2f}")
            
            print(f"\n💰 BUDGET BREAKDOWN")
            for category, amount in result.budget_optimization['optimized_budget'].items():
                print(f"  {category}: ${amount}")
            
            print(f"\n📅 DAILY SCHEDULE PREVIEW (First 3 Days)")
            for day in result.daily_schedule[:3]:
                print(f"  {day['date']} ({day['day_of_week']}) - {day['location']}")
                print(f"    Daily Cost: ${day['estimated_daily_cost']}")
                print(f"    Activities: {len(day['activities'])}")
                if day['notes']:
                    print(f"    Notes: {', '.join(day['notes'])}")
            
            print(f"\n📋 BOOKING CHECKLIST (First 10 Items)")
            for item in result.booking_checklist[:10]:
                print(f"  {item}")
            
            print(f"\n⚠️ WARNINGS & RECOMMENDATIONS")
            for warning in result.budget_optimization['warnings']:
                print(f"  Warning: {warning}")
            for rec in result.budget_optimization['recommendations'][:3]:
                print(f"  Tip: {rec}")
                
        except Exception as e:
            print(f"❌ Error testing scenario: {e}")

if __name__ == "__main__":
    asyncio.run(test_integration())