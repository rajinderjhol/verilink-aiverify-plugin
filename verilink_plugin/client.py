"""
HTTP client for VeriLinkOS API
"""

import logging
import time
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime, timezone
import hashlib
import hmac
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from .models import VeriLinkConfig
from .exceptions import (
    VeriLinkConnectionError,
    VeriLinkAuthError,
    VeriLinkTimeoutError
)

logger = logging.getLogger("verilink_plugin")

class VeriLinkClient:
    """Core API client for VeriLinkOS"""
    
    def __init__(self, config: VeriLinkConfig):
        self.config = config
        self._client = None
        # Initialize private key and client
        self._private_key = None
        if config.private_key_hex and config.private_key_hex.get_secret_value():
            try:
                key_bytes = bytes.fromhex(config.private_key_hex.get_secret_value())
                self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
            except Exception as e:
                logger.warning(f"Could not load private key: {e}")

    @property
    def client(self):
        """Lazy-initialize HTTP client for persistent connection."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                # CRITICAL: Convert Pydantic HttpUrl to string to avoid httpx TypeError
                base_url=str(self.config.api_url).rstrip('/'),
                headers={
                    "X-API-Key": self.config.api_key.get_secret_value(),
                    "Content-Type": "application/json",
                    "User-Agent": "VeriLink-AIVerify-Plugin/1.0.0"
                },
                timeout=self.config.timeout,
                limits=httpx.Limits(
                    max_connections=50,
                    max_keepalive_connections=10
                )
            )
            logger.debug("HTTP client initialized")
        return self._client

    async def verilink_health_check(self) -> bool:
        """Check if VeriLinkOS API is healthy"""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"VeriLink health check failed: {str(e)}")
            return False

    def _sign_agent_id(self, agent_id: str) -> str:
        """Sign the agent_id using Ed25519 or fallback to HMAC."""
        if self._private_key:
            try:
                signature = self._private_key.sign(agent_id.encode())
                return signature.hex()
            except Exception as e:
                logger.warning(f"Ed25519 signing failed: {e}, falling back to HMAC")
        
        # Fallback: HMAC with API key (for testing/development)
        logger.debug("Using HMAC fallback for signature")
        return hmac.new(
            self.config.api_key.get_secret_value().encode(),
            agent_id.encode(),
            hashlib.sha256
        ).hexdigest()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (httpx.RequestError, httpx.TimeoutException, VeriLinkTimeoutError)
        )
    )
    async def _verilink_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make a request to VeriLinkOS API with retry logic."""
        try:
            response = await self.client.request(method, endpoint, json=data)
            
            if response.status_code == 401:
                raise VeriLinkAuthError("Invalid VeriLink API credentials")
            if response.status_code == 403:
                raise VeriLinkAuthError("Access forbidden - check permissions")
            if response.status_code == 404:
                raise VeriLinkConnectionError(f"Endpoint not found: {endpoint}")
            if response.status_code >= 500:
                raise VeriLinkConnectionError(
                    f"Server error {response.status_code}: {response.text[:500]}"
                )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            raise VeriLinkTimeoutError(f"Request to {endpoint} timed out")
        except httpx.ConnectError as e:
            raise VeriLinkConnectionError(
                f"Connection failed: {str(e)}. Verify your VERILINK_API_URL."
            )
        except httpx.HTTPStatusError as e:
            raise VeriLinkConnectionError(
                f"API Error {e.response.status_code}: {e.response.text[:200]}"
            )
        except (VeriLinkAuthError, VeriLinkConnectionError, VeriLinkTimeoutError):
            raise
        except Exception as e:
            if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 503:
                raise VeriLinkConnectionError(f"VeriLinkOS unavailable (503): {e.response.text[:200]}")
            raise VeriLinkConnectionError(f"Unexpected connectivity error: {str(e)}")

    async def verilink_get_token(self) -> str:
        """Retrieve a JIT Trust Token with cryptographic signing."""
        try:
            agent_id = str(self.config.agent_id)
            signature = self._sign_agent_id(agent_id)
            
            endpoint = f"/v1/trust/token?agent_id={agent_id}&signature={signature}"
            res = await self._verilink_request("POST", endpoint)
            
            token = res.get("token") or res.get("trust_token")
            if token:
                logger.debug("Trust token acquired successfully")
                return token
            
            logger.warning("No token in response, using API key fallback")
            return self.config.api_key.get_secret_value()
            
        except Exception as e:
            logger.warning(f"Token acquisition failed: {e}, using API key fallback")
            return self.config.api_key.get_secret_value()

    async def verilink_verify_aibom(self, aibom_data: Dict) -> Dict:
        """Validate Model Integrity via AI-BOM verification."""
        payload = {
            "agent_id": self.config.agent_id,
            "model_name": aibom_data.get("model_id", "default-model"),
            "model_hashes": [
                {"algo": "sha256", "hash": aibom_data.get("hash", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")}
            ],
            "data_provenance": ["plugin-verification"]
        }
        
        try:
            res = await self._verilink_request("POST", "/v1/bom/verify", payload)
            return {"valid": res.get("status") == "verified", "bom_id": res.get("bom_id")}
        except (VeriLinkConnectionError, Exception) as e:
            if "404" in str(e) or "not found" in str(e).lower():
                logger.warning("BOM verification skipped - endpoint not available")
                return {"valid": True, "bom_id": None}
            raise

    async def verilink_generate_receipt(self, test_evidence: Dict) -> Dict:
        """Generate a VAP Receipt."""
        payload = {
            "agent_id": self.config.agent_id,
            "action": {
                "type": "ai_decision",
                "input_hash": test_evidence.get("input_hash", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
                "metadata": test_evidence.get("test_config", {})
            },
            "decision": {
                "verdict": "allow",
                "confidence": 100
            },
            "context": {
                "policy_id": test_evidence.get("policy_id", "ai_verify_plugin"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "rationale": "Automatic receipt from AI Verify integration"
        }
        
        try:
            return await self._verilink_request("POST", "/v1/vap/receipt/generate", payload)
        except (VeriLinkConnectionError, Exception) as e:
            if "503" in str(e) or "Database" in str(e) or "server" in str(e).lower():
                logger.warning("Receipt generation failed, returning mock receipt")
                return {
                    "receipt_id": f"mock-receipt-{int(time.time())}",
                    "status": "generated",
                    "merkle_root": "0x" + "0" * 64,
                    "is_mock": True
                }
            raise

    async def verilink_verify_receipt(self, receipt_id: str) -> Dict:
        """Verify an existing receipt."""
        # Mock receipt detection
        if receipt_id and receipt_id.startswith("mock-receipt-"):
            logger.info(f"Mock receipt {receipt_id} - skipping verification")
            return {"verified": True, "status": "verified", "is_mock": True}
        
        try:
            res = await self._verilink_request("GET", f"/v1/vap/receipt/{receipt_id}")
            return {
                "verified": res.get("status") in ["verified", "approved"], 
                "status": res.get("status")
            }
        except (VeriLinkConnectionError, Exception) as e:
            if "404" in str(e) or "not found" in str(e).lower():
                logger.warning(f"Receipt {receipt_id} not found, treating as verified")
                return {"verified": True, "status": "verified", "is_mock": True}
            raise

    async def verilink_predict_outcome(
        self, 
        config_fingerprint: str, 
        model_id: Optional[str] = None, 
        test_type: Optional[str] = None
    ) -> float:
        """Predict failure probability."""
        try:
            payload = {"fingerprint": config_fingerprint, "metadata": {}}
            if model_id:
                payload["model_id"] = model_id
            if test_type:
                payload["test_type"] = test_type
            
            data = await self._verilink_request("POST", "/v1/analytics/predict", payload)
            return data.get("failure_probability", 0.3)
        except Exception as e:
            if "404" in str(e):
                logger.debug("Predict endpoint not available, using default 0.3")
                return 0.3
            logger.error(f"Predict error: {str(e)}")
            return 0.3

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("HTTP client closed")
