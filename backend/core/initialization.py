import asyncio
import logging
from ..managers.config_manager import config_manager
from ..aws.aws_integration import AWSIntegration
from ..aws.storj_client import StorjClient

logger = logging.getLogger(__name__)

def initialize_storage():
    """Initialize storage integration with config"""
    try:
        config = config_manager.load_config()
        logger.info("Loaded config successfully")
        
        # Get storage provider from config or environment
        storage_provider = config.get('storage_provider', 'storj').lower()
        
        # Debug log the config (without sensitive data)
        logger.info(f"Storage Provider: {storage_provider}")
        logger.info(f"Config loaded with bucket: {config.get('bucket_name')}")
        
        if storage_provider == 'storj':
            logger.info("Initializing Storj integration...")
            logger.info(f"Storj endpoint: {config.get('storj_endpoint')}")
            logger.info(f"Storj access key present: {'Yes' if config.get('storj_access_key') else 'No'}")
        else:
            logger.info(f"Config loaded with region: {config.get('region')}")
            logger.info(f"AWS access key present: {'Yes' if config.get('aws_access_key') else 'No'}")
        
        # Create storage integration instance
        storage = AWSIntegration(config)
        
        return storage
    except Exception as e:
        logger.error(f"Error in initialize_storage: {str(e)}")
        raise

# Create storage integration instance
storage_integration = initialize_storage()

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
        run_async(storage_integration.initialize())
        logger.info("Application initialized successfully")
        
        # Log storage provider details
        provider = storage_integration.storage_provider
        logger.info(f"Storage Provider: {provider.upper()}")
        if provider == 'storj':
            logger.info("Using Storj decentralized storage")
            logger.info(f"Bucket: {storage_integration.bucket_name}")
            logger.info(f"Endpoint: {storage_integration.config.get('storj_endpoint')}")
        
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        raise e