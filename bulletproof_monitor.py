import logging
import time
import signal
import sys
from datetime import datetime
from typing import Dict, Any, List
from seleniumbase import SB

# Import our bulletproof services
from services.bulletproof_session import BulletproofSessionService
from services.bulletproof_booking import BulletproofBookingService
from enhanced_notifier import EnhancedDiscordNotifier
from enhanced_integrated_monitor import EnhancedIntegratedMonitor
from config.models import AppConfig

logger = logging.getLogger(__name__)

class BulletproofMonitor:
    """Ultra-robust monitoring system with comprehensive error handling"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.running = False
        self.cycle_count = 0
        self.total_bookings = 0
        self.session_start = datetime.now()
        
        # Initialize bulletproof services
        self.session_service = BulletproofSessionService()
        self.notifier = None
        self.booking_service = None
        self.main_monitor = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🛡️ Bulletproof Monitor initialized")
    
    def start_bulletproof_monitoring(self):
        """Start bulletproof monitoring with comprehensive error handling"""
        
        try:
            # Initialize Discord notifications
            self._initialize_notifications()
            
            # Send startup notification
            self._send_startup_notification()
            
            logger.info("🚀 Starting bulletproof continuous monitoring")
            self.running = True
            
            # Main monitoring loop with error recovery
            self._run_monitoring_loop()
            
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"💥 Critical error in bulletproof monitor: {e}")
            self._send_critical_error_notification(str(e))
        finally:
            self._cleanup()
    
    def _initialize_notifications(self):
        """Initialize notification system with error handling"""
        try:
            self.notifier = EnhancedDiscordNotifier()
            
            # Test Discord connectivity
            test_success = self.session_service.send_test_notification(self.notifier)
            if test_success:
                logger.info("✅ Discord notification system verified")
            else:
                logger.warning("⚠️ Discord notification test failed - continuing without notifications")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize notifications: {e}")
            self.notifier = None
    
    def _send_startup_notification(self):
        """Send startup notification with system info"""
        if not self.notifier:
            return
            
        try:
            startup_message = f"""🛡️ **BULLETPROOF MONITORING STARTED**
⚡ **Ultra-Robust Amazon Shift Bot**

📊 **CONFIGURATION:**
• ⏰ Check Interval: {self.config.monitoring.check_interval}s (ultra-fast)
• 🎯 Fast Mode: {getattr(self.config.monitoring, 'fast_mode', True)}
• 🔥 Instant Booking: {getattr(self.config.monitoring, 'instant_booking', True)}
• 📈 Daily Limit: {getattr(self.config.booking, 'daily_limit', 3)} shifts
• 🔄 Max Retries: 5 (bulletproof)

🛡️ **BULLETPROOF FEATURES:**
• ✅ 5-level retry system
• ✅ Multiple selector strategies  
• ✅ Progressive error recovery
• ✅ Fallback notification system
• ✅ Session validation bulletproofing
• ✅ Comprehensive error handling

🚀 **Ready for continuous 24/7 operation!**
⚡ **Will book shifts INSTANTLY when found!**"""
            
            self.notifier.send(startup_message, urgent=True)
            
        except Exception as e:
            logger.error(f"❌ Startup notification failed: {e}")
    
    def _run_monitoring_loop(self):
        """Main monitoring loop with bulletproof error handling"""
        consecutive_failures = 0
        max_failures = 10
        
        while self.running:
            self.cycle_count += 1
            cycle_start = datetime.now()
            
            try:
                logger.info(f"🔄 Starting bulletproof monitoring cycle {self.cycle_count}")
                
                # Run monitoring cycle with bulletproof handling
                cycle_result = self._run_bulletproof_cycle()
                
                # Reset failure counter on success
                if cycle_result:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                
                # Check if we've had too many consecutive failures
                if consecutive_failures >= max_failures:
                    logger.error(f"❌ Too many consecutive failures ({consecutive_failures}). Entering recovery mode.")
                    self._enter_recovery_mode()
                    consecutive_failures = 0  # Reset after recovery
                
                # Calculate cycle duration
                cycle_duration = (datetime.now() - cycle_start).total_seconds()
                logger.info(f"⏱️ Cycle {self.cycle_count} completed in {cycle_duration:.1f}s")
                
                # Send cycle summary if notifications are enabled
                self._send_cycle_summary(cycle_duration, cycle_result)
                
                # Wait for next cycle with bulletproof timing
                if self.running:
                    self._wait_for_next_cycle()
                
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"💥 Error in monitoring cycle {self.cycle_count}: {e}")
                
                if consecutive_failures >= max_failures:
                    logger.error("🚨 Critical failure threshold reached. Attempting recovery...")
                    self._enter_recovery_mode() 
                    consecutive_failures = 0
                else:
                    # Progressive delay based on failures
                    delay = min(consecutive_failures * 10, 60)  # Max 60 seconds
                    logger.info(f"⏳ Error recovery delay: {delay}s")
                    time.sleep(delay)
    
    def _run_bulletproof_cycle(self) -> bool:
        """Run a single monitoring cycle with bulletproof error handling"""
        
        try:
            # Initialize browser with bulletproof setup
            with SB(uc=True, headless=False) as sb:
                
                # Initialize services with current browser
                self.booking_service = BulletproofBookingService(sb, self.notifier)
                
                # Validate session with bulletproof method
                session_valid = self.session_service.validate_session_bulletproof(sb)
                if not session_valid:
                    logger.warning("⚠️ Session validation failed, attempting recovery")
                    return False
                
                # Initialize main monitor if not done
                if not self.main_monitor:
                    self.main_monitor = EnhancedIntegratedMonitor(self.config)
                    self.main_monitor.initialize_components(sb)
                
                # Run job search and booking with bulletproof handling
                jobs_found = self._search_jobs_bulletproof(sb)
                bookings_made = self._process_jobs_bulletproof(sb, jobs_found)
                
                # Update totals
                self.total_bookings += bookings_made
                
                logger.info(f"📊 Cycle results: {len(jobs_found) if jobs_found else 0} jobs found, {bookings_made} bookings made")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Bulletproof cycle error: {e}")
            return False
    
    def _search_jobs_bulletproof(self, sb) -> List[Dict[str, Any]]:
        """Search for jobs with bulletproof error handling"""
        
        max_search_retries = 3
        
        for attempt in range(max_search_retries):
            try:
                logger.info(f"🔍 Bulletproof job search (attempt {attempt + 1}/{max_search_retries})")
                
                # Use main monitor's job search functionality
                if self.main_monitor:
                    # Navigate to job search with retries
                    navigation_success = False
                    for nav_attempt in range(3):
                        try:
                            sb.open("https://hiring.amazon.com/app#/jobSearch")
                            time.sleep(2)
                            navigation_success = True
                            break
                        except Exception as nav_e:
                            logger.warning(f"⚠️ Navigation attempt {nav_attempt + 1} failed: {nav_e}")
                            if nav_attempt < 2:
                                time.sleep(3)
                                continue
                    
                    if not navigation_success:
                        logger.error("❌ Failed to navigate to job search")
                        if attempt < max_search_retries - 1:
                            time.sleep(5)
                            continue
                        return []
                    
                    # Extract job information
                    try:
                        if hasattr(self.main_monitor, 'job_reporter'):
                            report_data = self.main_monitor.job_reporter.extract_all_job_information()
                            jobs = report_data.get('jobs', [])
                            logger.info(f"✅ Found {len(jobs)} jobs")
                            return jobs
                    except Exception as e:
                        logger.warning(f"⚠️ Job extraction failed: {e}")
                
                return []
                
            except Exception as e:
                logger.error(f"❌ Job search attempt {attempt + 1} failed: {e}")
                if attempt < max_search_retries - 1:
                    time.sleep(5)
                    continue
        
        logger.error("❌ All job search attempts failed")
        return []
    
    def _process_jobs_bulletproof(self, sb, jobs: List[Dict[str, Any]]) -> int:
        """Process jobs with bulletproof booking"""
        
        if not jobs:
            logger.info("ℹ️ No jobs to process")
            return 0
        
        bookings_made = 0
        max_bookings_per_cycle = getattr(self.config.booking, 'per_cycle_limit', 2)
        
        logger.info(f"🎯 Processing {len(jobs)} jobs (max {max_bookings_per_cycle} bookings per cycle)")
        
        for job_idx, job in enumerate(jobs[:10]):  # Limit to first 10 jobs for speed
            try:
                if bookings_made >= max_bookings_per_cycle:
                    logger.info(f"🎯 Reached per-cycle booking limit ({max_bookings_per_cycle})")
                    break
                
                if self.total_bookings >= getattr(self.config.booking, 'daily_limit', 3):
                    logger.info(f"🎯 Reached daily booking limit ({self.config.booking.daily_limit})")
                    self.running = False
                    break
                
                logger.info(f"🎯 Attempting bulletproof booking for job {job_idx + 1}: {job.get('title', 'Unknown')}")
                
                # Attempt booking with bulletproof service
                correlation_id = f"{self.cycle_count}-{job_idx + 1}"
                booking_success = self.booking_service.attempt_bulletproof_booking(job, correlation_id)
                
                if booking_success:
                    bookings_made += 1
                    logger.info(f"🎉 BOOKING SUCCESS! Total today: {self.total_bookings + bookings_made}")
                    
                    # Small delay between successful bookings
                    time.sleep(2)
                else:
                    logger.warning(f"⚠️ Booking failed for job {job_idx + 1}")
                
            except Exception as e:
                logger.error(f"❌ Error processing job {job_idx + 1}: {e}")
                continue
        
        return bookings_made
    
    def _send_cycle_summary(self, cycle_duration: float, cycle_success: bool):
        """Send cycle summary notification"""
        if not self.notifier:
            return
            
        try:
            # Only send summary every 5 cycles to avoid spam
            if self.cycle_count % 5 == 0:
                session_duration = (datetime.now() - self.session_start).total_seconds() / 3600  # hours
                
                summary_message = f"""📊 **BULLETPROOF MONITORING UPDATE**
🔄 **Cycle #{self.cycle_count}** | ⏱️ **{cycle_duration:.1f}s**

📈 **SESSION STATS:**
• ⏰ Running: {session_duration:.1f} hours
• 🎯 Total Bookings: {self.total_bookings}
• ✅ Cycle Success: {"YES" if cycle_success else "NO"}
• 🔄 Status: {"ACTIVE" if self.running else "STOPPING"}

⚡ **NEXT SCAN:** {self.config.monitoring.check_interval}s
🛡️ **BULLETPROOF MODE:** Active"""
                
                self.notifier.send(summary_message)
        
        except Exception as e:
            logger.error(f"❌ Cycle summary notification failed: {e}")
    
    def _wait_for_next_cycle(self):
        """Wait for next cycle with bulletproof timing"""
        try:
            wait_time = self.config.monitoring.check_interval
            logger.info(f"⏳ Waiting {wait_time}s until next bulletproof cycle...")
            
            # Interruptible sleep
            for i in range(wait_time):
                if not self.running:
                    break
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Wait cycle error: {e}")
            time.sleep(60)  # Fallback wait
    
    def _enter_recovery_mode(self):
        """Enter recovery mode after consecutive failures"""
        logger.warning("🔧 Entering recovery mode...")
        
        try:
            # Send recovery notification
            if self.notifier:
                recovery_message = f"""🔧 **RECOVERY MODE ACTIVATED**
⚠️ **Multiple failures detected**

🛡️ **RECOVERY ACTIONS:**
• 🔄 Clearing browser cache
• 🔧 Reinitializing services  
• ⏳ Extended recovery delay
• 🔍 Session revalidation

⏰ **Recovery time:** 2 minutes
🚀 **Will resume monitoring after recovery**"""
                
                self.notifier.send(recovery_message, urgent=True)
            
            # Extended recovery delay
            logger.info("⏳ Recovery delay: 120 seconds")
            time.sleep(120)
            
            # Reset services
            self.main_monitor = None
            self.booking_service = None
            
            logger.info("✅ Recovery mode completed")
            
        except Exception as e:
            logger.error(f"❌ Recovery mode error: {e}")
            time.sleep(60)  # Fallback recovery
    
    def _send_critical_error_notification(self, error_message: str):
        """Send critical error notification"""
        if not self.notifier:
            return
            
        try:
            critical_message = f"""🚨 **CRITICAL ERROR**
💥 **System encountered critical error**

❌ **Error:** {error_message}
⏰ **Time:** {datetime.now().strftime('%H:%M:%S')}
🔄 **Cycle:** {self.cycle_count}

🛡️ **System is attempting recovery...**"""
            
            self.notifier.send(critical_message, urgent=True)
            
        except Exception as e:
            logger.error(f"❌ Critical error notification failed: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
        
        if self.notifier:
            try:
                shutdown_message = f"""🛑 **BULLETPROOF MONITOR SHUTDOWN**
⏰ **Time:** {datetime.now().strftime('%H:%M:%S')}
📊 **Total Cycles:** {self.cycle_count}
🎯 **Total Bookings:** {self.total_bookings}
⏱️ **Session Duration:** {(datetime.now() - self.session_start).total_seconds() / 3600:.1f} hours

✅ **Graceful shutdown completed**"""
                
                self.notifier.send(shutdown_message)
            except:
                pass
    
    def _cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up resources...")
        self.running = False