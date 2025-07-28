"""
Budget Optimization Engine for Trip Orchestration
Advanced budget allocation and optimization with constraint handling
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
import json
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """Budget optimization strategies"""
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_VALUE = "maximize_value"
    BALANCE_COMFORT = "balance_comfort"
    STRICT_BUDGET = "strict_budget"
    LUXURY_FOCUS = "luxury_focus"

class BudgetCategory(Enum):
    """Budget categories for detailed tracking"""
    FLIGHTS = "flights"
    ACCOMMODATION = "accommodation"
    ACTIVITIES = "activities"
    FOOD = "food"
    TRANSPORT = "transport"
    PET_COSTS = "pet_costs"
    BUSINESS = "business"
    CONTINGENCY = "contingency"
    SHOPPING = "shopping"
    INSURANCE = "insurance"

@dataclass
class BudgetConstraint:
    """Budget constraint definition"""
    category: BudgetCategory
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    percentage_min: Optional[float] = None
    percentage_max: Optional[float] = None
    priority: int = 1  # 1=highest, 5=lowest
    flexible: bool = True

@dataclass
class OptimizationResult:
    """Result of budget optimization"""
    optimized_budget: Dict[str, Decimal]
    total_cost: Decimal
    savings: Decimal
    efficiency_score: float
    constraints_met: int
    total_constraints: int
    recommendations: List[str]
    warnings: List[str]
    alternative_allocations: List[Dict[str, Any]]

class TripBudgetOptimizer:
    """
    Advanced budget optimization engine for trip planning
    """
    
    def __init__(self):
        # Base cost data per day/person (can be dynamically updated)
        self.base_costs = {
            BudgetCategory.ACCOMMODATION: {
                'budget': {'per_night': Decimal('60'), 'quality': 0.6},
                'mid_range': {'per_night': Decimal('120'), 'quality': 0.8},
                'luxury': {'per_night': Decimal('250'), 'quality': 1.0},
                'family_hosting': {'per_night': Decimal('0'), 'quality': 0.7, 'gift_cost': Decimal('25')}
            },
            BudgetCategory.FOOD: {
                'budget': {'per_day_per_person': Decimal('30'), 'quality': 0.6},
                'mid_range': {'per_day_per_person': Decimal('60'), 'quality': 0.8},
                'luxury': {'per_day_per_person': Decimal('120'), 'quality': 1.0}
            },
            BudgetCategory.TRANSPORT: {
                'public': {'per_day': Decimal('15'), 'quality': 0.6},
                'rideshare': {'per_day': Decimal('35'), 'quality': 0.8},
                'rental_car': {'per_day': Decimal('45'), 'quality': 0.9},
                'luxury_transport': {'per_day': Decimal('100'), 'quality': 1.0}
            },
            BudgetCategory.ACTIVITIES: {
                'free': {'per_day': Decimal('0'), 'quality': 0.5},
                'budget': {'per_day': Decimal('25'), 'quality': 0.7},
                'standard': {'per_day': Decimal('75'), 'quality': 0.8},
                'premium': {'per_day': Decimal('150'), 'quality': 1.0}
            }
        }
        
        # Default budget allocations by trip type
        self.default_allocations = {
            'family_vacation': {
                BudgetCategory.FLIGHTS: 0.35,
                BudgetCategory.ACCOMMODATION: 0.25,
                BudgetCategory.ACTIVITIES: 0.20,
                BudgetCategory.FOOD: 0.15,
                BudgetCategory.TRANSPORT: 0.03,
                BudgetCategory.CONTINGENCY: 0.02
            },
            'business_trip': {
                BudgetCategory.FLIGHTS: 0.40,
                BudgetCategory.ACCOMMODATION: 0.30,
                BudgetCategory.BUSINESS: 0.15,
                BudgetCategory.FOOD: 0.10,
                BudgetCategory.TRANSPORT: 0.03,
                BudgetCategory.CONTINGENCY: 0.02
            },
            'luxury_trip': {
                BudgetCategory.FLIGHTS: 0.30,
                BudgetCategory.ACCOMMODATION: 0.35,
                BudgetCategory.ACTIVITIES: 0.20,
                BudgetCategory.FOOD: 0.12,
                BudgetCategory.TRANSPORT: 0.02,
                BudgetCategory.CONTINGENCY: 0.01
            },
            'budget_trip': {
                BudgetCategory.FLIGHTS: 0.45,
                BudgetCategory.ACCOMMODATION: 0.20,
                BudgetCategory.ACTIVITIES: 0.15,
                BudgetCategory.FOOD: 0.15,
                BudgetCategory.TRANSPORT: 0.03,
                BudgetCategory.CONTINGENCY: 0.02
            }
        }
        
        # Pet-related costs
        self.pet_costs = {
            'airline_fee_per_pet': Decimal('125'),
            'pet_carrier': Decimal('80'),
            'health_certificate': Decimal('150'),
            'pet_insurance_per_day': Decimal('15'),
            'pet_accommodation_surcharge_per_night': Decimal('25'),
            'pet_food_per_day': Decimal('20'),
            'pet_daycare_per_day': Decimal('35')
        }
        
        # Business deduction rates
        self.business_deduction_rates = {
            BudgetCategory.ACCOMMODATION: 1.0,  # 100% deductible
            BudgetCategory.FLIGHTS: 1.0,
            BudgetCategory.TRANSPORT: 1.0,
            BudgetCategory.BUSINESS: 1.0,
            BudgetCategory.FOOD: 0.5,  # 50% deductible for meals
        }
    
    async def optimize_budget(self, 
                            total_budget: Decimal,
                            trip_params: Dict[str, Any],
                            constraints: List[BudgetConstraint] = None,
                            strategy: OptimizationStrategy = OptimizationStrategy.MAXIMIZE_VALUE) -> OptimizationResult:
        """
        Main budget optimization function
        """
        try:
            logger.info(f"Optimizing budget: ${total_budget} with strategy {strategy}")
            
            # Parse trip parameters
            duration_days = trip_params.get('duration_days', 7)
            passenger_count = trip_params.get('passenger_count', 1)
            destinations = trip_params.get('destinations', [])
            has_pets = trip_params.get('has_pets', False)
            business_portion = trip_params.get('business_portion', 0.0)
            accommodation_preferences = trip_params.get('accommodation_preferences', ['mid_range'])
            
            # Determine trip type for base allocation
            trip_type = self._determine_trip_type(trip_params)
            
            # Get base allocation
            base_allocation = self._get_base_allocation(trip_type, total_budget)
            
            # Apply constraints
            constrained_allocation = self._apply_constraints(base_allocation, constraints or [])
            
            # Optimize based on strategy
            optimized_allocation = await self._optimize_by_strategy(
                constrained_allocation, trip_params, strategy
            )
            
            # Calculate actual costs
            actual_costs = self._calculate_actual_costs(optimized_allocation, trip_params)
            
            # Add pet costs if needed
            if has_pets:
                pet_costs = self._calculate_pet_costs(trip_params)
                actual_costs[BudgetCategory.PET_COSTS] = pet_costs
            
            # Add business optimizations
            if business_portion > 0:
                business_optimizations = self._apply_business_optimizations(
                    actual_costs, business_portion
                )
                actual_costs.update(business_optimizations)
            
            # Calculate total and validate against budget
            total_cost = sum(actual_costs.values())
            
            # Rebalance if over budget
            if total_cost > total_budget:
                actual_costs = self._rebalance_budget(actual_costs, total_budget, strategy)
                total_cost = sum(actual_costs.values())
            
            # Calculate savings and efficiency
            savings = total_budget - total_cost
            efficiency_score = self._calculate_efficiency_score(actual_costs, trip_params)
            
            # Generate recommendations and warnings
            recommendations = self._generate_recommendations(actual_costs, trip_params, strategy)
            warnings = self._generate_warnings(actual_costs, trip_params, total_budget)
            
            # Generate alternative allocations
            alternatives = await self._generate_alternatives(total_budget, trip_params, actual_costs)
            
            # Check constraint compliance
            constraints_met, total_constraints = self._check_constraint_compliance(
                actual_costs, constraints or []
            )
            
            result = OptimizationResult(
                optimized_budget={
                    (category.value if hasattr(category, 'value') else str(category)): amount 
                    for category, amount in actual_costs.items()
                },
                total_cost=total_cost,
                savings=savings,
                efficiency_score=efficiency_score,
                constraints_met=constraints_met,
                total_constraints=total_constraints,
                recommendations=recommendations,
                warnings=warnings,
                alternative_allocations=alternatives
            )
            
            logger.info(f"Budget optimization complete. Efficiency: {efficiency_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing budget: {e}")
            raise
    
    def _determine_trip_type(self, trip_params: Dict[str, Any]) -> str:
        """Determine trip type for base allocation"""
        budget_constraints = trip_params.get('budget_constraints', {})
        business_portion = trip_params.get('business_portion', 0.0)
        
        if budget_constraints.get('luxury_preferred', False):
            return 'luxury_trip'
        elif budget_constraints.get('budget_conscious', False):
            return 'budget_trip'
        elif business_portion > 0.5:
            return 'business_trip'
        else:
            return 'family_vacation'
    
    def _get_base_allocation(self, trip_type: str, total_budget: Decimal) -> Dict[BudgetCategory, Decimal]:
        """Get base budget allocation"""
        allocation_percentages = self.default_allocations.get(trip_type, self.default_allocations['family_vacation'])
        
        allocation = {}
        for category, percentage in allocation_percentages.items():
            allocation[category] = total_budget * Decimal(str(percentage))
        
        return allocation
    
    def _apply_constraints(self, allocation: Dict[BudgetCategory, Decimal], 
                          constraints: List[BudgetConstraint]) -> Dict[BudgetCategory, Decimal]:
        """Apply budget constraints"""
        constrained_allocation = allocation.copy()
        
        for constraint in constraints:
            category = constraint.category
            if category not in constrained_allocation:
                constrained_allocation[category] = Decimal('0')
            
            current_amount = constrained_allocation[category]
            
            # Apply minimum constraint
            if constraint.min_amount and current_amount < constraint.min_amount:
                constrained_allocation[category] = constraint.min_amount
            
            # Apply maximum constraint
            if constraint.max_amount and current_amount > constraint.max_amount:
                constrained_allocation[category] = constraint.max_amount
            
            # Apply percentage constraints
            total_budget = sum(allocation.values())
            if constraint.percentage_min:
                min_amount = total_budget * Decimal(str(constraint.percentage_min))
                if current_amount < min_amount:
                    constrained_allocation[category] = min_amount
            
            if constraint.percentage_max:
                max_amount = total_budget * Decimal(str(constraint.percentage_max))
                if current_amount > max_amount:
                    constrained_allocation[category] = max_amount
        
        return constrained_allocation
    
    async def _optimize_by_strategy(self, allocation: Dict[BudgetCategory, Decimal],
                                   trip_params: Dict[str, Any],
                                   strategy: OptimizationStrategy) -> Dict[BudgetCategory, Decimal]:
        """Optimize allocation based on strategy"""
        optimized = allocation.copy()
        
        if strategy == OptimizationStrategy.MINIMIZE_COST:
            # Reduce all categories by 10% and put into contingency
            total_reduction = Decimal('0')
            for category in [BudgetCategory.ACCOMMODATION, BudgetCategory.ACTIVITIES, BudgetCategory.FOOD]:
                if category in optimized:
                    reduction = optimized[category] * Decimal('0.1')
                    optimized[category] -= reduction
                    total_reduction += reduction
            optimized[BudgetCategory.CONTINGENCY] = optimized.get(BudgetCategory.CONTINGENCY, Decimal('0')) + total_reduction
        
        elif strategy == OptimizationStrategy.MAXIMIZE_VALUE:
            # Reallocate to higher-value categories
            if BudgetCategory.CONTINGENCY in optimized and optimized[BudgetCategory.CONTINGENCY] > Decimal('100'):
                contingency = optimized[BudgetCategory.CONTINGENCY]
                optimized[BudgetCategory.CONTINGENCY] = contingency * Decimal('0.5')
                value_boost = contingency * Decimal('0.5')
                
                # Distribute to accommodation and activities
                optimized[BudgetCategory.ACCOMMODATION] += value_boost * Decimal('0.6')
                optimized[BudgetCategory.ACTIVITIES] += value_boost * Decimal('0.4')
        
        elif strategy == OptimizationStrategy.LUXURY_FOCUS:
            # Increase accommodation and decrease contingency
            if BudgetCategory.CONTINGENCY in optimized:
                luxury_boost = optimized[BudgetCategory.CONTINGENCY] * Decimal('0.8')
                optimized[BudgetCategory.CONTINGENCY] -= luxury_boost
                optimized[BudgetCategory.ACCOMMODATION] += luxury_boost * Decimal('0.7')
                optimized[BudgetCategory.FOOD] += luxury_boost * Decimal('0.3')
        
        elif strategy == OptimizationStrategy.STRICT_BUDGET:
            # Reduce all by 5% for safety margin
            total_budget = sum(optimized.values())
            safety_margin = total_budget * Decimal('0.05')
            
            for category in optimized:
                if category != BudgetCategory.CONTINGENCY:
                    reduction = optimized[category] * Decimal('0.05')
                    optimized[category] -= reduction
            
            optimized[BudgetCategory.CONTINGENCY] = optimized.get(BudgetCategory.CONTINGENCY, Decimal('0')) + safety_margin
        
        return optimized
    
    def _calculate_actual_costs(self, allocation: Dict[BudgetCategory, Decimal],
                               trip_params: Dict[str, Any]) -> Dict[BudgetCategory, Decimal]:
        """Calculate actual costs based on trip parameters"""
        actual_costs = allocation.copy()
        
        duration_days = trip_params.get('duration_days', 7)
        passenger_count = trip_params.get('passenger_count', 1)
        accommodation_preferences = trip_params.get('accommodation_preferences', ['mid_range'])
        
        # Calculate accommodation costs
        if 'family_hosting' in accommodation_preferences:
            # Hosting: minimal cost but bring gifts
            hosting_nights = duration_days // 2  # Assume half the trip is hosting
            hotel_nights = duration_days - hosting_nights
            
            hosting_cost = hosting_nights * self.base_costs[BudgetCategory.ACCOMMODATION]['family_hosting']['gift_cost']
            hotel_cost = hotel_nights * self.base_costs[BudgetCategory.ACCOMMODATION]['mid_range']['per_night']
            
            actual_costs[BudgetCategory.ACCOMMODATION] = hosting_cost + hotel_cost
        else:
            # Standard accommodation
            accommodation_level = 'mid_range'
            if 'luxury' in accommodation_preferences:
                accommodation_level = 'luxury'
            elif 'budget' in accommodation_preferences:
                accommodation_level = 'budget'
            
            per_night_cost = self.base_costs[BudgetCategory.ACCOMMODATION][accommodation_level]['per_night']
            actual_costs[BudgetCategory.ACCOMMODATION] = per_night_cost * duration_days
        
        # Calculate food costs
        food_level = 'mid_range'
        if trip_params.get('budget_constraints', {}).get('luxury_preferred', False):
            food_level = 'luxury'
        elif trip_params.get('budget_constraints', {}).get('budget_conscious', False):
            food_level = 'budget'
        
        per_person_per_day = self.base_costs[BudgetCategory.FOOD][food_level]['per_day_per_person']
        actual_costs[BudgetCategory.FOOD] = per_person_per_day * passenger_count * duration_days
        
        # Calculate transport costs
        transport_level = 'rideshare'  # Default
        if trip_params.get('budget_constraints', {}).get('budget_conscious', False):
            transport_level = 'public'
        elif trip_params.get('budget_constraints', {}).get('luxury_preferred', False):
            transport_level = 'luxury_transport'
        
        per_day_cost = self.base_costs[BudgetCategory.TRANSPORT][transport_level]['per_day']
        actual_costs[BudgetCategory.TRANSPORT] = per_day_cost * duration_days
        
        return actual_costs
    
    def _calculate_pet_costs(self, trip_params: Dict[str, Any]) -> Decimal:
        """Calculate pet-related costs"""
        duration_days = trip_params.get('duration_days', 7)
        pet_count = 1  # Assume 1 pet for now
        
        total_pet_cost = Decimal('0')
        
        # One-time costs
        total_pet_cost += self.pet_costs['airline_fee_per_pet'] * pet_count
        total_pet_cost += self.pet_costs['pet_carrier']  # One carrier
        total_pet_cost += self.pet_costs['health_certificate']
        
        # Daily costs
        daily_pet_cost = (self.pet_costs['pet_insurance_per_day'] + 
                         self.pet_costs['pet_food_per_day'])
        total_pet_cost += daily_pet_cost * duration_days
        
        # Accommodation surcharge
        accommodation_surcharge = self.pet_costs['pet_accommodation_surcharge_per_night'] * duration_days
        total_pet_cost += accommodation_surcharge
        
        return total_pet_cost
    
    def _apply_business_optimizations(self, costs: Dict[BudgetCategory, Decimal],
                                    business_portion: float) -> Dict[BudgetCategory, Decimal]:
        """Apply business trip optimizations and tax benefits"""
        optimizations = {}
        
        # Calculate tax savings
        total_deductible = Decimal('0')
        for category, amount in costs.items():
            if category in self.business_deduction_rates:
                business_amount = amount * Decimal(str(business_portion))
                deduction_rate = Decimal(str(self.business_deduction_rates[category]))
                deductible = business_amount * deduction_rate
                total_deductible += deductible
        
        # Assume 25% tax rate for savings calculation
        tax_savings = total_deductible * Decimal('0.25')
        
        # Add business category if not present
        if BudgetCategory.BUSINESS not in costs:
            optimizations[BudgetCategory.BUSINESS] = Decimal('0')
        
        # The tax savings effectively reduce the total cost
        optimizations['tax_savings'] = tax_savings
        
        return optimizations
    
    def _rebalance_budget(self, costs: Dict[BudgetCategory, Decimal],
                         target_budget: Decimal,
                         strategy: OptimizationStrategy) -> Dict[BudgetCategory, Decimal]:
        """Rebalance budget when over target"""
        total_cost = sum(costs.values())
        excess = total_cost - target_budget
        
        if excess <= 0:
            return costs
        
        rebalanced = costs.copy()
        
        # Priority order for reductions based on strategy
        if strategy == OptimizationStrategy.MINIMIZE_COST:
            reduction_order = [BudgetCategory.ACTIVITIES, BudgetCategory.FOOD, 
                             BudgetCategory.ACCOMMODATION, BudgetCategory.TRANSPORT]
        elif strategy == OptimizationStrategy.LUXURY_FOCUS:
            reduction_order = [BudgetCategory.TRANSPORT, BudgetCategory.CONTINGENCY,
                             BudgetCategory.ACTIVITIES, BudgetCategory.FOOD]
        else:
            reduction_order = [BudgetCategory.CONTINGENCY, BudgetCategory.ACTIVITIES,
                             BudgetCategory.FOOD, BudgetCategory.TRANSPORT]
        
        remaining_excess = excess
        
        for category in reduction_order:
            if category in rebalanced and remaining_excess > 0:
                # Reduce by up to 20% of this category
                max_reduction = rebalanced[category] * Decimal('0.2')
                reduction = min(max_reduction, remaining_excess)
                rebalanced[category] -= reduction
                remaining_excess -= reduction
                
                if remaining_excess <= 0:
                    break
        
        # If still over budget, reduce proportionally
        if remaining_excess > 0:
            scale_factor = target_budget / sum(rebalanced.values())
            for category in rebalanced:
                rebalanced[category] *= scale_factor
        
        return rebalanced
    
    def _calculate_efficiency_score(self, costs: Dict[BudgetCategory, Decimal],
                                   trip_params: Dict[str, Any]) -> float:
        """Calculate budget efficiency score (0-1)"""
        score = 0.0
        
        # Value-to-cost ratios
        total_cost = sum(costs.values())
        if total_cost == 0:
            return 0.0
        
        # Accommodation efficiency (30% of score)
        accommodation_cost = costs.get(BudgetCategory.ACCOMMODATION, Decimal('0'))
        accommodation_ratio = float(accommodation_cost / total_cost)
        if 0.2 <= accommodation_ratio <= 0.35:  # Optimal range
            score += 0.3
        else:
            score += 0.3 * (1 - abs(accommodation_ratio - 0.275) / 0.275)
        
        # Activities efficiency (25% of score)
        activities_cost = costs.get(BudgetCategory.ACTIVITIES, Decimal('0'))
        activities_ratio = float(activities_cost / total_cost)
        if activities_ratio >= 0.15:  # Good activity allocation
            score += 0.25
        else:
            score += 0.25 * (activities_ratio / 0.15)
        
        # Contingency efficiency (20% of score)
        contingency_cost = costs.get(BudgetCategory.CONTINGENCY, Decimal('0'))
        contingency_ratio = float(contingency_cost / total_cost)
        if 0.02 <= contingency_ratio <= 0.05:  # Optimal contingency
            score += 0.2
        else:
            score += 0.2 * max(0, 1 - abs(contingency_ratio - 0.035) / 0.035)
        
        # Special requirements efficiency (25% of score)
        if trip_params.get('has_pets', False) and BudgetCategory.PET_COSTS in costs:
            score += 0.125  # Bonus for handling pet requirements
        
        if trip_params.get('business_portion', 0) > 0:
            score += 0.125  # Bonus for business optimization
        
        return min(score, 1.0)
    
    def _generate_recommendations(self, costs: Dict[BudgetCategory, Decimal],
                                trip_params: Dict[str, Any],
                                strategy: OptimizationStrategy) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        total_cost = sum(costs.values())
        
        # Accommodation recommendations
        accommodation_ratio = float(costs.get(BudgetCategory.ACCOMMODATION, Decimal('0')) / total_cost)
        if accommodation_ratio > 0.4:
            recommendations.append("Consider vacation rentals or family hosting to reduce accommodation costs")
        elif accommodation_ratio < 0.2:
            recommendations.append("Consider upgrading accommodation for better comfort")
        
        # Activities recommendations
        activities_ratio = float(costs.get(BudgetCategory.ACTIVITIES, Decimal('0')) / total_cost)
        if activities_ratio < 0.1:
            recommendations.append("Allocate more budget to activities for a richer experience")
        
        # Food recommendations
        food_ratio = float(costs.get(BudgetCategory.FOOD, Decimal('0')) / total_cost)
        if food_ratio > 0.2:
            recommendations.append("Look for accommodation with kitchen facilities to save on dining costs")
        
        # Transport recommendations
        if trip_params.get('destinations') and len(trip_params['destinations']) > 1:
            recommendations.append("Consider train or bus travel between cities to save on transport costs")
        
        # Business trip recommendations
        if trip_params.get('business_portion', 0) > 0:
            recommendations.append("Ensure proper documentation for business expense deductions")
            recommendations.append("Schedule business activities early in the trip for better tax benefits")
        
        # Pet travel recommendations
        if trip_params.get('has_pets', False):
            recommendations.append("Book pet-friendly accommodations early for better rates")
            recommendations.append("Consider pet insurance for longer trips")
        
        return recommendations
    
    def _generate_warnings(self, costs: Dict[BudgetCategory, Decimal],
                          trip_params: Dict[str, Any],
                          total_budget: Decimal) -> List[str]:
        """Generate budget warnings"""
        warnings = []
        total_cost = sum(costs.values())
        
        # Over-budget warning
        if total_cost > total_budget:
            warnings.append(f"Budget exceeded by ${total_cost - total_budget:.2f}")
        
        # Low contingency warning
        contingency_ratio = float(costs.get(BudgetCategory.CONTINGENCY, Decimal('0')) / total_cost)
        if contingency_ratio < 0.02:
            warnings.append("Very low contingency budget - consider increasing for unexpected expenses")
        
        # High accommodation cost warning
        accommodation_ratio = float(costs.get(BudgetCategory.ACCOMMODATION, Decimal('0')) / total_cost)
        if accommodation_ratio > 0.5:
            warnings.append("Accommodation costs are very high - consider alternative options")
        
        # Pet cost warning
        if trip_params.get('has_pets', False):
            pet_cost = costs.get(BudgetCategory.PET_COSTS, Decimal('0'))
            if pet_cost > total_budget * Decimal('0.15'):
                warnings.append("Pet travel costs are significant - verify all requirements and fees")
        
        # Long trip warning
        if trip_params.get('duration_days', 0) > 14:
            warnings.append("Extended trip - consider mid-trip accommodation changes to optimize costs")
        
        return warnings
    
    async def _generate_alternatives(self, total_budget: Decimal,
                                   trip_params: Dict[str, Any],
                                   current_allocation: Dict[BudgetCategory, Decimal]) -> List[Dict[str, Any]]:
        """Generate alternative budget allocations"""
        alternatives = []
        
        # Create simple alternatives without recursive calls to avoid infinite recursion
        # Budget-conscious alternative - manual allocation
        budget_allocation = {}
        budget_allocation[BudgetCategory.FLIGHTS] = total_budget * Decimal('0.45')  # More for flights
        budget_allocation[BudgetCategory.ACCOMMODATION] = total_budget * Decimal('0.20')  # Less accommodation
        budget_allocation[BudgetCategory.ACTIVITIES] = total_budget * Decimal('0.15')
        budget_allocation[BudgetCategory.FOOD] = total_budget * Decimal('0.15')
        budget_allocation[BudgetCategory.TRANSPORT] = total_budget * Decimal('0.03')
        budget_allocation[BudgetCategory.CONTINGENCY] = total_budget * Decimal('0.02')
        
        budget_savings = total_budget - sum(budget_allocation.values())
        
        alternatives.append({
            'name': 'Budget-Conscious Option',
            'description': 'Minimize costs while maintaining essential experiences',
            'allocation': {cat.value: float(amount) for cat, amount in budget_allocation.items()},
            'savings': float(budget_savings),
            'efficiency': 0.75
        })
        
        # Luxury alternative (if budget allows) - manual allocation
        if total_budget > Decimal('3000'):
            luxury_allocation = {}
            luxury_allocation[BudgetCategory.FLIGHTS] = total_budget * Decimal('0.30')
            luxury_allocation[BudgetCategory.ACCOMMODATION] = total_budget * Decimal('0.35')  # More accommodation
            luxury_allocation[BudgetCategory.ACTIVITIES] = total_budget * Decimal('0.20')  # More activities
            luxury_allocation[BudgetCategory.FOOD] = total_budget * Decimal('0.12')
            luxury_allocation[BudgetCategory.TRANSPORT] = total_budget * Decimal('0.02')
            luxury_allocation[BudgetCategory.CONTINGENCY] = total_budget * Decimal('0.01')
            
            luxury_savings = total_budget - sum(luxury_allocation.values())
            
            alternatives.append({
                'name': 'Luxury Option',
                'description': 'Premium accommodations and experiences',
                'allocation': {cat.value: float(amount) for cat, amount in luxury_allocation.items()},
                'savings': float(luxury_savings),
                'efficiency': 0.85
            })
        
        return alternatives
    
    def _check_constraint_compliance(self, costs: Dict[BudgetCategory, Decimal],
                                   constraints: List[BudgetConstraint]) -> Tuple[int, int]:
        """Check how many constraints are met"""
        constraints_met = 0
        total_constraints = len(constraints)
        
        total_budget = sum(costs.values())
        
        for constraint in constraints:
            category = constraint.category
            amount = costs.get(category, Decimal('0'))
            
            constraint_satisfied = True
            
            # Check minimum amount
            if constraint.min_amount and amount < constraint.min_amount:
                constraint_satisfied = False
            
            # Check maximum amount
            if constraint.max_amount and amount > constraint.max_amount:
                constraint_satisfied = False
            
            # Check percentage constraints
            if constraint.percentage_min:
                min_amount = total_budget * Decimal(str(constraint.percentage_min))
                if amount < min_amount:
                    constraint_satisfied = False
            
            if constraint.percentage_max:
                max_amount = total_budget * Decimal(str(constraint.percentage_max))
                if amount > max_amount:
                    constraint_satisfied = False
            
            if constraint_satisfied:
                constraints_met += 1
        
        return constraints_met, total_constraints


# Example usage and testing
if __name__ == "__main__":
    optimizer = TripBudgetOptimizer()
    
    async def test_budget_optimization():
        print("Testing Trip Budget Optimizer")
        print("=" * 50)
        
        # Test scenario 1: Family budget trip
        scenario1_params = {
            'duration_days': 5,
            'passenger_count': 4,
            'destinations': ['LAX'],
            'accommodation_preferences': ['mid_range'],
            'has_pets': False,
            'business_portion': 0.0,
            'budget_constraints': {'strict_budget': True}
        }
        
        constraints1 = [
            BudgetConstraint(BudgetCategory.ACCOMMODATION, max_amount=Decimal('800')),
            BudgetConstraint(BudgetCategory.ACTIVITIES, min_amount=Decimal('500'))
        ]
        
        result1 = await optimizer.optimize_budget(
            Decimal('4000'), scenario1_params, constraints1, OptimizationStrategy.STRICT_BUDGET
        )
        
        print("\nScenario 1: Family Budget Trip ($4,000)")
        print(f"Total Cost: ${result1.total_cost}")
        print(f"Savings: ${result1.savings}")
        print(f"Efficiency Score: {result1.efficiency_score:.2f}")
        print(f"Constraints Met: {result1.constraints_met}/{result1.total_constraints}")
        print("Allocation:")
        for category, amount in result1.optimized_budget.items():
            print(f"  {category}: ${amount}")
        
        # Test scenario 2: Business trip with pets
        scenario2_params = {
            'duration_days': 14,
            'passenger_count': 1,
            'destinations': ['LAX', 'SFO'],
            'accommodation_preferences': ['family_hosting', 'hotel'],
            'has_pets': True,
            'business_portion': 0.6,
            'budget_constraints': {}
        }
        
        result2 = await optimizer.optimize_budget(
            Decimal('6000'), scenario2_params, [], OptimizationStrategy.MAXIMIZE_VALUE
        )
        
        print("\nScenario 2: Business Trip with Pets ($6,000)")
        print(f"Total Cost: ${result2.total_cost}")
        print(f"Savings: ${result2.savings}")
        print(f"Efficiency Score: {result2.efficiency_score:.2f}")
        print("Allocation:")
        for category, amount in result2.optimized_budget.items():
            print(f"  {category}: ${amount}")
        
        print(f"\nRecommendations:")
        for rec in result2.recommendations:
            print(f"  • {rec}")
        
        if result2.warnings:
            print(f"\nWarnings:")
            for warning in result2.warnings:
                print(f"  ⚠ {warning}")
    
    asyncio.run(test_budget_optimization())