# Amazon-specific page objects following SeleniumBase best practices
from seleniumbase import BaseCase
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AmazonConsentPage:
    """Page object for handling Amazon consent/cookie banners"""
    
    # Updated selectors to handle the specific blue "I consent" button structure
    CONSENT_BTN = 'button[data-test-id="consentBtn"]'
    CONSENT_FALLBACK = 'button:contains("I consent")'
    # Specific selector for the blue button from the HTML structure
    BLUE_CONSENT_BTN = 'button[data-test-component="StencilReactButton"] div[data-test-component="StencilReactRow"]:contains("I consent")'
    BLUE_CONSENT_BTN_ALT = 'div[data-test-component="StencilReactRow"] button[data-test-component="StencilReactButton"]:contains("I consent")'
    ACCEPT_ALL_BTN = 'button:contains("Accept All")'
    GENERIC_CONSENT = 'button[type="button"]:contains("consent")'
    
    def __init__(self):
        self.consent_handled = False  # Track if consent was already handled
    
    def handle_consent(self, sb: BaseCase) -> bool:
        """Handle consent with improved selectors for the blue button"""
        logger.info("🍪 Checking for consent buttons...")
        
        # Skip if consent was already handled
        if self.consent_handled:
            logger.info("ℹ️ Consent already handled, skipping...")
            return True
        
        # List of selectors to try in order of preference
        consent_selectors = [
            self.CONSENT_BTN,
            self.BLUE_CONSENT_BTN,
            self.BLUE_CONSENT_BTN_ALT,
            self.CONSENT_FALLBACK,
            self.GENERIC_CONSENT,
            self.ACCEPT_ALL_BTN,
            # Additional selectors for the specific button structure
            'button[data-test-component="StencilReactButton"]',
            'div[class*="css-hxw9t3"] button[type="button"]:contains("I consent")',
            'button[class*="e4s17lp0"]:contains("I consent")',
            # More generic fallbacks
            'button:contains("consent")',
            'button:contains("Accept")',
            'button[class*="consent"]',
            'button[id*="consent"]'
        ]
        
        for i, selector in enumerate(consent_selectors):
            try:
                if sb.is_element_visible(selector):
                    logger.info(f"✅ Found consent button with selector {i+1}: {selector}")
                    
                    # Scroll to element and click
                    sb.scroll_to_element(selector)
                    sb.sleep(0.5)
                    
                    # Try normal click first
                    try:
                        sb.click(selector)
                        logger.info(f"✅ Consent button clicked successfully with selector: {selector}")
                    except Exception as click_error:
                        logger.warning(f"Normal click failed, trying JS click: {click_error}")
                        sb.js_click(selector)
                        logger.info(f"✅ Consent button JS clicked successfully with selector: {selector}")
                    
                    sb.sleep(2)
                    self.consent_handled = True
                    return True
                    
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        logger.info("ℹ️ No consent buttons found")
        self.consent_handled = True  # Mark as handled even if no buttons found
        return True

    def handle_bottom_consent(self, sb: BaseCase) -> bool:
        """Specifically handle the blue consent button at the bottom of the page"""
        logger.info("🔍 Checking for bottom consent button...")
        
        # Scroll to bottom to ensure the button is visible
        sb.scroll_to_bottom()
        sb.sleep(1)
        
        # Specific selectors for the blue button structure
        bottom_consent_selectors = [
            'button[data-test-component="StencilReactButton"] div:contains("I consent")',
            'div[data-test-component="StencilReactRow"] button:contains("I consent")',
            'button[class*="e4s17lp0"] div:contains("I consent")',
            'div[class*="css-hxw9t3"] button:contains("I consent")',
            'button[type="button"]:contains("I consent")',
        ]
        
        for selector in bottom_consent_selectors:
            try:
                if sb.is_element_visible(selector):
                    logger.info(f"✅ Found bottom consent button: {selector}")
                    sb.scroll_to_element(selector)
                    sb.sleep(0.5)
                    
                    try:
                        sb.click(selector)
                        logger.info("✅ Bottom consent button clicked successfully")
                    except Exception:
                        sb.js_click(selector)
                        logger.info("✅ Bottom consent button JS clicked successfully")
                    
                    sb.sleep(2)
                    return True
                    
            except Exception as e:
                logger.debug(f"Bottom consent selector {selector} failed: {e}")
                continue
        
        logger.info("ℹ️ No bottom consent button found")
        return True

class AmazonLoginPage:
    """Page object for Amazon login flow"""
    
    # Best working selectors
    EMAIL_INPUT = 'input[data-test-id="input-test-id-login"]'
    CONTINUE_BTN = 'button[data-test-id="button-continue"]'
    PIN_INPUT = 'input[data-test-id="input-test-id-pin"]'
    OTP_INPUT = 'input[data-test-id="input-test-id-confirmOtp"]'
    SUBMIT_BTN = 'button[data-test-id="button-submit"]'
    
    # Navigation selectors
    SIDE_PANEL_OPEN = 'div[data-test-id="sidePanelOpenButton"]'
    SIGN_IN_BTN = 'button[data-test-id="sidePanelSignInButton"] > div > div'
    CLOSE_MODAL = 'svg[data-test-id="sortCloseModal"]'
    
    def navigate_to_login(self, sb: BaseCase) -> bool:
        """Navigate to login page with robust error handling"""
        logger.info("🔐 Navigating to login...")
        
        # Close modal if present
        if sb.is_element_visible(self.CLOSE_MODAL):
            sb.click(self.CLOSE_MODAL)
            sb.sleep(2)
        
        # Open side panel
        if sb.is_element_visible(self.SIDE_PANEL_OPEN):
            sb.click(self.SIDE_PANEL_OPEN)
            sb.sleep(2)
        
        # Click sign in
        if sb.is_element_visible(self.SIGN_IN_BTN):
            sb.click(self.SIGN_IN_BTN)
            sb.sleep(3)
            return True
        
        logger.error("❌ Could not navigate to login")
        return False
    
    def enter_email(self, sb: BaseCase, email: str) -> bool:
        """Enter email with robust error handling"""
        logger.info("📧 Entering email...")
        
        # Multiple selectors for email input
        login_selectors = [
            'input[data-test-id="input-test-id-login"]',
            'input[id="login"]',
            'input[name="login EmailId"]',
            'input[aria-label="Email or mobile number"]'
        ]
        
        email_input_found = False
        for selector in login_selectors:
            if sb.is_element_visible(selector):
                logger.info(f"📧 Found email input field: {selector}")
                
                try:
                    sb.wait_for_element_clickable(selector, timeout=10)
                    sb.scroll_to_element(selector)
                    sb.sleep(1)
                    
                    sb.click(selector)
                    sb.sleep(1)
                    
                    sb.clear(selector)
                    sb.sleep(0.5)
                    
                    try:
                        sb.type(selector, email)
                    except Exception as e:
                        logger.warning(f"⚠️ Normal typing failed, using JavaScript: {e}")
                        sb.execute_script(f"document.querySelector('{selector}').value = '{email}';")
                        sb.execute_script(f"document.querySelector('{selector}').dispatchEvent(new Event('input', {{bubbles: true}}));")
                    
                    sb.sleep(2)
                    email_input_found = True
                    break
                    
                except Exception as e:
                    logger.error(f"❌ Failed to interact with {selector}: {e}")
                    continue
        
        if not email_input_found:
            logger.error("❌ Email input field not found or not interactable")
            return False
        
        # Click Continue button for email
        continue_selectors = [
            'button[data-test-id="button-continue"]',
            'button:contains("Continue")',
            'button[type="button"]:contains("Continue")',
            'input[type="submit"]'
        ]
        
        return self.click_continue_button(sb, continue_selectors, "email page")
    
    def enter_pin(self, sb: BaseCase, pin: str) -> bool:
        """Enter PIN if required with robust error handling"""
        sb.sleep(3)
        logger.info("🔍 Checking for PIN page...")
        
        if sb.is_element_visible(self.PIN_INPUT):
            logger.info("🔐 Found PIN input field")
            try:
                sb.wait_for_element_clickable(self.PIN_INPUT, timeout=10)
                sb.scroll_to_element(self.PIN_INPUT)
                sb.click(self.PIN_INPUT)
                sb.sleep(1)
                
                sb.clear(self.PIN_INPUT)
                sb.type(self.PIN_INPUT, pin)
                logger.info(f"🔐 Entered PIN: {pin}")
                sb.sleep(2)
                
                # Click Continue button for PIN
                continue_selectors = [
                    'button[data-test-id="button-continue"]',
                    'button:contains("Continue")',
                    'button[type="button"]:contains("Continue")',
                    'input[type="submit"]'
                ]
                
                return self.click_continue_button(sb, continue_selectors, "PIN page")
                
            except Exception as e:
                logger.error(f"❌ Failed to handle PIN page: {e}")
                return False
        else:
            logger.info("ℹ️ No PIN page found, continuing...")
            return True
    
    def request_verification_code(self, sb: BaseCase) -> bool:
        """Request email verification code if needed"""
        sb.sleep(3)
        logger.info("🔍 Checking for email verification selection page...")
        
        if sb.is_element_visible(self.SUBMIT_BTN):
            logger.info("📧 Found email verification selection page")
            try:
                sb.wait_for_element_clickable(self.SUBMIT_BTN, timeout=10)
                sb.scroll_to_element(self.SUBMIT_BTN)
                sb.click(self.SUBMIT_BTN)
                logger.info("📧 Clicked 'Send verification code' button")
                sb.sleep(3)
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to handle email verification selection: {e}")
                return False
        else:
            logger.info("ℹ️ No email verification selection page found, continuing...")
            return True
    
    def enter_otp(self, sb: BaseCase, otp: str) -> bool:
        """Enter OTP with robust error handling"""
        logger.info("🔍 Checking for OTP verification page...")
        sb.sleep(3)
        
        if sb.is_element_visible(self.OTP_INPUT):
            logger.info("🔍 OTP verification page found")
            logger.info("📧 Entering OTP...")
            sb.sleep(2)
            
            try:
                sb.wait_for_element_clickable(self.OTP_INPUT, timeout=10)
                sb.scroll_to_element(self.OTP_INPUT)
                sb.click(self.OTP_INPUT)
                sb.clear(self.OTP_INPUT)
                sb.type(self.OTP_INPUT, otp)
                logger.info(f"✅ Entered OTP: {otp}")
                sb.sleep(3)
                
                # Look for submit button or press Enter
                submit_selectors = [
                    'button[data-test-id="button-submit"]',
                    'button[data-test-id="button-continue"]',
                    'button[type="submit"]',
                    'button:contains("Verify")',
                    'button:contains("Submit")',
                    'button:contains("Continue")'
                ]
                
                submit_clicked = False
                for submit_selector in submit_selectors:
                    if sb.is_element_visible(submit_selector):
                        sb.click(submit_selector)
                        logger.info("🎉 OTP submitted successfully!")
                        sb.sleep(4)
                        submit_clicked = True
                        break
                
                if not submit_clicked:
                    sb.press_keys(self.OTP_INPUT, "\n")
                    logger.info("🎉 OTP submitted via Enter key!")
                    sb.sleep(4)
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to enter OTP: {e}")
                return False
        else:
            logger.info("ℹ️ No OTP verification required or element not found. Proceeding...")
            return True
    
    def click_continue_button(self, sb: BaseCase, continue_selectors, page_name):
        """Helper method to click continue button"""
        continue_clicked = False
        for selector in continue_selectors:
            try:
                if sb.is_element_visible(selector):
                    logger.info(f"➡️ Clicking continue button on {page_name}: {selector}")
                    sb.wait_for_element_clickable(selector, timeout=10)
                    sb.scroll_to_element(selector)
                    sb.click(selector)
                    sb.sleep(3)
                    continue_clicked = True
                    break
            except Exception as e:
                logger.error(f"❌ Failed to click continue button {selector}: {e}")
                continue
        
        if not continue_clicked:
            logger.error(f"❌ Continue button not found on {page_name}")
            return False
        return True

class AmazonJobDashboard:
    """Page object for Amazon job dashboard"""
    
    # Dashboard selectors
    DASHBOARD_CONTAINER = 'div[data-test-component="StencilReactRow"].hvh-careers-emotion-160xmit'
    MY_JOBS_BTN = 'button:contains("Go to my jobs")'
    SEARCH_JOBS_BTN = 'button:contains("Search all jobs")'
    ACTIVE_JOBS_COUNT = 'div[data-test-component="StencilText"].hvh-careers-emotion-1ptjr73'
    
    # Job search selectors
    JOB_SEARCH_CONTAINER = "div.hvh-careers-emotion-14hcg2z"
    JOB_FILTER_BTN = "div.hvh-careers-emotion-1jk3vbz button:nth-of-type(2) div"
    
    def assert_dashboard_loaded(self, sb: BaseCase) -> bool:
        """Assert dashboard is properly loaded with robust waiting"""
        logger.info("📊 Verifying job dashboard...")
        
        # Wait longer for the React app to load
        sb.sleep(5)
        
        # Try multiple selectors and wait longer
        dashboard_selectors = [
            self.DASHBOARD_CONTAINER,
            'div[data-test-component="StencilReactRow"]',
            'div[class*="hvh-careers-emotion"]',
            'div:contains("Active jobs")',
            'div:contains("Recommended jobs")'
        ]
        
        dashboard_found = False
        for selector in dashboard_selectors:
            try:
                if sb.is_element_visible(selector, timeout=15):
                    logger.info(f"✅ Dashboard found with selector: {selector}")
                    dashboard_found = True
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} not found: {e}")
                continue
        
        if not dashboard_found:
            # Try waiting for page to be ready
            sb.wait_for_ready_state_complete(timeout=20)
            sb.sleep(3)
            
            # Final attempt with original selector
            try:
                sb.wait_for_element_visible(self.DASHBOARD_CONTAINER, timeout=15)
                dashboard_found = True
            except Exception as e:
                logger.error(f"❌ Dashboard still not loaded after extended wait: {e}")
                # Take screenshot for debugging
                sb.save_screenshot("dashboard_load_failure.png")
                return False
        
        # Verify text content is present
        try:
            sb.wait_for_text("Active jobs", timeout=10)
            logger.info("✅ 'Active jobs' text found")
        except:
            logger.warning("⚠️ 'Active jobs' text not found, but dashboard container exists")
        
        logger.info("✅ Job dashboard verified")
        return True
    
    def get_active_jobs_count(self, sb: BaseCase) -> int:
        """Get count of active jobs"""
        if sb.is_element_visible(self.ACTIVE_JOBS_COUNT):
            count_text = sb.get_text(self.ACTIVE_JOBS_COUNT)
            # Extract number from text
            import re
            numbers = re.findall(r'\d+', count_text)
            return int(numbers[0]) if numbers else 0
        return 0
    
    def navigate_to_my_jobs(self, sb: BaseCase) -> bool:
        """Navigate to my jobs section"""
        sb.assert_element(self.MY_JOBS_BTN)
        sb.click(self.MY_JOBS_BTN)
        logger.info("✅ Navigated to my jobs")
        return True
    
    def navigate_to_job_search(self, sb: BaseCase) -> bool:
        """Navigate to job search"""
        sb.assert_element(self.SEARCH_JOBS_BTN)
        sb.click(self.SEARCH_JOBS_BTN)
        logger.info("✅ Navigated to job search")
        return True
    
    def perform_job_search_navigation(self, sb: BaseCase) -> bool:
        """Perform job search navigation steps"""
        logger.info("🔍 Performing job search navigation...")
        
        # Click job search container
        if sb.is_element_visible(self.JOB_SEARCH_CONTAINER):
            sb.click(self.JOB_SEARCH_CONTAINER)
            sb.sleep(2)
        
        # Click job filter button
        if sb.is_element_visible(self.JOB_FILTER_BTN):
            sb.click(self.JOB_FILTER_BTN)
            sb.sleep(3)
            
            # Handle consent after navigation
            consent_page = AmazonConsentPage()
            consent_page.handle_consent(sb)
        
        logger.info("✅ Job search navigation completed")
        return True