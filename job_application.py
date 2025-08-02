# job_application.py
import logging
from seleniumbase import BaseCase
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ElementType(Enum):
    BUTTON = "button"
    INPUT = "input"
    LINK = "link"
    MODAL = "modal"
    FORM = "form"

@dataclass
class ElementSelector:
    primary: str
    fallbacks: List[str]
    element_type: ElementType
    description: str
    timeout: int = 10
    retry_count: int = 3

class JobApplicationHandler:
    """Encapsulates shift/role filter + job apply flow."""

    def __init__(self, driver: BaseCase, pause: float = 1.0, location: str = "90210"):
        self.driver = driver
        self.pause = pause
        self.location = location
        self.setup_selectors()

    def setup_selectors(self):
        """Setup enhanced selectors for robust element interaction"""
        self.selectors = {
            'consent_buttons': ElementSelector(
                primary='button:contains("Accept")',
                fallbacks=[
                    'button:contains("Accept All")',
                    'button:contains("Allow")',
                    'button[data-test-id*="consent"]',
                    'button[aria-label*="accept"]',
                    '#sp-cc-accept',
                    '.consent-accept'
                ],
                element_type=ElementType.BUTTON,
                description="Consent/Cookie Accept Button"
            )
        }

    def safe_click(self, selector_config: ElementSelector, **kwargs) -> bool:
        """Enhanced click with multiple selector attempts and error handling"""
        logger.info(f"🎯 Attempting to click: {selector_config.description}")
        all_selectors = [selector_config.primary] + selector_config.fallbacks
        
        for attempt in range(selector_config.retry_count):
            logger.debug(f"Attempt {attempt + 1}/{selector_config.retry_count}")
            
            for i, selector in enumerate(all_selectors):
                try:
                    logger.debug(f"Trying selector {i+1}/{len(all_selectors)}: {selector}")
                    
                    if self.driver.is_element_visible(selector, timeout=2):
                        logger.info(f"✅ Found {selector_config.description} with selector: {selector}")
                        
                        # Wait for element to be clickable
                        self.driver.wait_for_element_clickable(selector, timeout=selector_config.timeout)
                        
                        # Scroll element into view
                        self.driver.scroll_to_element(selector)
                        self.driver.sleep(0.5)
                        
                        # Try normal click first
                        try:
                            self.driver.click(selector)
                            logger.info(f"🎉 Successfully clicked {selector_config.description}")
                            return True
                        except Exception as click_error:
                            logger.warning(f"⚠️ Normal click failed, trying JS click: {click_error}")
                            # Fallback to JavaScript click
                            self.driver.js_click(selector)
                            logger.info(f"🎉 Successfully JS clicked {selector_config.description}")
                            return True
                            
                except Exception as e:
                    logger.debug(f"❌ Selector {selector} failed: {e}")
                    continue
            
            if attempt < selector_config.retry_count - 1:
                logger.info(f"🔄 Retrying {selector_config.description} click (attempt {attempt + 2})")
                self.driver.sleep(2)
        
        logger.error(f"💥 Failed to click {selector_config.description} after all attempts")
        return False

    def handle_consent_buttons(self) -> bool:
        """Enhanced consent button handling with comprehensive selectors"""
        logger.info("🍪 Checking for consent/cookie buttons...")
        
        # Check multiple times as consent buttons might appear with delay
        for check_attempt in range(3):
            logger.debug(f"Consent check attempt {check_attempt + 1}/3")
            
            if self.safe_click(self.selectors['consent_buttons']):
                logger.info("✅ Consent button handled successfully")
                self.driver.sleep(2)  # Wait for any animations
                return True
            
            if check_attempt < 2:
                logger.debug("No consent buttons found, waiting and retrying...")
                self.driver.sleep(3)
        
        logger.info("ℹ️ No consent buttons found or needed")
        return True

    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """Wait for page to fully load with multiple indicators"""
        try:
            # Wait for document ready state
            self.driver.wait_for_ready_state_complete(timeout=timeout)
            
            # Wait for any loading indicators to disappear
            loading_selectors = [
                '.loading',
                '.spinner',
                '[data-test-id*="loading"]',
                '.loader',
                '[aria-label*="loading"]'
            ]
            
            for selector in loading_selectors:
                if self.driver.is_element_visible(selector):
                    self.driver.wait_for_element_not_visible(selector, timeout=timeout)
            
            logger.info("Page loaded successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Page load check failed: {e}")
            return False

    def apply_job_filters(self) -> bool:
        """Apply job filters with enhanced selectors"""
        logger.info("Applying job filters...")
        
        try:
            # Navigate to job search section
            job_nav_selectors = [
                "div.hvh-careers-emotion-14hcg2z",
                '[data-test-id*="job"]',
                'button:contains("Jobs")',
                'a:contains("Jobs")'
            ]
            
            for selector in job_nav_selectors:
                if self.driver.is_element_visible(selector, timeout=5):
                    self.driver.click(selector)
                    self.driver.sleep(2)
                    break
            
            # Apply location filter
            location_selectors = [
                'button:contains("Within 30 miles")',
                '[data-test-id*="location"]',
                'button[aria-label*="location"]'
            ]
            
            for selector in location_selectors:
                if self.driver.is_element_visible(selector, timeout=3):
                    self.driver.click(selector)
                    self.driver.sleep(1)
                    break
            
            # Enter location
            location_input_selectors = [
                "input#zipcode-nav-filter",
                'input[placeholder*="location"]',
                'input[name*="location"]',
                'input[aria-label*="location"]'
            ]
            
            for selector in location_input_selectors:
                if self.driver.is_element_visible(selector):
                    self.driver.type(selector, self.location)
                    self.driver.sleep(2)
                    
                    # Select first suggestion
                    suggestion_selectors = [
                        'div[id="0"]',
                        '.suggestion:first-child',
                        '[data-test-id*="suggestion"]:first-child'
                    ]
                    
                    for suggestion in suggestion_selectors:
                        if self.driver.is_element_visible(suggestion):
                            self.driver.click(suggestion)
                            self.driver.sleep(1)
                            break
                    break
            
            # Apply shift and role filters
            self.apply_shift_filters()
            self.apply_role_filters()
            
            return True
            
        except Exception as e:
            logger.error(f"Filter application failed: {e}")
            return False

    def apply_shift_filters(self):
        """Apply shift filters with error handling."""
        shift_filters = [
            ('EarlyMorning', 'Early Morning'),
            ('Daytime',     'Daytime'),
            ('Evening',     'Evening'),
            ('Weekend',     'Weekend'),
            ('Weekday',     'Weekday'),
            ('Night',       'Night'),
        ]
        for shift_id, shift_name in shift_filters:
            selectors = [
                f'button[data-test-id="filter-schedule-shift-button-{shift_id}"]',
                f'button:contains("{shift_name}")',
                f'[data-test-id*="{shift_id.lower()}"]',
            ]
            for sel in selectors:
                if self.driver.is_element_visible(sel, timeout=2):
                    try:
                        self.driver.click(sel)
                        logger.info(f"Applied {shift_name} filter")
                        self.driver.sleep(self.pause)
                        break
                    except Exception as e:
                        logger.debug(f"Click failed for {shift_name} ({sel}): {e}")
                        continue

    def apply_role_filters(self):
        """Apply role filters with error handling."""
        roles = [
            'Amazon Fulfillment Center Warehouse Associate',
            'Amazon Sortation Center Warehouse Associate',
            'Amazon Delivery Station Warehouse Associate',
            'Amazon Distribution Center Associate',
            'Amazon Grocery Warehouse Associate',
        ]
        for role in roles:
            selectors = [
                f'button[data-test-id="filter-role-button-{role}"]',
                f'button:contains("{role}")',
                f'[data-test-id*="{role.lower().replace(" ", "-")}"]',
            ]
            for sel in selectors:
                if self.driver.is_element_visible(sel, timeout=2):
                    try:
                        self.driver.click(sel)
                        logger.info(f"Applied {role} filter")
                        self.driver.sleep(self.pause)
                        break
                    except Exception as e:
                        logger.debug(f"Click failed for {role} ({sel}): {e}")
                        continue

    def select_and_apply_job(self) -> bool:
        """Select first available job and click Apply."""
        # 1) Open results
        for sel in ("button#filterPanelShowFiltersButton",
                    'button:contains("Show")',
                    '[data-test-id*="show-filters"]'):
            if self.driver.is_element_visible(sel, timeout=3):
                self.driver.click(sel)
                self.driver.sleep(self.pause * 2)
                break

        # 2) Pick first job card
        job_card_sel = next((
            sel for sel in (
                'div[data-test-id="JobCard"]',
                '.job-card',
                '[data-test-id*="job"][data-test-id*="card"]'
            ) if self.driver.is_element_visible(sel, timeout=5)
        ), None)
        if job_card_sel:
            self.driver.click(job_card_sel)
            logger.info("Selected first job card")
            self.driver.sleep(self.pause * 3)
        else:
            logger.warning("No job card found")
            return False

        # 3) Click Apply
        for sel in (
            'button[data-test-id="jobDetailApplyButtonDesktop"]',
            'button:contains("Apply")',
            '[data-test-id*="apply"]',
            '.apply-button'
        ):
            if self.driver.is_element_visible(sel, timeout=5):
                self.driver.click(sel)
                logger.info("Clicked apply button")
                self.driver.sleep(self.pause * 4)
                return True

        logger.warning("No apply button found")
        return False
