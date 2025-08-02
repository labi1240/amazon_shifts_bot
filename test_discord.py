#!/usr/bin/env python3
"""
Discord Notification Test Script
Tests the bulletproof Discord notification system
"""

import sys
import os
sys.path.append('.')

from enhanced_notifier import EnhancedDiscordNotifier
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_discord_notifications():
    """Test Discord notification system comprehensively"""
    
    print("🔧 Testing Discord Notification System...")
    print("=" * 50)
    
    try:
        # Initialize notifier
        print("1. Initializing Discord notifier...")
        notifier = EnhancedDiscordNotifier()
        
        if not notifier.webhook:
            print("❌ No Discord webhook configured!")
            return False
        
        print(f"✅ Discord webhook configured: {notifier.webhook[:50]}...")
        
        # Test 1: Basic notification
        print("\n2. Testing basic notification...")
        basic_success = notifier.send("🔧 **Discord Test #1**\n✅ Basic notification test")
        print(f"   Result: {'✅ SUCCESS' if basic_success else '❌ FAILED'}")
        
        # Test 2: Urgent notification
        print("\n3. Testing urgent notification...")
        urgent_success = notifier.send("🚨 **Discord Test #2**\n⚡ Urgent notification test", urgent=True)
        print(f"   Result: {'✅ SUCCESS' if urgent_success else '❌ FAILED'}")
        
        # Test 3: Bulletproof notification with retries
        print("\n4. Testing bulletproof notification with retries...")
        bulletproof_success = notifier.send("🛡️ **Discord Test #3**\n🔄 Bulletproof notification with retry system", urgent=False, max_retries=3)
        print(f"   Result: {'✅ SUCCESS' if bulletproof_success else '❌ FAILED'}")
        
        # Test 4: Mock instant booking notification
        print("\n5. Testing instant booking notification...")
        try:
            notifier.notify_instant_booking_success(
                shift_number=1,
                title="Test Warehouse Associate",
                location="Seattle, WA",
                schedule="Flexible Shifts (19h)",
                pay_rate="Up to $20",
                discovered_at="TEST",
                correlation_id="test-123"
            )
            print("   Result: ✅ SUCCESS")
            booking_success = True
        except Exception as e:
            print(f"   Result: ❌ FAILED - {e}")
            booking_success = False
        
        # Test 5: Monitoring summary notification
        print("\n6. Testing monitoring summary notification...")
        try:
            notifier.notify_monitoring_summary(
                cycle=1,
                jobs_found=25,
                bookings_made=1,
                cities_processed=["Seattle, WA", "Bellevue, WA"],
                next_check_in=45
            )
            print("   Result: ✅ SUCCESS")
            summary_success = True
        except Exception as e:
            print(f"   Result: ❌ FAILED - {e}")
            summary_success = False
        
        # Final summary
        print("\n" + "=" * 50)
        print("📊 DISCORD TEST SUMMARY:")
        print(f"   • Basic Notification: {'✅' if basic_success else '❌'}")
        print(f"   • Urgent Notification: {'✅' if urgent_success else '❌'}")
        print(f"   • Bulletproof Notification: {'✅' if bulletproof_success else '❌'}")
        print(f"   • Booking Notification: {'✅' if booking_success else '❌'}")
        print(f"   • Summary Notification: {'✅' if summary_success else '❌'}")
        
        total_tests = 5
        passed_tests = sum([basic_success, urgent_success, bulletproof_success, booking_success, summary_success])
        
        print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Discord notification system is working perfectly!")
            
            # Send final success notification
            notifier.send(f"""🎉 **DISCORD TEST COMPLETE**
✅ **All {total_tests} notification tests passed!**

🔧 **System is ready for bulletproof operation!**
⚡ **Notifications will work perfectly during monitoring!**""", urgent=True)
            
            return True
        else:
            print(f"⚠️ {total_tests - passed_tests} tests failed. Check Discord webhook configuration.")
            return False
        
    except Exception as e:
        print(f"💥 Critical error during Discord testing: {e}")
        return False

if __name__ == "__main__":
    success = test_discord_notifications()
    sys.exit(0 if success else 1)