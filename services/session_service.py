import logging
import time
from typing import Optional
from seleniumbase import BaseCase
from session_manager import AmazonSessionManager

logger = logging.getLogger(__name__)

class SessionService:
    """Service for managing Amazon login sessions"""
    
    def __init__(self):
        self.session_manager = AmazonSessionManager()
    
    def establish_session(self, sb: BaseCase, correlation_id: str = None) -> bool:
        """Establish an Amazon session, using saved session if available"""
        log_extra = {'correlation_id': correlation_id} if correlation_id else {}
        logger.info("🔐 Establishing Amazon session", extra=log_extra)
        
        try:
            # Try to restore existing session first
            if self.session_manager.load_session(sb):
                logger.info("✅ Session restored from saved state", extra=log_extra)
                
                # Validate the restored session
                if self._validate(sb):
                    logger.info("✅ Restored session is valid", extra=log_extra)
                    return True
                else:
                    logger.warning("⚠️ Restored session is invalid, creating new session", extra=log_extra)
                    self.session_manager.clear_session()
            
            # Create new session if restoration failed or session is invalid
            logger.info("🔄 Creating new session from scratch", extra=log_extra)
            from create_session import create_amazon_session
            
            success = create_amazon_session(sb)
            if success:
                # Save the new session
                self.session_manager.save_session(sb)
                logger.info("✅ New session created and saved", extra=log_extra)
                return True
            else:
                logger.error("❌ Failed to create new session", extra=log_extra)
                return False
            
        except Exception as e:
            logger.error(f"❌ Session establishment failed: {e}", extra=log_extra)
            return False
    
    def _validate(self, sb: BaseCase) -> bool:
        """Confirm we're actually logged in by looking for a page element."""
        try:
            # Navigate to a reliable page
            sb.open("https://hiring.amazon.com/app#/jobSearch")
            sb.sleep(1)  # Quick validation
            
            # Check for multiple login indicators
            login_indicators = [
                'div:contains("Recommended jobs")',
                'button:contains("Go to my jobs")',
                'button:contains("Search all jobs")',
                'div:contains("Active jobs")',
                'div[data-test-component="StencilReactRow"]'
            ]
            
            # Check for logout indicators (if present, we're not logged in)
            logout_indicators = [
                'button:contains("Sign in")',
                'input[data-test-id="input-test-id-login"]',
                'div:contains("Sign in to your account")'
            ]
            
            # Check if we're logged out
            for indicator in logout_indicators:
                if sb.is_element_visible(indicator):
                    logger.debug(f"Found logout indicator: {indicator}")
                    return False
            
            # Check if we're logged in
            for indicator in login_indicators:
                if sb.is_element_visible(indicator):
                    logger.debug(f"Session valid - found: {indicator}")
                    return True
            
            # Fallback: check URL pattern
            current_url = sb.get_current_url()
            if "hiring.amazon.com" in current_url and ("jobSearch" in current_url or "dashboard" in current_url):
                logger.debug("Session appears valid based on URL")
                return True
                
            return False
            
        except Exception as e:
            logger.debug(f"Session validation failed: {e}")
            return False
    
    def refresh_session(self, sb: BaseCase, correlation_id: str = None) -> bool:
        """Force refresh the current session."""
        log_extra = {'correlation_id': correlation_id} if correlation_id else {}
        logger.info("🔄 Refreshing session", extra=log_extra)
        
        # Clear existing session and create new one
        self.session_manager.clear_session()
        return self.establish_session(sb, correlation_id)
    
    def clear_session(self) -> bool:
        """Clear the current session."""
        return self.session_manager.clear_session()
    
    def is_session_valid(self, sb: BaseCase) -> bool:
        """Check if current session is valid."""
        return self._validate(sb)
    
    def ensure_authenticated_session(self, sb: BaseCase = None) -> bool:
        """Ensure we have an authenticated session."""
        if sb:
            return self.establish_session(sb)
        else:
            # For compatibility when called without sb parameter
            return True