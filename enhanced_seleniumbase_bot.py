from seleniumbase import BaseCase
from utils.otp_reader import get_recent_otp_from_gmail
from config.settings import get_settings
import logging

BaseCase.main(__name__, __file__)

class EnhancedAmazonShiftBot(BaseCase):
    """Enhanced Amazon Shift Bot with job dashboard assert methods"""
    
    def setUp(self):
        super().setUp()
        self.config = EnhancedBotConfig.from_env()
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    # ... existing methods (login_flow, handle_consent_buttons, etc.) ...
    
    def assert_job_dashboard_loaded(self):
        """Assert that the job dashboard is properly loaded"""
        dashboard_container = 'div[data-test-component="StencilReactRow"].hvh-careers-emotion-160xmit'
        self.assert_element(dashboard_container, timeout=10)
        self.logger.info("✅ Job dashboard loaded")
        
        # Assert key elements
        self.assert_element('img[src*="application_dashboard"]')
        self.assert_text("Active jobs")
        self.assert_text("Recommended jobs")
        return True
    
    def navigate_to_my_jobs(self):
        """Navigate to my jobs with proper assertions"""
        # Assert dashboard is loaded first
        self.assert_job_dashboard_loaded()
        
        # Assert and click 'Go to my jobs' button
        my_jobs_btn = 'button:contains("Go to my jobs")'
        self.assert_element(my_jobs_btn)
        self.assert_element_clickable(my_jobs_btn)
        
        self.scroll_to_element(my_jobs_btn)
        self.click(my_jobs_btn)
        self.logger.info("🎯 Navigated to my jobs")
        
        # Assert navigation was successful
        self.wait_for_ready_state_complete()
        self.assert_no_js_errors()
        return True
    
    def navigate_to_job_search(self):
        """Navigate to job search with proper assertions"""
        # Assert dashboard is loaded first
        self.assert_job_dashboard_loaded()
        
        # Assert and click 'Search all jobs' button
        search_jobs_btn = 'button:contains("Search all jobs")'
        self.assert_element(search_jobs_btn)
        self.assert_element_clickable(search_jobs_btn)
        
        self.scroll_to_element(search_jobs_btn)
        self.click(search_jobs_btn)
        self.logger.info("🎯 Navigated to job search")
        
        # Assert navigation was successful
        self.wait_for_ready_state_complete()
        self.assert_no_js_errors()
        return True
    
    def test_job_dashboard_interaction(self):
        """Test job dashboard interactions with assertions"""
        self.logger.info("🚀 Testing job dashboard interactions...")
        
        # Navigate to Amazon and login (existing flow)
        self.open(self.config.base_url)
        # ... existing login flow ...
        
        # Once at job dashboard, validate it
        dashboard_data = self.validate_job_dashboard_content()
        
        # Test navigation based on job availability
        if dashboard_data['active_jobs'] > 0:
            self.logger.info(f"📋 Found {dashboard_data['active_jobs']} active jobs, navigating to my jobs")
            self.navigate_to_my_jobs()
        else:
            self.logger.info("🔍 No active jobs found, searching all jobs")
            self.navigate_to_job_search()
        
        # Assert final state
        self.assert_no_js_errors()
        self.logger.info("✅ Job dashboard interaction test completed")
    
    def validate_job_dashboard_content(self):
        """Validate job dashboard content with assertions"""
        # Assert dashboard elements
        self.assert_job_dashboard_loaded()
        
        # Get job counts with validation
        active_jobs_element = 'div[data-test-component="StencilText"].hvh-careers-emotion-1ptjr73'
        self.assert_element(active_jobs_element)
        
        job_counts = self.find_elements(active_jobs_element)
        active_count = int(job_counts[0].text) if len(job_counts) > 0 else 0
        recommended_count = int(job_counts[1].text) if len(job_counts) > 1 else 0
        
        # Assert buttons are available
        self.assert_element('button:contains("Go to my jobs")')
        self.assert_element('button:contains("Search all jobs")')
        
        self.logger.info(f"📊 Dashboard validated: {active_count} active, {recommended_count} recommended jobs")
        
        return {
            'active_jobs': active_count,
            'recommended_jobs': recommended_count,
            'buttons_available': True
        }

if __name__ == "__main__":
    pass