#!/usr/bin/env python3
"""
Setup script for FlightPath with Gemini 2.0 Flash
"""

import os
import sys
import subprocess

def check_python_version():
    """Ensure Python 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def install_dependencies():
    """Install required packages"""
    print("\n📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Dependencies installed")

def setup_environment():
    """Create .env file if not exists"""
    if not os.path.exists('.env'):
        print("\n🔧 Creating .env file...")
        with open('.env', 'w') as f:
            f.write("""# FlightPath Environment Configuration

# Gemini API (primary AI)
GEMINI_API_KEY=your-gemini-api-key-here

# Optional: Anthropic API (for backwards compatibility)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Optional: Other APIs
OPENAI_API_KEY=
SERPAPI_KEY=

# Application settings
DEBUG=False
LOG_LEVEL=INFO
""")
        print("✅ .env file created")
        print("⚠️  Please add your API keys to .env file")
    else:
        print("✅ .env file already exists")

def test_gemini():
    """Test Gemini connection"""
    print("\n🧪 Testing Gemini connection...")
    try:
        import google.generativeai as genai
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key or api_key == 'your-gemini-api-key-here':
            print("⚠️  Please set GEMINI_API_KEY in .env file")
            print("Get your key at: https://makersuite.google.com/app/apikey")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Say 'FlightPath is ready!'")
        print(f"✅ Gemini says: {response.text.strip()}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False

def main():
    """Run setup"""
    print("🚀 FlightPath Setup with Gemini 2.0 Flash")
    print("=" * 50)
    
    check_python_version()
    install_dependencies()
    setup_environment()
    
    if test_gemini():
        print("\n✅ Setup complete! FlightPath is ready to use.")
        print("\nQuick start:")
        print("  python gemini_travel_agent.py")
    else:
        print("\n⚠️  Setup complete but Gemini not configured.")
        print("Please add your GEMINI_API_KEY to .env file")

if __name__ == "__main__":
    main()