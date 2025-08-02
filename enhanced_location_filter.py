from seleniumbase import BaseCase
import time
from typing import Optional, Dict, Any

class EnhancedLocationFilter:
    def __init__(self, driver):
        self.driver = driver  # Can accept both BaseCase and SB instances
        self.selectors = {
            'zipcode_input': 'input[data-test-id="zipcode-input"]',
            'commute_distance': 'select[data-test-id="commute-distance-select"]',
            'location_suggestions': '.location-suggestion-item',
            'apply_filters_btn': 'button[data-test-id="apply-filters"]'
        }
    
    def apply_location_filter(self, zipcode: str, commute_distance: str = "25") -> bool:
        """Apply location-based filtering"""
        try:
            # Set zipcode
            if self.driver.is_element_present(self.selectors['zipcode_input']):
                self.driver.clear(self.selectors['zipcode_input'])
                self.driver.type(self.selectors['zipcode_input'], zipcode)
                time.sleep(1)
            
            # Set commute distance
            if self.driver.is_element_present(self.selectors['commute_distance']):
                self.driver.select_option_by_value(self.selectors['commute_distance'], commute_distance)
            
            # Apply filters
            if self.driver.is_element_present(self.selectors['apply_filters_btn']):
                self.driver.click(self.selectors['apply_filters_btn'])
                time.sleep(2)
            
            return True
        except Exception as e:
            print(f"Error applying location filter: {e}")
            return False
    
    def get_current_location_settings(self) -> Dict[str, str]:
        """Get current location filter settings"""
        settings = {}
        try:
            if self.driver.is_element_present(self.selectors['zipcode_input']):
                settings['zipcode'] = self.driver.get_attribute(self.selectors['zipcode_input'], 'value')
            
            if self.driver.is_element_present(self.selectors['commute_distance']):
                settings['commute_distance'] = self.driver.get_attribute(self.selectors['commute_distance'], 'value')
        except Exception as e:
            print(f"Error getting location settings: {e}")
        
        return settings