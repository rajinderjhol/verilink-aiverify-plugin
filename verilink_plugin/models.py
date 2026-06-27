"""
Data models for VeriLinkOS plugin
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

class VeriLinkEnforcementMode(str, Enum):
    """Enforcement modes for governance"""
    BLOCK = "block"
    WARN = "warn"
    LOG = "log"
    OBSERVE = "observe"

class VeriLinkConfig(BaseModel):
    """Configuration for VeriLinkOS plugin"""
    api_url: str = Field(..., description="VeriLinkOS API URL")
    api_key: str = Field(..., description="VeriLinkOS API key")
    agent_id: str = Field(..., description="Agent identifier")
    organization_id: str = Field(..., description="Organization identifier")
    enforce_mode: VeriLinkEnforcementMode = Field(
        default=VeriLinkEnforcementMode.BLOCK,
        description="Enforcement mode"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    use_cache: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    predictive_enabled: bool = Field(default=True, description="Enable predictive enforcement")
    jurisdiction: str = Field(default="SG", description="Legal jurisdiction")

    @validator("api_url")
    def validate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("VERILINK_API_URL must start with http:// or https://")
        return v

class VeriLinkTestResult(BaseModel):
    """Result of a test with VeriLinkOS governance"""
    passed: bool
    error: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    receipt_id: Optional[str] = None
    verification_url: Optional[str] = None
    merkle_root: Optional[str] = None
    prediction_score: Optional[float] = None
    governance_status: str = "evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)

class VeriLinkReceipt(BaseModel):
    """VAP Receipt model"""
    receipt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_id: str
    timestamp: float
    signature: str
    evidence_hash: str
    merkle_root: Optional[str] = None
    verification_url: Optional[str] = None
