#!/bin/bash

# Amazon Shift Bot - BULLETPROOF MODE Startup Script
# Ultra-robust system with comprehensive error handling and retry mechanisms

echo "🛡️ Starting Amazon Shift Bot - BULLETPROOF MODE"
echo "⚡ Ultra-robust system with 5-level retry mechanisms"
echo "🔧 Comprehensive error handling and automatic recovery"
echo ""

# Set environment variables for bulletproof operation
export PYTHON_UNBUFFERED=1
export BULLETPROOF_MODE=true
export RECOVERY_MODE=enabled

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies with error handling
echo "📚 Installing dependencies with bulletproof handling..."
pip install -q -r requirements.txt || {
    echo "❌ Dependency installation failed, trying alternative method..."
    pip install --no-cache-dir -r requirements.txt || {
        echo "❌ Critical: Cannot install dependencies!"
        exit 1
    }
}

# Check for .env file
if [ ! -f ".env" ]; then
    echo "❌ CRITICAL: .env file not found!"
    echo "Please create .env file with:"
    echo "AMAZON_EMAIL=your_email@domain.com"
    echo "AMAZON_PASSWORD=your_password"
    echo "DISCORD_WEBHOOK_URL=your_discord_webhook_url"
    echo ""
    exit 1
fi

# Validate Discord webhook
if ! grep -q "DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks" .env; then
    echo "⚠️ WARNING: Discord webhook URL not found or invalid!"
    echo "Notifications may not work properly."
    echo ""
fi

# Clear any existing sessions for fresh start
echo "🧹 Clearing existing sessions for bulletproof startup..."
python clear_session.py 2>/dev/null || echo "No sessions to clear"

# Create bulletproof directories
mkdir -p logs
mkdir -p backups
mkdir -p recovery

# Display bulletproof configuration
echo ""
echo "🛡️ BULLETPROOF CONFIGURATION:"
echo "   • Check Interval: 45 seconds (ultra-fast)"
echo "   • Retry Levels: 5 (bulletproof)"
echo "   • Error Recovery: ENABLED"
echo "   • Session Validation: BULLETPROOF"
echo "   • Booking Strategies: MULTIPLE"
echo "   • Notification Fallbacks: ENABLED"
echo "   • Auto Recovery: ENABLED"
echo "   • Failure Tolerance: HIGH"
echo ""

# Test system components before starting
echo "🔧 Testing system components..."

# Test Python imports
echo "   • Testing imports..."
python -c "
import requests, selenium, seleniumbase
from enhanced_notifier import EnhancedDiscordNotifier
from services.bulletproof_session import BulletproofSessionService
from services.bulletproof_booking import BulletproofBookingService
print('   ✅ All imports successful')
" || {
    echo "   ❌ Import test failed!"
    exit 1
}

# Test Discord connectivity
echo "   • Testing Discord connectivity..."
python -c "
import sys
sys.path.append('.')
from enhanced_notifier import EnhancedDiscordNotifier
try:
    notifier = EnhancedDiscordNotifier()
    if notifier.webhook:
        print('   ✅ Discord webhook configured')
    else:
        print('   ⚠️ Discord webhook not configured')
except Exception as e:
    print(f'   ⚠️ Discord test warning: {e}')
"

echo "   ✅ System component tests completed"
echo ""

# Start the bulletproof monitoring system
echo "🚀 Starting bulletproof continuous monitoring..."
echo "🛡️ System will handle all errors automatically!"
echo "⚡ Bot will book shifts INSTANTLY when found!"
echo "🔄 Automatic recovery enabled for maximum uptime!"
echo ""
echo "🔥 BULLETPROOF FEATURES ACTIVE:"
echo "   • 5-level retry system"
echo "   • Multiple selector strategies"
echo "   • Progressive error recovery"
echo "   • Fallback notification system"
echo "   • Session validation bulletproofing"
echo "   • Comprehensive error handling"
echo "   • Automatic failure recovery"
echo "   • 24/7 operation optimized"
echo ""

# Start with bulletproof configuration
python -c "
import sys
sys.path.append('.')
from bulletproof_monitor import BulletproofMonitor
from config.models import AppConfig

# Load configuration
try:
    import yaml
    with open('instant_booking_config.yaml', 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Create config
    cfg = AppConfig()
    
    # Apply monitoring config
    if 'monitoring' in config_data:
        for key, value in config_data['monitoring'].items():
            if hasattr(cfg.monitoring, key):
                setattr(cfg.monitoring, key, value)
    
    # Apply booking config  
    if 'booking' in config_data:
        for key, value in config_data['booking'].items():
            if hasattr(cfg.booking, key):
                setattr(cfg.booking, key, value)
    
    print('✅ Configuration loaded successfully')
    
    # Start bulletproof monitor
    monitor = BulletproofMonitor(cfg)
    monitor.start_bulletproof_monitoring()
    
except KeyboardInterrupt:
    print('\n🛑 Bulletproof monitoring stopped by user')
except Exception as e:
    print(f'\n💥 Critical error: {e}')
    print('🔧 Check logs for details')
"

echo ""
echo "🛑 Bulletproof monitoring stopped."
echo "📝 Check logs/ directory for detailed information."