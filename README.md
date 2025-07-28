# 🛫 FlightPath - AI-Powered Travel Orchestration Platform

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![Claude AI](https://img.shields.io/badge/Claude-AI-orange.svg)](https://claude.ai/)

**FlightPath** is an intelligent travel planning platform that combines AI-powered flight optimization, natural language processing, and comprehensive trip orchestration to deliver personalized travel recommendations.

## 🌟 Key Features

### ✈️ **AI-Powered Flight Optimization**
- **Claude AI Integration**: Advanced flight analysis and recommendations
- **Points Transfer Intelligence**: Comprehensive database of 50+ transfer partners
- **Real-time Pricing**: Dynamic flight cost analysis and optimization
- **Multi-airline Support**: Compare across carriers with preference handling

### 🗣️ **Natural Language Processing**
- **Voice Input Support**: WebKit Speech API integration
- **Complex Query Parsing**: Handle requests like "wedding by 12pm August 15th, leave Sunday from LA to NY"
- **Context Understanding**: Extract dates, preferences, constraints, and requirements
- **High Confidence Scoring**: Validate parsing accuracy for reliable results

### 🎯 **Trip Orchestration Engine**
- **Multi-City Planning**: Handle complex itineraries across multiple destinations
- **Budget Optimization**: Advanced constraint solving with multiple strategies
- **Business Travel Support**: Tax optimization and expense categorization
- **Pet Travel Logistics**: Comprehensive pet travel planning and requirements
- **Family Trip Planning**: Group composition handling and activity planning

### 🧠 **Context Intelligence Engine**
- **Holiday Awareness**: Holiday calendars and seasonal pricing intelligence
- **Weather Integration**: Climate considerations for travel planning
- **Event Detection**: Local events and peak season analysis
- **Peak Season Analytics**: Dynamic pricing and crowd level predictions

### 🌐 **Web Interface**
- **Modern UI**: Bootstrap-powered responsive design
- **Voice Search**: Hands-free trip planning
- **Real-time Results**: Instant AI-powered recommendations
- **Interactive Maps**: Visual destination selection
- **Mobile Optimized**: Full mobile device support

## 🚀 Current Capabilities

### ✅ **Implemented Features**
- [x] AI-powered flight analysis with Claude integration
- [x] Natural language query processing with spaCy
- [x] Context engine with holiday and weather intelligence
- [x] Trip orchestration for complex multi-city journeys
- [x] Budget optimization with constraint solving
- [x] Business travel tax optimization
- [x] Pet travel logistics planning
- [x] Web interface with voice input support
- [x] Points transfer partner database (50+ partners)

## 💡 Usage Examples

### Natural Language Queries
```
"$4000 budget, family of 4, SF to Disneyland, flexible dates"
"LA and SF for 2 weeks, sister hosting, bring dog, music conference"
"Wedding by 12pm August 15th, leave Sunday from LA to NY"
"NYC to Martha's Vineyard, 5-bedroom house in Oak Bluffs for $5000"
"Japan trip from SF $1500 budget, United flights only, have 40,000 points"
```

## 🏗️ Architecture

The system consists of multiple integrated components:

- **ai_flightpath.py**: Core AI flight analysis engine
- **nlp_parser.py**: Natural language processing for flight queries
- **context_engine.py**: Travel context intelligence
- **trip_orchestration_engine.py**: Complex trip planning
- **trip_budget_optimizer.py**: Budget optimization algorithms
- **trip_nlp_parser.py**: Enhanced NLP for complex trips
- **enhanced_app.py**: Flask web application with voice support

## 🧪 Testing

Test the complete system:
```bash
python trip_orchestration_integration.py
```

This will run both test scenarios:
1. **Family Disneyland Trip**: $4000 budget, family of 4
2. **Complex Business Trip**: Multi-city with pets and conferences

## 📊 Performance Results

From recent testing:
- **Scenario 1**: $4000 budget → $685 actual cost, 0.62 efficiency score
- **Scenario 2**: Complex trip → $8515 cost with $270 tax savings, 0.78 efficiency
- **NLP Confidence**: 0.80-1.00 for well-formed queries
- **Processing Time**: <3 seconds for complete trip orchestration

## 🎯 Recent Accomplishments

- ✅ **Trip Orchestration Engine**: Handles complex multi-component trips
- ✅ **Budget Optimization**: Advanced constraint solving with tax benefits
- ✅ **Pet Travel Logistics**: Comprehensive pet travel planning
- ✅ **Business Tax Optimization**: Automatic deduction calculations
- ✅ **Multi-City Planning**: Segments with different accommodation types
- ✅ **Natural Language Enhancement**: Improved parsing for complex requests

## 🛠️ Technical Stack

- **AI**: Anthropic Claude 3.5 Sonnet
- **NLP**: spaCy with custom travel domain patterns
- **Backend**: Flask with asyncio support
- **Frontend**: Bootstrap with WebKit Speech API
- **Data**: Decimal precision for financial calculations
- **Architecture**: Modular design with clear separation of concerns

---

**Built for intelligent, personalized trip planning with AI-powered optimization.**