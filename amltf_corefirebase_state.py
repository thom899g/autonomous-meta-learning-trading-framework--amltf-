"""
Firebase state management for AMLTF.
Handles all real-time data persistence and state synchronization.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
import json
from contextlib import contextmanager

from amltf_core.config import get_config

logger = logging.getLogger(__name__)

@dataclass
class StateMetadata:
    """Metadata for state tracking."""
    created_at: datetime
    updated_at: datetime
    version: str
    checksum: Optional[str] = None

class FirebaseStateManager:
    """Manages all Firebase interactions with error handling and retries."""
    
    def __init__(self):
        config = get_config()
        
        try:
            # Initialize Firebase app if not already initialized
            if not firebase_admin._apps:
                cred = credentials.Certificate(config.firebase.credentials_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': config.firebase.project_id
                })
            
            self.db = firestore.client()
            self._collections_initialized = False
            self._initialize_collections()
            logger.info("Firebase State Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def _initialize_collections(self) -> None:
        """Initialize required Firestore collections."""
        required_collections = [
            'market_data',
            'trading_strategies',
            'model_performance',
            'system_metrics',
            'feature_store'
        ]
        
        for collection in required_collections:
            # Firestore creates collections automatically on first write
            # We'll just verify we can access them
            try:
                # Test write to ensure collection exists
                test_ref