import click
import logging
import uuid
import sys
import yaml
from pathlib import Path
from seleniumbase import SB
from config.models import AppConfig
from config.settings import get_settings
from utils.logging_config import setup_logging
from services.session_service import SessionService
from enhanced_integrated_monitor import EnhancedIntegratedMonitor

logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Amazon Shift Bot - Production-grade shift monitoring and booking."""
    pass

@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Path to YAML/JSON configuration file')
@click.option('--headless/--no-headless', default=None, 
              help='Run browser in headless mode (overrides config)')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def run(config, headless, debug):
    """Start the enhanced shift monitor."""
    # Setup logging
    log_level = logging.DEBUG if debug else logging.INFO
    setup_logging(level=log_level)
    
    # Load configuration
    if config:
        try:
            config_path = Path(config)
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                # Load YAML configuration
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Create AppConfig from YAML data
                cfg = AppConfig()
                
                # Apply monitoring config if present
                if 'monitoring' in config_data:
                    for key, value in config_data['monitoring'].items():
                        if hasattr(cfg.monitoring, key):
                            setattr(cfg.monitoring, key, value)
                
                # Apply booking config if present  
                if 'booking' in config_data:
                    for key, value in config_data['booking'].items():
                        if hasattr(cfg.booking, key):
                            setattr(cfg.booking, key, value)
                
                # Store advanced settings for later use
                cfg._advanced_settings = config_data.get('advanced', {})
                            
                logger.info(f"✅ Loaded YAML configuration from: {config}")
                logger.info(f"⚡ Fast mode: {getattr(cfg.monitoring, 'fast_mode', False)}")
                logger.info(f"🎯 Instant booking: {getattr(cfg.monitoring, 'instant_booking', False)}")
                logger.info(f"⏰ Check interval: {cfg.monitoring.check_interval}s")
                logger.info(f"👁️ Headless mode: {config_data.get('advanced', {}).get('headless', True)}")
            else:
                # Try JSON/other format (deprecated)
                logger.warning("⚠️ Using deprecated parse_file method. Consider using YAML format.")
                cfg = AppConfig.parse_file(config)
                logger.info(f"Loaded configuration from: {config}")
        except Exception as e:
            logger.error(f"❌ Failed to load configuration from {config}: {e}")
            logger.info("Using default configuration")
            cfg = AppConfig()
    else:
        cfg = AppConfig()
        logger.info("Using default configuration")
    
    # Use headless from CLI if provided, otherwise use config setting
    settings = get_settings()
    
    # Check for headless setting in YAML config
    config_headless = None
    if hasattr(cfg, '_advanced_settings'):
        config_headless = cfg._advanced_settings.get('headless')
    
    # Priority: CLI option > YAML config > environment settings
    if headless is not None:
        use_headless = headless
        logger.info(f"👁️ Using CLI headless setting: {use_headless}")
    elif config_headless is not None:
        use_headless = config_headless
        logger.info(f"👁️ Using YAML config headless setting: {use_headless}")
    else:
        use_headless = settings.headless
        logger.info(f"👁️ Using environment headless setting: {use_headless}")
    
    correlation_id = str(uuid.uuid4())[:8]
    logger.info(f"🚀 Starting Amazon Shift Bot [ID: {correlation_id}]")
    
    try:
        with SB(headless=use_headless, 
                undetectable=True,
                uc_cdp_events=True,
                block_images=False) as sb:  # Images will now load properly
            
            # 1) establish or restore session
            sess = SessionService()
            if not sess.ensure_authenticated_session(sb):
                logger.error("❌ Failed to establish authenticated session")
                sys.exit(1)
            
            # 2) create monitor and inject driver
            monitor = EnhancedIntegratedMonitor(cfg)
            monitor.driver = sb  # inject the driver
            
            # 3) start monitoring
            monitor.start_monitoring(correlation_id)
            
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True))
def validate_config(config):
    """Validate configuration file."""
    try:
        if config:
            cfg = AppConfig.parse_file(config)
            click.echo(f"✅ Configuration file {config} is valid")
            click.echo(f"Auth email: {cfg.auth.email}")
            click.echo(f"Booking enabled: {cfg.booking.enabled}")
        else:
            cfg = AppConfig()
            click.echo("✅ Default configuration is valid")
    except Exception as e:
        click.echo(f"❌ Configuration validation failed: {e}")
        sys.exit(1)

@cli.command()
def test_session():
    """Test session establishment without monitoring."""
    setup_logging(level=logging.INFO)
    cfg = AppConfig()
    settings = get_settings()
    
    try:
        with SB(headless=settings.headless) as sb:
            sess = SessionService()
            if sess.ensure_authenticated_session():
                click.echo("✅ Session test successful")
            else:
                click.echo("❌ Session test failed")
                sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Session test error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()