import time
import json
import logging
from datetime import datetime, date
from dataclasses import dataclass, asdict
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Set, Optional

logger = logging.getLogger(__name__)

@dataclass
class ShiftSlot:
    job_id: str
    title: str
    location: str
    schedule: str
    card_index: int
    pay_rate: Optional[str] = None
    discovered_at: Optional[str] = None
    
    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.now().isoformat()

class ShiftBookingState:
    """Manages booking state and idempotency."""
    
    def __init__(self, state_file: str = "booking_state.json"):
        self.state_file = Path(state_file)
        self.booked_today: Set[str] = set()
        self.daily_count = 0
        self.last_reset_date = date.today().isoformat()
        self._load_state()
    
    def _load_state(self):
        """Load booking state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    
                # Reset if it's a new day
                if data.get('last_reset_date') != date.today().isoformat():
                    self._reset_daily_state()
                else:
                    self.booked_today = set(data.get('booked_today', []))
                    self.daily_count = data.get('daily_count', 0)
                    self.last_reset_date = data.get('last_reset_date', date.today().isoformat())
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load booking state: {e}. Starting fresh.")
                self._reset_daily_state()
    
    def _reset_daily_state(self):
        """Reset state for a new day."""
        self.booked_today.clear()
        self.daily_count = 0
        self.last_reset_date = date.today().isoformat()
        self._save_state()
        logger.info("🔄 Daily booking state reset")
    
    def _save_state(self):
        """Save current state to file."""
        try:
            data = {
                'booked_today': list(self.booked_today),
                'daily_count': self.daily_count,
                'last_reset_date': self.last_reset_date
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save booking state: {e}")
    
    def is_already_booked(self, job_id: str) -> bool:
        """Check if job was already booked today."""
        return job_id in self.booked_today
    
    def mark_as_booked(self, job_id: str):
        """Mark job as booked and increment counters."""
        self.booked_today.add(job_id)
        self.daily_count += 1
        self._save_state()
    
    def can_book_more(self, daily_limit: int) -> bool:
        """Check if we can book more shifts today."""
        return self.daily_count < daily_limit

class ShiftBooking:
    """Production-grade shift booking with idempotency and resilience."""
    
    def __init__(self, driver, state_file: str = "booking_state.json"):
        self.driver = driver
        self.wait = WebDriverWait(driver, 3)  # Ultra-fast waits for instant booking
        self.state = ShiftBookingState(state_file)
        self.fast_booking_mode = True  # Enable aggressive booking optimizations
        
    def click_with_retry(self, element_or_selector, max_retries: int = 2, backoff_factor: float = 1.2) -> bool:
        """Click with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                if isinstance(element_or_selector, str):
                    element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, element_or_selector)))
                else:
                    element = element_or_selector
                    
                # Scroll into view and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                element.click()
                return True
                
            except (TimeoutException, NoSuchElementException) as e:
                wait_time = backoff_factor ** attempt
                logger.warning(f"Click attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    
        logger.error(f"Failed to click after {max_retries} attempts")
        return False
    
    def discover_available_slots(self, correlation_id: str = None) -> List[ShiftSlot]:
        """Discover available shift slots with structured logging."""
        log_extra = {'correlation_id': correlation_id} if correlation_id else {}
        logger.info("🔎 Starting shift slot discovery", extra=log_extra)
        
        try:
            # Wait for job cards to load
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='JobCard'], .job-card")))
        except TimeoutException:
            logger.warning("No job cards found on page", extra=log_extra)
            return []
        
        # Try multiple selectors for job cards
        card_selectors = [
            "div[data-test-id='JobCard']",
            ".job-card",
            "div[class*='job'][class*='card']",
            "[data-testid*='job']"
        ]
        
        cards = []
        for selector in card_selectors:
            cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if cards:
                logger.debug(f"Found {len(cards)} cards using selector: {selector}", extra=log_extra)
                break
        
        if not cards:
            logger.warning("No job cards found with any selector", extra=log_extra)
            return []
        
        slots = []
        for idx, card in enumerate(cards):
            try:
                slot = self._extract_slot_info(card, idx)
                if slot and not self.state.is_already_booked(slot.job_id):
                    slots.append(slot)
                elif slot:
                    logger.debug(f"Skipping already booked slot: {slot.job_id}", extra=log_extra)
            except Exception as e:
                logger.debug(f"Failed to extract slot info from card {idx}: {e}", extra=log_extra)
        
        logger.info(f"✅ Discovered {len(slots)} available slots (excluding already booked)", extra=log_extra)
        return slots
    
    def _extract_slot_info(self, card, idx: int) -> Optional[ShiftSlot]:
        """Extract shift information from a job card element."""
        try:
            # Multiple selectors for robustness
            title_selectors = ["strong", ".job-title", "h3", "h4", "[data-testid*='title']"]
            location_selectors = [".location", "[data-testid*='location']", ".job-location"]
            schedule_selectors = [".schedule", "[data-testid*='schedule']", ".time", ".shift-time"]
            pay_selectors = [".pay", ".rate", "[data-testid*='pay']", ".wage"]
            
            title = self._find_text_by_selectors(card, title_selectors) or f"Shift {idx + 1}"
            location = self._find_text_by_selectors(card, location_selectors) or "Location TBD"
            schedule = self._find_text_by_selectors(card, schedule_selectors) or "Schedule TBD"
            pay_rate = self._find_text_by_selectors(card, pay_selectors)
            
            # Try to get job ID from various attributes
            job_id = (card.get_attribute("data-job-id") or 
                     card.get_attribute("data-testid") or 
                     card.get_attribute("id") or 
                     f"shift_{idx}_{int(time.time())}")
            
            return ShiftSlot(
                job_id=job_id,
                title=title,
                location=location,
                schedule=schedule,
                card_index=idx,
                pay_rate=pay_rate
            )
        except Exception as e:
            logger.debug(f"Failed to extract slot info: {e}")
            return None
    
    def _find_text_by_selectors(self, parent, selectors: List[str]) -> Optional[str]:
        """Try multiple selectors to find text content."""
        for selector in selectors:
            try:
                element = parent.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
            except NoSuchElementException:
                continue
        return None
    
    def book_slot(self, slot: ShiftSlot, correlation_id: str = None) -> bool:
        """Book a specific shift slot with retry logic and enhanced error handling."""
        log_extra = {'correlation_id': correlation_id, 'job_id': slot.job_id} if correlation_id else {'job_id': slot.job_id}
        logger.info(f"▶️ Attempting to book slot: {slot.title} @ {slot.location}", extra=log_extra)
        
        try:
            # Take a screenshot before starting
            try:
                self.driver.get_screenshot_as_png()
                logger.debug("📸 Took initial screenshot", extra=log_extra)
            except Exception as e:
                logger.warning(f"Failed to take initial screenshot: {e}", extra=log_extra)
            
            # Find job cards with better selectors and error handling
            card_selectors = [
                "div[data-test-id='JobCard']",
                ".job-card", 
                "[data-testid*='JobCard']",
                "[data-testid*='job-card']",
                "div[class*='JobCard']",
                "div[class*='job-card']",
                "[role='listitem']"
            ]
            
            cards = []
            for selector in card_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"🔍 Found {len(elements)} job cards with selector: {selector}", extra=log_extra)
                        cards = elements
                        break
                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed: {e}", extra=log_extra)
            
            if not cards:
                logger.error("❌ No job cards found on the page", extra=log_extra)
                return False
                
            if slot.card_index >= len(cards):
                logger.error(f"❌ Card index {slot.card_index} out of range (found {len(cards)} cards)", extra=log_extra)
                return False
            
            # Click the job card with multiple methods
            card = cards[slot.card_index]
            logger.info(f"🖱️ Attempting to click job card {slot.card_index + 1} of {len(cards)}", extra=log_extra)
            
            click_methods = [
                lambda: card.click(),
                lambda: (self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'}});", card),
                        time.sleep(1),
                        card.click()),
                lambda: self.driver.execute_script("arguments[0].click();", card),
                lambda: ActionChains(self.driver).move_to_element(card).click().perform()
            ]
            
            card_clicked = False
            for i, click_method in enumerate(click_methods):
                try:
                    click_method()
                    logger.info(f"✅ Card clicked using method {i+1}", extra=log_extra)
                    card_clicked = True
                    break
                except Exception as e:
                    logger.warning(f"Click method {i+1} failed: {e}", extra=log_extra)
            
            if not card_clicked:
                logger.error("❌ All card click methods failed", extra=log_extra)
                return False
            
            # Ultra-fast booking mode - minimal stabilization time
            if self.fast_booking_mode:
                time.sleep(0.5)  # Minimal wait for instant booking
            else:
                time.sleep(2)  # Standard wait
            
            # Quick URL check for fast mode
            if self.fast_booking_mode:
                try:
                    current_url = self.driver.current_url
                    logger.debug(f"Current URL after card click: {current_url}", extra=log_extra)
                except Exception:
                    pass  # Skip URL check in fast mode if it fails
            
            # Handle shift selection dropdown with ultra-fast processing
            logger.info("⚡ Fast shift dropdown handling", extra=log_extra)
            try:
                dropdown_result = self._handle_shift_dropdown_fast(log_extra)
                if dropdown_result is False:
                    logger.warning("⚠️ Fast shift dropdown failed, using standard method...", extra=log_extra)
                    self._handle_shift_dropdown(log_extra)
            except Exception as e:
                logger.debug(f"Fast dropdown handling failed: {e}", extra=log_extra)
                # Continue without shift selection for speed
            
            # Minimal modal settle time for instant booking
            if not self.fast_booking_mode:
                time.sleep(1)
            
            # Click Apply button with enhanced selectors based on current Amazon structure
            apply_selectors = [
                # Primary apply button selectors
                "button[data-test-id='jobDetailApplyButtonDesktop']",
                "button[data-testid*='apply']",
                "button[data-test-id*='apply']",
                
                # Blue apply button (Amazon's primary CTA color)
                "button.hvh-careers-emotion-*[style*='background-color']:contains('Apply')",
                "button[class*='hvh-careers-emotion'][style*='rgb']:contains('Apply')",
                
                # Text-based selectors
                "button:contains('Apply')",
                "button:contains('Apply Now')",
                "button:contains('APPLY')",
                
                # Class and attribute-based
                ".apply-button",
                "button[class*='apply']",
                "button[aria-label*='Apply']",
                
                # Generic button in job detail area
                "[data-test-component*='JobDetail'] button:contains('Apply')",
                ".job-detail button:contains('Apply')",
                
                # Fallback to any prominent button after modal appears
                "button[class*='primary']",
                "button[class*='cta']",
                "button[style*='background-color']:not([style*='transparent'])",
                
                # Last resort - any button that might be apply button
                "div[class*='job'] button:contains('Apply')",
                "[role='main'] button:contains('Apply')"
            ]
            
            # Wait for apply button to be available
            apply_clicked = False
            max_apply_attempts = 3
            
            for attempt in range(max_apply_attempts):
                logger.info(f"🔍 Looking for apply button (attempt {attempt + 1}/{max_apply_attempts})", extra=log_extra)
                
                for selector in apply_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if not elements:
                            continue
                            
                        for btn in elements:
                            try:
                                if btn.is_displayed() and btn.is_enabled():
                                    # Scroll button into view
                                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn)
                                    time.sleep(0.5)
                                    
                                    btn.click()
                                    logger.info(f"✅ Clicked apply button: {selector}", extra=log_extra)
                                    apply_clicked = True
                                    break
                            except Exception as btn_e:
                                logger.debug(f"Error clicking button with selector '{selector}': {btn_e}", extra=log_extra)
                                continue
                                
                        if apply_clicked:
                            break
                            
                    except Exception as e:
                        logger.debug(f"Error with apply selector '{selector}': {e}", extra=log_extra)
                        continue
                
                if apply_clicked:
                    break
                    
                # Wait between attempts
                if attempt < max_apply_attempts - 1:
                    logger.info(f"⏳ Apply button not found, waiting before retry...", extra=log_extra)
                    time.sleep(2)
            
            if not apply_clicked:
                logger.error("❌ Failed to click any apply button", extra=log_extra)
                return False
            
            time.sleep(3)
            
            # Handle Next/Submit buttons
            next_button_texts = ["Next", "Create Application", "Continue", "Submit", "Confirm"]
            for text in next_button_texts:
                try:
                    xpath = f"//button[contains(translate(., 'NEXT', 'next'), '{text.lower()}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for btn in elements:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            logger.info(f"✅ Clicked '{text}' button", extra=log_extra)
                            time.sleep(2)
                            break
                except Exception as e:
                    logger.debug(f"Error with next button '{text}': {e}", extra=log_extra)
            
            # Mark as successfully booked
            self.state.mark_as_booked(slot.job_id)
            logger.info("✅ Booking flow completed successfully", extra=log_extra)
            return True
            
        except Exception as e:
            logger.error(f"❌ Booking failed with exception: {e}", extra=log_extra)
            return False
    
    def _handle_shift_dropdown(self, log_extra: dict) -> bool:
        """Handle shift selection dropdown that opens a modal/sidebar in Amazon's hiring portal."""
        try:
            # Step 1: Look for the "Work shift" dropdown with "Select one" text
            dropdown_selectors = [
                '.jobDetailScheduleDropdown.hvh-careers-emotion-1uzwmf0',  # Primary selector from XML
                'div[class*="jobDetailScheduleDropdown"]',                   # Fallback with partial class
                '.hvh-careers-emotion-1uzwmf0[tabindex="0"]',               # Fallback with tabindex
                'div:contains("Select one")',                               # Text-based fallback
                '[data-test-component="StencilReactRow"]:contains("Select one")', # Component-based
            ]
            
            dropdown_element = None
            for selector in dropdown_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Check if it contains "Select one" text
                            if "select one" in element.text.lower() or "work shift" in element.get_attribute("class"):
                                dropdown_element = element
                                logger.info(f"✅ Found shift dropdown: {selector}", extra=log_extra)
                                break
                    if dropdown_element:
                        break
                except Exception as e:
                    logger.debug(f"Dropdown selector {selector} failed: {e}", extra=log_extra)
                    continue
            
            if not dropdown_element:
                logger.info("No shift dropdown found, checking for existing modal", extra=log_extra)
                # Maybe modal is already open, skip to step 2
            else:
                # Click the dropdown to open the modal
                logger.info("🖱️ Clicking shift dropdown to open modal", extra=log_extra)
                try:
                    dropdown_element.click()
                    time.sleep(1)  # Wait for modal to appear
                except Exception as e:
                    logger.warning(f"Failed to click dropdown: {e}", extra=log_extra)
            
            # Step 2: Wait for the shift selection modal/sidebar to appear
            modal_selectors = [
                '[data-test-component="StencilFlyoutBody"]',  # Primary selector from XML
                '.hvh-careers-emotion-wuykcp',                # Specific class from XML
                '[data-test-component*="StencilFlyout"]',     # Broader flyout selector
                'div:contains("Select work shift")',          # Title-based selector
                'div:contains("Showing 1 of 1 shift")',      # Content-based selector
            ]
            
            modal_found = False
            for selector in modal_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.info(f"✅ Found shift selection modal: {selector}", extra=log_extra)
                    modal_found = True
                    break
                except TimeoutException:
                    continue
                    
            if not modal_found:
                logger.info("No shift selection modal found after dropdown click, proceeding without shift selection", extra=log_extra)
                return True
            
            # Step 3: Look for shift cards in the modal (based on XML structure)
            shift_card_selectors = [
                # Primary selector: StencilReactCard with role="button" (from XML)
                '[data-test-component="StencilReactCard"][role="button"]',
                '[data-test-component="StencilReactCard"][tabindex="0"]',
                
                # Backup with class selectors from XML
                '.hvh-careers-emotion-h6jfyp[role="button"]',
                '.focusableItem.hvh-careers-emotion-h6jfyp',
                
                # Text-based selectors for the specific shift from XML
                'div:contains("Flexible Shifts (19h)")',
                'div:contains("Featured")',
                'div:contains("$20.00")',
                
                # Generic card selectors in the flyout
                '[data-test-component="StencilFlyoutBody"] [role="button"]',
                '[data-test-component="StencilFlyoutBody"] [tabindex="0"]',
                '.hvh-careers-emotion-wuykcp [role="button"]',
                
                # Fallback to any clickable element with shift content
                '[data-test-component="StencilFlyoutBody"] div:contains("Shift:")',
                '[data-test-component="StencilFlyoutBody"] div:contains("Duration:")',
                
                # Last resort - any clickable element in the modal
                '[data-test-component="StencilFlyoutBody"] div[tabindex="0"]',
                '[data-test-component="StencilFlyoutBody"] .pointer',
                
                # Alternative class-based selectors
                '.scheduleFlyoutSelection.pointer',
                '.scheduleDetails',
            ]
            
            # Find the first available shift card/option
            shift_element = None
            for selector in shift_card_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"✅ Found {len(elements)} shift element(s): {selector}", extra=log_extra)
                        
                        # Get the first visible and clickable element
                        for element in elements:
                            try:
                                if element.is_displayed() and element.is_enabled():
                                    text = element.text.strip()
                                    logger.info(f"📋 Evaluating shift element: '{text[:100]}...'", extra=log_extra)
                                    
                                    # Accept any visible clickable element in the modal
                                    # Priority: elements with shift content, but accept any clickable element
                                    shift_element = element
                                    logger.info(f"✅ Selected shift element: '{text[:50]}...'", extra=log_extra)
                                    break
                            except Exception as elem_e:
                                logger.debug(f"Error evaluating element: {elem_e}", extra=log_extra)
                                continue
                                
                        if shift_element:
                            break
                                
                except Exception as e:
                    logger.debug(f"Shift selector {selector} failed: {e}", extra=log_extra)
                    continue
            
            if not shift_element:
                logger.info("No shift selection elements found, proceeding without selection", extra=log_extra)
                return True  # Not an error if no shift selection exists
            
            # Click the shift card/element 
            try:
                element_text = shift_element.text.strip() if hasattr(shift_element, 'text') else "N/A"
                logger.info(f"📋 Attempting to select shift card: '{element_text[:100]}...'", extra=log_extra)
                
                # Enhanced click methods for shift card selection
                click_methods = [
                    # Method 1: Direct click
                    lambda: shift_element.click(),
                    
                    # Method 2: Scroll into view and click
                    lambda: (self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", shift_element),
                            time.sleep(0.5),
                            shift_element.click()),
                    
                    # Method 3: JavaScript click (most reliable for Amazon)
                    lambda: self.driver.execute_script("arguments[0].click();", shift_element),
                    
                    # Method 4: ActionChains click with hover
                    lambda: (ActionChains(self.driver).move_to_element(shift_element).pause(0.3).click().perform()),
                    
                    # Method 5: Focus and Enter key
                    lambda: (shift_element.send_keys(""),  # Focus element
                            time.sleep(0.2),
                            shift_element.send_keys("\n")),
                    
                    # Method 6: Focus and Space key
                    lambda: (shift_element.send_keys(""),  # Focus element  
                            time.sleep(0.2),
                            shift_element.send_keys(" ")),
                ]
                
                click_success = False
                for i, click_method in enumerate(click_methods):
                    try:
                        click_method()
                        logger.info(f"✅ Clicked shift card using method {i+1}", extra=log_extra)
                        time.sleep(1.5)  # Wait for selection to take effect and modal to update
                        
                        # Check if modal closed or selection was successful
                        try:
                            # Try to find the modal again - if it's gone, selection likely succeeded
                            modal_still_open = self.driver.find_elements(By.CSS_SELECTOR, '[data-test-component="StencilFlyoutBody"]')
                            if not modal_still_open:
                                logger.info("✅ Modal closed - shift selection successful", extra=log_extra)
                                click_success = True
                                break
                            else:
                                logger.debug(f"Modal still open after method {i+1}, trying next method", extra=log_extra)
                        except Exception:
                            # If we can't check, assume success and continue
                            logger.info("✅ Shift selection completed (unable to verify modal state)", extra=log_extra)
                            click_success = True
                            break
                            
                    except Exception as e:
                        logger.debug(f"Click method {i+1} failed: {e}", extra=log_extra)
                        continue
                
                if not click_success:
                    logger.warning("⚠️ All shift selection methods completed, proceeding (may have succeeded)", extra=log_extra)
                
                return True  # Always return True since selection issues aren't critical for booking flow
                    
            except Exception as e:
                logger.error(f"Error interacting with shift dropdown: {e}", extra=log_extra)
                return False
            
        except Exception as e:
            logger.error(f"Error handling shift selection: {e}", extra=log_extra)
            return False

    def _handle_shift_dropdown_fast(self, log_extra: dict) -> bool:
        """Ultra-fast shift dropdown handling for instant booking."""
        try:
            # Quick check for dropdown - skip if not immediately visible
            dropdown_selectors = [
                '.jobDetailScheduleDropdown.hvh-careers-emotion-1uzwmf0',
                'div:contains("Select one")'
            ]
            
            dropdown_element = None
            for selector in dropdown_selectors[:1]:  # Only check first selector for speed
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        dropdown_element = elements[0]
                        break
                except Exception:
                    continue
            
            if not dropdown_element:
                logger.debug("⚡ No shift dropdown found in fast mode, skipping", extra=log_extra)
                return True
            
            # Quick dropdown click
            try:
                dropdown_element.click()
                time.sleep(0.3)  # Minimal wait
            except Exception:
                return False
            
            # Quick shift selection - grab first available option
            shift_selectors = [
                '[data-test-component="StencilReactCard"][role="button"]',
                '[data-test-component="StencilFlyoutBody"] [role="button"]'
            ]
            
            for selector in shift_selectors[:1]:  # Only try first selector for speed
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        elements[0].click()
                        logger.info("⚡ Fast shift selection completed", extra=log_extra)
                        time.sleep(0.2)  # Minimal wait
                        return True
                except Exception:
                    continue
            
            return True  # Return success even if no selection for speed
            
        except Exception as e:
            logger.debug(f"Fast dropdown handling error: {e}", extra=log_extra)
            return False
    
    def get_booking_summary(self) -> dict:
        """Get current booking state summary."""
        return {
            'daily_count': self.state.daily_count,
            'booked_today': list(self.state.booked_today),
            'last_reset_date': self.state.last_reset_date
        }