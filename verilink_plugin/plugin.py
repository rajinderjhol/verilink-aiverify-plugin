"""
Main VeriLinkOS Governance Plugin for AI Verify
"""
import logging
import asyncio
import hashlib
import json
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from .models import (
    VeriLinkConfig,
    VeriLinkTestResult,
    VeriLinkEnforcementMode
)
from .client import VeriLinkClient
from .exceptions import VeriLinkAuthError, VeriLinkConfigError

logger = logging.getLogger("verilink_plugin")

class VeriLinkGovernancePlugin:
    """Main integration plugin for AI Verify"""
    
    PLUGIN_ID = "verilink_os_governance"
    PLUGIN_VERSION = "1.0.0"
    
    def __init__(self, config_dict: Optional[Dict] = None):
        """Initialize plugin with validated configuration."""
        try:
            self.config = VeriLinkConfig(**(config_dict or {}))
            logger.info("Configuration validated successfully")
            
            if self.config.predictive_enabled and not self.config.private_key_hex:
                logger.warning(
                    "Predictive enforcement enabled without Ed25519 private key. "
                    "Will fall back to HMAC signing."
                )
        except Exception as e:
            raise VeriLinkConfigError(f"Configuration validation failed: {str(e)}")
        
        self.client = VeriLinkClient(self.config)
        self._aibom_cache: Dict[str, Any] = {}
        self._initialized = False
        self._start_time = time.time()
    
    async def verilink_setup(self):
        """Initialize plugin and check connectivity."""
        try:
            if await self.client.verilink_health_check():
                self._initialized = True
                logger.info("VeriLinkOS connection established")
            else:
                logger.warning("VeriLinkOS API unreachable. Operating in degraded mode.")
                self._initialized = False
        except Exception as e:
            logger.error(f"VeriLink setup failed: {str(e)}")
            self._initialized = False
    
    async def run_test(self, test_config: Dict[str, Any], test_func: Callable) -> VeriLinkTestResult:
        """Run an AI test with VeriLinkOS governance."""
        prediction = None
        try:
            if not self._initialized:
                await self.verilink_setup()
            
            # 1. Predictive enforcement
            if self.config.predictive_enabled:
                try:
                    prediction = await self._verilink_predict_risk(test_config)
                    if prediction > 0.8 and self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                        return VeriLinkTestResult(
                            passed=False, 
                            error=f"Predictive block: risk score {prediction:.2f} exceeds threshold",
                            prediction_score=prediction,
                            governance_status="blocked"
                        )
                except Exception as e:
                    logger.warning(f"Prediction failed: {e}")
            
            # 2. Get trust token
            try:
                await self.client.verilink_get_token()
            except Exception as e:
                if self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                    return VeriLinkTestResult(
                        passed=False,
                        error=f"Authentication failed: {str(e)}",
                        governance_status="blocked"
                    )
                logger.warning(f"Token acquisition failed: {e}")
            
            # 3. Verify AI-BOM
            try:
                aibom_status = await self._verilink_check_aibom(test_config)
                if not aibom_status.get("valid") and self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                    return VeriLinkTestResult(
                        passed=False,
                        error="AI-BOM Verification Failed",
                        governance_status="blocked"
                    )
            except Exception as e:
                if self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                    return VeriLinkTestResult(
                        passed=False,
                        error=f"AI-BOM verification error: {str(e)}",
                        governance_status="blocked"
                    )
                logger.warning(f"AI-BOM verification degraded: {e}")
            
            # 4. Run the test
            test_start = time.time()
            test_raw_result = await test_func(test_config)
            test_duration = time.time() - test_start
            
            # 5. Generate VAP receipt
            evidence = {
                "test_config": test_config,
                "raw_result": test_raw_result,
                "duration": test_duration,
                "timestamp": datetime.now().isoformat()
            }
            
            receipt_data = await self.client.verilink_generate_receipt(evidence)
            receipt_id = receipt_data.get("receipt_id")
            is_mock = receipt_data.get("is_mock", False)
            
            # 6. Verify the receipt
            # Verify receipt (skip for mock)
            is_verified = False
            if is_mock:
                is_verified = True
            elif receipt_id:
                verification = await self.client.verilink_verify_receipt(receipt_id)
                is_verified = verification.get("verified", False)
            
            return VeriLinkTestResult(
                passed=test_raw_result.get("passed", False),
                receipt_id=receipt_id,
                verification_url=f"{self.config.api_url}/verify/{receipt_id}" if not is_mock else None,
                merkle_root=receipt_data.get("merkle_root"),
                details={
                    "receipt_verified": is_verified,
                    "duration": test_duration,
                    "governance_mode": self.config.enforce_mode.value,
                    "is_mock": is_mock
                },
                artifacts=test_raw_result.get("artifacts", {}),
                governance_status="approved" if is_verified else "pending",
                prediction_score=prediction
            )
            
        except Exception as e:
            logger.error(f"VeriLink plugin error: {e}", exc_info=True)
            if self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                return VeriLinkTestResult(
                    passed=False,
                    error=str(e),
                    governance_status="blocked"
                )
            return self._fail_open_result(str(e))
    
    async def _verilink_check_aibom(self, test_config: Dict) -> Dict:
        """Check AI-BOM with caching."""
        model_id = test_config.get("model_id", "default")
        model_hash = test_config.get("model_hash", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        
        if self.config.use_cache and model_id in self._aibom_cache:
            return self._aibom_cache[model_id]
        
        res = await self.client.verilink_verify_aibom({
            "model_id": model_id,
            "hash": model_hash
        })
        
        if self.config.use_cache:
            self._aibom_cache[model_id] = res
        
        return res
    
    async def _verilink_predict_risk(self, test_config: Dict) -> float:
        """Predict failure probability."""
        fingerprint = hashlib.sha256(
            json.dumps(test_config, sort_keys=True).encode()
        ).hexdigest()
        
        return await self.client.verilink_predict_outcome(
            fingerprint,
            model_id=test_config.get("model_id"),
            test_type=test_config.get("test_type")
        )
    
    def _fail_open_result(self, error_msg: str) -> VeriLinkTestResult:
        """Return fail-open result (pass with warning)"""
        logger.warning(f"VeriLink fail-open: {error_msg}")
        return VeriLinkTestResult(
            passed=True,
            error=error_msg,
            governance_status="degraded",
            details={"mode": "fail_open"}
        )
    
    def get_metadata(self) -> Dict[str, str]:
        """Return plugin metadata."""
        return {
            "name": "VeriLinkOS Governance Plugin",
            "version": self.PLUGIN_VERSION,
            "entry_point": "verilink_os",
            "description": "Active governance integration for AI Verify"
        }
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Return configuration summary."""
        return {
            "api_url": str(self.config.api_url),
            "agent_id": self.config.agent_id,
            "enforce_mode": self.config.enforce_mode.value,
            "predictive_enabled": self.config.predictive_enabled,
            "timeout": self.config.timeout,
            "use_cache": self.config.use_cache,
            "jurisdiction": self.config.jurisdiction,
            "uptime_seconds": time.time() - self._start_time
        }
    
    async def cleanup(self):
        """Clean up resources."""
        await self.client.close()
