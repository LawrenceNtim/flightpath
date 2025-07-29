# ai_flightpath.py
# Requires: anthropic (pip install anthropic)
# Make sure PointsOptimizer is available in your environment (copy from your main script if needed)

import anthropic
import json
from datetime import datetime

# Import PointsOptimizer from your main script or define it here if running standalone
from flightpath_test import PointsOptimizer

class AIFlightPath:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.points_optimizer = PointsOptimizer()
        
    def analyze_with_ai(self, origin, destination, date, user_profile=None):
        """Complete AI-powered flight analysis"""
        
        print(f"🤖 AI FLIGHTPATH ANALYZING: {origin} → {destination}")
        print("🧠 Claude is thinking...")
        print("=" * 60)
        
        # Step 1: Get technical analysis (rule-based, fast)
        technical_analysis = self.points_optimizer.optimize_flight(origin, destination, date)
        
        # Step 2: Prepare context for Claude
        ai_context = self.prepare_ai_context(technical_analysis, user_profile, origin, destination, date)
        
        # Step 3: Get Claude's strategic insights
        ai_insights = self.get_claude_recommendation(ai_context)
        
        # Step 4: Combine technical + AI analysis
        return self.combine_analysis(technical_analysis, ai_insights)
    
    def prepare_ai_context(self, technical_analysis, user_profile, origin, destination, date):
        """Prepare structured context for Claude"""
        
        # Extract key data for Claude
        flight_options = []
        for i, rec in enumerate(technical_analysis[:3]):  # Top 3 options
            flight = rec['flight']
            option = {
                'rank': i + 1,
                'airline': rec['airline'],
                'duration': flight.duration,
                'cash_price': f"${rec['cash_price_usd']:.0f}",
                'departure': flight.departure,
                'arrival': flight.arrival
            }
            
            if rec['award_info']:
                option['points_option'] = {
                    'points_needed': rec['award_info']['points_needed'],
                    'cents_per_point': rec['award_info']['cents_per_point'],
                    'worth_it': rec['award_info']['worth_it'],
                    'type': rec['award_info']['type']
                }
                
                if rec['best_strategy']:
                    option['best_transfer'] = {
                        'program': rec['best_strategy']['program'],
                        'points_from_program': rec['best_strategy']['points_from_program']
                    }
            
            flight_options.append(option)
        
        context = {
            'route': f"{origin} → {destination}",
            'travel_date': date,
            'flight_options': flight_options,
            'user_profile': user_profile or {
                'experience_level': 'intermediate',
                'primary_goal': 'value_optimization'
            }
        }
        
        return context
    
    def get_claude_recommendation(self, context):
        """Get strategic recommendation from Claude"""
        
        prompt = f"""You are FlightPath AI, the world's most advanced travel optimization assistant. You help travelers make the best flight decisions by considering both immediate value and long-term travel strategy.

FLIGHT ANALYSIS REQUEST:
Route: {context['route']}
Date: {context['travel_date']}

FLIGHT OPTIONS:
{json.dumps(context['flight_options'], indent=2)}

USER CONTEXT:
{json.dumps(context['user_profile'], indent=2)}

TASK:
Analyze these flight options and provide your expert recommendation. Consider:

1. **Immediate Value**: Which option offers the best value right now?
2. **Points Strategy**: Are the points redemptions worthwhile, or should they pay cash?
3. **Long-term Impact**: How does this decision affect their overall travel strategy?
4. **Risk Factors**: Any concerns about connections, aircraft, or booking strategies?
5. **Actionable Advice**: Specific next steps they should take.

RESPONSE FORMAT:
Provide a clear, actionable recommendation in this structure:

🎯 **TOP RECOMMENDATION**: [Which flight option and why]

💡 **REASONING**: [2-3 key factors that make this the best choice]

⚠️ **WATCH OUT FOR**: [Any risks or considerations]

🚀 **ACTION PLAN**: [Exactly what they should do next]

💰 **VALUE INSIGHT**: [Why this maximizes their travel value]

Keep it concise but insightful. Think like a travel hacker who optimizes everything."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"AI analysis temporarily unavailable: {str(e)}"
    
    def combine_analysis(self, technical_analysis, ai_insights):
        """Combine rule-based and AI analysis"""
        
        return {
            'technical_data': technical_analysis,
            'ai_recommendation': ai_insights,
            'timestamp': datetime.now().isoformat(),
            'confidence': 'high' if 'temporarily unavailable' not in ai_insights else 'medium'
        }
    
    def chat_with_user(self, user_message, context=None):
        """Handle follow-up questions from user"""
        
        prompt = f"""You are FlightPath AI. The user is asking a follow-up question about their travel plans.

CONTEXT: {context if context else 'No previous context'}

USER QUESTION: {user_message}

Respond as a helpful travel expert. Be conversational but informative. If they're asking about booking, transferring points, or specific actions, give them clear step-by-step guidance."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return "I'm having trouble processing that right now. Can you try again?"

# Test the AI-powered system
if __name__ == "__main__":
    # You'll need to add your API key here
    API_KEY = "your-anthropic-api-key-here"  # Replace with your actual key
    
    # Create user profile
    user_profile = {
        'experience_level': 'advanced',
        'primary_goal': 'maximize_points_value',
        'status_goals': ['United Premier Gold'],
        'upcoming_trips': ['Tokyo in January 2026'],
        'risk_tolerance': 'medium',
        'credit_cards': ['Chase Sapphire Reserve', 'Amex Platinum']
    }
    
    # Initialize AI FlightPath
    ai_flightpath = AIFlightPath(API_KEY)
    
    # Run complete AI analysis
    result = ai_flightpath.analyze_with_ai("LAX", "JFK", "2025-08-15", user_profile)
    
    # Display results
    print("\n🤖 CLAUDE'S STRATEGIC ANALYSIS:")
    print("=" * 60)
    print(result['ai_recommendation'])
    
    print("\n💬 ASK CLAUDE ANYTHING:")
    print("=" * 30)
    
    # Interactive chat example
    follow_up = "Should I book this now or wait for a better deal?"
    response = ai_flightpath.chat_with_user(follow_up, result)
    print(f"You: {follow_up}")
    print(f"Claude: {response}") 