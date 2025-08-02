import json
import os
import pickle
import time
from datetime import datetime, timedelta
from seleniumbase import BaseCase
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class AmazonSessionManager:
    """Manages Amazon session persistence for continuous monitoring"""
    
    def __init__(self, session_file: str = "amazon_session.pkl"):
        self.session_file = session_file
        self.cookies_file = "amazon_cookies.json"
        self.session_data = {}
        
    def save_session(self, sb: BaseCase, user_email: str = None) -> bool:
        """Save current session state including cookies and metadata"""
        try:
            # If no email provided, try to get from config or use default
            if not user_email:
                try:
                    from config.settings import get_settings
                    settings = get_settings()
                    user_email = settings.amazon_email
                except:
                    user_email = "lovepreet@teamarora.com"
            
            # Get all cookies
            cookies = sb.get_cookies()
            
            # Get current URL and page state
            current_url = sb.get_current_url()
            
            # Session metadata
            session_data = {
                'cookies': cookies,
                'current_url': current_url,
                'user_email': user_email,
                'timestamp': datetime.now().isoformat(),
                'user_agent': sb.execute_script("return navigator.userAgent;"),
                'session_storage': self._get_session_storage(sb),
                'local_storage': self._get_local_storage(sb)
            }
            
            # Save to pickle file
            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)
            
            # Also save cookies as JSON for backup
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            logger.info(f"✅ Session saved successfully for {user_email}")
            logger.info(f"📁 Session file: {self.session_file}")
            logger.info(f"🍪 Cookies count: {len(cookies)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save session: {e}")
            return False
    
    def load_session(self, sb: BaseCase) -> bool:
        """Load and restore previous session"""
        try:
            if not os.path.exists(self.session_file):
                logger.warning("⚠️ No saved session found")
                return False
            
            # Load session data
            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            # Check if session is not too old (reduce to 12 hours)
            session_time = datetime.fromisoformat(session_data['timestamp'])
            if datetime.now() - session_time > timedelta(hours=12):
                logger.warning("⚠️ Session is too old, clearing and requiring fresh login")
                self.clear_session()  # Clear expired session
                return False
            
            # Navigate to Amazon first
            sb.open("https://hiring.amazon.com")
            sb.sleep(5)  # Increased wait time
            
            # Handle consent if needed
            self._handle_consent(sb)
            
            # Restore cookies
            cookies_added = 0
            for cookie in session_data['cookies']:
                try:
                    sb.add_cookie(cookie)
                    cookies_added += 1
                except Exception as e:
                    logger.debug(f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}")
            
            logger.info(f"📊 Added {cookies_added}/{len(session_data['cookies'])} cookies")
            
            # Restore session and local storage
            self._restore_session_storage(sb, session_data.get('session_storage', {}))
            self._restore_local_storage(sb, session_data.get('local_storage', {}))
            
            # Navigate to the dashboard with retry
            for attempt in range(3):
                try:
                    sb.open("https://hiring.amazon.com/app#/myApplications")
                    sb.sleep(5)
                    
                    if self.validate_session(sb):
                        logger.info(f"✅ Session restored successfully for {session_data['user_email']}")
                        return True
                        
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    sb.sleep(2)
            
            logger.warning("⚠️ Session restoration failed after validation, clearing invalid session")
            self.clear_session()  # Clear invalid session
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to load session: {e}")
            return False
    
    def _handle_consent(self, sb: BaseCase):
        """Handle consent prompts during session loading"""
        consent_selectors = [
            'button[data-test-id="consentBtn"]',
            'button[data-test-component="StencilReactButton"] div:contains("I consent")',
            'button:contains("Accept All Cookies")'
        ]
        
        for selector in consent_selectors:
            try:
                if sb.is_element_visible(selector, timeout=2):
                    sb.click(selector)
                    sb.sleep(2)
                    logger.info(f"✅ Handled consent with selector: {selector}")
                    break
            except:
                continue
    
    def validate_session(self, sb: BaseCase, max_attempts: int = 3) -> bool:
        """Validate if current session is still active with retry logic"""
        for attempt in range(max_attempts):
            try:
                # Check for logout indicators first (more reliable)
                logout_indicators = [
                    'button:contains("Sign in")',
                    'input[data-test-id="input-test-id-login"]',
                    'div:contains("Sign in to your account")',
                    'div:contains("We need you to sign in")',
                    'button[data-test-id="signin-button"]'
                ]
                
                # Check for login indicators
                login_indicators = [
                    'div[data-test-component="StencilReactRow"]',  # Dashboard rows
                    'button:contains("Go to my jobs")',
                    'button:contains("Search all jobs")',
                    'div:contains("Active jobs")',
                    'div:contains("Recommended jobs")',
                    'div:contains("My Applications")',
                    'div:contains("Application status")'
                ]
                
                # Wait for page to load
                sb.sleep(3)
                
                # First check for logout indicators (if found, definitely invalid)
                for indicator in logout_indicators:
                    if sb.is_element_visible(indicator):
                        logger.warning(f"⚠️ Session invalid - found logout indicator: {indicator}")
                        return False
                
                # Then check for login indicators
                for indicator in login_indicators:
                    if sb.is_element_visible(indicator):
                        logger.info(f"✅ Session valid - found: {indicator}")
                        return True
                
                # Check URL as fallback
                current_url = sb.get_current_url()
                if any(path in current_url for path in ["myApplications", "dashboard", "jobSearch"]):
                    # Additional check: make sure we're not on a login page
                    if "login" not in current_url.lower():
                        logger.info("✅ Session appears valid based on URL")
                        return True
                
                if attempt < max_attempts - 1:
                    logger.warning(f"⚠️ Session validation attempt {attempt + 1} inconclusive, retrying...")
                    sb.sleep(2)
                    continue
                
                logger.warning("⚠️ Session validation failed after all attempts")
                return False
                
            except Exception as e:
                if attempt < max_attempts - 1:
                    logger.warning(f"❌ Session validation error on attempt {attempt + 1}: {e}, retrying...")
                    sb.sleep(2)
                    continue
                else:
                    logger.error(f"❌ Session validation error after all attempts: {e}")
                    return False
        
        return False
    
    def _get_session_storage(self, sb: BaseCase) -> Dict:
        """Get session storage data"""
        try:
            return sb.execute_script("""
                var sessionData = {};
                for (var i = 0; i < sessionStorage.length; i++) {
                    var key = sessionStorage.key(i);
                    sessionData[key] = sessionStorage.getItem(key);
                }
                return sessionData;
            """)
        except:
            return {}
    
    def _get_local_storage(self, sb: BaseCase) -> Dict:
        """Get local storage data"""
        try:
            return sb.execute_script("""
                var localData = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    localData[key] = localStorage.getItem(key);
                }
                return localData;
            """)
        except:
            return {}
    
    def _restore_session_storage(self, sb: BaseCase, session_storage: Dict):
        """Restore session storage"""
        for key, value in session_storage.items():
            try:
                sb.execute_script(f"sessionStorage.setItem('{key}', '{value}');")
            except Exception as e:
                logger.debug(f"Failed to restore session storage {key}: {e}")
    
    def _restore_local_storage(self, sb: BaseCase, local_storage: Dict):
        """Restore local storage"""
        for key, value in local_storage.items():
            try:
                sb.execute_script(f"localStorage.setItem('{key}', '{value}');")
            except Exception as e:
                logger.debug(f"Failed to restore local storage {key}: {e}")
    
    def clear_session(self):
        """Clear saved session files"""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            if os.path.exists(self.cookies_file):
                os.remove(self.cookies_file)
            logger.info("🗑️ Session files cleared")
        except Exception as e:
            logger.error(f"❌ Failed to clear session: {e}")

    def is_session_expired(self) -> bool:
        """Check if the saved session is expired without loading it"""
        try:
            if not os.path.exists(self.session_file):
                return True
            
            # Load just the timestamp to check age
            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            session_time = datetime.fromisoformat(session_data['timestamp'])
            is_expired = datetime.now() - session_time > timedelta(hours=12)
            
            if is_expired:
                logger.info("🕐 Session has expired based on timestamp")
                
            return is_expired
            
        except Exception as e:
            logger.warning(f"⚠️ Could not check session expiry: {e}")
            return True  # Assume expired if we can't check

    def cleanup_expired_sessions(self):
        """Clean up expired session files automatically"""
        try:
            if self.is_session_expired():
                logger.info("🧹 Cleaning up expired session files")
                self.clear_session()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to cleanup expired sessions: {e}")
            return False