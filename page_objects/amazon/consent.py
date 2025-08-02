import logging
from seleniumbase import BaseCase
from typing import List

logger = logging.getLogger(__name__)

class AmazonConsentPage:
    """Handles Amazon consent and privacy popups."""
    
    CONSENT_SELECTORS = [
        'button[data-test-id="consentBtn"]',
        'button[data-test-component="StencilReactButton"] div:contains("I consent")',
        'button:contains("Accept")',
        'button:contains("I Agree")',
        'button:contains("Continue")',
        '[data-testid*="consent"][data-testid*="accept"]',
        '.consent-button',
        '#consent-accept'
    ]
    
    def accept_if_present(self, driver: BaseCase, timeout: int = 5) -> bool:
        """Accept consent popup if present."""
        logger.debug("Checking for consent popups")
        
        try:
            for selector in self.CONSENT_SELECTORS:
                # Fixed: Use is_element_visible instead of is_element_present with timeout
                if driver.is_element_visible(selector):
                    logger.info(f"Found consent popup, accepting with selector: {selector}")
                    driver.click(selector)
                    driver.sleep(1)
                    return True
            
            logger.debug("No consent popups found")
            return False
            
        except Exception as e:
            logger.warning(f"Error handling consent popup: {e}")
            return False
    
    def dismiss_privacy_notices(self, driver: BaseCase) -> bool:
        """Dismiss any privacy notices or cookie banners."""
        privacy_selectors = [
            'button:contains("Accept Cookies")',
            'button:contains("Accept All")',
            '.privacy-notice button',
            '[data-testid*="privacy"] button',
            '#privacy-accept'
        ]
        
        dismissed = False
        for selector in privacy_selectors:
            try:
                # Fixed: Use is_element_visible instead of is_element_present with timeout
                if driver.is_element_visible(selector):
                    driver.click(selector)
                    driver.sleep(0.5)
                    dismissed = True
                    logger.debug(f"Dismissed privacy notice: {selector}")
            except Exception:
                continue
                
        return dismissed