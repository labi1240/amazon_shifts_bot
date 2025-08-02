from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Amazon credentials
    amazon_email: str = ""
    amazon_password: str = ""
    
    # Legacy bot behavior (for backward compatibility)
    hours_back: int = 12
    max_applications_per_day: int = 10
    max_applications_per_round: int = 3
    timeout: int = 15
    retry_attempts: int = 3
    wait_between_applications: int = 5
    imap_server: str = "imap.gmail.com"
    email_account: str = ""
    
    # Booking configuration
    booking_enabled: bool = False
    booking_look_back_hours: int = 6
    booking_per_cycle_limit: int = 2
    booking_daily_limit: int = 5
    booking_pause_between: float = 2.0
    booking_retry_attempts: int = 3
    booking_state_file: str = "booking_state.json"
    
    # Notification settings
    discord_webhook_url: Optional[str] = None
    email_smtp_server: str = "smtp.gmail.com"
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    
    # Monitoring settings
    check_interval: int = 300  # 5 minutes
    error_retry_delay: int = 60
    max_cycles: Optional[int] = None
    
    # Selenium settings
    headless: bool = False
    browser_timeout: int = 30
    implicit_wait: int = 10
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings."""
    return settings