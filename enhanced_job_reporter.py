from seleniumbase import BaseCase
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

class EnhancedJobReporter:
    def __init__(self, driver: BaseCase):
        self.driver = driver
        self.selectors = {
            'job_count_header': 'h1[aria-live="assertive"]',
            'job_cards': 'div[data-test-id="JobCard"]',
            'job_title': '.jobDetailText strong',
            'shifts_available': 'div:contains("shift available")',
            'job_type': 'div:contains("Type:")',
            'job_duration': 'div[data-test-id="jobCardDurationText"]',
            'pay_rate': 'div[data-test-id="jobCardPayRateText"]',
            'job_location': '.hvh-careers-emotion-1lcyul5 strong'
        }
    
    def extract_all_jobs(self) -> Dict[str, Any]:
        """Extract comprehensive job information"""
        try:
            # Get total job count
            total_jobs = self._extract_job_count()
            
            # Extract individual job details
            jobs = self._extract_job_details()
            
            # Generate summary statistics
            summary = self._generate_job_summary(jobs)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_jobs_found': total_jobs,
                'jobs_extracted': len(jobs),
                'jobs': jobs,
                'summary': summary
            }
        except Exception as e:
            print(f"Error extracting jobs: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def extract_all_job_information(self) -> Dict[str, Any]:
        """Alias for extract_all_jobs for compatibility"""
        return self.extract_all_jobs()
    
    def _extract_job_count(self) -> int:
        """Extract total job count from header"""
        try:
            if self.driver.is_element_present(self.selectors['job_count_header']):
                header_text = self.driver.get_text(self.selectors['job_count_header'])
                # Extract number from "Total X jobs found"
                match = re.search(r'Total (\d+) jobs found', header_text)
                if match:
                    return int(match.group(1))
            return 0
        except Exception as e:
            print(f"Error extracting job count: {e}")
            return 0
    
    def _extract_job_details(self) -> List[Dict[str, Any]]:
        """Extract detailed information from job cards"""
        jobs = []
        try:
            job_cards = self.driver.find_elements(self.selectors['job_cards'])
            
            for i, card in enumerate(job_cards):
                try:
                    job_data = self._parse_job_card(card, i)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    print(f"Error parsing job card {i}: {e}")
                    continue
        except Exception as e:
            print(f"Error extracting job details: {e}")
        
        return jobs
    
    def _parse_job_card(self, card_element, index: int) -> Optional[Dict[str, Any]]:
        """Parse individual job card for details"""
        try:
            # Extract job title
            title_elements = card_element.find_elements('css selector', 'strong')
            title = title_elements[0].text if title_elements else "Unknown"
            
            # Extract shifts available
            shifts_text = ""
            shift_elements = card_element.find_elements('css selector', 'div')
            for elem in shift_elements:
                if 'shift available' in elem.text:
                    shifts_text = elem.text
                    break
            
            shifts_available = self._extract_number_from_text(shifts_text)
            
            # Extract job type, duration, pay rate
            job_type = self._extract_field_value(card_element, "Type:")
            duration = self._extract_field_value(card_element, "Duration:")
            pay_rate = self._extract_field_value(card_element, "Pay rate:")
            
            # Extract location (last strong element)
            location_elements = card_element.find_elements('css selector', 'strong')
            location = location_elements[-1].text if location_elements else "Unknown"
            
            # Determine shift type based on title and other factors
            shift_type = self._determine_shift_type(title, job_type)
            
            return {
                'index': index,
                'title': title,
                'location': location,
                'shifts_available': shifts_available,
                'job_type': job_type,
                'duration': duration,
                'pay_rate': pay_rate,
                'shift_type': shift_type,
                'extracted_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error parsing job card: {e}")
            return None
    
    def _extract_field_value(self, card_element, field_name: str) -> str:
        """Extract specific field value from job card"""
        try:
            text_elements = card_element.find_elements('css selector', 'div')
            for elem in text_elements:
                if field_name in elem.text:
                    # Extract value after the field name
                    text = elem.text
                    if ':' in text:
                        return text.split(':', 1)[1].strip()
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def _extract_number_from_text(self, text: str) -> int:
        """Extract number from text like '2 shifts available'"""
        try:
            match = re.search(r'(\d+)', text)
            return int(match.group(1)) if match else 0
        except Exception:
            return 0
    
    def _determine_shift_type(self, title: str, job_type: str) -> str:
        """Determine shift type based on job information"""
        title_lower = title.lower()
        if 'fulfillment' in title_lower:
            return 'Fulfillment Center'
        elif 'sortation' in title_lower:
            return 'Sortation Center'
        elif 'delivery' in title_lower:
            return 'Delivery Station'
        else:
            return 'Warehouse Associate'
    
    def _generate_job_summary(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from job data"""
        if not jobs:
            return {}
        
        # Location distribution
        locations = {}
        shift_types = {}
        job_types = {}
        total_shifts = 0
        
        for job in jobs:
            # Count by location
            location = job.get('location', 'Unknown')
            locations[location] = locations.get(location, 0) + 1
            
            # Count by shift type
            shift_type = job.get('shift_type', 'Unknown')
            shift_types[shift_type] = shift_types.get(shift_type, 0) + 1
            
            # Count by job type
            job_type = job.get('job_type', 'Unknown')
            job_types[job_type] = job_types.get(job_type, 0) + 1
            
            # Total shifts
            total_shifts += job.get('shifts_available', 0)
        
        return {
            'total_positions': len(jobs),
            'total_shifts_available': total_shifts,
            'locations_distribution': locations,
            'shift_types_distribution': shift_types,
            'job_types_distribution': job_types,
            'average_shifts_per_position': round(total_shifts / len(jobs), 2) if jobs else 0
        }
    
    def save_report_to_file(self, report_data: Dict[str, Any], filename: str = None) -> str:
        """Save report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"job_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2)
            return filename
        except Exception as e:
            print(f"Error saving report: {e}")
            return ""