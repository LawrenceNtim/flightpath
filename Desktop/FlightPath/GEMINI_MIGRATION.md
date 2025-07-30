# FlightPath Gemini 2.0 Flash Migration Guide

## Overview

This guide helps you migrate from Claude/Anthropic to Gemini 2.0 Flash for cost-efficient AI-powered travel assistance.

## Key Benefits of Gemini 2.0 Flash

1. **Cost Efficiency**: Up to 10x cheaper than Claude 3.5 Sonnet
2. **Speed**: Faster response times for better user experience
3. **Multimodal**: Native support for images (future: boarding passes, hotel photos)
4. **Free Tier**: Generous free tier for development and testing

## Quick Start

### 1. Install Dependencies

```bash
# Install all requirements
pip install -r requirements.txt

# Or just Gemini
pip install google-generativeai
```

### 2. Get API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your key

### 3. Configure Environment

Create or update `.env` file:

```bash
GEMINI_API_KEY=your-api-key-here
```

### 4. Test Installation

```bash
python test_gemini_agent.py
```

## Migration from Claude

### Simple Replacement

Replace Claude imports:

```python
# Before
import anthropic
client = anthropic.Anthropic(api_key=key)

# After
import google.generativeai as genai
genai.configure(api_key=key)
model = genai.GenerativeModel('gemini-2.0-flash-exp')
```

### API Differences

Claude:
```python
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": prompt}]
)
result = response.content[0].text
```

Gemini:
```python
response = model.generate_content(prompt)
result = response.text
```

## Usage Examples

### Basic Travel Query

```python
from gemini_travel_agent import GeminiTravelAgent

agent = GeminiTravelAgent()
response = await agent.process_request(
    "Find flights from NYC to Paris next month",
    user_id="user123"
)
```

### Complete Trip Planning

```python
# Plan entire trip with one request
response = await agent.process_request(
    "Plan a 5-day trip to Tokyo including flights and hotel",
    user_id="user123"
)
```

### Conversation Flow

```python
# Multi-turn conversation
agent = GeminiTravelAgent()
user_id = "user123"

# First message
response1 = await agent.process_request("I want to visit Rome", user_id)

# Follow-up with context
response2 = await agent.process_request("What about hotels?", user_id)

# Booking confirmation
response3 = await agent.process_request("Book it!", user_id)
```

## Integration with Existing FlightPath

The new Gemini agent seamlessly integrates with existing components:

```python
# It automatically uses these if available:
- FlightPathOrchestrator (flight search)
- AccommodationOrchestratorV2 (hotel search)
- FastFlightsEngine (award flight search)
```

## Cost Comparison

| Model | Cost per 1M tokens | Speed | Best For |
|-------|-------------------|--------|----------|
| Claude 3.5 Sonnet | $3.00 input / $15.00 output | Medium | Complex reasoning |
| Gemini 2.0 Flash | $0.075 input / $0.30 output | Fast | High-volume queries |
| Gemini 1.5 Flash | Free tier available | Very Fast | Development |

## Advanced Features

### 1. Streaming Responses

```python
# For real-time responses
for chunk in model.generate_content_stream(prompt):
    print(chunk.text, end='')
```

### 2. Safety Settings

```python
model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',
    safety_settings={
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    }
)
```

### 3. System Instructions

```python
model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',
    system_instruction="You are a helpful travel agent..."
)
```

## Troubleshooting

### API Key Issues
- Ensure key is in `.env` file
- Check key permissions in Google AI Studio

### Rate Limits
- Free tier: 60 requests per minute
- Implement exponential backoff for production

### Model Availability
- If `gemini-2.0-flash-exp` unavailable, falls back to `gemini-1.5-flash`

## Production Deployment

### 1. Environment Variables

```bash
# Production .env
GEMINI_API_KEY=your-production-key
LOG_LEVEL=WARNING
DEBUG=False
```

### 2. Error Handling

```python
try:
    response = await agent.process_request(message, user_id)
except Exception as e:
    logger.error(f"Request failed: {e}")
    return "I'm having trouble right now. Please try again."
```

### 3. Monitoring

- Log all requests and responses
- Track token usage for cost management
- Monitor response times

## Next Steps

1. Run setup: `python setup_gemini.py`
2. Test agent: `python test_gemini_agent.py`
3. Integrate into your app: `from gemini_travel_agent import GeminiTravelAgent`

## Support

- [Gemini Documentation](https://ai.google.dev/docs)
- [Google AI Studio](https://makersuite.google.com/)
- [Gemini API Reference](https://ai.google.dev/api/python/google/generativeai)