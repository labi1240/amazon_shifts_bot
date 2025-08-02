
from seleniumbase import BaseCase
import logging

logger = logging.getLogger(__name__)

class JobSearchPage:
    """Page object for the job search and filtering functionality."""

    # Filter selectors
    LOCATION_FILTER = 'button:contains("Within 30 miles")'
    LOCATION_INPUT = "input#zipcode-nav-filter"
    LOCATION_SUGGESTION = 'div[id="0"]'
    SHOW_FILTERS_BTN = "button#filterPanelShowFiltersButton div"

    # Shift filter selectors
    SHIFT_FILTERS = {
        "early_morning": 'button[data-test-id="filter-schedule-shift-button-EarlyMorning"] div',
        "daytime": 'button[data-test-id="filter-schedule-shift-button-Daytime"] div',
        "evening": 'button[data-test-id="filter-schedule-shift-button-Evening"] div',
        "weekend": 'button[data-test-id="filter-schedule-shift-button-Weekend"]',
        "weekday": 'button[data-test-id="filter-schedule-shift-button-Weekday"] div',
        "night": 'button[data-test-id="filter-schedule-shift-button-Night"]',
    }

    # Role filter selectors
    ROLE_FILTERS = {
        "fulfillment_center": 'button[data-test-id="filter-role-button-Amazon Fulfillment Center Warehouse Associate"] div',
        "sortation_center": 'button[data-test-id="filter-role-button-Amazon Sortation Center Warehouse Associate"] div',
        "delivery_station": 'button[data-test-id="filter-role-button-Amazon Delivery Station Warehouse Associate"] div',
        "distribution_center": 'button[data-test-id="filter-role-button-Amazon Distribution Center Associate"] div',
        "grocery_warehouse": 'button[data-test-id="filter-role-button-Amazon Grocery Warehouse Associate"] div',
    }

    # Job card and application selectors
    FIRST_JOB_CARD = 'div[data-test-id="JobCard"] div div:nth-of-type(2) div strong'
    APPLY_BTN = 'button[data-test-id="jobDetailApplyButtonDesktop"] div'

    def apply_filters(self, sb: BaseCase, location: str):
        """Applies all the job search filters."""
        logger.info("Applying job search filters...")
        self._apply_location_filter(sb, location)
        self._apply_shift_filters(sb)
        self._apply_role_filters(sb)
        sb.click(self.SHOW_FILTERS_BTN)
        sb.sleep(3)

    def _apply_location_filter(self, sb: BaseCase, location: str):
        """Applies the location filter."""
        if sb.is_element_visible(self.LOCATION_FILTER):
            sb.click(self.LOCATION_FILTER)
            sb.sleep(2)
        if sb.is_element_visible(self.LOCATION_INPUT):
            sb.press_keys(self.LOCATION_INPUT, location)
            sb.sleep(2)
            if sb.is_element_visible(self.LOCATION_SUGGESTION):
                sb.click(self.LOCATION_SUGGESTION)
                sb.sleep(2)

    def _apply_shift_filters(self, sb: BaseCase):
        """Applies the shift filters."""
        for filter_name, selector in self.SHIFT_FILTERS.items():
            if sb.is_element_visible(selector):
                sb.click(selector)
                sb.sleep(1.5)

    def _apply_role_filters(self, sb: BaseCase):
        """Applies the role filters."""
        for role_name, selector in self.ROLE_FILTERS.items():
            if sb.is_element_visible(selector):
                sb.click(selector)
                sb.sleep(1.5)

    def select_first_job_and_apply(self, sb: BaseCase):
        """Selects the first job card and clicks the apply button."""
        logger.info("Selecting first job and applying...")
        if sb.is_element_visible(self.FIRST_JOB_CARD):
            sb.click(self.FIRST_JOB_CARD)
            sb.sleep(3)
        if sb.is_element_visible(self.APPLY_BTN):
            sb.click(self.APPLY_BTN)
            sb.sleep(4)
