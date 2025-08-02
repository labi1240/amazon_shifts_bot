# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Testing
```bash
# Run unit tests
pytest tests/

# Run integration tests with specific options
python test_integration.py --unit
python test_integration.py --live

# Run tests with coverage
pytest --cov=. tests/
```

### Development Environment
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e .[dev]
```

### Running the Application
```bash
# Quick start with interactive menu
./start_monitor.sh

# CLI interface - production mode
python cli.py run

# CLI interface with options
python cli.py run --headless --debug

# Legacy monitoring system
python integrated_monitor.py --test
python integrated_monitor.py --interval 300

# Session creation (one-time setup)
python create_session.py
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8

# Type checking
mypy .
```

## Architecture Overview

### Core System Design
The Amazon Shift Bot is a web automation system with a **two-phase architecture**:

1. **Session Creation Phase**: Handles complex Amazon login flow once and saves session state
2. **Monitoring Phase**: Uses saved session for continuous job monitoring and booking

### Key Components

#### Authentication & Session Management
- `create_session.py`: Creates and persists Amazon login sessions
- `session_manager.py`: Manages session persistence using pickle files and cookies
- `services/session_service.py`: Modern session service implementation
- Session files: `amazon_session.pkl`, `amazon_cookies.json`

#### Main Entry Points
- `cli.py`: Modern Click-based CLI with structured commands
- `integrated_monitor.py`: Legacy monitoring system entry point
- `start_monitor.sh`: Interactive bash script for quick setup

#### Page Object Architecture
- `amazon_page_objects.py`: Page object models for Amazon website automation
- `page_objects/`: Structured page object modules (login, consent, filters, booking)
- Uses Selenium WebDriver with SeleniumBase framework for stability

#### Configuration System
- `config/`: Modern Pydantic-based configuration with models and settings
- `usa_config.py`: US-specific job targeting configuration
- `.env` file: Environment variables for credentials and settings
- `pyproject.toml`: Project metadata and tool configurations

#### Monitoring & Automation
- `smart_job_monitor_sb.py`: Core monitoring logic using SeleniumBase
- `enhanced_integrated_monitor.py`: Enhanced monitoring with better error handling
- `job_*.py` files: Job-specific automation components

#### Notification System
- `enhanced_notifier.py`: Rich Discord notifications with embeds
- `utils/notifier.py`: Basic notification utilities
- Supports webhook-based Discord integration

### Data Flow
1. **Session Creation**: `create_session.py` → saves to `amazon_session.pkl`
2. **Configuration**: Environment variables → `config/` modules → application settings
3. **Monitoring**: Saved session → job search → filtering → notifications/booking
4. **Notifications**: Job events → Discord webhooks → user alerts

### Testing Strategy
- `tests/`: Pytest-based test suite with SeleniumBase integration
- `base_test_case.py`: Base test class with common functionality
- Supports both unit tests and live integration tests

### File Organization Patterns
- **Legacy files**: Direct Python scripts in root (e.g., `amazon_shift_bot.py`)
- **Modern files**: Organized in modules (`config/`, `services/`, `utils/`, `page_objects/`)
- **Documentation**: Multiple `.md` files with specific component documentation

## Environment Setup Requirements

### Required Environment Variables (.env file)
```bash
# Essential credentials
AMAZON_EMAIL=your_email@domain.com
AMAZON_PASSWORD=your_password
DISCORD_WEBHOOK_URL=your_discord_webhook_url

# Optional configuration
HOURS_BACK=12
MAX_APPLICATIONS_PER_DAY=10
HEADLESS=false
CHECK_INTERVAL=300
```

### System Dependencies
- Python 3.8+ (supports up to 3.12)
- Chrome/Chromium browser
- Virtual environment recommended

## Development Notes

### SeleniumBase Integration
- Uses SeleniumBase framework for robust web automation
- Supports both UC (undetected) mode and standard mode
- Context manager pattern: `with SB(uc=True) as sb:`

### Session Persistence Strategy
- Sessions saved as pickle files for quick restoration
- Cookie-based authentication backup
- Automatic session validation with retry logic
- **Automatic cleanup of expired sessions** (12 hour expiry)
- **Invalid session detection and removal** to prevent login loops
- Manual session cleanup utility: `python clear_session.py`

### Error Handling Patterns
- Comprehensive logging to both file and console
- Graceful shutdown with signal handlers
- Retry logic for transient failures

### Code Organization Philosophy
- Page Object Model for maintainable web automation
- Separation of concerns between authentication, monitoring, and notification
- Configuration-driven behavior for flexibility

## Troubleshooting

### Session Issues
If you encounter login loops or "Active window was already closed!" errors:

```bash
# Clear expired/invalid sessions manually
python clear_session.py

# Or delete session files directly
rm amazon_session.pkl amazon_cookies.json
```

### Common Issues
- **"Could not open filters panel"**: Fixed with updated selectors that try multiple fallback options
- **Missing method errors**: All required methods now implemented in enhanced_integrated_monitor.py
- **Session validation loops**: Improved with automatic cleanup of expired sessions

### Development Tips
- Session files expire after 12 hours automatically
- Invalid sessions are detected and cleared to prevent infinite loops  
- Use `--debug` flag with CLI for detailed logging
- Check logs in `logs/` directory for troubleshooting