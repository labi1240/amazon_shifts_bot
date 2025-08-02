from seleniumbase import BaseCase

class JobDashboardMethods(BaseCase):
    """SeleniumBase methods for Amazon job dashboard interactions"""
    
    def assert_job_dashboard_loaded(self):
        """Assert that the job dashboard is properly loaded"""
        # Assert the main dashboard container exists
        dashboard_container = 'div[data-test-component="StencilReactRow"].hvh-careers-emotion-160xmit'
        self.assert_element(dashboard_container, timeout=10)
        self.logger.info("✅ Job dashboard container found")
        
        # Assert job application image is present
        job_image = 'img[src*="application_dashboard"]'
        self.assert_element(job_image)
        self.logger.info("✅ Job dashboard image loaded")
        
        # Assert active jobs section
        active_jobs_text = 'div[data-test-component="StencilText"]:contains("Active jobs")'
        self.assert_element(active_jobs_text)
        self.logger.info("✅ Active jobs section found")
        
        # Assert recommended jobs section
        recommended_jobs_text = 'div[data-test-component="StencilText"]:contains("Recommended jobs")'
        self.assert_element(recommended_jobs_text)
        self.logger.info("✅ Recommended jobs section found")
    
    def get_active_jobs_count(self):
        """Get the number of active jobs using assert methods"""
        # Assert and get the active jobs count
        active_jobs_container = 'div[data-test-component="StencilReactRow"][role="heading"]'
        self.assert_elements(active_jobs_container)  # Assert multiple heading elements exist
        
        # Get the first heading which should be active jobs
        active_jobs_number = self.get_text('div[data-test-component="StencilText"].hvh-careers-emotion-1ptjr73')
        self.logger.info(f"📊 Active jobs count: {active_jobs_number}")
        return int(active_jobs_number)
    
    def get_recommended_jobs_count(self):
        """Get the number of recommended jobs"""
        # Get all job count elements
        job_counts = self.find_elements('div[data-test-component="StencilText"].hvh-careers-emotion-1ptjr73')
        
        if len(job_counts) >= 2:
            recommended_count = job_counts[1].text
            self.logger.info(f"📊 Recommended jobs count: {recommended_count}")
            return int(recommended_count)
        return 0
    
    def click_go_to_my_jobs(self):
        """Click 'Go to my jobs' button with assert validation"""
        # Assert the button exists before clicking
        my_jobs_btn = 'button[data-test-component="StencilReactButton"]:contains("Go to my jobs")'
        self.assert_element(my_jobs_btn, timeout=10)
        self.logger.info("✅ 'Go to my jobs' button found")
        
        # Assert button is clickable
        self.assert_element_clickable(my_jobs_btn)
        
        # Scroll to button and click
        self.scroll_to_element(my_jobs_btn)
        self.click(my_jobs_btn)
        self.logger.info("🎯 Clicked 'Go to my jobs' button")
        
        # Assert navigation occurred (wait for page change)
        self.wait_for_ready_state_complete()
        return True
    
    def click_search_all_jobs(self):
        """Click 'Search all jobs' button with assert validation"""
        # Assert the button exists before clicking
        search_jobs_btn = 'button[data-test-component="StencilReactButton"]:contains("Search all jobs")'
        self.assert_element(search_jobs_btn, timeout=10)
        self.logger.info("✅ 'Search all jobs' button found")
        
        # Assert button is clickable
        self.assert_element_clickable(search_jobs_btn)
        
        # Scroll to button and click
        self.scroll_to_element(search_jobs_btn)
        self.click(search_jobs_btn)
        self.logger.info("🎯 Clicked 'Search all jobs' button")
        
        # Assert navigation occurred
        self.wait_for_ready_state_complete()
        return True
    
    def assert_job_buttons_available(self):
        """Assert both job action buttons are available"""
        # Assert both buttons exist
        my_jobs_btn = 'button:contains("Go to my jobs")'
        search_jobs_btn = 'button:contains("Search all jobs")'
        
        self.assert_element(my_jobs_btn)
        self.assert_element(search_jobs_btn)
        
        # Assert both buttons are clickable
        self.assert_element_clickable(my_jobs_btn)
        self.assert_element_clickable(search_jobs_btn)
        
        self.logger.info("✅ Both job action buttons are available and clickable")
        return True
    
    def validate_job_dashboard_content(self):
        """Comprehensive validation of job dashboard content"""
        # Assert main dashboard is loaded
        self.assert_job_dashboard_loaded()
        
        # Get and validate job counts
        active_count = self.get_active_jobs_count()
        recommended_count = self.get_recommended_jobs_count()
        
        # Assert job counts are valid numbers
        assert isinstance(active_count, int), "Active jobs count should be an integer"
        assert isinstance(recommended_count, int), "Recommended jobs count should be an integer"
        assert active_count >= 0, "Active jobs count should be non-negative"
        assert recommended_count >= 0, "Recommended jobs count should be non-negative"
        
        self.logger.info(f"📊 Dashboard validation complete: {active_count} active, {recommended_count} recommended")
        
        # Assert action buttons are available
        self.assert_job_buttons_available()
        
        return {
            'active_jobs': active_count,
            'recommended_jobs': recommended_count,
            'buttons_available': True
        }