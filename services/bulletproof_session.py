import logging
import time
from typing import Optional
from seleniumbase import BaseCase

logger = logging.getLogger(__name__)

class BulletproofSessionService:
    """Ultra-robust session service with comprehensive error handling"""
    
    def __init__(self):
        self.max_retries = 5
        self.retry_delay_base = 2
        
    def validate_session_bulletproof(self, sb: BaseCase) -> bool:
        """Bulletproof session validation with comprehensive retry logic"""
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🔍 Bulletproof session validation (attempt {attempt + 1}/{self.max_retries})")
                
                # Step 1: Navigate with retry logic
                navigation_success = self._navigate_with_retries(sb, attempt)
                if not navigation_success:
                    if attempt < self.max_retries - 1:
                        self._progressive_delay(attempt)
                        continue
                    return False
                
                # Step 2: Check for logout indicators first
                if self._check_logout_indicators(sb):
                    logger.warning(f"⚠️ Found logout indicators on attempt {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        self._progressive_delay(attempt)
                        continue
                    return False
                
                # Step 3: Check for login indicators  
                if self._check_login_indicators(sb):
                    logger.info(f"✅ Session validated successfully on attempt {attempt + 1}")
                    return True
                
                # Step 4: URL-based validation as fallback
                if self._validate_by_url(sb):
                    logger.info(f"✅ Session validated by URL on attempt {attempt + 1}")
                    return True
                
                logger.warning(f"⚠️ Session validation inconclusive on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    self._progressive_delay(attempt)
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Session validation error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    self._progressive_delay(attempt)
                    continue
        
        logger.error(f"❌ Session validation failed after {self.max_retries} attempts")
        return False
    
    def _navigate_with_retries(self, sb: BaseCase, base_attempt: int) -> bool:
        """Navigate with multiple retry strategies"""
        urls_to_try = [
            "https://hiring.amazon.com/app#/jobSearch",
            "https://hiring.amazon.com/app#/dashboard", 
            "https://hiring.amazon.com/"
        ]
        
        for url_idx, url in enumerate(urls_to_try):
            for nav_attempt in range(3):  # 3 attempts per URL
                try:
                    logger.debug(f"🌐 Navigating to {url} (attempt {nav_attempt + 1})")
                    sb.open(url)
                    time.sleep(min(1 + nav_attempt * 0.5, 3))  # Progressive wait
                    return True
                except Exception as e:
                    logger.warning(f"⚠️ Navigation to {url} failed (attempt {nav_attempt + 1}): {e}")
                    if nav_attempt < 2:  # Not last attempt for this URL
                        time.sleep(2)
                        continue
        
        return False
    
    def _check_logout_indicators(self, sb: BaseCase) -> bool:
        """Check for logout indicators with multiple strategies"""
        logout_indicators = [
            ('css', 'button:contains("Sign in")'),
            ('css', 'input[data-test-id="input-test-id-login"]'),
            ('css', 'div:contains("Sign in to your account")'),
            ('xpath', '//button[contains(text(), "Sign in")]'),
            ('xpath', '//input[@placeholder="Email"]'),
            ('css', '[data-test-id="input-test-id-login"]')
        ]
        
        for selector_type, selector in logout_indicators:
            try:
                if selector_type == 'css':
                    if sb.is_element_visible(selector):
                        logger.debug(f"🚪 Found logout indicator (CSS): {selector}")
                        return True
                elif selector_type == 'xpath':
                    if sb.is_element_visible(selector):
                        logger.debug(f"🚪 Found logout indicator (XPath): {selector}")
                        return True
            except Exception:
                continue  # Ignore individual selector failures
        
        return False
    
    def _check_login_indicators(self, sb: BaseCase) -> bool:
        """Check for login indicators with multiple strategies"""
        login_indicators = [
            ('css', 'div:contains("Recommended jobs")'),
            ('css', 'button:contains("Go to my jobs")'),
            ('css', 'button:contains("Search all jobs")'),
            ('css', 'div:contains("Active jobs")'),
            ('css', 'div[data-test-component="StencilReactRow"]'),
            ('xpath', '//div[contains(text(), "job")]'),
            ('css', '[data-test-id="JobCard"]'),
            ('css', '.jobCardItem'),
            ('css', '[data-test-component="StencilReactCard"]')
        ]
        
        for selector_type, selector in login_indicators:
            try:
                if selector_type == 'css':
                    if sb.is_element_visible(selector):
                        logger.debug(f"✅ Found login indicator (CSS): {selector}")
                        return True
                elif selector_type == 'xpath':
                    if sb.is_element_visible(selector):
                        logger.debug(f"✅ Found login indicator (XPath): {selector}")
                        return True
            except Exception:
                continue  # Ignore individual selector failures
        
        return False
    
    def _validate_by_url(self, sb: BaseCase) -> bool:
        """Validate session based on URL patterns"""
        try:
            current_url = sb.get_current_url()
            logger.debug(f"🔗 Current URL: {current_url}")
            
            valid_url_patterns = [
                "hiring.amazon.com/app#/jobSearch",
                "hiring.amazon.com/app#/dashboard",
                "hiring.amazon.com/application"
            ]
            
            for pattern in valid_url_patterns:
                if pattern in current_url:
                    logger.debug(f"✅ URL pattern match: {pattern}")
                    return True
            
            # Check if we're not on a login page
            login_url_patterns = [
                "/signin",
                "/login", 
                "/auth",
                "input-test-id-login"
            ]
            
            for pattern in login_url_patterns:
                if pattern in current_url:
                    logger.debug(f"❌ Found login URL pattern: {pattern}")
                    return False
            
            # If we're on Amazon hiring domain but not on login, assume valid
            if "hiring.amazon.com" in current_url:
                logger.debug("✅ On Amazon hiring domain, assuming valid")
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ URL validation failed: {e}")
        
        return False
    
    def _progressive_delay(self, attempt: int):
        """Progressive delay with exponential backoff"""
        delay = min(self.retry_delay_base ** attempt, 30)  # Max 30 seconds
        logger.info(f"⏳ Progressive delay: {delay}s before next attempt")
        time.sleep(delay)
    
    def send_test_notification(self, notifier) -> bool:
        """Send test notification to verify Discord connectivity"""
        try:
            if notifier:
                test_message = "🔧 **Bulletproof System Test**\n✅ All systems operational!\n🚀 Ready for continuous monitoring!"
                return notifier.send(test_message, urgent=False)
            return False
        except Exception as e:
            logger.error(f"❌ Test notification failed: {e}")
            return False