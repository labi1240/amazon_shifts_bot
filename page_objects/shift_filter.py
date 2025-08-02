# enhanced_shift_filter.py
from seleniumbase import BaseCase
import time
from typing import List, Dict, Any
from selenium.webdriver.common.action_chains import ActionChains

class EnhancedShiftFilter:
    def __init__(self, driver: BaseCase):
        self.driver = driver
        self.selectors = {
            # — Panel structure —
            'filters_panel': 'div[data-test-id="filters-panel"]',
            'filters_button': 'button:contains("Filters")',
            'view_filters_button': 'button:contains("View all filters")',
            'view_filters_button_alt': 'button.guidedSearchFilterButton',
            
            # — Clear / Apply —
            'clear_filters': 'button[data-test-id="filter-clear-button"]',
            'apply_filters': 'button[data-test-component="StencilReactButton"]:contains("Show")',

            # — Schedule‑Hours panel structure —
            'schedule_hours_section': '#filterPanelScheduleHoursSection',
            'schedule_hours_label': 'label#filter-panel-schedule-hours[data-test-component="StencilLabel"]',

            # — Work‑hours slider & handles —
            'work_hours_summary': 'div[data-test-id="workHourRangeSelectorSummary"]',
            'work_hours_slider': '.rc-slider.rc-slider-with-marks.workHourRangeSelector',
            'slider_handle_min': '.rc-slider-handle[data-index="0"]',
            'slider_handle_max': '.rc-slider-handle[data-index="1"]',

            # — Schedule‑shift buttons —
            'schedule_early_morning': 'button[data-test-id="filter-schedule-shift-button-EarlyMorning"]',
            'schedule_day_time': 'button[data-test-id="filter-schedule-shift-button-Daytime"]',
            'schedule_evening': 'button[data-test-id="filter-schedule-shift-button-Evening"]',
            'schedule_night': 'button[data-test-id="filter-schedule-shift-button-Night"]',
            'schedule_weekday': 'button[data-test-id="filter-schedule-shift-button-Weekday"]',
            'schedule_weekend': 'button[data-test-id="filter-schedule-shift-button-Weekend"]',

            # — Job Role filters (under "Job Types") —
            'role_buttons': 'button[data-test-id^="filter-role-button-"]',
            'role_fulfillment_center': 'button[data-test-id="filter-role-button-Amazon Fulfillment Center Warehouse Associate"]',
            'role_sortation_center': 'button[data-test-id="filter-role-button-Amazon Sortation Center Warehouse Associate"]',
            'role_delivery_station': 'button[data-test-id="filter-role-button-Amazon Delivery Station Warehouse Associate"]',
            'role_distribution_center': 'button[data-test-id="filter-role-button-Amazon Distribution Center Associate"]',
            'role_grocery': 'button[data-test-id="filter-role-button-Amazon Fresh Warehouse Associate"]',
            'role_air_hub': 'button[data-test-id="filter-role-button-Amazon Air Hub Associate"]',
            'role_customer_service': 'button[data-test-id="filter-role-button-Customer Service Associate"]',

            # — Other filters —
            'length_of_employment_select': 'div[data-test-component="StencilSelect"][data-test-id="select-test-id-lengthOfEmployment"]',
            'length_of_employment_trigger': 'button[data-test-component="StencilSelectTrigger"][aria-labelledby*="filter-panel-length-of-employment"]',

            'language_requirement_select': 'div[data-test-component="StencilSelect"][data-test-id="languageRequirementSelectionButton"]',
            'language_requirement_trigger': 'button[data-test-component="StencilSelectTrigger"][aria-labelledby*="filter-panel-language-requirements"]',

            'start_date_select': 'div[data-test-component="StencilSelect"][data-test-id="filter-panel-start-date-select"]',
            'start_date_trigger': 'button[data-test-component="StencilSelectTrigger"][aria-labelledby*="filter-panel-start-date"]',
            'start_date_input': 'input[data-test-id="filter-panel-start-date-input"]',
        }
    
    def apply_shift_filters(self, work_hours_range: tuple = (0, 40), 
                           schedule_preferences: List[str] = None,
                           job_roles: List[str] = None,
                           length_of_employment: str = None,
                           language_requirement: str = None,
                           start_date: str = None) -> bool:
        """Apply comprehensive shift filtering with proper panel management"""
        try:
            # Ensure filters panel is open
            if not self._ensure_filters_panel_open():
                return False
            
            # Set work hours range using slider
            if not self._set_work_hours_range(work_hours_range):
                print("⚠️ Failed to set work hours range")
            
            # Apply schedule preferences
            if schedule_preferences:
                self._apply_schedule_filters(schedule_preferences)
            
            # Apply job role filters
            if job_roles:
                self._apply_job_role_filters(job_roles)
            
            # Apply additional filters if provided
            if length_of_employment:
                self._set_length_of_employment(length_of_employment)
            
            if language_requirement:
                self._set_language_requirement(language_requirement)
            
            if start_date:
                self._set_start_date(start_date)
            
            # NOTE: do NOT call _apply_filters() here—we'll apply once commute is set
            # self._apply_filters()  # REMOVED
            
            return True
        except Exception as e:
            print(f"Error applying shift filters: {e}")
            return False
    
    def _ensure_filters_panel_open(self) -> bool:
        """Ensure the filters panel is open using correct button text"""
        try:
            # Check if filters panel is already visible
            if self.driver.is_element_present(self.selectors['filters_panel']):
                print("✅ Filters panel already open")
                return True
            
            # Try to open the filters panel
            if self.driver.is_element_present(self.selectors['view_filters_button']):
                self.driver.click(self.selectors['view_filters_button'])
                time.sleep(2)
                print("✅ Clicked 'View all filters' button")
                
                # Verify the panel opened
                if self.driver.is_element_present(self.selectors['filters_panel']):
                    return True
            
            # Try alternative button if first one didn't work
            if self.driver.is_element_present(self.selectors['view_filters_button_alt']):
                self.driver.click(self.selectors['view_filters_button_alt'])
                time.sleep(2)
                print("✅ Clicked alternative filters button")
                
                if self.driver.is_element_present(self.selectors['filters_panel']):
                    return True
            
            print("❌ Could not open filters panel")
            return False
        except Exception as e:
            print(f"Error opening filters panel: {e}")
            return False
    
    def _set_work_hours_range(self, hours_range: tuple) -> bool:
        """Set work hours range using slider handles with drag functionality"""
        try:
            min_hours, max_hours = hours_range
            
            # Check if work hours slider is present
            if not self.driver.is_element_present(self.selectors['work_hours_slider']):
                print("⚠️ Work hours slider not found")
                return False
            
            print(f"🎯 Setting work hours range: {min_hours}-{max_hours}")
            
            # Get slider element for calculations
            slider = self.driver.find_element(self.selectors['work_hours_slider'])
            slider_width = slider.size['width']
            
            # Calculate positions (assuming 0-40 hour range)
            min_position = (min_hours / 40) * slider_width
            max_position = (max_hours / 40) * slider_width
            
            # Move minimum handle
            if self.driver.is_element_present(self.selectors['slider_handle_min']):
                min_handle = self.driver.find_element(self.selectors['slider_handle_min'])
                current_min_pos = min_handle.location['x']
                min_offset = min_position - current_min_pos
                
                action_chains = ActionChains(self.driver.driver)
                action_chains.click_and_hold(min_handle).move_by_offset(min_offset, 0).release().perform()
                time.sleep(0.5)
                print(f"✅ Set minimum hours to {min_hours}")
            
            # Move maximum handle
            if self.driver.is_element_present(self.selectors['slider_handle_max']):
                max_handle = self.driver.find_element(self.selectors['slider_handle_max'])
                current_max_pos = max_handle.location['x']
                max_offset = max_position - current_max_pos
                
                action_chains = ActionChains(self.driver.driver)
                action_chains.click_and_hold(max_handle).move_by_offset(max_offset, 0).release().perform()
                time.sleep(0.5)
                print(f"✅ Set maximum hours to {max_hours}")
            
            return True
            
        except Exception as e:
            print(f"Error setting work hours range: {e}")
            # Fallback: just log that we found the slider
            if self.driver.is_element_present(self.selectors['work_hours_slider']):
                print(f"Found work hours slider, attempted to set range: {min_hours}-{max_hours}")
                return True
            return False
    
    def _apply_schedule_filters(self, preferences: List[str]) -> bool:
        """Apply schedule preference filters using exact selectors"""
        try:
            # Mapping user preferences to selector keys
            schedule_mapping = {
                'early_morning': 'schedule_early_morning',
                'daytime': 'schedule_day_time',
                'day_time': 'schedule_day_time',
                'evening': 'schedule_evening',
                'night': 'schedule_night',
                'weekday': 'schedule_weekday',
                'weekend': 'schedule_weekend'
            }
            
            for preference in preferences:
                pref_key = preference.lower().replace(' ', '_')
                if pref_key in schedule_mapping:
                    selector_key = schedule_mapping[pref_key]
                    selector = self.selectors[selector_key]
                    
                    if self.driver.is_element_present(selector):
                        self.driver.click(selector)
                        print(f"✅ Applied {preference} filter")
                        time.sleep(0.5)
                    else:
                        print(f"⚠️ Could not find {preference} filter button")
            
            return True
        except Exception as e:
            print(f"Error applying schedule filters: {e}")
            return False
    
    def _set_length_of_employment(self, employment_length: str) -> bool:
        """Set length of employment filter"""
        try:
            if self.driver.is_element_present(self.selectors['length_of_employment_trigger']):
                self.driver.click(self.selectors['length_of_employment_trigger'])
                time.sleep(1)
                
                # Look for the specific option
                option_selector = f"li:contains('{employment_length}')"
                if self.driver.is_element_present(option_selector):
                    self.driver.click(option_selector)
                    print(f"✅ Set length of employment to {employment_length}")
                    return True
                    
            print(f"⚠️ Could not set length of employment to {employment_length}")
            return False
        except Exception as e:
            print(f"Error setting length of employment: {e}")
            return False
    
    def _set_language_requirement(self, language: str) -> bool:
        """Set language requirement filter"""
        try:
            if self.driver.is_element_present(self.selectors['language_requirement_trigger']):
                self.driver.click(self.selectors['language_requirement_trigger'])
                time.sleep(1)
                
                # Look for the specific language option
                option_selector = f"li:contains('{language}')"
                if self.driver.is_element_present(option_selector):
                    self.driver.click(option_selector)
                    print(f"✅ Set language requirement to {language}")
                    return True
                    
            print(f"⚠️ Could not set language requirement to {language}")
            return False
        except Exception as e:
            print(f"Error setting language requirement: {e}")
            return False
    
    def _set_start_date(self, start_date: str) -> bool:
        """Set start date filter"""
        try:
            if self.driver.is_element_present(self.selectors['start_date_trigger']):
                self.driver.click(self.selectors['start_date_trigger'])
                time.sleep(1)
                
                # Look for the specific date option
                option_selector = f"li:contains('{start_date}')"
                if self.driver.is_element_present(option_selector):
                    self.driver.click(option_selector)
                    print(f"✅ Set start date to {start_date}")
                    return True
                    
            print(f"⚠️ Could not set start date to {start_date}")
            return False
        except Exception as e:
            print(f"Error setting start date: {e}")
            return False
    
    def _apply_filters(self) -> bool:
        """Apply the selected filters by clicking the Show Results button"""
        # NOTE: we no longer auto‑apply "Show Results" here.
        # The outer monitor will click "Apply" once ALL filters (including commute) are set.
        print("✅ Filters configured (not applied yet)")
        return True
        try:
            if self.driver.is_element_present(self.selectors['apply_filters']):
                self.driver.click(self.selectors['apply_filters'])
                time.sleep(3)  # Wait for results to refresh
                print("✅ Applied filters successfully")
                return True
            else:
                print("⚠️ Could not find Apply Filters button")
                return False
        except Exception as e:
            print(f"Error applying filters: {e}")
            return False
    
    def clear_all_filters(self) -> bool:
        """Clear all applied filters"""
        try:
            if self.driver.is_element_present(self.selectors['clear_filters']):
                self.driver.click(self.selectors['clear_filters'])
                time.sleep(2)
                print("✅ Cleared all filters")
                return True
            else:
                print("⚠️ Could not find Clear Filters button")
                return False
        except Exception as e:
            print(f"Error clearing filters: {e}")
            return False
    
    def _apply_job_role_filters(self, job_roles: List[str]) -> bool:
        """Apply job role filters from the Job Types section"""
        try:
            for role in job_roles:
                if role == 'all':
                    # Click all available role buttons
                    role_buttons = self.driver.find_elements(self.selectors['role_buttons'])
                    for btn in role_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            time.sleep(0.5)
                    print(f"✅ Selected all available job roles ({len(role_buttons)} roles)")
                elif role in ['fulfillment_center', 'sortation_center', 'delivery_station', 
                             'distribution_center', 'grocery', 'air_hub', 'customer_service']:
                    selector_key = f'role_{role}'
                    if selector_key in self.selectors:
                        if self.driver.is_element_present(self.selectors[selector_key]):
                            self.driver.click(self.selectors[selector_key])
                            time.sleep(0.5)
                            print(f"✅ Selected job role: {role}")
                        else:
                            print(f"⚠️ Job role button not found: {role}")
                else:
                    print(f"⚠️ Unknown job role: {role}")
            return True
        except Exception as e:
            print(f"Error applying job role filters: {e}")
            return False
    
    # Map "short names" to the methods that set them
    _FILTER_DISPATCH = {
        'hours': '_set_work_hours_range',
        'schedule': '_apply_schedule_filters', 
        'roles': '_apply_job_role_filters',
        'employment': '_set_length_of_employment',
        'language': '_set_language_requirement',
        'start_date': '_set_start_date',
    }
    
    def apply_shift_filters(self, cfg: Dict[str, Any], which: List[str]) -> bool:
        """
        cfg: { 'hours':(min,max), 'schedule':[…], … }
        which: subset of keys you actually want to run today.
        """
        if not self._ensure_filters_panel_open():
            return False

        for key in which:
            if key not in self._FILTER_DISPATCH:
                print(f"⚠️ Unknown filter '{key}'")
                continue

            method = getattr(self, self._FILTER_DISPATCH[key])
            val = cfg.get(key)
            if val is None:
                print(f"⚠️ No value for {key}, skipping")
                continue

            # tuple/list → unpack, scalar → pass directly
            if isinstance(val, (list, tuple)):
                method(val)
            else:
                method(val)

            print(f"✅ Done {key}")
            time.sleep(0.5)

        return True
    
    # Alternative: **kwargs-based approach
    def apply_shift_filters_kwargs(self, **filters) -> bool:
        """
        Dynamically calls any "_set_<key>" method for each
        key=value passed in.
        E.g. apply_shift_filters(hours=(20,40), roles=['a','b'])
        """
        if not self._ensure_filters_panel_open():
            return False

        for key, val in filters.items():
            # Map some keys to their actual method names
            method_mapping = {
                'hours': '_set_work_hours_range',
                'schedule': '_apply_schedule_filters',
                'roles': '_apply_job_role_filters',
                'employment': '_set_length_of_employment',
                'language': '_set_language_requirement',
                'start_date': '_set_start_date'
            }
            
            method_name = method_mapping.get(key, f"_set_{key}")
            if not hasattr(self, method_name):
                print(f"⚠️ No handler for {key}")
                continue

            getattr(self, method_name)(val)
            print(f"✅ {key} applied")
            time.sleep(0.5)

        return True
    
    def _apply_filters(self) -> bool:
        """Apply the selected filters by clicking the Show Results button"""
        # NOTE: we no longer auto‑apply "Show Results" here.
        # The outer monitor will click "Apply" once ALL filters (including commute) are set.
        print("✅ Filters configured (not applied yet)")
        return True
        try:
            if self.driver.is_element_present(self.selectors['apply_filters']):
                self.driver.click(self.selectors['apply_filters'])
                time.sleep(3)  # Wait for results to refresh
                print("✅ Applied filters successfully")
                return True
            else:
                print("⚠️ Could not find Apply Filters button")
                return False
        except Exception as e:
            print(f"Error applying filters: {e}")
            return False
    
    def clear_all_filters(self) -> bool:
        """Clear all applied filters"""
        try:
            if self.driver.is_element_present(self.selectors['clear_filters']):
                self.driver.click(self.selectors['clear_filters'])
                time.sleep(2)
                print("✅ Cleared all filters")
                return True
            else:
                print("⚠️ Could not find Clear Filters button")
                return False
        except Exception as e:
            print(f"Error clearing filters: {e}")
            return False
    
    def _apply_job_role_filters(self, job_roles: List[str]) -> bool:
        """Apply job role filters from the Job Types section"""
        try:
            for role in job_roles:
                if role == 'all':
                    # Click all available role buttons
                    role_buttons = self.driver.find_elements(self.selectors['role_buttons'])
                    for btn in role_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            time.sleep(0.5)
                    print(f"✅ Selected all available job roles ({len(role_buttons)} roles)")
                elif role in ['fulfillment_center', 'sortation_center', 'delivery_station', 
                             'distribution_center', 'grocery', 'air_hub', 'customer_service']:
                    selector_key = f'role_{role}'
                    if selector_key in self.selectors:
                        if self.driver.is_element_present(self.selectors[selector_key]):
                            self.driver.click(self.selectors[selector_key])
                            time.sleep(0.5)
                            print(f"✅ Selected job role: {role}")
                        else:
                            print(f"⚠️ Job role button not found: {role}")
                else:
                    print(f"⚠️ Unknown job role: {role}")
            return True
        except Exception as e:
            print(f"Error applying job role filters: {e}")
            return False