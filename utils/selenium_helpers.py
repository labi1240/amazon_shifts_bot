import time
import logging
from typing import List, Optional, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from seleniumbase import BaseCase

logger = logging.getLogger(__name__)

def click_with_retry(
    driver: BaseCase, 
    selectors: List[str], 
    max_retries: int = 3, 
    backoff_factor: float = 1.5,
    use_js_fallback: bool = True
) -> bool:
    """Click an element with multiple selector attempts and retry logic."""
    
    for attempt in range(max_retries):
        for selector in selectors:
            try:
                # Try normal click first
                element = driver.find_element(selector)
                if element and element.is_displayed() and element.is_enabled():
                    element.click()
                    logger.debug(f"Successfully clicked element with selector: {selector}")
                    return True
                    
            except (ElementClickInterceptedException, StaleElementReferenceException) as e:
                if use_js_fallback:
                    try:
                        # Fallback to JavaScript click
                        driver.execute_script("arguments[0].click();", element)
                        logger.debug(f"Successfully clicked element with JS fallback: {selector}")
                        return True
                    except Exception as js_e:
                        logger.debug(f"JS click also failed for {selector}: {js_e}")
                        
            except Exception as e:
                logger.debug(f"Click attempt {attempt + 1} failed for {selector}: {e}")
                
        # Wait before retry
        if attempt < max_retries - 1:
            time.sleep(backoff_factor ** attempt)
            
    logger.warning(f"Failed to click element after {max_retries} attempts with selectors: {selectors}")
    return False

def safe_get_text(driver: BaseCase, selectors: List[str], default: str = "") -> str:
    """Safely get text from an element using multiple selectors."""
    
    for selector in selectors:
        try:
            element = driver.find_element(selector)
            if element:
                text = element.text.strip()
                if text:
                    return text
                # Try getting text from value attribute if text is empty
                value = element.get_attribute('value')
                if value:
                    return value.strip()
        except Exception as e:
            logger.debug(f"Failed to get text with selector {selector}: {e}")
            continue
            
    return default

def wait_for_element(
    driver: BaseCase, 
    selectors: List[str], 
    timeout: int = 10,
    condition: str = "presence"
) -> Optional[Any]:
    """Wait for an element to meet a specific condition."""
    
    wait = WebDriverWait(driver, timeout)
    
    for selector in selectors:
        try:
            if condition == "presence":
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            elif condition == "visible":
                element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
            elif condition == "clickable":
                element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            else:
                raise ValueError(f"Unknown condition: {condition}")
                
            return element
            
        except TimeoutException:
            logger.debug(f"Timeout waiting for element with selector: {selector}")
            continue
        except Exception as e:
            logger.debug(f"Error waiting for element with selector {selector}: {e}")
            continue
            
    return None

def wait_for_page_load(driver, timeout: int = 15) -> bool:  # Restored from 5 to 15
    """Wait for page to load completely with Amazon-specific checks"""
    try:
        # Wait for document ready state with restored timeout
        driver.wait_for_ready_state_complete(timeout=10)  # Restored from 3 to 10
        
        # Amazon-specific loading indicators
        amazon_loading_selectors = [
            '.loading',
            '.spinner', 
            '[data-testid="loading"]',
            '.loading-spinner',
            '[aria-label*="loading"]',
            '[aria-label*="Loading"]'
        ]
        
        # Wait for any loading indicators to disappear with restored timeout
        for selector in amazon_loading_selectors:
            try:
                if driver.is_element_present(selector):
                    driver.wait_for_element_not_visible(selector, timeout=8)  # Restored from 2 to 8
            except Exception:
                continue  # Ignore if selector not found
        
        # Amazon-specific content checks
        amazon_content_selectors = [
            '[data-testid="job-card"]',
            '.job-card',
            'div:contains("Recommended jobs")',
            'div:contains("Total")',
            '[data-test-component="StencilReactRow"]'
        ]
        
        # Quick check for Amazon content to appear
        for selector in amazon_content_selectors:
            try:
                if driver.is_element_present(selector):
                    return True
            except Exception:
                continue
        
        logger.debug("Page loaded but no Amazon content detected")
        return True  # Don't fail if content not found
        
    except Exception as e:
        logger.warning(f"Page load wait failed: {e}")
        return False  # Return False but don't raise exception

def handle_consent_buttons(driver: BaseCase) -> bool:
    """Handle common consent/cookie buttons."""
    consent_selectors = [
        "button[data-action-type='ACCEPT']",
        "#sp-cc-accept",
        "button:contains('Accept')",
        "button:contains('Allow')",
        "button:contains('Continue')",
        ".consent-accept",
        "[data-testid='consent-accept']"
    ]
    
    for selector in consent_selectors:
        try:
            element = driver.find_element(selector)
            if element and element.is_displayed():
                element.click()
                logger.info(f"Clicked consent button: {selector}")
                time.sleep(1)  # Brief pause after consent
                return True
        except Exception:
            continue
            
    return False

def scroll_to_element(driver: BaseCase, selector: str) -> bool:
    """Scroll to an element to ensure it's visible."""
    try:
        element = driver.find_element(selector)
        if element:
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)  # Brief pause after scroll
            return True
    except Exception as e:
        logger.debug(f"Failed to scroll to element {selector}: {e}")
        
    return False

def get_element_attribute(
    driver: BaseCase, 
    selectors: List[str], 
    attribute: str, 
    default: Any = None
) -> Any:
    """Get an attribute value from an element using multiple selectors."""
    
    for selector in selectors:
        try:
            element = driver.find_element(selector)
            if element:
                value = element.get_attribute(attribute)
                if value is not None:
                    return value
        except Exception as e:
            logger.debug(f"Failed to get attribute {attribute} with selector {selector}: {e}")
            continue
            
    return default