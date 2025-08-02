
import time
import logging
import sys
import yaml
import os
from typing import Dict, Any, List, Optional
from config.models import AppConfig
from page_objects.shift_booking import ShiftBooking
from job_components import EnhancedShiftFilter, EnhancedShiftBooking, EnhancedJobReporter
from services.session_service import SessionService
from utils.selenium_helpers import wait_for_page_load, handle_consent_buttons
from enhanced_notifier import EnhancedDiscordNotifier

logger = logging.getLogger(__name__)

class EnhancedIntegratedMonitor:
    def __init__(self, config: AppConfig):
        """
        config: your AppConfig instance (Pydantic)
        driver: will be injected by CLI after session is established
        """
        self.config = config
        self.driver = None
        self.shift_filter = None
        self.job_reporter = None
        self.shift_booking = None
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.daily_booking_count = 0  # Track bookings for continuous monitoring
        self.last_jobs_found = 0  # Track jobs found in last cycle
        self.cycle_bookings = 0  # Track bookings in current cycle
        
        # Initialize Enhanced Discord notifier for booking notifications
        try:
            self.notifier = EnhancedDiscordNotifier()
            self.logger.info("🔔 Enhanced Discord notifier initialized successfully")
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to initialize Enhanced Discord notifier: {e}")
            self.notifier = None
        
        # Load filter configuration from YAML file
        self.filter_config = self._load_filter_config()
        
        # COMPLETELY REVISED: Multiple URL strategies
        self.job_search_urls = [
            "https://hiring.amazon.com/app#/jobSearch",  # Primary: General search
            "https://hiring.amazon.com/app#/dashboard",   # Fallback: Dashboard
            "https://hiring.amazon.com/",                # Fallback: Home page
        ]
        
        # Optimized retry configuration for instant booking
        self.max_navigation_retries = 2  # Reduced retries for speed
        self.page_stabilization_time = 1  # Ultra-fast page stabilization

    def _load_filter_config(self) -> Dict[str, Any]:
        """Load filter configuration from YAML file"""
        config_path = os.path.join(os.path.dirname(__file__), 'filter_config.yaml')
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                self.logger.info(f"✅ Loaded filter configuration from {config_path}")
                return config
        except FileNotFoundError:
            self.logger.error(f"❌ Filter config file not found: {config_path}")
            return {'active_filters': [], 'shift_filters': {}}
        except yaml.YAMLError as e:
            self.logger.error(f"❌ Error parsing YAML config: {e}")
            return {'active_filters': [], 'shift_filters': {}}

    def start_monitoring(self, correlation_id: str = None):
        """Start enhanced monitoring; assumes self.driver is already logged in."""
        log_extra = {'correlation_id': correlation_id} if correlation_id else {}
        self.logger.info("🚀 Starting Enhanced Job Monitor", extra=log_extra)
        
        if not self.driver:
            raise RuntimeError("driver not set on monitor; forgot to inject it?")
        
        # initialize components now that driver is ready
        self._initialize_enhanced_components()
        
        cycle = 0
        self.running = True
        
        try:
            while self.running and (self.config.monitoring.max_cycles is None or cycle < self.config.monitoring.max_cycles):
                cycle += 1
                cycle_correlation_id = f"{correlation_id}-{cycle}" if correlation_id else f"cycle-{cycle}"
                
                self.logger.info(f"📊 Starting monitoring cycle {cycle}", extra={'correlation_id': cycle_correlation_id})
                
                try:
                    workflow_result = self._run_enhanced_workflow(cycle_correlation_id)
                    
                    # Always continue monitoring - track bookings for limits
                    if workflow_result == "BOOKING_SUCCESS":
                        self.daily_booking_count += 1
                        self.cycle_bookings += 1
                        self.logger.info(f"🎉 SHIFT #{self.daily_booking_count} SUCCESSFULLY BOOKED! Continuing to monitor for more shifts...", extra={'correlation_id': cycle_correlation_id})
                        
                        # Check daily booking limit
                        if hasattr(self.config.booking, 'daily_limit') and self.daily_booking_count >= self.config.booking.daily_limit:
                            self.logger.info(f"🎯 Reached daily booking limit ({self.config.booking.daily_limit}). Stopping monitoring.", extra={'correlation_id': cycle_correlation_id})
                            self.running = False
                            break
                        else:
                            limit_text = f"{self.daily_booking_count}/{self.config.booking.daily_limit}" if hasattr(self.config.booking, 'daily_limit') else str(self.daily_booking_count)
                            self.logger.info(f"🔄 Booked {limit_text} shifts today. Continuing monitoring for more...", extra={'correlation_id': cycle_correlation_id})
                    
                except Exception as e:
                    self.logger.error(f"Error in monitoring cycle {cycle}: {e}", extra={'correlation_id': cycle_correlation_id})
                    time.sleep(self.config.monitoring.error_retry_delay)
                    continue
                
                if self.running:
                    # Send cycle summary notification
                    try:
                        if hasattr(self, 'notifier') and self.notifier:
                            cities_processed = self.filter_config.get('shift_filters', {}).get('cities', [])
                            self.notifier.notify_monitoring_summary(
                                cycle=cycle,
                                jobs_found=getattr(self, 'last_jobs_found', 0),
                                bookings_made=getattr(self, 'cycle_bookings', 0),
                                cities_processed=cities_processed,
                                next_check_in=self.config.monitoring.check_interval
                            )
                    except Exception as e:
                        self.logger.debug(f"Failed to send cycle summary: {e}")
                    
                    # Reset cycle booking counter
                    setattr(self, 'cycle_bookings', 0)
                    
                    self.logger.info(f"⏰ Waiting {self.config.monitoring.check_interval}s until next cycle", extra={'correlation_id': cycle_correlation_id})
                    time.sleep(self.config.monitoring.check_interval)
                    
        except KeyboardInterrupt:
            self.logger.info("🛑 Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Fatal error in monitoring: {e}")
            raise
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop the monitoring loop."""
        self.running = False
        self.logger.info("🏁 Enhanced monitoring stopped")
        
    def initialize_components(self, driver):
        """Initialize all enhanced components with the driver (public method for bulletproof monitor)."""
        self.driver = driver
        self._initialize_enhanced_components()
    
    def _initialize_enhanced_components(self):
        """Initialize all enhanced components with the driver."""
        try:
            self.shift_filter = EnhancedShiftFilter(self.driver)
            self.job_reporter = EnhancedJobReporter(self.driver)
            self.shift_booking = EnhancedShiftBooking(self.driver)
            
            self.logger.info("✅ Enhanced components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced components: {e}")
            raise
    
    def _run_enhanced_workflow(self, correlation_id: str):
        """Run the complete enhanced workflow for one cycle."""
        log_extra = {'correlation_id': correlation_id}
        
        for url_index, url in enumerate(self.job_search_urls):
            success = False
            
            for retry in range(self.max_navigation_retries):
                try:
                    self.logger.info(f"🔍 Attempt {retry + 1}: Processing URL {url_index + 1}/{len(self.job_search_urls)}: {url}", extra=log_extra)
                    
                    # Navigate with optimized timeout
                    self.driver.open(url)
                    
                    # Optimized page load wait for instant booking
                    page_loaded = wait_for_page_load(self.driver, timeout=6)  # Reduced from 10 to 6 seconds
                    if not page_loaded:
                        self.logger.warning(f"Page load timeout for {url}, attempt {retry + 1}", extra=log_extra)
                        if retry < self.max_navigation_retries - 1:
                            time.sleep(0.5)  # Reduced from 1 to 0.5 seconds
                            continue
                    
                    # Ultra-fast stabilization for instant booking
                    time.sleep(self.page_stabilization_time)
                    handle_consent_buttons(self.driver)
                    
                    # Enhanced navigation sequence
                    if self._navigate_to_job_search_with_filters():
                        success = True
                        break
                    else:
                        self.logger.warning(f"Navigation failed for {url}, attempt {retry + 1}", extra=log_extra)
                        if retry < self.max_navigation_retries - 1:
                            time.sleep(1)  # Reduced from 3 to 1 second
                            continue
                        
                except Exception as e:
                    self.logger.error(f"Error in attempt {retry + 1} for URL {url}: {e}", extra=log_extra)
                    if retry < self.max_navigation_retries - 1:
                        time.sleep(2)  # Reduced from 5 to 2 seconds
                        continue
            
            if success:
                # Process filters and jobs - check for booking success
                processing_result = self._process_job_search_with_filters(correlation_id)
                if processing_result == "BOOKING_SUCCESS":
                    return "BOOKING_SUCCESS"
                break  # Success with this URL, no need to try others
            else:
                self.logger.error(f"All attempts failed for URL: {url}", extra=log_extra)
                continue  # Try next URL
        
        if not success:
            self.logger.error("All URLs and attempts failed", extra=log_extra)
            
        return "CONTINUE"  # Continue monitoring if no booking success

    def _navigate_to_job_search_with_filters(self) -> bool:
        """Enhanced navigation to ensure we reach a page with working filters."""
        try:
            # Step 1: Handle any modals or overlays
            self._handle_all_modals_and_overlays()
            
            # Step 2: Detect current page type and navigate accordingly
            page_type = self._detect_current_page_type()
            self.logger.info(f"Detected page type: {page_type}")
            
            if page_type == "loading":
                self.logger.info("Detected loading page, waiting for completion...")
                loading_completed = self._wait_for_loading_completion()
                if not loading_completed:
                    self.logger.warning("Loading completion failed, attempting direct navigation")
                    return self._navigate_back_to_job_search()
                time.sleep(1)  # Reduced from 3 to 1 second
                page_type = self._detect_current_page_type()
            
            if page_type == "dashboard":
                self.logger.info("On dashboard, navigating to job search...")
                if not self._navigate_from_dashboard_to_search():
                    return False
            elif page_type == "application":
                self.logger.info("On application page, navigating back to search...")
                if not self._navigate_from_application_to_search():
                    return False
            elif page_type == "home":
                self.logger.info("On home page, navigating to job search...")
                if not self._navigate_from_home_to_search():
                    return False
            
            # Step 3: Verify we can access filters
            time.sleep(1)  # Reduced from 3 to 1 second
            return self._verify_filters_accessible()
            
        except Exception as e:
            self.logger.error(f"Navigation error: {e}")
            return False

    def _detect_current_page_type(self) -> str:
        """Detect what type of page we're currently on."""
        try:
            # Check for loading page - enhanced detection
            loading_indicators = [
                "Loading...",
                "Your application details are on their way",
                "Please give it a few moments to load",
                ".loading",
                "[data-test-id='loading']",
                "application details are on their way"
            ]
            for indicator in loading_indicators:
                if self.driver.is_text_visible(indicator) or self.driver.is_element_present(indicator):
                    self.logger.warning(f"Detected loading page with indicator: {indicator}")
                    return "loading"
    
            # Check for dashboard (enhanced detection)
            dashboard_indicators = [
                "Welcome back",                                 # Primary: "Welcome back Lovepreet"
                "continue where you left off",                 # Primary: Main dashboard text  
                "Continue where you left off",                 # Capitalized version
                "Active jobs",                                  # Dashboard shows job counts
                "Recommended jobs",                             # Dashboard shows recommendations
                "Search all jobs",                              # Dashboard has this button
                "Go to my jobs",                                # Dashboard has this button
                "Welcome to Amazon jobs",                       # Alternative welcome text
                "[data-test-id='dashboard']",                   # Test ID
                ".dashboard",                                   # CSS class
                "My Jobs",                                      # My Jobs section
                "Application Status"                            # Application status section
            ]
            current_url = self.driver.get_current_url()
            if "dashboard" in current_url.lower():
                return "dashboard"
                
            for indicator in dashboard_indicators:
                if self.driver.is_text_visible(indicator) or self.driver.is_element_present(indicator):
                    return "dashboard"
    
            # Check for application page
            application_indicators = [
                "Application",
                "Apply for this job",
                "Job Details",
                "[data-test-id='application']"
            ]
            for indicator in application_indicators:
                if self.driver.is_text_visible(indicator):
                    return "application"
    
            # Check for job search page
            search_indicators = [
                "Add filter",
                "Filters",
                "jobs found",
                "[data-test-id='job-search']"
            ]
            for indicator in search_indicators:
                if self.driver.is_text_visible(indicator) or self.driver.is_element_present(indicator):
                    return "search"
    
            return "unknown"
        except Exception as e:
            self.logger.error(f"Error detecting page type: {e}")
            return "unknown"

    def _navigate_from_dashboard_to_search(self) -> bool:
        """Navigate from dashboard to job search page."""
        try:
            self.logger.info("🔄 Attempting to navigate from dashboard to job search...")
            
            # Debug: Log what buttons are visible on the dashboard
            self._debug_dashboard_buttons()
            
            # Enhanced search button selectors - using exact HTML structure from dashboardwidget.xml
            search_buttons = [
                # Priority 1: Exact selectors from the XML structure
                'button[data-test-component="StencilReactButton"].hvh-careers-emotion-1c3a5a2',  # Search all jobs exact class
                'button[data-test-component="StencilReactButton"]:contains("Search all jobs")',   # React component + text
                'button.hvh-careers-emotion-1c3a5a2',                                            # Specific CSS class
                'button[aria-label="Search all jobs"]',
                
                # Priority 2: More general selectors for "Search all jobs"
                'button:contains("Search all jobs")',                                            
                'a:contains("Search all jobs")',
                'button[type="button"]:contains("Search all jobs")',
                
                # Priority 3: Nested div structure from XML
                'button[data-test-component="StencilReactButton"] div:contains("Search all jobs")',
                'div[data-test-component="StencilReactRow"]:contains("Search all jobs")',
                
                # Priority 4: If Search all jobs doesn't work, try other methods
                'a[href*="jobSearch"]',
                'a[href*="/app#/jobSearch"]',
                'button:contains("Find jobs")',
                
                # Priority 5: Last resort - Go to my jobs button (from XML structure)
                'button[data-test-component="StencilReactButton"].hvh-careers-emotion-1exe8dr',  # Go to my jobs exact class
                'button:contains("Go to my jobs")',
                'a:contains("Go to my jobs")'
            ]
            
            for selector in search_buttons:
                try:
                    if self.driver.is_element_visible(selector):
                        self.logger.info(f"🔄 Found dashboard button: {selector}")
                        
                        # Try multiple click methods for better reliability
                        clicked = False
                        
                        # Method 1: Standard click
                        try:
                            self.driver.click(selector)
                            clicked = True
                            self.logger.info("✅ Clicked using standard method")
                        except Exception as e:
                            self.logger.debug(f"Standard click failed: {e}")
                            
                            # Method 2: JavaScript click
                            try:
                                element = self.driver.find_element(selector)
                                self.driver.execute_script("arguments[0].click();", element)
                                clicked = True
                                self.logger.info("✅ Clicked using JavaScript method")
                            except Exception as e2:
                                self.logger.debug(f"JavaScript click failed: {e2}")
                                
                                # Method 3: Scroll and click
                                try:
                                    element = self.driver.find_element(selector)
                                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                    time.sleep(1)
                                    element.click()
                                    clicked = True
                                    self.logger.info("✅ Clicked using scroll+click method")
                                except Exception as e3:
                                    self.logger.debug(f"Scroll+click failed: {e3}")
                        
                        if clicked:
                            time.sleep(3)  # Reduced from 5 to 3 seconds for navigation
                            
                            # Verify navigation success multiple times
                            for attempt in range(3):
                                current_page = self._detect_current_page_type()
                                self.logger.info(f"Navigation verification {attempt + 1}: Current page type: {current_page}")
                                
                                if current_page != "dashboard":
                                    self.logger.info(f"✅ Successfully navigated away from dashboard to: {current_page}")
                                    return True
                                time.sleep(1)  # Reduced from 2 to 1 second
                            
                            self.logger.warning(f"Still on dashboard after clicking {selector}")
                        else:
                            self.logger.warning(f"Failed to click {selector} with any method")
                            
                except Exception as e:
                    self.logger.debug(f"Dashboard navigation selector {selector} failed: {e}")
                    continue
            
            # Fallback: direct navigation to job search URL
            self.logger.warning("🔄 Dashboard navigation buttons not found, trying direct URL navigation")
            self.driver.open("https://hiring.amazon.com/app#/jobSearch")
            time.sleep(4)  # Reduced from 8 to 4 seconds for page load
            
            # Verify navigation with multiple checks
            for attempt in range(3):
                current_page = self._detect_current_page_type()
                self.logger.info(f"Direct navigation attempt {attempt + 1}: Current page type: {current_page}")
                
                if current_page == "search" or self._verify_filters_accessible():
                    self.logger.info("✅ Successfully navigated to job search via direct URL")
                    return True
                    
                time.sleep(1.5)  # Reduced from 3 to 1.5 seconds
            
            self.logger.error("❌ Failed to navigate away from dashboard")
            return False
            
        except Exception as e:
            self.logger.error(f"Error navigating from dashboard to search: {e}")
            return False

    def _navigate_from_application_to_search(self) -> bool:
        """Navigate from application page back to job search."""
        try:
            # Click a "Back to search" or similar link
            back_buttons = [
                'a:contains("Back to search results")',
                'button[aria-label="Back to search"]'
            ]
            
            visible_button = self._find_visible_element(back_buttons)
            if visible_button:
                self.driver.click(visible_button)
                time.sleep(3)
                return True
            
            # If no specific button, try going back in browser history
            self.driver.open(self.job_search_urls[0])
            time.sleep(3)
            return True
        except Exception as e:
            self.logger.error(f"Error navigating from application to search: {e}")
            return False

    def _navigate_from_home_to_search(self) -> bool:
        """Navigate from home page to job search."""
        try:
            # Use the main search input on the home page
            search_input_selectors = [
                'input[placeholder="Enter zipcode or city"]',
                'input[id="zipcode-nav-guide"]'
            ]
            search_button_selectors = [
                'button:contains("Find jobs")',
                'button[aria-label="Search jobs"]'
            ]
            
            for selector in search_input_selectors:
                if self.driver.is_element_visible(selector):
                    self.driver.type(selector, "remote") # search for a default term
                    time.sleep(1)
                    for btn_selector in search_button_selectors:
                        if self.driver.is_element_visible(btn_selector):
                            self.driver.click(btn_selector)
                            time.sleep(3)
                            return True
            return False
        except Exception as e:
            self.logger.error(f"Error navigating from home to search: {e}")
            return False

    def _wait_for_loading_completion(self, max_wait: int = 30) -> bool:
        """Wait for loading page to complete."""
        try:
            start_time = time.time()
            while time.time() - start_time < max_wait:
                # Check if still loading
                if not (self.driver.is_text_visible("Loading...") or 
                       self.driver.is_text_visible("Your application details are on their way") or
                       self.driver.is_text_visible("application details are on their way")):
                    self.logger.info("Loading completed")
                    
                    # Check if we ended up on an application page instead of job search
                    current_page = self._detect_current_page_type()
                    if current_page in ["application", "dashboard"]:
                        self.logger.warning(f"Loading completed but landed on {current_page} page. Navigating back to job search...")
                        return self._navigate_back_to_job_search()
                    
                    return True
                time.sleep(2)
            
            self.logger.warning("Loading timeout reached, attempting to navigate back to job search")
            return self._navigate_back_to_job_search()
            
        except Exception as e:
            self.logger.error(f"Error waiting for loading: {e}")
            return False

    def _debug_dashboard_buttons(self):
        """Debug method to see what buttons are available on dashboard."""
        try:
            # Look for all buttons and links on the page
            buttons = self.driver.find_elements("button")
            links = self.driver.find_elements("a")
            
            self.logger.info(f"🔍 Dashboard debugging - Found {len(buttons)} buttons and {len(links)} links")
            
            # Log button details with attributes
            for i, button in enumerate(buttons[:10]):  # Limit to first 10 to avoid spam
                try:
                    text = button.text.strip()
                    data_test = button.get_attribute('data-test-component')
                    css_class = button.get_attribute('class')
                    button_type = button.get_attribute('type')
                    
                    if text:
                        self.logger.info(f"Button {i+1}: '{text}' | data-test-component='{data_test}' | class='{css_class}' | type='{button_type}'")
                except:
                    pass
            
            # Look specifically for StencilReactButton components
            react_buttons = self.driver.find_elements('[data-test-component="StencilReactButton"]')
            self.logger.info(f"🔍 Found {len(react_buttons)} StencilReactButton components")
            
            for i, button in enumerate(react_buttons[:5]):
                try:
                    text = button.text.strip()
                    css_class = button.get_attribute('class')
                    if text:
                        self.logger.info(f"React Button {i+1}: '{text}' | class='{css_class}'")
                except:
                    pass
                    
        except Exception as e:
            self.logger.debug(f"Error in dashboard debugging: {e}")

    def _navigate_back_to_job_search(self) -> bool:
        """Navigate back to job search from any page."""
        try:
            self.logger.info("🔄 Attempting to navigate back to job search page...")
            
            # Try direct URL navigation first
            self.driver.open("https://hiring.amazon.com/app#/jobSearch")
            time.sleep(5)
            
            # Verify we're on job search page
            if self._verify_filters_accessible():
                self.logger.info("✅ Successfully navigated back to job search")
                return True
            
            # Fallback: try other job search URLs
            for url in self.job_search_urls[1:]:
                try:
                    self.logger.info(f"🔄 Trying fallback URL: {url}")
                    self.driver.open(url)
                    time.sleep(5)
                    
                    current_page = self._detect_current_page_type()
                    if current_page == "search" or self._verify_filters_accessible():
                        self.logger.info(f"✅ Successfully reached job search via: {url}")
                        return True
                except Exception as e:
                    self.logger.debug(f"Fallback URL {url} failed: {e}")
                    continue
            
            self.logger.error("❌ Failed to navigate back to job search with any method")
            return False
            
        except Exception as e:
            self.logger.error(f"Error navigating back to job search: {e}")
            return False

    def _handle_all_modals_and_overlays(self):
        """Handle all possible modals and overlays."""
        modal_selectors = [
            # Guided search modal - prioritize the close button
            '.guidedSearchCloseButton',
            'button:contains("Skip")',
            '[data-test-component="StencilReactButton"]:contains("Skip")',
            'button[aria-label="Close guided search"]',
            
            # View all filters button (this opens the filters panel)
            'button:contains("View all filters")',
            '.guidedSearchFilterButton',
            
            # General modal close buttons
            '[aria-label="Close"]',
            '.modal-close',
            '.close-button',
            'button:contains("Close")',
            
            # Cookie/consent banners
            'button:contains("Accept")',
            'button:contains("Allow")',
            '#consent-accept',
        ]
        
        # Try to handle guided search modal specifically first - optimized for speed
        try:
            # Multiple modal detection methods for the "Tell us about yourself" modal
            modal_indicators = [
                'div:contains("Tell us a little more about yourself")',
                'div:contains("Step 1/5")',
                'div:contains("What\'s the location of your home address?")',
                '.guidedSearchContainer',
                '[role="dialog"]'
            ]
            
            modal_found = False
            for indicator in modal_indicators:
                if self.driver.is_element_visible(indicator):
                    self.logger.info(f"Found guided search modal: {indicator}")
                    modal_found = True
                    break
            
            if modal_found:
                # Priority 1: Click "View all filters" to bypass the modal
                view_filters_selectors = [
                    'button:contains("View all filters")',
                    'a:contains("View all filters")',
                    '[data-testid*="view-filters"]',
                    '.view-all-filters'
                ]
                
                for selector in view_filters_selectors:
                    try:
                        if self.driver.is_element_visible(selector):
                            self.logger.info(f"Clicking 'View all filters' using: {selector}")
                            self.driver.click(selector)
                            time.sleep(1)  # Reduced from 2 to 1 second
                            return
                    except:
                        continue
                
                # Priority 2: Click "Skip" to bypass the modal
                skip_selectors = [
                    'button:contains("Skip")',
                    'a:contains("Skip")',
                    '[data-testid*="skip"]',
                    '.skip-button'
                ]
                
                for selector in skip_selectors:
                    try:
                        if self.driver.is_element_visible(selector):
                            self.logger.info(f"Clicking 'Skip' using: {selector}")
                            self.driver.click(selector)
                            time.sleep(1)  # Reduced from 2 to 1 second
                            return
                    except:
                        continue
                
                # Priority 3: Close the modal with X button
                close_selectors = [
                    '.guidedSearchCloseButton',
                    'button[aria-label="Close"]',
                    '[data-testid*="close"]',
                    '.close-button',
                    'button:contains("×")'
                ]
                
                for selector in close_selectors:
                    try:
                        if self.driver.is_element_visible(selector):
                            self.logger.info(f"Closing modal using: {selector}")
                            self.driver.click(selector)
                            time.sleep(1)  # Reduced from 2 to 1 second
                            return
                    except:
                        continue
                        
                self.logger.warning("⚠️ Modal detected but couldn't close it with any method")
                
        except Exception as e:
            self.logger.debug(f"Error handling guided search modal: {e}")
        
        # Handle other modals
        for selector in modal_selectors:
            try:
                if self.driver.is_element_visible(selector):
                    self.logger.info(f"Closing modal with: {selector}")
                    self.driver.click(selector)
                    time.sleep(1)
            except Exception:
                continue

    def _verify_filters_accessible(self) -> bool:
        """Verify that filters are accessible on the current page."""
        filter_indicators = [
            '[data-test-id="openFiltersButton"]',      # Primary - from filtersontop.xml
            'button:contains("Add filter")',           # Secondary
            '.topBar:contains("Add filter")',          # Alternative topbar
            'button:contains("View all filters")',     # Guided search modal
            'button:contains("Filters")',              # Generic
            '.filter-button'                           # Fallback
        ]
        
        visible_button = self._find_visible_element(filter_indicators)
        if visible_button:
            self.logger.info(f"✅ Filters accessible via: {visible_button}")
            return True
        
        self.logger.error("❌ No filter buttons found - filters not accessible")
        return False

    def _find_visible_element(self, selectors: List[str]) -> Optional[str]:
        """Find the first visible element from a list of selectors."""
        for selector in selectors:
            try:
                if self.driver.is_element_visible(selector):
                    self.logger.info(f"Found visible element with selector: {selector}")
                    return selector
            except Exception:
                continue
        return None

    def _process_job_search_with_filters(self, correlation_id: str):
        """Process job search with enhanced filter handling."""
        try:
            # Get cities from config
            shift_filters = self.filter_config.get('shift_filters', {})
            cities = shift_filters.get('cities', [])
            
            # Process each city individually
            if cities and 'cities' in self.filter_config.get('active_filters', []):
                processing_result = self._process_cities_individually(correlation_id, cities)
                if processing_result == "BOOKING_SUCCESS":
                    self.logger.info("🎉 Booking successful! Stopping monitoring.")
                    return "BOOKING_SUCCESS"
            else:
                # Apply non-city filters and process normally
                self._apply_enhanced_filters_without_cities(correlation_id)
                processing_result = self._handle_shift_processing(correlation_id)
                if processing_result == "BOOKING_SUCCESS":
                    self.logger.info("🎉 Booking successful! Stopping monitoring.")
                    return "BOOKING_SUCCESS"
                
        except Exception as e:
            self.logger.error(f"Error processing job search: {e}")
            
        return "CONTINUE"  # Default to continue if no booking success

    def _process_cities_individually(self, correlation_id: str, cities: List[str]):
        """Process each city individually with ultra-fast processing for instant booking."""
        try:
            # Check if fast mode and parallel processing are enabled
            if hasattr(self.config.monitoring, 'fast_mode') and self.config.monitoring.fast_mode:
                return self._process_cities_fast_mode(correlation_id, cities)
            
            for i, city in enumerate(cities, 1):
                self.logger.info(f"🏙️ Processing city {i}/{len(cities)}: {city}")
                
                # Apply city filter with minimal delay
                self.logger.info(f"🔧 Applying city filter: {city}")
                success = self.shift_filter.apply_filters(['cities'], {'cities': [city]})
                
                if not success:
                    self.logger.warning(f"⚠️ City filter may not have been applied: {city}")
                
                # Process jobs for this city - check for booking success
                processing_result = self._handle_shift_processing(correlation_id)
                
                # Instant booking check - stop immediately if booking successful
                if processing_result == "BOOKING_SUCCESS":
                    self.logger.info(f"🎉 INSTANT BOOKING SUCCESS in city: {city}! Continuing to next city for more bookings...")
                    # Continue processing other cities instead of stopping
                    continue
                
                # Clear city filter with minimal delay
                self._clear_city_filter()
                
                self.logger.info(f"✅ Completed processing for city: {city}")
                
                # Minimal delay between cities for speed
                time.sleep(0.2)  # Reduced from 0.5 to 0.2 seconds
            
            self.logger.info(f"✅ Completed processing all {len(cities)} cities. No bookings made.")
            return "CONTINUE"
                
        except Exception as e:
            self.logger.error(f"Error processing cities individually: {e}")
            return "CONTINUE"

    def _process_cities_fast_mode(self, correlation_id: str, cities: List[str]):
        """Ultra-fast city processing with aggressive optimizations."""
        try:
            self.logger.info(f"🚀 FAST MODE: Processing {len(cities)} cities with aggressive optimizations")
            
            for i, city in enumerate(cities, 1):
                self.logger.info(f"⚡ Fast processing city {i}/{len(cities)}: {city}")
                
                # Skip filter application if jobs are already visible
                current_jobs = self._quick_job_check()
                if current_jobs > 0:
                    self.logger.info(f"⚡ Found {current_jobs} jobs without filters, attempting instant booking")
                    processing_result = self._handle_shift_processing(correlation_id)
                    if processing_result == "BOOKING_SUCCESS":
                        self.logger.info(f"🎉 LIGHTNING BOOKING SUCCESS! Job booked in {city}")
                        return "BOOKING_SUCCESS"
                
                # Quick filter application
                success = self.shift_filter.apply_filters(['cities'], {'cities': [city]})
                
                # Immediate job processing without delay
                processing_result = self._handle_shift_processing(correlation_id)
                
                if processing_result == "BOOKING_SUCCESS":
                    self.logger.info(f"🎉 FAST MODE BOOKING SUCCESS in city: {city}! Continuing to next city...")
                    # Continue processing other cities instead of stopping
                    continue
                
                # Quick filter clear
                self._clear_city_filter()
                
                # No delay between cities in fast mode
                
            self.logger.info(f"⚡ Fast mode processing complete. No bookings made.")
            return "CONTINUE"
                
        except Exception as e:
            self.logger.error(f"Error in fast mode city processing: {e}")
            return "CONTINUE"

    def _quick_job_check(self) -> int:
        """Quick check to see if jobs are already visible on the page."""
        try:
            job_cards = self.driver.find_elements('div[data-test-id="JobCard"]')
            return len(job_cards)
        except Exception:
            return 0

    def _apply_enhanced_filters_without_cities(self, correlation_id: str):
        """Apply non-city filters from configuration."""
        try:
            # Get active filters excluding cities
            active_filters = [f for f in self.filter_config.get('active_filters', []) if f != 'cities']
            
            if active_filters:
                self.logger.info(f"🔧 Applying filters: {active_filters}")
                shift_filters = self.filter_config.get('shift_filters', {})
                
                # Build filter data excluding cities
                filter_data = {key: value for key, value in shift_filters.items() if key != 'cities'}
                
                success = self.shift_filter.apply_filters(active_filters, filter_data)
                if not success:
                    self.logger.warning("⚠️ Some filters may not have been applied")
            else:
                self.logger.info("ℹ️ No non-city filters to apply")
                
        except Exception as e:
            self.logger.error(f"Error applying enhanced filters: {e}")

    def _handle_shift_processing(self, correlation_id: str):
        """Handle the core shift processing workflow with immediate booking."""
        try:
            # Extract job information
            report_data = self.job_reporter.extract_all_job_information()
            
            # Get job count from report and track it
            jobs_found = report_data.get('jobs_extracted', 0)
            total_jobs = report_data.get('total_jobs_found', 0)
            self.last_jobs_found = total_jobs  # Track for cycle summary
            self.logger.info(f"📊 Generated report: {total_jobs} total jobs, {jobs_found} jobs extracted")
            
            # Immediate booking attempt if jobs are found and booking is enabled
            if jobs_found > 0 and report_data.get('jobs'):
                self.logger.info(f"🎯 JOBS FOUND! {jobs_found} jobs available.")
                
                # Check if booking is enabled in config
                if hasattr(self.config, 'booking') and getattr(self.config.booking, 'enabled', False):
                    self.logger.info(f"🎯 Booking enabled! Attempting immediate booking for {jobs_found} jobs...")
                    jobs = report_data.get('jobs', [])
                    
                    # Stop other processing and focus on booking
                    booking_success = self._attempt_immediate_booking(jobs, correlation_id)
                    
                    if booking_success:
                        self.logger.info("🎉 SHIFT SUCCESSFULLY BOOKED! Continuing monitoring for more shifts...")
                        # Continue monitoring instead of stopping
                        # return "BOOKING_SUCCESS"  # Don't return - keep processing
                    else:
                        self.logger.warning("⚠️ Booking attempt failed, continuing monitoring...")
                else:
                    self.logger.info("📊 Booking disabled in config. Jobs found but not attempting to book.")
            else:
                self.logger.debug(f"No jobs found for this location/filter combination")
            
            return "CONTINUE"  # Signal to continue monitoring
            
        except Exception as e:
            self.logger.error(f"Error handling shift processing: {e}")
            return "CONTINUE"

    def _attempt_immediate_booking(self, jobs: List[Dict], correlation_id: str) -> bool:
        """Attempt to immediately book the first available job."""
        try:
            # Initialize booking component if not already done
            if not hasattr(self, 'shift_booking_handler'):
                self.shift_booking_handler = ShiftBooking(self.driver)
            
            # Convert job data to shift slots and attempt booking
            for i, job in enumerate(jobs):
                self.logger.info(f"🎯 Attempting to book job {i+1}/{len(jobs)}: {job.get('title', 'Unknown')}")
                
                # Discover available slots from current page
                slots = self.shift_booking_handler.discover_available_slots(correlation_id)
                
                if slots:
                    # Try to book the first available slot
                    for slot in slots:
                        self.logger.info(f"🎯 Attempting to book slot: {slot.title} at {slot.location}")
                        
                        booking_result = self.shift_booking_handler.book_slot(slot, correlation_id)
                        
                        if booking_result:
                            self.logger.info(f"🎉 SUCCESSFULLY BOOKED: {slot.title} at {slot.location}")
                            
                            # Send notification if available
                            self._send_booking_notification(slot, correlation_id)
                            
                            return True
                        else:
                            self.logger.warning(f"⚠️ Failed to book slot: {slot.title}")
                            continue
                else:
                    self.logger.warning(f"⚠️ No bookable slots found for job: {job.get('title', 'Unknown')}")
                    
            self.logger.warning("⚠️ No slots could be booked from available jobs")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error in immediate booking: {e}")
            return False

    def _send_booking_notification(self, slot, correlation_id: str):
        """Send detailed notification about successful booking."""
        try:
            if hasattr(self, 'notifier') and self.notifier:
                # Create detailed booking notification with all available information
                self.notifier.notify_instant_booking_success(
                    shift_number=self.daily_booking_count,
                    title=slot.title,
                    location=slot.location,
                    schedule=getattr(slot, 'schedule', 'TBD'),
                    pay_rate=getattr(slot, 'pay_rate', 'TBD'),
                    discovered_at=getattr(slot, 'discovered_at', 'Now'),
                    correlation_id=correlation_id
                )
                self.logger.info("🔔 Enhanced Discord booking notification sent successfully")
            else:
                self.logger.debug("No notifier configured for booking notifications")
        except Exception as e:
            self.logger.error(f"Failed to send booking notification: {e}")

    def _clear_city_filter(self):
        """Clear the currently applied city filter."""
        try:
            # Try different methods to clear the filter
            clear_selectors = [
                '[data-test-component="StencilReactButton"]',  # Standard close button
                'button[aria-label="Clear filter"]',
                'button[aria-label="Remove filter"]',
                '.filter-close-button',
                '.close-filter',
                'button:contains("Clear")'
            ]
            
            for selector in clear_selectors:
                try:
                    if self.driver.is_element_visible(selector):
                        self.driver.click(selector)
                        self.logger.info(f"✅ Cleared city filter using close button: {selector}")
                        time.sleep(1)
                        return
                except Exception:
                    continue
            
            self.logger.warning("⚠️ Could not find clear filter button, filter may still be active")
            
        except Exception as e:
            self.logger.error(f"Error clearing city filter: {e}")