# OpenBNB MCP Server Setup Guide

## Quick Setup for Airbnb Integration

The accommodation engine is designed to work with OpenBNB MCP server for real Airbnb searches. Here's how to set it up:

### 1. Install OpenBNB MCP Server

```bash
# Clone the OpenBNB MCP repository
git clone https://github.com/modelcontextprotocol/openbnb-mcp.git
cd openbnb-mcp

# Install dependencies
npm install

# Start the server
npm start
```

### 2. Configure Environment Variables

```bash
# In your FlightPath directory
export OPENBNB_SERVER_URL=http://localhost:3000

# Optional: Configure OpenBNB API keys if required
export OPENBNB_API_KEY=your-key-here
```

### 3. Test the Integration

```python
# Test the accommodation engine
python accommodation_engine.py
```

### 4. API Endpoints Used

The accommodation engine expects these OpenBNB MCP endpoints:

- `GET /search` - Search for Airbnb listings
  - Parameters: location, checkin, checkout, guests, filters
  - Returns: Array of listing objects

### 5. Fallback Behavior

If OpenBNB MCP server is not running, the engine automatically falls back to mock data for testing, so you can still develop and test the optimization logic.

## Complete Setup for All Services

### Required API Keys:

1. **Booking.com API**
   - Sign up at: https://www.booking.com/affiliate-program/v2/
   - Set: `BOOKING_API_KEY=your-key`

2. **Marriott (Future Enhancement)**
   - Currently using mock data
   - Real scraping would require session management

3. **OpenBNB MCP**
   - Follow setup above
   - Provides real Airbnb data

### Running the Complete System:

```bash
# 1. Start OpenBNB MCP server (in separate terminal)
cd openbnb-mcp && npm start

# 2. Set environment variables
export ANTHROPIC_API_KEY=your-key
export BOOKING_API_KEY=your-key
export OPENBNB_SERVER_URL=http://localhost:3000
export REDIS_URL=redis://localhost:6379  # Optional

# 3. Run the complete trip optimizer
python complete_trip_optimizer.py
```

## Architecture Overview

```
FlightPath Complete System
├── Fast Flights Engine (Award Search)
│   ├── United Awards API
│   ├── American Awards API  
│   └── Marriott Awards API
│
├── Accommodation Engine
│   ├── OpenBNB MCP → Airbnb
│   ├── Booking.com API → Hotels
│   └── Marriott Scraper → Points
│
└── Complete Trip Optimizer
    ├── Budget Allocation
    ├── Points Optimization
    └── Value Scoring
```

## Testing Without External Services

The system includes comprehensive mock data, so you can test without setting up external services:

```python
# Test just accommodation search
python accommodation_engine.py

# Test complete trip optimization
python complete_trip_optimizer.py
```

Mock data includes realistic examples for:
- Disney World area properties
- Various price points
- Points redemption options
- Family-friendly amenities