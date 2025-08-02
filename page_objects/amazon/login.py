import logging
import time
from seleniumbase import BaseCase
from typing import Optional

logger = logging.getLogger(__name__)

class AmazonLoginPage:
    """Handles Amazon login flow interactions."""
    
    EMAIL_SELECTORS = [
        'input[data-test-id="input-test-id-login"]',
        'input[name="email"]',
        'input[type="email"]',
        '#email',
        '.email-input'
    ]
    
    PASSWORD_SELECTORS = [
        'input[type="password"]',
        'input[data-test-id="password"]',
        '#password',
        '.password-input'
    ]
    
    CONTINUE_SELECTORS = [
        'button[data-test-id="button-continue"]',
        'button:contains("Continue")',
        'button:contains("Sign In")',
        'button[type="submit"]',
        '.continue-button'
    ]
    
    def enter_credentials(self, driver: BaseCase, email: str, password: str, 
                         correlation_id: str = None) -> bool:
        """Enter login credentials with robust element detection."""
        log_extra = {'correlation_id': correlation_id} if correlation_id else {}
        logger.info("Entering login credentials", extra=log_extra)
        
        try:
            # Enter email
            if not self._enter_email(driver, email):
                logger.error("Failed to enter email", extra=log_extra)
                return False
            
            # Click continue after email
            if not self._click_continue(driver, "after email"):
                logger.error("Failed to click continue after email", extra=log_extra)
                return False
            
            # Wait for password field
            time.sleep(2)
            
            # Enter password
            if not self._enter_password(driver, password):
                logger.error("Failed to enter password", extra=log_extra)
                return False
            
            # Click final continue
            if not self._click_continue(driver, "after password"):
                logger.error("Failed to click continue after password", extra=log_extra)
                return False
            
            # Wait for login to process
            time.sleep(3)
            logger.info("Login credentials entered successfully", extra=log_extra)
            return True
            
        except Exception as e:
            logger.error(f"Exception during credential entry: {e}", extra=log_extra)
            return False
    
    def _enter_email(self, driver: BaseCase, email: str) -> bool:
        """Enter email with multiple selector fallbacks."""
        for selector in self.EMAIL_SELECTORS:
            try:
                if driver.is_element_present(selector, timeout=5):
                    driver.clear(selector)
                    driver.type(selector, email)
                    logger.debug(f"Email entered using selector: {selector}")
                    return True
            except Exception:
                continue
        return False
    
    def _enter_password(self, driver: BaseCase, password: str) -> bool:
        """Enter password with multiple selector fallbacks."""
        for selector in self.PASSWORD_SELECTORS:
            try:
                if driver.is_element_present(selector, timeout=5):
                    driver.clear(selector)
                    driver.type(selector, password)
                    logger.debug(f"Password entered using selector: {selector}")
                    return True
            except Exception:
                continue
        return False
    
    def _click_continue(self, driver: BaseCase, context: str) -> bool:
        """Click continue button with multiple selector fallbacks."""
        for selector in self.CONTINUE_SELECTORS:
            try:
                if driver.is_element_present(selector, timeout=5):
                    driver.click(selector)
                    logger.debug(f"Continue clicked {context} using: {selector}")
                    return True
            except Exception:
                continue
        return False
    
    def handle_two_factor(self, driver: BaseCase, code: str = None) -> bool:
        """Handle two-factor authentication if required."""
        two_factor_selectors = [
            'input[data-test-id="mfa-input"]',
            'input[name="code"]',
            'input[placeholder*="code"]',
            '.mfa-input'
        ]
        
        # Check if 2FA is required
        for selector in two_factor_selectors:
            if driver.is_element_present(selector, timeout=3):
                logger.info("Two-factor authentication required")
                if code:
                    driver.type(selector, code)
                    self._click_continue(driver, "after 2FA")
                    return True
                else:
                    logger.warning("2FA required but no code provided")
                    return False
        
        return True  # No 2FA required