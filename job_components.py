# job_components.py
from seleniumbase import BaseCase
import time
import logging
import json
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class EnhancedShiftFilter:
    """
    Dispatch-based filter application with robust panel-opening and slider logic.
    Clean mapping of short keys to filter methods.
    """
    
    # Dispatch mapping: key -> method name
    _FILTER_DISPATCH = {
        'hours': '_set_work_hours_range',
        'schedule': '_apply_schedule_filters', 
        'roles': '_apply_job_role_filters',
        'employment': '_set_length_of_employment',
        'language': '_set_language_requirement',
        'start_date': '_set_start_date',
        'cities': '_apply_city_filter',  # Added city filtering
    }

    def __init__(self, driver: BaseCase, pause: float = 0.5):
        self.driver = driver
        self.pause = pause
        self.current_city_index = 0
        
        # Updated selectors based on current Amazon jobs page structure (from filtersontop.xml & panel.html)
        self.selectors = {
            # Main filters button - targets the real "Add filter" button on search page
            'filters_button': '[data-test-id="openFiltersButton"]',
            'filters_button_alt': 'button:contains("Add filter")',
            'filters_button_alt2': '.topBar:contains("Add filter")',
            'filters_button_alt3': 'button:contains("View all filters")',
            
            # Actual filters panel (right side panel from screenshot)
            'filters_panel': '[data-test-component="StencilFlyoutBody"]',
            'filters_panel_alt': '.jobFilterPanelContent',
            'filters_panel_alt2': '[data-test-id="StencilReactPageContainer"]',
            'filters_panel_alt3': '.guidedSearchContainer',  # Guided search modal panel
            'filters_panel_alt4': '.locationInputContainer',  # Location input container
            
            # Job card
            'job_card': '[data-test-id="JobCard"]',
            
            # Guided search modal close buttons (if guided search appears)
            'guided_search_close': '.guidedSearchCloseButton',
            'guided_search_skip': 'button:contains("Skip")',
            'guided_search_x': 'svg[data-test-component="StencilIconCrossSmall"]',
            
            # City/Location input - Based on actual Amazon UI structure from viewfilters.xml
            'city_input': 'input[id="zipcode-nav-guide"]',  # Main guided search input
            'city_input_alt': '[data-test-id="zipcodeInputField"] input',  # Alternative search field wrapper
            'city_input_alt2': 'input[placeholder="Enter zipcode or city"]',  # By placeholder text
            'city_input_alt3': '[data-test-component="StencilSearchFieldInput"]',  # By component type
            'city_input_alt4': 'input[id="zipcode-nav-filter"]',  # Legacy filter panel input (if exists)
            'city_input_alt5': 'input[aria-autocomplete="list"]',  # Autocomplete input field
            'city_input_alt6': 'input[role="combobox"]',  # Combobox role input
            'city_input_alt7': '.hvh-careers-emotion-1negirf',  # Specific class from actual UI
            'city_input_alt8': 'input[placeholder*="city"]',  # Any input with "city" in placeholder
            'city_input_alt9': 'input[placeholder*="zip"]',  # Any input with "zip" in placeholder
            'city_input_alt10': '[data-test-component="StencilFlyoutBody"] input[type="text"]',  # Flyout panel input
            'city_input_alt11': '.jobFilterPanelContent input[type="text"]',  # Filter panel content input
            'city_input_alt12': '[data-test-id="StencilReactPageContainer"] input[type="text"]',  # Page container input
            'city_input_alt13': '[data-test-id="location-filter-input"]',  # Specific location filter
            
            # Show results/Apply button (from panel bottom)
            'show_results_button': 'button:contains("Show")',
            'show_results_button_alt': '[data-test-id*="show"]',
            
            # Clear filters
            'clear_filters': 'button:contains("Clear")',
            'clear_filters_alt': '[data-test-id*="clear"]',
        }

    def apply_filters(self, which: List[str], cfg: Dict[str, Any]) -> bool:
        """
        Dispatch-based filter application with fallback for city search.
        which: subset of keys you actually want to run today.
        cfg: {'hours': (min,max), 'schedule': [...], 'roles': [...], ...}
        """
        logger.info(f"Applying filters: {which}")
        
        # First, check if we're stuck on the guided search modal and handle it
        cities = cfg.get('cities', [])
        if not self._handle_guided_search_modal():
            logger.error("Failed to handle guided search modal")
            return False
        
        # Special handling for cities - try main search field if filters panel fails
        if 'cities' in which and not self._ensure_filters_panel_open():
            logger.warning("Filters panel failed to open, trying fallback city search")
            if cities:
                return self._apply_city_search_fallback(cities)
            else:
                logger.error("Failed to open filters panel and no cities to search")
                return False
        
        # Normal filter processing
        if not self._ensure_filters_panel_open():
            logger.error("Failed to open filters panel")
            return False

        success_count = 0
        for key in which:
            if key not in self._FILTER_DISPATCH:
                logger.warning(f"Unknown filter '{key}'")
                continue

            method_name = self._FILTER_DISPATCH[key]
            method = getattr(self, method_name)
            val = cfg.get(key)
            
            if val is None:
                logger.warning(f"No value for {key}, skipping")
                continue

            try:
                # Handle different parameter types
                if isinstance(val, (list, tuple)):
                    method(val)
                else:
                    method(val)
                
                logger.info(f"✅ Applied {key} filter")
                success_count += 1
                time.sleep(self.pause)
                
            except Exception as e:
                logger.error(f"Failed to apply {key} filter: {e}")

        logger.info(f"Successfully applied {success_count}/{len(which)} filters")
        return success_count > 0

    def _handle_guided_search_modal(self) -> bool:
        """
        Handle the guided search modal that Amazon shows.
        This modal appears instead of the regular job search page and needs to be 
        either completed or dismissed to access regular filters.
        """
        logger.info("🔍 Checking for guided search modal...")
        
        # Check if guided search modal is present
        guided_search_selectors = [
            '.guidedSearchContainer',
            '[data-test-component="StencilReactCol"].guidedSearchContainer',
            '.locationInputContainer'
        ]
        
        modal_present = False
        for selector in guided_search_selectors:
            try:
                if self.driver.is_element_visible(selector):
                    modal_present = True
                    logger.info(f"✅ Guided search modal detected: {selector}")
                    break
            except Exception:
                continue
        
        if not modal_present:
            logger.info("No guided search modal found - proceeding normally")
            return True
        
        # Strategy 1: Try to skip the guided search
        skip_selectors = [
            'button:contains("Skip")',
            '.guidedSearchForwardButton',
            '[data-test-component="StencilReactButton"]:contains("Skip")'
        ]
        
        for selector in skip_selectors:
            try:
                if self.driver.is_element_visible(selector):
                    logger.info(f"🚀 Clicking skip button: {selector}")
                    self.driver.click(selector)
                    time.sleep(2)
                    
                    # Check if we successfully moved past the modal
                    if not any(self.driver.is_element_visible(s) for s in guided_search_selectors):
                        logger.info("✅ Successfully skipped guided search modal")
                        return True
                    break
            except Exception as e:
                logger.debug(f"Skip selector {selector} failed: {e}")
                continue
        
        # Strategy 2: Try to close the guided search modal
        close_selectors = [
            '.guidedSearchCloseButton', 
            '[data-test-component="StencilReactRow"].guidedSearchCloseButton',
            'svg[data-test-component="StencilIconCrossSmall"]'
        ]
        
        for selector in close_selectors:
            try:
                if self.driver.is_element_visible(selector):
                    logger.info(f"❌ Clicking close button: {selector}")
                    self.driver.click(selector)
                    time.sleep(2)
                    
                    # Check if we successfully closed the modal
                    if not any(self.driver.is_element_visible(s) for s in guided_search_selectors):
                        logger.info("✅ Successfully closed guided search modal")
                        return True
                    break
            except Exception as e:
                logger.debug(f"Close selector {selector} failed: {e}")
                continue
        
        # Strategy 3: Complete the guided search with first city
        logger.info("⚡ Attempting to complete guided search with location input...")
        return self._complete_guided_search_with_city(["Seattle, WA"])  # Use default city
        
    def _complete_guided_search_with_city(self, cities: List[str]) -> bool:
        """Complete the guided search modal by entering a city and proceeding."""
        if not cities:
            return False
            
        city = cities[0]
        logger.info(f"📍 Completing guided search with city: {city}")
        
        # Find and fill the location input in guided search
        location_input_selectors = [
            'input[id="zipcode-nav-guide"]',
            '[data-test-component="StencilSearchFieldInput"]',
            'input[placeholder="Enter zipcode or city"]',
            '.locationInputContainer input'
        ]
        
        for selector in location_input_selectors:
            try:
                if self.driver.is_element_visible(selector):
                    logger.info(f"📝 Found location input: {selector}")
                    
                    # Clear and enter city
                    element = self.driver.find_element(selector)
                    element.clear()
                    time.sleep(0.5)
                    element.send_keys(city)
                    time.sleep(1)
                    
                    # Look for and click "Next" or "Continue" button
                    continue_selectors = [
                        'button:contains("Next")',
                        'button:contains("Continue")', 
                        '.guidedSearchForwardButton',
                        'button:contains("Search")'
                    ]
                    
                    for continue_sel in continue_selectors:
                        try:
                            if self.driver.is_element_visible(continue_sel):
                                logger.info(f"➡️ Clicking continue button: {continue_sel}")
                                self.driver.click(continue_sel)
                                time.sleep(3)
                                return True
                        except Exception:
                            continue
                    
                    # If no continue button, try pressing Enter
                    try:
                        element.send_keys("\n")
                        time.sleep(3)
                        return True
                    except Exception:
                        pass
                        
            except Exception as e:
                logger.debug(f"Location input selector {selector} failed: {e}")
                continue
        
        logger.error("❌ Could not complete guided search - no location input found")
        return False

    def _apply_city_search_fallback(self, cities: List[str]) -> bool:
        """
        Fallback method to search for cities using the main search input field
        when the filters panel cannot be opened.
        """
        if not cities:
            logger.warning("No cities provided for fallback search")
            return False
            
        current_city = cities[0]  # Use first city
        logger.info(f"🔍 Fallback: Searching for city using main search field: {current_city}")
        
        try:
            # Try to find the main search input field - guided search modal (left side of screenshot)
            main_search_selectors = [
                'input[id="zipcode-nav-guide"]',  # Guided search modal input
                'input[placeholder="Enter zipcode or city"]',
                '[data-test-component="StencilSearchFieldInput"]',
                'input[aria-autocomplete="list"]',
                '.hvh-careers-emotion-1negirf',
                '[data-test-id="zipcodeInputField"] input',
                'input[role="combobox"]'
            ]
            
            search_input = None
            for selector in main_search_selectors:
                try:
                    if self.driver.is_element_visible(selector):
                        search_input = self.driver.find_element(selector)
                        logger.info(f"✅ Found main search input using: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Main search selector {selector} failed: {e}")
                    continue
            
            if not search_input:
                logger.error("❌ Could not find main search input field with any selector")
                return False
            
            # Clear and enter the city
            search_input.clear()
            time.sleep(0.5)
            search_input.send_keys(current_city)
            time.sleep(1)
            
            # Press Enter to search
            search_input.send_keys("\n")
            logger.info(f"✅ Fallback city search completed: {current_city}")
            
            # Wait for results to load
            time.sleep(1.5)  # Reduced from 3 to 1.5 seconds
            return True
            
        except Exception as e:
            logger.error(f"❌ Fallback city search failed for {current_city}: {e}")
            return False

    def _ensure_filters_panel_open(self) -> bool:
        """Enhanced filter panel opening with multiple strategies."""
        try:
            # Strategy 1: Check if already open
            if self._is_filters_panel_open():
                logger.info("Filters panel already open")
                return True

            # Strategy 2: Try all filter button selectors
            filter_button_selectors = [
                self.selectors['filters_button'],
                self.selectors['filters_button_alt'],
                self.selectors['filters_button_alt2'],
                self.selectors['filters_button_alt3']
            ]
            
            for selector in filter_button_selectors:
                if self._try_open_with_selector(selector):
                    return True

            logger.error("Could not open filters panel with any selector")
            return False

        except Exception as e:
            logger.error(f"Error opening filters panel: {e}")
            return False
    
    def _try_open_with_selector(self, selector: str) -> bool:
        """Try to open filters panel with a specific selector."""
        try:
            if self.driver.is_element_visible(selector):
                logger.info(f"Attempting to open filters with: {selector}")
                self.driver.click(selector)
                time.sleep(2)
                
                if self._is_filters_panel_open():
                    logger.info(f"✅ Successfully opened filters with: {selector}")
                    return True
                else:
                    logger.debug(f"Click successful but panel not opened: {selector}")
                    
        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
        
        return False
    
    def _is_filters_panel_open(self) -> bool:
        """Check if filters panel is currently open."""
        try:
            # Check multiple possible panel selectors including guided search modal
            panel_selectors = [
                self.selectors['filters_panel'],
                self.selectors['filters_panel_alt'],
                self.selectors['filters_panel_alt2'],
                self.selectors['filters_panel_alt3'],  # Guided search container
                self.selectors['filters_panel_alt4']   # Location input container
            ]
            
            logger.debug("🔍 Checking if filters panel is open...")
            for selector in panel_selectors:
                try:
                    is_visible = self.driver.is_element_visible(selector)
                    logger.debug(f"   Panel selector '{selector}': {'✅ VISIBLE' if is_visible else '❌ not visible'}")
                    if is_visible:
                        logger.info(f"✅ Filters panel detected as open: {selector}")
                        return True
                except Exception as e:
                    logger.debug(f"   Panel selector '{selector}': ❌ ERROR - {e}")
                    continue
            
            logger.info("❌ No filters panel detected as open")
            return False
        except Exception as e:
            logger.error(f"Error checking filters panel state: {e}")
            return False

    def _find_visible_element(self, selectors: List[str]) -> Optional[str]:
        """Find the first visible element from a list of selectors."""
        for selector in selectors:
            try:
                if self.driver.is_element_visible(selector):
                    logger.info(f"Found visible element with selector: {selector}")
                    return selector
            except Exception:
                continue
        return None

    def _apply_schedule_filters(self, preferences: List[str]) -> None:
        """Apply schedule preference filters"""
        schedule_mapping = {
            'early_morning': 'schedule_early_morning',
            'day_time': 'schedule_day_time', 
            'evening': 'schedule_evening',
            'night': 'schedule_night',
            'weekday': 'schedule_weekday',
            'weekend': 'schedule_weekend'
        }
        
        for pref in preferences:
            selector_key = schedule_mapping.get(pref)
            if selector_key and selector_key in self.selectors:
                try:
                    if self.driver.is_element_visible(self.selectors[selector_key]):
                        self.driver.click(self.selectors[selector_key])
                        logger.info(f"✅ Applied schedule filter: {pref}")
                        time.sleep(0.5)
                    else:
                        logger.warning(f"Schedule filter not found: {pref}")
                except Exception as e:
                    logger.error(f"Error applying schedule filter {pref}: {e}")
            else:
                logger.warning(f"Unknown schedule preference: {pref}")

    def _apply_job_role_filters(self, job_roles: List[str]) -> None:
        """Apply job role filters"""
        role_mapping = {
            'fulfillment_center': 'role_fulfillment_center',
            'sortation_center': 'role_sortation_center',
            'delivery_station': 'role_delivery_station',
            'distribution_center': 'role_distribution_center',
            'grocery': 'role_grocery',
            'air_hub': 'role_air_hub',
            'customer_service': 'role_customer_service'
        }
        
        for role in job_roles:
            if role == 'all':
                # Click all available role buttons
                try:
                    role_buttons = self.driver.find_elements(self.selectors['role_buttons'])
                    for btn in role_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            time.sleep(0.3)
                    logger.info(f"✅ Selected all available job roles ({len(role_buttons)} roles)")
                except Exception as e:
                    logger.error(f"Error selecting all roles: {e}")
            else:
                selector_key = role_mapping.get(role)
                if selector_key and selector_key in self.selectors:
                    try:
                        if self.driver.is_element_visible(self.selectors[selector_key], timeout=3):
                            self.driver.click(self.selectors[selector_key])
                            logger.info(f"✅ Applied role filter: {role}")
                            time.sleep(0.5)
                        else:
                            logger.warning(f"Role filter not found: {role}")
                    except Exception as e:
                        logger.error(f"Error applying role filter {role}: {e}")
                else:
                    logger.warning(f"Unknown job role: {role}")

    def _set_length_of_employment(self, employment_length: str) -> None:
        """Set length of employment filter"""
        logger.info(f"Setting employment length: {employment_length}")
        # Implementation depends on specific UI elements
        pass

    def _set_language_requirement(self, language: str) -> None:
        """Set language requirement filter"""
        logger.info(f"Setting language requirement: {language}")
        # Implementation depends on specific UI elements
        pass

    def _set_start_date(self, start_date: str) -> None:
        """Set start date filter"""
        logger.info(f"Setting start date: {start_date}")
        # Implementation depends on specific UI elements
        pass

    def _apply_city_filter(self, cities: List[str]) -> None:
        """
        Apply city filter and click show results button.
        """
        if not cities:
            logger.warning("No cities provided for filtering")
            return
            
        # Use the first city in the list (for individual city processing)
        current_city = cities[0]
        logger.info(f"🔧 Applying city filter: {current_city}")
        
        try:
            # First, try to clear any existing city filter by clicking close button
            close_button_selectors = [
                'city_close_button', 'city_close_button_alt', 
                'city_close_button_alt2', 'city_close_button_alt3'
            ]
            
            for selector in close_button_selectors:
                try:
                    if self.driver.is_element_visible(self.selectors[selector], timeout=2):
                        self.driver.click(self.selectors[selector])
                        time.sleep(0.5)
                        logger.debug(f"Cleared existing city filter using: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Close button {selector} not found: {e}")
            
            # Ensure filters panel is open
            if not self._ensure_filters_panel_open():
                logger.error("Failed to open filters panel for city filter")
                return
            
            # Try multiple selectors to find the city input field in the filters panel
            city_input = None
            city_selectors = [
                self.selectors['city_input'],          # 'input[id="zipcode-nav-filter"]'
                self.selectors['city_input_alt'],      # '[data-test-id="zipcodeInputField"] input'
                self.selectors['city_input_alt2'],     # 'input[placeholder="Enter zipcode or city"]'
                self.selectors['city_input_alt3'],     # '[data-test-component="StencilSearchFieldInput"]'
                self.selectors['city_input_alt4'],     # 'input[placeholder*="city"]'
                self.selectors['city_input_alt5'],     # 'input[placeholder*="zip"]'
                self.selectors['city_input_alt6'],     # 'input[aria-label*="location"]'
                self.selectors['city_input_alt7'],     # 'input[aria-label*="city"]'
                self.selectors['city_input_alt8'],     # 'input[name*="location"]'
                self.selectors['city_input_alt9'],     # 'input[name*="city"]'
                self.selectors['city_input_alt10'],    # '[data-test-component="StencilFlyoutBody"] input[type="text"]'
                self.selectors['city_input_alt11'],    # '.jobFilterPanelContent input[type="text"]'
                self.selectors['city_input_alt12'],    # '[data-test-id="StencilReactPageContainer"] input[type="text"]'
                self.selectors['city_input_alt13'],    # '[data-test-id="location-filter-input"]'
                self.selectors['city_input_alt14'],    # 'input[data-test-id*="location"][type="text"]'
                self.selectors['city_input_alt15'],    # 'input[data-testid*="location"]'
                self.selectors['city_input_alt16'],    # 'input[data-testid*="city"]'
                self.selectors['city_input_alt17'],    # 'input[data-testid*="zip"]'
                self.selectors['city_input_alt18'],    # 'input[data-test-id*="zip"]'
                self.selectors['city_input_alt19'],    # 'input[data-testid*="search"]'
                self.selectors['city_input_alt20'],    # 'input[data-test-id*="search"]'
                'input[type="text"]',                 # Fallback to any text input
            ]
            
            # Retry logic: if input field not found, try reopening filters panel
            max_retries = 3
            for retry in range(max_retries):
                logger.info(f"🔍 City input search attempt {retry + 1}/{max_retries}")
                
                # Try each selector until we find a match
                for i, selector in enumerate(city_selectors, 1):
                    try:
                        if self.driver.is_element_visible(selector, timeout=2):
                            city_input = self.driver.find_element(selector)
                            logger.info(f"✅ Found city input using selector: {selector}")
                            
                            # Scroll the element into view
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", city_input)
                            time.sleep(0.5)
                            
                            # Click the input to ensure it's focused
                            try:
                                city_input.click()
                                time.sleep(0.5)
                            except Exception as e:
                                logger.debug(f"Could not click city input: {e}")
                            
                            break
                    except Exception as e:
                        logger.debug(f"City input selector {i}/{len(city_selectors)} failed: {e}")
                        continue
                
                if city_input:
                    break
                    
                # If no input found and this isn't the last retry, try reopening filters
                if retry < max_retries - 1:
                    logger.warning(f"City input not found, attempt {retry + 1}/{max_retries}. Trying to reopen filters panel...")
                    time.sleep(1)
                    # Try to reopen filters panel
                    if not self._ensure_filters_panel_open():
                        logger.warning("Failed to reopen filters panel")
                    time.sleep(1)
            
            if not city_input:
                logger.error("❌ Could not find city input field with any selector after retries")
                # Try fallback method before giving up
                logger.info("Attempting fallback city search method...")
                self._apply_city_search_fallback([current_city])
                return
            
            # Clear the input field with multiple methods for robustness
            clear_success = False
            clear_methods = [
                # Method 1: Standard clear
                lambda: city_input.clear(),
                # Method 2: Select all and delete
                lambda: [city_input.send_keys("\u0001"), city_input.send_keys("\u007F")],
                # Method 3: JavaScript clear
                lambda: self.driver.execute_script("arguments[0].value = '';", city_input),
                # Method 4: Click and clear with backspaces
                lambda: [city_input.click(), city_input.send_keys("\b" * 100)]
            ]
            
            for method in clear_methods:
                try:
                    method()
                    time.sleep(0.3)
                    # Verify the field is actually cleared
                    if not city_input.get_attribute('value'):
                        clear_success = True
                        break
                except Exception as e:
                    logger.debug(f"Clear method failed: {e}")
            
            if not clear_success:
                logger.warning("Could not clear city input field")
            
            # Enter the new city
            logger.info(f"Entering city: {current_city}")
            city_input.send_keys(current_city)
            time.sleep(1)  # Wait for any autocomplete
            
            # Try to select from autocomplete if it appears
            try:
                autocomplete_item = self.driver.find_element(f'//*[contains(text(), "{current_city}")]', by='xpath')
                if autocomplete_item:
                    autocomplete_item.click()
                    logger.info(f"✅ Selected city from autocomplete: {current_city}")
                    time.sleep(1)
            except:
                pass
            
            # Try to trigger search (press Enter or click search button)
            search_triggered = False
            
            # Try pressing Enter
            try:
                city_input.send_keys("\n")
                logger.info(f"✅ Pressed Enter to search for: {current_city}")
                search_triggered = True
            except Exception as e:
                logger.debug(f"Could not press Enter: {e}")
            
            # If Enter didn't work, try clicking search button
            if not search_triggered:
                search_button_selectors = [
                    self.selectors['location_search_button'],
                    self.selectors['location_search_button_alt'],
                    self.selectors['location_search_button_alt2'],
                    self.selectors['location_search_button_alt3'],
                    self.selectors['location_search_button_alt4'],
                    'button:contains("Search")',
                    'button:contains("Apply")',
                    'button[data-test-id*="search"]',
                    'button[data-test-id*="apply"]'
                ]
                
                for selector in search_button_selectors:
                    try:
                        if self.driver.is_element_visible(selector, timeout=1):
                            self.driver.click(selector)
                            logger.info(f"✅ Clicked search button: {selector}")
                            search_triggered = True
                            break
                    except:
                        continue
            
            if not search_triggered:
                logger.warning("Could not trigger search - trying to proceed anyway")
            
            # Wait for results to load
            time.sleep(2)  # Increased wait time for results to load
            
            # Click the "Show result" button if it exists
            self._click_show_results_button()
                
        except Exception as e:
            logger.error(f"❌ Error in city filter process: {e}")
            # Take a screenshot for debugging
            try:
                self.driver.save_screenshot(f"city_filter_error_{current_city.replace(' ', '_')}.png")
                logger.info("Saved screenshot for debugging")
            except:
                pass

    def _click_show_results_button(self) -> bool:
        """
        Click the "Show result" button after applying filters.
        """
        try:
            show_button_selectors = [
                self.selectors['show_results_button'],      # 'button:contains("Show")'
                self.selectors['show_results_button_alt'],  # '[data-test-id*="show"]'
                'button:contains("Show 22 results")',       # From screenshot
                'button:contains("Show") and contains("results")',
                '#filterPanelShowFiltersButton',
                '[data-test-id="filter-show-button"]',
                'button[id*="ShowFilters"]'
            ]
            
            for selector in show_button_selectors:
                try:
                    if self.driver.is_element_visible(selector):
                        self.driver.click(selector)
                        time.sleep(1)  # Reduced from 2 to 1 second  # Wait for results to load
                        logger.info(f"✅ Clicked show results button using: {selector}")
                        return True
                except Exception as e:
                    logger.debug(f"Show button selector {selector} failed: {e}")
                    continue
            
            logger.warning("Could not find show results button")
            return False
            
        except Exception as e:
            logger.error(f"Error clicking show results button: {e}")
            return False

    def clear_all_filters(self) -> bool:
        """Clear all applied filters"""
        try:
            if self.driver.is_element_visible(self.selectors['clear_filters']):
                self.driver.click(self.selectors['clear_filters'])
                time.sleep(2)
                logger.info("✅ Cleared all filters")
                return True
            else:
                logger.warning("Clear filters button not found")
                return False
        except Exception as e:
            logger.error(f"Error clearing filters: {e}")
            return False


@dataclass
class Shift:
    """Data class for shift information"""
    job_id: str
    title: str
    location: str
    schedule: str
    element_index: int
    pay_rate: Optional[str] = None
    duration: Optional[str] = None


class EnhancedShiftBooking:
    """
    Search for shifts with fallback selectors, extract rich shift details,
    simplified booking flow with retries and clear logging.
    """
    
    def __init__(self, driver: BaseCase, timeout: int = 10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.timeout = timeout

    def search_shifts(self, hours_back: int = 24) -> List[Shift]:
        """Search for available shifts with fallback selectors"""
        logger.info(f"Searching for shifts (looking back {hours_back} hours)")
        
        time.sleep(1)  # Allow page to stabilize
        
        try:
            # Wait for job cards to load with multiple selectors
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                "div[data-test-id='JobCard'], .job-card, .shift-card")))
        except TimeoutException:
            logger.warning("No job cards found within timeout")
            return []
        
        # Try multiple selectors to find job cards
        cards = []
        for selector in ["div[data-test-id='JobCard']", ".job-card", ".shift-card"]:
            cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if cards:
                logger.info(f"Found {len(cards)} job cards using selector: {selector}")
                break
        
        if not cards:
            logger.warning("No job cards found with any selector")
            return []
        
        # Extract shift information
        results = []
        for i, card in enumerate(cards):
            shift_info = self._extract_shift_details(card, i)
            if shift_info:
                results.append(shift_info)
        
        logger.info(f"Successfully extracted {len(results)} shifts")
        return results

    def _extract_shift_details(self, card, idx: int) -> Optional[Shift]:
        """Extract detailed information from a job card"""
        def find_text_by_selectors(selectors: List[str]) -> Optional[str]:
            """Try multiple selectors to find text content"""
            for selector in selectors:
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if text:
                        return text
                except:
                    continue
            return None
        
        try:
            # Extract basic information
            title = find_text_by_selectors(["strong", ".job-title", "h3", ".title"]) or f"Shift {idx+1}"
            location = find_text_by_selectors([".location", ".job-location", ".facility"]) or "Unknown"
            schedule = find_text_by_selectors([".schedule", ".shift-time", ".time"]) or "Unknown"
            
            # Extract job ID
            job_id = card.get_attribute("data-job-id") or f"shift_{idx}"
            
            # Extract optional information
            pay_rate = find_text_by_selectors([".pay", ".rate", ".wage", "[data-test-id*='pay']"])
            duration = find_text_by_selectors([".duration", ".length", "[data-test-id*='duration']"])
            
            return Shift(
                job_id=job_id,
                title=title,
                location=location,
                schedule=schedule,
                element_index=idx,
                pay_rate=pay_rate,
                duration=duration
            )
            
        except Exception as e:
            logger.error(f"Error extracting shift details from card {idx}: {e}")
            return None

    def book_shift(self, shift: Shift) -> bool:
        """Book a specific shift with retries and error handling"""
        logger.info(f"Attempting to book shift: {shift.title} at {shift.location}")
        
        try:
            # Find the job cards again (page might have refreshed)
            cards = self.driver.find_elements(By.CSS_SELECTOR,
                "div[data-test-id='JobCard'], .job-card, .shift-card")
            
            if shift.element_index >= len(cards):
                logger.error(f"Shift index {shift.element_index} out of range (only {len(cards)} cards found)")
                return False
            
            card = cards[shift.element_index]
            
            # Scroll card into view and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
            time.sleep(0.5)
            
            card.click()
            logger.info("✅ Clicked on job card")
            time.sleep(1)
            
            # Try to find and click apply button with multiple selectors
            apply_selectors = [
                "button[data-test-id='jobDetailApplyButtonDesktop']",
                "button:contains('Apply')",
                "button:contains('Book')",
                ".apply-button",
                "[data-test-id*='apply']"
            ]
            
            for selector in apply_selectors:
                try:
                    apply_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    apply_button.click()
                    logger.info(f"✅ Successfully booked shift: {shift.title}")
                    time.sleep(1)
                    return True
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"Apply button selector failed: {selector} - {e}")
                    continue
            
            logger.error("Could not find apply button with any selector")
            return False
            
        except Exception as e:
            logger.error(f"Error booking shift: {e}")
            return False


class EnhancedJobReporter:
    """
    Pulls total count and per-card details, summarizes results for quick overviews.
    """
    
    def __init__(self, driver: BaseCase, timeout: int = 5):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.selectors = {
            'job_count_header': 'h1[aria-live="assertive"]',
            'job_cards': 'div[data-test-id="JobCard"]',
            'job_title': '.jobDetailText strong',
            'shifts_available': 'div:contains("shift available")',
            'job_type': 'div:contains("Type:")',
            'job_duration': 'div[data-test-id="jobCardDurationText"]',
            'pay_rate': 'div[data-test-id="jobCardPayRateText"]',
            'job_location': '.hvh-careers-emotion-1lcyul5 strong'
        }

    def extract_all_jobs(self) -> Dict[str, Any]:
        """Extract comprehensive job information with structured logging"""
        logger.info("Extracting all job information")
        
        try:
            # Get total job count
            total_jobs = self._extract_job_count()
            logger.info(f"Total jobs found: {total_jobs}")
            
            # Extract individual job details
            jobs = self._extract_job_details()
            logger.info(f"Successfully extracted details for {len(jobs)} jobs")
            
            # Generate summary statistics
            summary = self._generate_job_summary(jobs)
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'total_jobs_found': total_jobs,
                'jobs_extracted': len(jobs),
                'jobs': jobs,
                'summary': summary
            }
            
            logger.info(f"Job extraction complete: {len(jobs)} jobs, {summary.get('total_shifts_available', 0)} total shifts")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting jobs: {e}")
            return {
                'error': str(e), 
                'timestamp': datetime.now().isoformat(),
                'total_jobs_found': 0,
                'jobs_extracted': 0,
                'jobs': [],
                'summary': {}
            }

    def extract_all_job_information(self) -> Dict[str, Any]:
        """Alias for extract_all_jobs for compatibility"""
        return self.extract_all_jobs()

    def _extract_job_count(self) -> int:
        """Extract total job count from header"""
        try:
            if self.driver.is_element_present(self.selectors['job_count_header']):
                header_text = self.driver.get_text(self.selectors['job_count_header'])
                # Extract number from "Total X jobs found"
                match = re.search(r'Total (\d+) jobs found', header_text)
                if match:
                    return int(match.group(1))
                
                # Fallback: extract any number from header
                numbers = re.findall(r'\d+', header_text)
                if numbers:
                    return int(numbers[0])
            
            return 0
        except Exception as e:
            logger.error(f"Error extracting job count: {e}")
            return 0

    def _extract_job_details(self) -> List[Dict[str, Any]]:
        """Extract detailed information from all job cards"""
        jobs = []
        
        try:
            job_cards = self.driver.find_elements(self.selectors['job_cards'])
            logger.debug(f"Found {len(job_cards)} job cards to process")
            
            for index, card in enumerate(job_cards):
                job_info = self._parse_job_card(card, index)
                if job_info:
                    jobs.append(job_info)
                    
        except Exception as e:
            logger.error(f"Error extracting job details: {e}")
        
        return jobs

    def _parse_job_card(self, card_element, index: int) -> Optional[Dict[str, Any]]:
        """Parse individual job card for detailed information"""
        try:
            # Extract basic job information
            title = self._extract_field_value(card_element, 'title')
            location = self._extract_field_value(card_element, 'location')
            job_type = self._extract_field_value(card_element, 'job_type')
            duration = self._extract_field_value(card_element, 'duration')
            pay_rate = self._extract_field_value(card_element, 'pay_rate')
            
            # Extract shifts available
            shifts_text = self._extract_field_value(card_element, 'shifts_available')
            shifts_available = self._extract_number_from_text(shifts_text)
            
            # Determine shift type from title and job type
            shift_type = self._determine_shift_type(title, job_type)
            
            return {
                'index': index,
                'title': title,
                'location': location,
                'job_type': job_type,
                'shift_type': shift_type,
                'duration': duration,
                'pay_rate': pay_rate,
                'shifts_available': shifts_available,
                'raw_shifts_text': shifts_text
            }
            
        except Exception as e:
            logger.error(f"Error parsing job card {index}: {e}")
            return None

    def _extract_field_value(self, card_element, field_name: str) -> str:
        """Extract field value from job card using multiple selectors"""
        field_selectors = {
            'title': ['strong', '.job-title', 'h3', '.title'],
            'location': ['.location', '.job-location', '.facility', 'strong'],
            'job_type': ['.job-type', '[data-test-id*="type"]'],
            'duration': ['[data-test-id="jobCardDurationText"]', '.duration'],
            'pay_rate': ['[data-test-id="jobCardPayRateText"]', '.pay-rate', '.wage'],
            'shifts_available': ['[data-test-component="StencilText"]', '.hvh-careers-emotion-1lcyul5']
        }
        
        selectors = field_selectors.get(field_name, [])
        
        # Special handling for shifts_available
        if field_name == 'shifts_available':
            try:
                # Search for elements containing "shift available" text
                elements = card_element.find_elements(By.CSS_SELECTOR, '[data-test-component="StencilText"]')
                for element in elements:
                    text = element.text.strip()
                    if 'shift available' in text.lower():
                        return text
            except:
                pass
        
        for selector in selectors:
            try:
                element = card_element.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
            except:
                continue
        
        return 'Unknown'

    def _extract_number_from_text(self, text: str) -> int:
        """Extract number from text string"""
        if not text or text == 'Unknown':
            return 0
        
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else 0

    def _determine_shift_type(self, title: str, job_type: str) -> str:
        """Determine shift type from title and job type"""
        title_lower = title.lower()
        job_type_lower = job_type.lower()
        
        if 'fulfillment' in title_lower or 'fulfillment' in job_type_lower:
            return 'Fulfillment Center'
        elif 'sortation' in title_lower or 'sortation' in job_type_lower:
            return 'Sortation Center'
        elif 'delivery' in title_lower or 'delivery' in job_type_lower:
            return 'Delivery Station'
        elif 'distribution' in title_lower or 'distribution' in job_type_lower:
            return 'Distribution Center'
        elif 'fresh' in title_lower or 'grocery' in title_lower:
            return 'Amazon Fresh'
        else:
            return 'Warehouse Associate'

    def _generate_job_summary(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from job data"""
        if not jobs:
            return {
                'total_positions': 0,
                'total_shifts_available': 0,
                'locations_distribution': {},
                'shift_types_distribution': {},
                'job_types_distribution': {},
                'average_shifts_per_position': 0
            }
        
        # Initialize counters
        locations = {}
        shift_types = {}
        job_types = {}
        total_shifts = 0
        
        for job in jobs:
            # Count by location
            location = job.get('location', 'Unknown')
            locations[location] = locations.get(location, 0) + 1
            
            # Count by shift type
            shift_type = job.get('shift_type', 'Unknown')
            shift_types[shift_type] = shift_types.get(shift_type, 0) + 1
            
            # Count by job type
            job_type = job.get('job_type', 'Unknown')
            job_types[job_type] = job_types.get(job_type, 0) + 1
            
            # Total shifts
            total_shifts += job.get('shifts_available', 0)
        
        return {
            'total_positions': len(jobs),
            'total_shifts_available': total_shifts,
            'locations_distribution': locations,
            'shift_types_distribution': shift_types,
            'job_types_distribution': job_types,
            'average_shifts_per_position': round(total_shifts / len(jobs), 2) if jobs else 0
        }

    def save_report_to_file(self, report_data: Dict[str, Any], filename: str = None) -> str:
        """Save report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"job_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"Report saved to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return ""


def debug_page_elements(self) -> None:
    """Debug method to identify available elements on the page"""
    try:
        # Check for any button containing "filter"
        filter_buttons = self.driver.find_elements('button:contains("filter")')
        logger.info(f"Found {len(filter_buttons)} buttons containing 'filter'")
        
        # Check for any button containing "Filter"
        filter_buttons_cap = self.driver.find_elements('button:contains("Filter")')
        logger.info(f"Found {len(filter_buttons_cap)} buttons containing 'Filter'")
        
        # Check current URL
        current_url = self.driver.get_current_url()
        logger.info(f"Current URL: {current_url}")
        
        # Check page title
        page_title = self.driver.get_title()
        logger.info(f"Page title: {page_title}")
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")