from pydantic import BaseModel, Field
from typing import Optional
import os

class AuthConfig(BaseModel):
    email: str = Field(default_factory=lambda: os.getenv('AMAZON_EMAIL', ''))
    password: str = Field(default_factory=lambda: os.getenv('AMAZON_PASSWORD', ''))

class MonitoringConfig(BaseModel):
    check_interval: int = 45  # Ultra-fast monitoring - 45 seconds for instant booking
    error_retry_delay: int = 10  # Fast error recovery - 10 seconds
    max_cycles: Optional[int] = None
    fast_mode: bool = True  # Enable aggressive performance optimizations
    parallel_city_processing: bool = True  # Process multiple cities simultaneously
    instant_booking: bool = True  # Book immediately when shifts found

class BookingConfig(BaseModel):
    enabled: bool = True  # Enable booking by default
    per_cycle_limit: int = 1
    daily_limit: int = 5
    pause_between_bookings: int = 30  # seconds
    state_file: str = "booking_state.json"
    retry_attempts: int = 3
    
class AppConfig(BaseModel):
    auth: AuthConfig = AuthConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    booking: BookingConfig = BookingConfig()