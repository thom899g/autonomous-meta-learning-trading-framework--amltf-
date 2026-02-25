"""
Core configuration for AMLTF with environment validation.
Centralizes all external dependencies and service configurations.
"""
import os
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

# Initialize logging before any imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation."""
    project_id: str
    credentials_path: str
    
    def validate(self) -> bool:
        """Validate Firebase configuration exists."""
        if not os.path.exists(self.credentials_path):
            logger.error(f"Firebase credentials not found: {self.credentials_path}")
            return False
        return True

@dataclass
class DataSourceConfig:
    """Data source configuration."""
    ccxt_timeout: int = 30000  # milliseconds
    max_retries: int = 3
    rate_limit_delay: float = 1.0  # seconds

class AMLTFConfig:
    """Main configuration manager."""
    
    def __init__(self):
        self._validate_environment()
        self.firebase = self._load_firebase_config()
        self.data_sources = DataSourceConfig()
        self.feature_store_path = "data/features"
        
        # Ensure directories exist
        os.makedirs(self.feature_store_path, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
    def _validate_environment(self) -> None:
        """Validate critical environment variables."""
        required_vars = ['GOOGLE_APPLICATION_CREDENTIALS']
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            error_msg = f"Missing environment variables: {', '.join(missing)}"
            logger.critical(error_msg)
            raise EnvironmentError(error_msg)
            
        logger.info("Environment validation passed")
    
    def _load_firebase_config(self) -> FirebaseConfig:
        """Load and validate Firebase configuration."""
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
        project_id = os.getenv('FIREBASE_PROJECT_ID', 'amltf-production')
        
        config = FirebaseConfig(
            project_id=project_id,
            credentials_path=creds_path
        )
        
        if not config.validate():
            raise RuntimeError("Firebase configuration invalid")
            
        logger.info(f"Firebase configured for project: {project_id}")
        return config
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Return logging configuration."""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'detailed',
                    'level': 'INFO'
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'filename': 'logs/amltf.log',
                    'formatter': 'detailed',
                    'level': 'DEBUG'
                }
            },
            'root': {
                'handlers': ['console', 'file'],
                'level': 'INFO'
            }
        }

# Singleton instance
_config_instance: Optional[AMLTFConfig] = None

def get_config() -> AMLTFConfig:
    """Get or create configuration singleton."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AMLTFConfig()
    return _config_instance