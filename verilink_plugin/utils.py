"""
Utility functions for VeriLinkOS plugin
"""

import logging
import hashlib
import json
from typing import Dict, Any

def verilink_setup_logger(name: str = "verilink_plugin") -> logging.Logger:
    """Setup and return a logger for the plugin"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def verilink_calculate_evidence_hash(data: Dict[str, Any]) -> str:
    """Computes a deterministic SHA256 hash of the evidence data."""
    encoded = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()

def verilink_validate_config(url: str, key: str) -> bool:
    """Basic validation for VeriLink API connectivity parameters."""
    if not url.startswith(("http://", "https://")):
        return False
    return len(key) > 8
