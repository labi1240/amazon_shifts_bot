import requests
import logging
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from config.settings import get_settings

logger = logging.getLogger(__name__)

@dataclass
class JobMatch:
    """Represents a job match with details"""
    job_id: str
    title: str
    location: str
    schedule: str
    role_type: str
    score: float
    url: Optional[str] = None

@dataclass
class MonitoringStats:
    """System monitoring statistics"""
    session_duration: int
    jobs_found: int
    applications_submitted: int
    success_rate: float
    errors_count: int
    last_activity: datetime

class EnhancedDiscordNotifier:
    """Enhanced Discord notification system with comprehensive monitoring"""
    
    def __init__(self):
        settings = get_settings()
        self.webhook = settings.discord_webhook_url
        self.session_start = datetime.now()
        self.stats = MonitoringStats(
            session_duration=0,
            jobs_found=0,
            applications_submitted=0,
            success_rate=0.0,
            errors_count=0,
            last_activity=datetime.now()
        )
        
        # Test Discord connectivity on initialization
        if self.webhook:
            self._test_discord_connection()
        else:
            logger.error("❌ No Discord webhook URL configured! Notifications will not work!")
    
    def _test_discord_connection(self):
        """Test Discord connectivity on startup"""
        try:
            test_message = f"🔧 **Discord Connection Test**\n✅ Amazon Shift Bot notification system online!\n⏰ Started at: {datetime.now().strftime('%H:%M:%S')}"
            success = self.send(test_message, urgent=False, max_retries=3)
            if success:
                logger.info("✅ Discord notification system tested successfully!")
            else:
                logger.error("❌ Discord notification test failed!")
        except Exception as e:
            logger.error(f"❌ Discord connection test failed: {e}")
    
    def send(self, message: str, urgent: bool = False, max_retries: int = 5) -> bool:
        """Send message to Discord with bulletproof error handling and retries"""
        if not self.webhook:
            logger.error("❌ No Discord webhook configured - notifications disabled!")
            return False
        
        # Add timestamp and urgency indicator
        timestamp = datetime.now().strftime('%H:%M:%S')
        if urgent:
            message = f"🚨 **URGENT** 🚨\n🕐 **{timestamp}** | {message}"
        else:
            message = f"🕐 **{timestamp}** | {message}"
        
        for attempt in range(max_retries):
            try:
                payload = {
                    "content": message,
                    "username": "Amazon Shift Bot" + (" 🚨" if urgent else " 🤖"),
                    "avatar_url": "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=100",
                    "embeds": [{
                        "color": 0xFF0000 if urgent else 0x00FF00,
                        "footer": {
                            "text": f"Attempt {attempt + 1}/{max_retries} | Shift Bot v2.0"
                        },
                        "timestamp": datetime.now().isoformat()
                    }] if urgent else None
                }
                
                # Progressive timeout strategy
                timeout_values = [5, 10, 15, 20, 30]
                timeout = timeout_values[min(attempt, len(timeout_values) - 1)]
                
                logger.info(f"🔔 Sending Discord notification (attempt {attempt + 1}/{max_retries}) with {timeout}s timeout")
                
                response = requests.post(
                    self.webhook,
                    json=payload,
                    timeout=timeout,
                    headers={
                        'User-Agent': 'Amazon-Shift-Bot/2.0',
                        'Content-Type': 'application/json'
                    }
                )
                
                if response.status_code == 204:
                    logger.info(f"✅ Discord notification sent successfully on attempt {attempt + 1}")
                    return True
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 1))
                    logger.warning(f"⚠️ Discord rate limited, waiting {retry_after}s before retry")
                    time.sleep(retry_after)
                    continue
                else:
                    logger.error(f"❌ Discord notification failed: Status {response.status_code}, Response: {response.text[:200]}")
                    
            except requests.exceptions.Timeout as e:
                logger.warning(f"⏰ Discord notification timeout on attempt {attempt + 1}: {e}")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"🌐 Discord connection error on attempt {attempt + 1}: {e}")
            except requests.exceptions.RequestException as e:
                logger.error(f"📡 Discord request error on attempt {attempt + 1}: {e}")
            except Exception as e:
                logger.error(f"💥 Unexpected error sending Discord notification on attempt {attempt + 1}: {e}")
            
            # Progressive backoff delay
            if attempt < max_retries - 1:
                delay = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                logger.info(f"⏳ Waiting {delay}s before retry...")
                time.sleep(delay)
        
        logger.error(f"❌ Failed to send Discord notification after {max_retries} attempts")
        # Try fallback notification
        self._send_fallback_notification(message, urgent)
        return False
    
    def _send_fallback_notification(self, message: str, urgent: bool = False):
        """Fallback notification methods when Discord fails"""
        try:
            # Log to file as fallback
            fallback_file = 'discord_failures.log'
            with open(fallback_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} - {message}\n")
            
            # Try console beep for urgent messages
            if urgent:
                try:
                    os.system('afplay /System/Library/Sounds/Sosumi.aiff 2>/dev/null || echo -e "\a"')
                except:
                    pass
                    
            logger.warning(f"📝 Fallback: Logged notification to {fallback_file}")
            
        except Exception as e:
            logger.error(f"💥 Even fallback notification failed: {e}")
    
    def notify_bot_startup(self, config_info: Dict[str, Any]):
        """Notify when bot starts up"""
        message = f"""🤖 **Amazon Job Bot Started**
⏰ **Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 **Target Roles**: {len(config_info.get('target_roles', []))} roles configured
⚙️ **Check Interval**: {config_info.get('check_interval', 'N/A')} seconds
📧 **Email**: {config_info.get('email', 'N/A')}
🌐 **Headless Mode**: {config_info.get('headless', False)}
📊 **Max Applications/Day**: {config_info.get('max_per_day', 'N/A')}

✅ **Bot is now monitoring for jobs!**"""
        self.send(message)
    
    def notify_login_status(self, success: bool, method: str = "fresh", details: str = ""):
        """Notify login attempt results"""
        if success:
            emoji = "✅" if method == "fresh" else "🔄"
            message = f"{emoji} **Login Successful** ({method})\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            if details:
                message += f"\n📝 {details}"
        else:
            message = f"❌ **Login Failed** ({method})\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            if details:
                message += f"\n🔍 **Error**: {details}"
            self.stats.errors_count += 1
        
        self.send(message, urgent=not success)
    
    def notify_session_status(self, status: str, details: str = ""):
        """Notify session management events"""
        emoji_map = {
            "restored": "🔄",
            "saved": "💾",
            "expired": "⏰",
            "refreshed": "🔃",
            "failed": "❌"
        }
        
        emoji = emoji_map.get(status, "ℹ️")
        message = f"{emoji} **Session {status.title()}**\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        
        if details:
            message += f"\n📝 {details}"
        
        urgent = status in ["expired", "failed"]
        self.send(message, urgent=urgent)
    
    def notify_job_search_start(self, role_type: str, search_url: str):
        """Notify when starting job search for specific role"""
        message = f"""🔍 **Job Search Started**
🎯 **Role**: {role_type}
🌐 **URL**: {search_url}
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}

🔄 Scanning for available positions..."""
        self.send(message)
    
    def notify_jobs_found(self, jobs: List[JobMatch], role_type: str):
        """Notify when jobs are found"""
        if not jobs:
            message = f"""📭 **No Jobs Found**
🎯 **Role**: {role_type}
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}

🔄 Will check again in next cycle..."""
            self.send(message)
            return
        
        self.stats.jobs_found += len(jobs)
        
        # Create detailed job listing
        job_list = "\n".join([
            f"• **{job.title}**\n  📍 {job.location}\n  📅 {job.schedule}\n  ⭐ Score: {job.score:.1f}/100\n"
            for job in jobs[:5]  # Limit to first 5 jobs
        ])
        
        if len(jobs) > 5:
            job_list += f"\n... and {len(jobs) - 5} more jobs"
        
        message = f"""🎯 **{len(jobs)} Jobs Found!**
🎭 **Role**: {role_type}
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}

📋 **Job Details**:
{job_list}

🚀 **Starting application process...**"""
        
        self.send(message)
    
    def notify_application_attempt(self, job: JobMatch, attempt_num: int):
        """Notify when attempting to apply for a job"""
        message = f"""📝 **Application Attempt #{attempt_num}**
🎯 **Job**: {job.title}
📍 **Location**: {job.location}
🆔 **Job ID**: {job.job_id}
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}

🔄 Processing application..."""
        self.send(message)
    
    def notify_application_result(self, job: JobMatch, success: bool, details: str = ""):
        """Notify application result with instant booking alerts"""
        if success:
            self.stats.applications_submitted += 1
            message = f"""🎉 **INSTANT BOOKING SUCCESS!**
⚡ **SHIFT BOOKED IMMEDIATELY**
🎯 **Job**: {job.title}
📍 **Location**: {job.location}
🆔 **Job ID**: {job.job_id}
⏰ **Booked at**: {datetime.now().strftime('%H:%M:%S')}
💰 **Pay**: {getattr(job, 'pay_rate', 'TBD')}

✅ **CONGRATULATIONS! Your shift has been secured!**
🚀 **Ultra-fast booking system worked perfectly!**"""
        else:
            self.stats.errors_count += 1
            message = f"""❌ **INSTANT BOOKING FAILED**
🎯 **Job**: {job.title}
📍 **Location**: {job.location}
🆔 **Job ID**: {job.job_id}
⏰ **Failed at**: {datetime.now().strftime('%H:%M:%S')}
🔍 **Error**: {details}

⚡ **Fast retry in progress - will attempt again in 10 seconds...**"""
        
        self.send(message, urgent=True)  # All booking results are urgent

    def notify_instant_booking_attempt(self, job: JobMatch):
        """Notify when instant booking is attempted"""
        message = f"""⚡ **INSTANT BOOKING IN PROGRESS!**
🎯 **Job**: {job.title}
📍 **Location**: {job.location}
⏰ **Started**: {datetime.now().strftime('%H:%M:%S')}

🚀 **Lightning-fast booking system activated!**
⏳ **Booking in progress...**"""
        
        self.send(message, urgent=True)

    def notify_instant_booking_success(self, shift_number: int, title: str, location: str, 
                                     schedule: str, pay_rate: str, discovered_at: str, 
                                     correlation_id: str):
        """Send detailed notification for successful instant booking."""
        message = f"""🎉 **INSTANT BOOKING SUCCESS #{shift_number}!**
⚡ **SHIFT BOOKED IMMEDIATELY**

📋 **SHIFT DETAILS:**
🎯 **Position**: {title}
📍 **Location**: {location}
📅 **Schedule**: {schedule}
💰 **Pay Rate**: {pay_rate}
🕐 **Discovered**: {discovered_at}
🆔 **Booking ID**: {correlation_id}

✅ **CONGRATULATIONS! Your shift has been secured!**
🚀 **Ultra-fast booking system worked perfectly!**
🔄 **Continuing to monitor for more shifts...**"""
        
        self.send(message, urgent=True)

    def notify_monitoring_summary(self, cycle: int, jobs_found: int, bookings_made: int, 
                                cities_processed: List[str], next_check_in: int):
        """Send monitoring cycle summary."""
        cities_text = ", ".join(cities_processed[:3])
        if len(cities_processed) > 3:
            cities_text += f" + {len(cities_processed) - 3} more"
            
        message = f"""📊 **MONITORING CYCLE #{cycle} COMPLETE**
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}

🔍 **CYCLE RESULTS:**
• 🎯 Jobs Found: {jobs_found}
• ✅ Bookings Made: {bookings_made}
• 🏙️ Cities Scanned: {cities_text}
• ⚡ Status: {"BOOKING SUCCESS!" if bookings_made > 0 else "Continuing search..."}

⏳ **Next scan in {next_check_in} seconds...**
🔄 **Continuous monitoring active**"""
        
        self.send(message)
    
    def notify_cycle_complete(self, cycle_stats: Dict[str, Any]):
        """Notify when a monitoring cycle completes"""
        duration = datetime.now() - self.session_start
        self.stats.session_duration = int(duration.total_seconds())
        
        # Calculate success rate
        total_attempts = cycle_stats.get('total_attempts', 0)
        successful_apps = cycle_stats.get('successful_applications', 0)
        success_rate = (successful_apps / total_attempts * 100) if total_attempts > 0 else 0
        
        message = f"""📊 **Monitoring Cycle Complete**
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}
🔄 **Cycle Duration**: {cycle_stats.get('cycle_duration', 'N/A')} seconds

📈 **Cycle Stats**:
• 🎯 Jobs Found: {cycle_stats.get('jobs_found', 0)}
• 📝 Applications Attempted: {total_attempts}
• ✅ Successful Applications: {successful_apps}
• 📊 Success Rate: {success_rate:.1f}%
• ❌ Errors: {cycle_stats.get('errors', 0)}

📊 **Session Stats**:
• ⏱️ Total Runtime: {self._format_duration(self.stats.session_duration)}
• 🎯 Total Jobs Found: {self.stats.jobs_found}
• 📝 Total Applications: {self.stats.applications_submitted}
• ❌ Total Errors: {self.stats.errors_count}

⏳ **Next check in {cycle_stats.get('next_check_in', 'N/A')} seconds...**"""
        
        self.send(message)
    
    def notify_error(self, error_type: str, error_message: str, critical: bool = False):
        """Notify when errors occur"""
        self.stats.errors_count += 1
        
        message = f"""❌ **Error Detected**
🔍 **Type**: {error_type}
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}
📝 **Details**: {error_message}

{'🚨 **CRITICAL ERROR** - Bot may need attention!' if critical else '🔄 Bot will attempt to recover...'}"""
        
        self.send(message, urgent=critical)
    
    def notify_daily_summary(self, daily_stats: Dict[str, Any]):
        """Send daily summary report"""
        message = f"""📊 **Daily Summary Report**
📅 **Date**: {datetime.now().strftime('%Y-%m-%d')}
⏰ **Report Time**: {datetime.now().strftime('%H:%M:%S')}

📈 **Performance Metrics**:
• 🎯 Total Jobs Found: {daily_stats.get('total_jobs_found', 0)}
• 📝 Applications Submitted: {daily_stats.get('applications_submitted', 0)}
• ✅ Success Rate: {daily_stats.get('success_rate', 0):.1f}%
• ⏱️ Total Runtime: {self._format_duration(daily_stats.get('total_runtime', 0))}
• 🔄 Monitoring Cycles: {daily_stats.get('total_cycles', 0)}
• ❌ Total Errors: {daily_stats.get('total_errors', 0)}

🎭 **Role Performance**:
{self._format_role_stats(daily_stats.get('role_stats', {}))}

{'🎉 **Excellent performance today!**' if daily_stats.get('success_rate', 0) > 80 else '📈 **Room for improvement - analyzing patterns...**'}"""
        
        self.send(message)
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in human readable format"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _format_role_stats(self, role_stats: Dict[str, Any]) -> str:
        """Format role-specific statistics"""
        if not role_stats:
            return "• No role-specific data available"
        
        formatted = []
        for role, stats in role_stats.items():
            formatted.append(
                f"• **{role}**: {stats.get('jobs_found', 0)} jobs, "
                f"{stats.get('applications', 0)} applications"
            )
        
        return "\n".join(formatted)
    
    # Legacy methods for backward compatibility
    def notify_shifts(self, shifts):
        """Legacy method - convert to new format"""
        if not shifts:
            return
        
        job_matches = [
            JobMatch(
                job_id=getattr(s, 'job_id', 'N/A'),
                title=getattr(s, 'title', 'Unknown'),
                location=getattr(s, 'location', 'Unknown'),
                schedule=getattr(s, 'schedule', 'Unknown'),
                role_type='Legacy',
                score=75.0
            ) for s in shifts
        ]
        
        self.notify_jobs_found(job_matches, "Legacy Search")
    
    def notify_booking(self, shift):
        """Legacy method - convert to new format"""
        job_match = JobMatch(
            job_id=getattr(shift, 'job_id', 'N/A'),
            title=getattr(shift, 'title', 'Unknown'),
            location=getattr(shift, 'location', 'Unknown'),
            schedule=getattr(shift, 'schedule', 'Unknown'),
            role_type='Legacy',
            score=75.0
        )
        
        self.notify_application_result(job_match, True, "Legacy booking successful")