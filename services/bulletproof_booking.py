import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BulletproofBookingService:
    """Ultra-robust booking service with comprehensive error handling and retry mechanisms"""
    
    def __init__(self, driver, notifier=None):
        self.driver = driver
        self.notifier = notifier
        self.max_booking_retries = 5
        self.max_click_retries = 3
        self.booking_success_count = 0
        self.booking_failure_count = 0
        
    def attempt_bulletproof_booking(self, job_data: Dict[str, Any], correlation_id: str) -> bool:
        """Attempt booking with comprehensive error handling and multiple strategies"""
        
        job_title = job_data.get('title', 'Unknown Job')
        job_location = job_data.get('location', 'Unknown Location')
        
        logger.info(f"🎯 Starting bulletproof booking for: {job_title} at {job_location}")
        
        # Send booking attempt notification
        if self.notifier:
            try:
                self.notifier.notify_instant_booking_attempt(job_data)
            except Exception as e:
                logger.warning(f"⚠️ Booking attempt notification failed: {e}")
        
        for attempt in range(self.max_booking_retries):
            try:
                logger.info(f"🔄 Booking attempt {attempt + 1}/{self.max_booking_retries} for {job_title}")
                
                # Step 1: Find and click job card with multiple strategies
                card_clicked = self._click_job_card_bulletproof(job_data, attempt)
                if not card_clicked:
                    logger.warning(f"❌ Failed to click job card on attempt {attempt + 1}")
                    if attempt < self.max_booking_retries - 1:
                        self._recovery_delay(attempt)
                        continue
                    return False
                
                # Step 2: Handle any modals or dropdowns
                self._handle_booking_modals_bulletproof()
                
                # Step 3: Click apply button with multiple strategies
                apply_clicked = self._click_apply_button_bulletproof(attempt)
                if not apply_clicked:
                    logger.warning(f"❌ Failed to click apply button on attempt {attempt + 1}")
                    if attempt < self.max_booking_retries - 1:
                        self._recovery_delay(attempt)
                        continue
                    return False
                
                # Step 4: Handle application flow
                application_completed = self._complete_application_flow_bulletproof(attempt)
                if not application_completed:
                    logger.warning(f"❌ Failed to complete application on attempt {attempt + 1}")
                    if attempt < self.max_booking_retries - 1:
                        self._recovery_delay(attempt)
                        continue
                    return False
                
                # Success!
                self.booking_success_count += 1
                logger.info(f"🎉 BULLETPROOF BOOKING SUCCESS! {job_title} at {job_location}")
                
                # Send success notification
                if self.notifier:
                    try:
                        booking_details = {
                            'title': job_title,
                            'location': job_location,
                            'schedule': job_data.get('schedule', 'TBD'),
                            'pay_rate': job_data.get('pay_rate', 'TBD'),
                            'discovered_at': datetime.now().strftime('%H:%M:%S'),
                            'booking_id': correlation_id,
                            'attempt_number': attempt + 1
                        }
                        self.notifier.notify_instant_booking_success(
                            shift_number=self.booking_success_count,
                            **booking_details,
                            correlation_id=correlation_id
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ Success notification failed: {e}")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Booking attempt {attempt + 1} failed with error: {e}")
                if attempt < self.max_booking_retries - 1:
                    self._recovery_delay(attempt)
                    continue
        
        # All attempts failed
        self.booking_failure_count += 1
        logger.error(f"❌ BOOKING FAILED after {self.max_booking_retries} attempts: {job_title}")
        
        # Send failure notification
        if self.notifier:
            try:
                failure_message = f"❌ **BOOKING FAILED**\n🎯 Job: {job_title}\n📍 Location: {job_location}\n🔄 Attempts: {self.max_booking_retries}\n⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
                self.notifier.send(failure_message, urgent=True)
            except Exception as e:
                logger.warning(f"⚠️ Failure notification failed: {e}")
        
        return False
    
    def _click_job_card_bulletproof(self, job_data: Dict[str, Any], base_attempt: int) -> bool:
        """Click job card with multiple strategies and fallbacks"""
        
        # Multiple selector strategies
        card_selectors = [
            'div[data-test-id="JobCard"]',
            '[data-test-component="StencilReactCard"][data-test-id="JobCard"]',
            '.jobCardItem',
            '[role="link"][data-test-id="JobCard"]',
            'div.pointer.focusableItem.jobCardItem'
        ]
        
        click_strategies = [
            'direct_click',
            'javascript_click', 
            'action_chains_click',
            'coordinate_click'
        ]
        
        for selector in card_selectors:
            try:
                elements = self.driver.find_elements('css selector', selector)
                if not elements:
                    continue
                
                logger.debug(f"🔍 Found {len(elements)} job cards with selector: {selector}")
                
                # Try to find the specific job card
                target_element = None
                for element in elements:
                    try:
                        element_text = element.text.lower()
                        job_title = job_data.get('title', '').lower()
                        if job_title and job_title in element_text:
                            target_element = element
                            break
                    except:
                        continue
                
                # If specific job not found, use first available
                if not target_element and elements:
                    target_element = elements[0]
                
                if target_element:
                    # Try different click strategies
                    for strategy in click_strategies:
                        try:
                            success = self._execute_click_strategy(target_element, strategy)
                            if success:
                                logger.info(f"✅ Job card clicked using {strategy} with selector {selector}")
                                return True
                        except Exception as e:
                            logger.debug(f"⚠️ Click strategy {strategy} failed: {e}")
                            continue
            
            except Exception as e:
                logger.debug(f"⚠️ Selector {selector} failed: {e}")
                continue
        
        return False
    
    def _execute_click_strategy(self, element, strategy: str) -> bool:
        """Execute specific click strategy"""
        try:
            if strategy == 'direct_click':
                element.click()
                time.sleep(1)
                return True
                
            elif strategy == 'javascript_click':
                self.driver.execute_script("arguments[0].click();", element)
                time.sleep(1)
                return True
                
            elif strategy == 'action_chains_click':
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).move_to_element(element).click().perform()
                time.sleep(1)
                return True
                
            elif strategy == 'coordinate_click':
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).move_to_element(element).click().perform()
                time.sleep(1)
                return True
                
        except Exception as e:
            logger.debug(f"❌ Click strategy {strategy} failed: {e}")
            return False
        
        return False
    
    def _handle_booking_modals_bulletproof(self):
        """Handle any modals, dropdowns, or overlays that might appear"""
        try:
            # Wait for page to stabilize
            time.sleep(1)
            
            # Check for and handle shift selection dropdown
            dropdown_selectors = [
                '.jobDetailScheduleDropdown',
                'div:contains("Select one")',
                '[data-test-component="StencilReactSelect"]'
            ]
            
            for selector in dropdown_selectors:
                try:
                    elements = self.driver.find_elements('css selector', selector)
                    if elements and elements[0].is_displayed():
                        logger.info("🔧 Handling shift selection dropdown")
                        elements[0].click()
                        time.sleep(0.5)
                        
                        # Select first available option
                        option_selectors = [
                            '[data-test-component="StencilReactCard"][role="button"]',
                            '[role="button"]:contains("shift")',
                            '.dropdown-option'
                        ]
                        
                        for option_selector in option_selectors:
                            try:
                                options = self.driver.find_elements('css selector', option_selector)
                                if options and options[0].is_displayed():
                                    options[0].click()
                                    logger.info("✅ Shift selection completed")
                                    time.sleep(0.5)
                                    break
                            except:
                                continue
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"⚠️ Modal handling error (non-critical): {e}")
    
    def _click_apply_button_bulletproof(self, base_attempt: int) -> bool:
        """Click apply button with multiple strategies"""
        
        apply_selectors = [
            'button[data-test-id="jobDetailApplyButtonDesktop"]',
            'button:contains("Apply")',
            '[data-test-id*="apply"]',
            'button.apply-button',
            '.apply-btn'
        ]
        
        for attempt in range(self.max_click_retries):
            for selector in apply_selectors:
                try:
                    elements = self.driver.find_elements('css selector', selector)
                    if elements:
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                # Try multiple click strategies
                                for strategy in ['direct_click', 'javascript_click']:
                                    try:
                                        if strategy == 'direct_click':
                                            element.click()
                                        else:
                                            self.driver.execute_script("arguments[0].click();", element)
                                        
                                        logger.info(f"✅ Apply button clicked using {strategy}")
                                        time.sleep(2)
                                        return True
                                    except:
                                        continue
                except:
                    continue
            
            if attempt < self.max_click_retries - 1:
                time.sleep(2)
        
        return False
    
    def _complete_application_flow_bulletproof(self, base_attempt: int) -> bool:
        """Complete the application flow with multiple strategies"""
        
        # Handle various application flow buttons
        flow_button_texts = [
            "Next",
            "Continue", 
            "Create Application",
            "Submit",
            "Confirm",
            "Apply Now"
        ]
        
        max_flow_attempts = 5
        
        for flow_attempt in range(max_flow_attempts):
            try:
                # Check if we've completed the flow
                if self._check_booking_completion():
                    logger.info("✅ Booking flow completed successfully")
                    return True
                
                # Try to click next flow button
                button_clicked = False
                for button_text in flow_button_texts:
                    try:
                        # Multiple selector strategies for each button text
                        selectors = [
                            f'button:contains("{button_text}")',
                            f'//button[contains(text(), "{button_text}")]',
                            f'[data-test-id*="{button_text.lower()}"]'
                        ]
                        
                        for selector in selectors:
                            try:
                                if selector.startswith('//'):
                                    elements = self.driver.find_elements('xpath', selector)
                                else:
                                    elements = self.driver.find_elements('css selector', selector)
                                
                                if elements:
                                    for element in elements:
                                        if element.is_displayed() and element.is_enabled():
                                            element.click()
                                            logger.info(f"✅ Clicked '{button_text}' button")
                                            time.sleep(2)
                                            button_clicked = True
                                            break
                                
                                if button_clicked:
                                    break
                            except:
                                continue
                        
                        if button_clicked:
                            break
                    except:
                        continue
                
                if not button_clicked:
                    # Check if we're done anyway
                    if self._check_booking_completion():
                        return True
                    
                    if flow_attempt < max_flow_attempts - 1:
                        time.sleep(2)
                        continue
                
            except Exception as e:
                logger.debug(f"⚠️ Application flow error: {e}")
                if flow_attempt < max_flow_attempts - 1:
                    time.sleep(2)
                    continue
        
        # Final completion check
        return self._check_booking_completion()
    
    def _check_booking_completion(self) -> bool:
        """Check if booking has been completed successfully"""
        try:
            # Check for success indicators
            success_indicators = [
                'div:contains("Application submitted")',
                'div:contains("Thank you")', 
                'div:contains("Success")',
                'div:contains("Confirmation")',
                '.success-message',
                '.confirmation-message'
            ]
            
            for indicator in success_indicators:
                try:
                    elements = self.driver.find_elements('css selector', indicator)
                    if elements and elements[0].is_displayed():
                        logger.debug(f"✅ Found completion indicator: {indicator}")
                        return True
                except:
                    continue
            
            # Check URL for completion patterns
            current_url = self.driver.current_url
            completion_url_patterns = [
                'confirmation',
                'success',
                'thank-you',
                'application-complete'
            ]
            
            for pattern in completion_url_patterns:
                if pattern in current_url.lower():
                    logger.debug(f"✅ Found completion URL pattern: {pattern}")
                    return True
            
        except Exception as e:
            logger.debug(f"⚠️ Completion check error: {e}")
        
        return False
    
    def _recovery_delay(self, attempt: int):
        """Progressive delay for recovery between attempts"""
        delay = min(2 ** attempt, 10)  # Exponential backoff, max 10 seconds
        logger.info(f"⏳ Recovery delay: {delay}s before next booking attempt")
        time.sleep(delay)
    
    def get_booking_stats(self) -> Dict[str, int]:
        """Get current booking statistics"""
        return {
            'success_count': self.booking_success_count,
            'failure_count': self.booking_failure_count,
            'total_attempts': self.booking_success_count + self.booking_failure_count,
            'success_rate': (self.booking_success_count / max(1, self.booking_success_count + self.booking_failure_count)) * 100
        }