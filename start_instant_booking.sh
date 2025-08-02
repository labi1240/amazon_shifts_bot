#!/bin/bash

# Amazon Shift Bot - Instant Booking Mode Startup Script
# Optimized for lightning-fast continuous monitoring and instant booking

echo "🚀 Starting Amazon Shift Bot - INSTANT BOOKING MODE"
echo "⚡ Optimized for ultra-fast shift booking and continuous monitoring"
echo ""

# Set environment variables for optimal performance
export PYTHON_UNBUFFERED=1
export INSTANT_BOOKING_MODE=true

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "Please create .env file with:"
    echo "AMAZON_EMAIL=lovepreet@teamarora.com"
    echo "AMAZON_PASSWORD=151093"
    echo "DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1399303189622296577/0sNzPRnz6nH5BWXW3Jg1khIeFOLENSLeXJNbOU9zD4K43aT6DFQNR349EOBCw44Wi5le"
    echo ""
    exit 1
fi

# Clear any existing sessions for fresh start
echo "🧹 Clearing existing sessions for instant booking optimization..."
python clear_session.py 2>/dev/null || echo "No sessions to clear"

# Display current configuration
echo ""
echo "📋 INSTANT BOOKING CONFIGURATION:"
echo "   • Check Interval: 45 seconds (ultra-fast)"
echo "   • Fast Mode: ENABLED"
echo "   • Instant Booking: ENABLED"
echo "   • Headless Mode: DISABLED (visible browser)"
echo "   • Session Duration: 24 hours"
echo "   • Parallel Processing: ENABLED"
echo "   • Performance Optimizations: ENABLED"
echo ""

# Start the bot with instant booking configuration
echo "🎯 Starting continuous monitoring with instant booking..."
echo "⚡ Bot will book shifts IMMEDIATELY when found!"
echo ""

# Run with ultra-fast configuration
python cli.py run --config instant_booking_config.yaml --debug

echo ""
echo "🛑 Instant booking monitoring stopped."