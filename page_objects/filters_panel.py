from seleniumbase import BaseCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FiltersPanel:
    """Generic filters panel component for handling filter interactions."""
    
    def __init__(self, driver: BaseCase):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        
    def open_filters_panel(self, selectors: List[str]) -> bool:
        """Open the filters panel using multiple selector attempts."""
        for selector in selectors:
            try:
                element = self.driver.find_element(selector)
                if element and element.is_displayed():
                    self.driver.click(selector)
                    logger.info(f"Successfully opened filters panel with selector: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"Failed to open filters with selector {selector}: {e}")
                continue
        
        logger.warning("Failed to open filters panel with any selector")
        return False
    
    def apply_filter(self, filter_type: str, value: Any, selectors: Dict[str, List[str]]) -> bool:
        """Apply a specific filter with the given value."""
        if filter_type not in selectors:
            logger.error(f"Unknown filter type: {filter_type}")
            return False
            
        filter_selectors = selectors[filter_type]
        
        for selector in filter_selectors:
            try:
                if self._apply_single_filter(selector, value):
                    logger.info(f"Successfully applied {filter_type} filter with value: {value}")
                    return True
            except Exception as e:
                logger.debug(f"Failed to apply filter with selector {selector}: {e}")
                continue
                
        logger.warning(f"Failed to apply {filter_type} filter with value: {value}")
        return False
    
    def _apply_single_filter(self, selector: str, value: Any) -> bool:
        """Apply a single filter using the given selector and value."""
        element = self.driver.find_element(selector)
        if not element or not element.is_displayed():
            return False
            
        # Handle different input types
        tag_name = element.tag_name.lower()
        input_type = element.get_attribute('type')
        
        if tag_name == 'input':
            if input_type in ['checkbox', 'radio']:
                if value and not element.is_selected():
                    element.click()
                elif not value and element.is_selected():
                    element.click()
            elif input_type in ['text', 'number']:
                element.clear()
                element.send_keys(str(value))
        elif tag_name == 'select':
            from selenium.webdriver.support.ui import Select
            select = Select(element)
            select.select_by_visible_text(str(value))
        else:
            # For buttons, divs, etc.
            element.click()
            
        return True
    
    def clear_all_filters(self, clear_selector: str) -> bool:
        """Clear all applied filters."""
        try:
            self.driver.click(clear_selector)
            logger.info("Successfully cleared all filters")
            return True
        except Exception as e:
            logger.warning(f"Failed to clear filters: {e}")
            return False
    
    def get_filter_state(self, selectors: Dict[str, List[str]]) -> Dict[str, Any]:
        """Get the current state of all filters."""
        state = {}
        
        for filter_type, filter_selectors in selectors.items():
            for selector in filter_selectors:
                try:
                    element = self.driver.find_element(selector)
                    if element and element.is_displayed():
                        if element.tag_name.lower() == 'input':
                            input_type = element.get_attribute('type')
                            if input_type in ['checkbox', 'radio']:
                                state[filter_type] = element.is_selected()
                            else:
                                state[filter_type] = element.get_attribute('value')
                        else:
                            state[filter_type] = element.text
                        break
                except Exception:
                    continue
                    
        return state