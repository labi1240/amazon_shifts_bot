#!/bin/bash

# Amazon Job Monitor - Quick Start Script

echo "🚀 Amazon Job Monitor - Quick Start"
echo "==================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Check configuration
echo "🔍 Checking configuration..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your credentials."
    exit 1
fi

# Run quick test first
echo "🧪 Running quick system test..."
python test_integration.py --unit

if [ $? -eq 0 ]; then
    echo "✅ Unit tests passed!"
    
    # Ask user what to do
    echo ""
    echo "Choose an option:"
    echo "1) Run live Discord test"
    echo "2) Start monitoring (test mode - 1 minute intervals)"
    echo "3) Start monitoring (production mode - 5 minute intervals)"
    echo "4) Exit"
    
    read -p "Enter choice (1-4): " choice
    
    case $choice in
        1)
            echo "🔗 Running live Discord test..."
            python test_integration.py --live
            ;;
        2)
            echo "🧪 Starting test mode monitoring..."
            python integrated_monitor.py --test --interval 60
            ;;
        3)
            echo "🚀 Starting production monitoring..."
            python integrated_monitor.py --interval 300
            ;;
        4)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice"
            exit 1
            ;;
    esac
else
    echo "❌ Tests failed. Please check the configuration and try again."
    exit 1
fi