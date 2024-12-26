import asyncio
import logging
from .config_manager import config_manager
from .aws_integration import AWSIntegration

logger = logging.getLogger(__name__)

def initialize_aws():
    """Initialize AWS integration with config"""
    try:
        config = config_manager.load_config()
        logger.info("Loaded config successfully")
        
        # Debug log the config (without sensitive data)
        logger.info(f"Config loaded with bucket: {config.get('bucket_name')}")
        logger.info(f"Config loaded with region: {config.get('region')}")
        logger.info(f"AWS access key present: {'Yes' if config.get('aws_access_key') else 'No'}")
        
        # Create AWS integration instance
        aws = AWSIntegration(config)
        
        return aws
    except Exception as e:
        logger.error(f"Error in initialize_aws: {str(e)}")
        raise

# Create AWS integration instance
aws_integration = initialize_aws()

def run_async(coro):
    """Run an async function in the current thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def initialize_app():
    """Initialize the application before first request"""
    try:
        # Run async initialization in a synchronous way
        run_async(aws_integration.initialize())
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        raise e