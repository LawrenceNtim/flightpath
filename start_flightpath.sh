#!/bin/bash
# FlightPath Enhanced System Launcher

echo "🚀 Starting Enhanced FlightPath System..."
echo "================================================================="

# Check if Python dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import spacy, anthropic, flask, holidays, geopy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Please run:"
    echo "   pip3 install spacy anthropic flask flask-cors holidays geopy python-dateutil pytz requests-cache"
    echo "   python3 -m spacy download en_core_web_sm"
    exit 1
fi

# Check if API key is configured
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it with your Anthropic API key:"
    echo "   cp .env.example .env"
    echo "   # Then edit .env and add your API key"
    exit 1
fi

# Kill any existing processes
echo "🔄 Cleaning up existing processes..."
pkill -f "enhanced_app.py" 2>/dev/null
pkill -f "app.py" 2>/dev/null

# Start the enhanced application
echo "🎯 Starting enhanced FlightPath application..."
cd flightpath_web
python3 enhanced_app.py > /tmp/flightpath.log 2>&1 &

# Wait for startup
sleep 3

# Check if server is running
if curl -s http://localhost:5003/api/health > /dev/null; then
    echo "✅ Enhanced FlightPath system is running!"
    echo ""
    echo "🌐 Access the application at: http://localhost:5003"
    echo ""
    echo "🎉 Features Available:"
    echo "   • Natural Language Search: 'wedding by 12pm August 15th, leave Sunday from LA to NY'"
    echo "   • Voice Input: Click the microphone button (Chrome/Edge)"
    echo "   • Context Insights: Real-time travel intelligence"
    echo "   • AI Chat: Conversational flight assistance"
    echo "   • Traditional Form: Fallback structured input"
    echo ""
    echo "📋 Example Queries:"
    echo "   • 'Business trip from Miami to Denver next Tuesday, first class'"
    echo "   • 'Family vacation to Orlando, 4 passengers, flexible dates'"
    echo "   • 'Cheap flight from Vegas to Phoenix this weekend'"
    echo ""
    echo "📊 View logs: tail -f /tmp/flightpath.log"
    echo "🛑 Stop server: pkill -f enhanced_app.py"
else
    echo "❌ Failed to start server. Check logs:"
    echo "   tail -f /tmp/flightpath.log"
    exit 1
fi