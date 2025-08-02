#!/usr/bin/env python3
"""
Simple script to create and save Amazon session using existing proven login flow
"""

import os
import sys
import logging
from dotenv import load_dotenv
from seleniumbase import SB
from amazon_page_objects import AmazonConsentPage, AmazonLoginPage
from session_manager import AmazonSessionManager
from utils.otp_reader import get_recent_otp_from_gmail
from config.settings import get_settings

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SessionCreator:
    """Create and save Amazon session using proven login flow"""
    
    def __init__(self):
        # Create a simple config object with the needed attributes
        self.config = type('Config', (), {
            'email': os.getenv('AMAZON_EMAIL', 'lovepreet@teamarora.com'),
            'pin': os.getenv('AMAZON_PASSWORD', '151093'),
            'base_url': 'https://hiring.amazon.com',
            'location': os.getenv('JOB_LOCATION', 'nyc'),
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'default_timeout': int(os.getenv('DEFAULT_TIMEOUT', '15')),
            'page_load_timeout': int(os.getenv('PAGE_LOAD_TIMEOUT', '30')),
            'otp_search_hours': int(os.getenv('OTP_SEARCH_HOURS', '1')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_file': os.getenv('LOG_FILE', 'amazon_bot.log'),
            'headless': os.getenv('HEADLESS', 'false').lower() == 'true',
            'demo_mode': os.getenv('DEMO_MODE', 'false').lower() == 'true'
        })()
        
        # Add validate method
        def validate():
            if not self.config.email or '@' not in self.config.email:
                raise ValueError("Invalid email configuration")
            if not self.config.pin or len(self.config.pin) < 4:
                raise ValueError("Invalid PIN configuration")
            return True
        
        self.config.validate = validate
        self.config.validate()
        
        self.session_manager = AmazonSessionManager()
        self.consent_page = AmazonConsentPage()
        self.login_page = AmazonLoginPage()
    
    def create_session(self, sb) -> bool:
        """Create session using existing login flow with SB context manager"""
        logger.info("🔐 Creating Amazon session...")
        
        try:
            # Navigate to Amazon hiring page
            logger.info("🌐 Navigating to Amazon hiring page...")
            sb.open("https://hiring.amazon.com")
            sb.sleep(3)
            
            # Handle consent
            self.consent_page.handle_consent(sb)
            
            # Navigate to login
            if not self.login_page.navigate_to_login(sb):
                logger.error("❌ Failed to navigate to login")
                return False
            
            # Handle consent after navigation
            self.consent_page.handle_consent(sb)
            self.consent_page.handle_bottom_consent(sb)
            
            # Enter email
            if not self.login_page.enter_email(sb, self.config.email):
                logger.error("❌ Failed to enter email")
                return False
            
            # Handle consent again
            self.consent_page.handle_bottom_consent(sb)
            
            # Enter PIN if required
            if not self.login_page.enter_pin(sb, self.config.pin):
                logger.error("❌ Failed to enter PIN")
                return False
            
            # Request verification code if needed
            if not self.login_page.request_verification_code(sb):
                logger.error("❌ Failed to request verification code")
                return False
            
            # Handle OTP if required
            if sb.is_element_visible(self.login_page.OTP_INPUT):
                logger.info("📧 Retrieving OTP from Gmail...")
                otp = get_recent_otp_from_gmail(hours_back=self.config.otp_search_hours)
                
                if otp:
                    logger.info(f"✅ Retrieved OTP: {otp}")
                    if not self.login_page.enter_otp(sb, otp):
                        logger.error("❌ Failed to enter OTP")
                        return False
                else:
                    logger.error("❌ Could not retrieve OTP")
                    return False
            
            # Final consent check
            self.consent_page.handle_bottom_consent(sb)
            
            # Save session with user email
            logger.info("💾 Saving session...")
            self.session_manager.save_session(sb, self.config.email)
            
            logger.info("✅ Session created and saved successfully!")
            logger.info(f"📁 Session saved to: amazon_session.pkl")
            logger.info(f"🍪 Cookies saved to: amazon_cookies.json")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating session: {e}")
            return False

def main():
    """Main entry point"""
    logger.info("🚀 Starting session creation...")
    
    # Create session creator instance
    creator = SessionCreator()
    
    # SB options for session creation - explicitly disable incognito
    sb_options = {
        'uc': True,
        'headed': True,  # Show browser for login
        'incognito': False  # Explicitly disable incognito mode
    }
    
    try:
        with SB(**sb_options) as sb:
            # Create session
            success = creator.create_session(sb)
            
            if success:
                logger.info("🎉 Session creation completed successfully!")
                logger.info("💡 You can now run the monitoring system with: python integrated_monitor.py --test")
                sys.exit(0)
            else:
                logger.error("❌ Session creation failed")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()