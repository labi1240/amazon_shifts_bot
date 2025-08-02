# Utils package
from .logging_config import setup_logging

# Import existing utility functions
import logging
import functools
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def init_logger(name=__name__, level=logging.INFO, log_file: str = None):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s • %(levelname)s • %(message)s")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger

def retry(exceptions, tries=3, delay=2, backoff=2):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger = logging.getLogger(func.__module__)
                    logger.warning(f"{e!r} – retrying in {mdelay}s…")
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator

def wait_for_presence(driver, selector, timeout=15):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(("css selector", selector))
        )
    except TimeoutException:
        return None

def click_when_ready(driver, selector, timeout=15):
    """Wait for element to be clickable and click it"""
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(("css selector", selector))
        )
        el.click()
        return True
    except TimeoutException:
        return False

def wait_for_clickable(driver, selector, timeout=15):
    """Wait for element to be clickable and visible"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(("css selector", selector))
        )
    except TimeoutException:
        return None

def safe_send_keys(driver, element, text, clear_first=True):
    """Safely send keys to an element with proper waiting"""
    try:
        # Scroll element into view
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        
        # Wait for element to be clickable
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element))
        
        # Click to focus
        element.click()
        time.sleep(0.3)
        
        if clear_first:
            element.clear()
            time.sleep(0.2)
            
        element.send_keys(text)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to send keys: {e}")
        return False

__all__ = [
    'setup_logging', 'init_logger', 'retry', 'wait_for_presence', 
    'click_when_ready', 'wait_for_clickable', 'safe_send_keys'
]