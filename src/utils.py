"""
Utility functions for the face ID pipeline.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any
import hashlib

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def save_result(result: Dict[str, Any], output_path: str) -> bool:
    """
    Save pipeline result to JSON file.
    
    Args:
        result: Result dictionary from pipeline
        output_path: Path to save JSON file
        
    Returns:
        True if successful
    """
    try:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_result = {}
        for key, value in result.items():
            if hasattr(value, 'tolist'):  # numpy array
                serializable_result[key] = value.tolist()
            else:
                serializable_result[key] = value
        
        with open(output_path, 'w') as f:
            json.dump(serializable_result, f, indent=2, default=str)
        
        logger.info(f"Result saved to {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to save result: {str(e)}")
        return False


def load_env_vars() -> Dict[str, str]:
    """Load environment variables from .env file."""
    try:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        env_vars = {
            "ETHEREUM_RPC_URL": os.getenv("ETHEREUM_RPC_URL"),
            "ETHEREUM_PRIVATE_KEY": os.getenv("ETHEREUM_PRIVATE_KEY"),
            "BING_SEARCH_KEY": os.getenv("BING_SEARCH_KEY"),
            "CONTRACT_ADDRESS": os.getenv("CONTRACT_ADDRESS"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        }
        
        return env_vars
    
    except Exception as e:
        logger.error(f"Failed to load environment variables: {str(e)}")
        return {}


def validate_image_path(image_path: str) -> bool:
    """Validate that image file exists and is accessible."""
    path = Path(image_path)
    if not path.exists():
        logger.error(f"Image file not found: {image_path}")
        return False
    if not path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        logger.error(f"Invalid image format: {path.suffix}")
        return False
    return True


def hash_string(value: str) -> str:
    """Generate SHA256 hash of a string."""
    return hashlib.sha256(value.encode()).hexdigest()[:32]
