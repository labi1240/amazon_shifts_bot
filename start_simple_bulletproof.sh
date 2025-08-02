#!/bin/bash

# Amazon Shift Bot - Simple Bulletproof Mode
# Uses existing enhanced system with bulletproof Discord notifications

echo "🛡️ Starting Amazon Shift Bot - SIMPLE BULLETPROOF MODE"
echo "⚡ Enhanced system with bulletproof Discord notifications"
echo ""

# Activate virtual environment
source venv/bin/activate

# Test Discord notifications first
echo "🔧 Testing Discord notifications..."
python test_discord.py || {
    echo "❌ Discord test failed! Check your webhook URL."
    exit 1
}

echo ""
echo "✅ Discord notifications working perfectly!"
echo "🚀 Starting enhanced monitoring with bulletproof notifications..."
echo ""

# Start the enhanced system with bulletproof config
python cli.py run --config instant_booking_config.yaml --debug

echo ""
echo "🛑 Bulletproof monitoring stopped."