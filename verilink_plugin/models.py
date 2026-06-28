"""
Data models for VeriLinkOS plugin with Pydantic v2 validation
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator, HttpUrl, SecretStr
from enum import Enum
import binascii
import uuid
from datetime import datetime

class VeriLinkEnforcementMode(str, Enum):
    """Enforcement modes for governance"""
    BLOCK = "block"
    WARN = "warn"
    LOG = "log"
    OBSERVE = "observe"

class VeriLinkConfig(BaseModel):
    """
    Configuration for VeriLinkOS plugin with validation.
    """
    api_url: HttpUrl = Field(..., description="VeriLinkOS API URL")
    api_key: SecretStr = Field(..., description="VeriLinkOS API key")
    agent_id: str = Field(..., description="Agent identifier")
    organization_id: str = Field(..., description="Organization identifier")
    
    private_key_hex: Optional[SecretStr] = Field(
        None, 
        description="Agent private key hex for Ed25519 signing"
    )
    enforce_mode: VeriLinkEnforcementMode = Field(
        default=VeriLinkEnforcementMode.BLOCK,
        description="Enforcement mode"
    )
    timeout: int = Field(default=30, ge=1, le=120)
    max_retries: int = Field(default=3, ge=0, le=10)
    use_cache: bool = Field(default=True)
    cache_ttl: int = Field(default=300, ge=60, le=3600)
    predictive_enabled: bool = Field(default=True)
    jurisdiction: str = Field(default="SG")
    
    @field_validator('private_key_hex')
    @classmethod
    def validate_hex_key(cls, v: Optional[SecretStr]) -> Optional[SecretStr]:
        if v:
            try:
                key_str = v.get_secret_value()
                key_bytes = binascii.unhexlify(key_str)
                if len(key_bytes) != 32:
                    raise ValueError("Private key must be 32 bytes (64 hex characters)")
            except binascii.Error:
                raise ValueError("private_key_hex must be a valid hex string")
        return v
    
    @field_validator('agent_id')
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        if not v or len(v) < 10:
            raise ValueError("Agent ID must be a valid UUID or identifier")
        return v

class VeriLinkTestResult(BaseModel):
    """Result of a test with VeriLinkOS governance."""
    passed: bool
    error: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    receipt_id: Optional[str] = None
    verification_url: Optional[str] = None
    merkle_root: Optional[str] = None
    prediction_score: Optional[float] = None
    governance_status: str = "evaluated"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)

class VeriLinkReceipt(BaseModel):
    receipt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_id: str
    timestamp: float
    signature: str
    evidence_hash: str
    is_mock: bool = False