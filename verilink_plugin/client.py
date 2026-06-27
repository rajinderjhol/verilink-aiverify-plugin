"""
HTTP client for VeriLinkOS API
"""

import logging
import time
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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
        self.headers = {
            "X-VeriLink-API-Key": config.api_key,
            "X-VeriLink-Agent-ID": config.agent_id,
            "Content-Type": "application/json",
            "User-Agent": "VeriLink-AIVerify-Plugin/1.0.0"
        }
        self.client = httpx.AsyncClient(
            base_url=config.api_url,
            headers=self.headers,
            timeout=config.timeout
        )

    async def verilink_health_check(self) -> bool:
        """Check if VeriLinkOS API is healthy"""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"VeriLink health check failed: {str(e)}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, VeriLinkTimeoutError))
    )
    async def _verilink_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make a request to VeriLinkOS API with retry logic"""
        try:
            response = await self.client.request(method, endpoint, json=data)
            
            if response.status_code == 401:
                raise VeriLinkAuthError("Invalid VeriLink API credentials")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            raise VeriLinkTimeoutError(f"Request to {endpoint} timed out")
        except httpx.HTTPStatusError as e:
            raise VeriLinkConnectionError(f"API Error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise VeriLinkConnectionError(f"Unexpected connection error: {str(e)}")

    async def verilink_get_token(self) -> str:
        """Retrieve a short-lived JIT Trust Token"""
        res = await self._verilink_request("POST", "/v1/auth/token", {
            "org_id": self.config.organization_id,
            "agent_id": self.config.agent_id
        })
        return res["trust_token"]

    async def verilink_verify_aibom(self, aibom_data: Dict) -> Dict:
        """Validate Model Integrity via AI-BOM verification"""
        return await self._verilink_request("POST", "/v1/governance/verify-aibom", aibom_data)

    async def verilink_generate_receipt(self, test_evidence: Dict) -> Dict:
        """Generate a VAP Receipt"""
        return await self._verilink_request("POST", "/v1/governance/receipt", {
            "evidence": test_evidence,
            "timestamp": time.time(),
            "batch": True
        })

    async def verilink_verify_receipt(self, receipt_id: str) -> Dict:
        """Verify an existing receipt"""
        return await self._verilink_request("GET", f"/v1/governance/receipt/{receipt_id}/verify")

    async def verilink_predict_outcome(self, config_fingerprint: str) -> float:
        """Predict failure probability"""
        res = await self._verilink_request("POST", "/v1/analytics/predict", {
            "fingerprint": config_fingerprint
        })
        return res.get("failure_probability", 0.0)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
