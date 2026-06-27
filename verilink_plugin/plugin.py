"""
Main VeriLinkOS Governance Plugin for AI Verify
"""

import logging
import asyncio
import hashlib
import json
from typing import Dict, Any, Optional, Callable

from .models import VeriLinkConfig, VeriLinkTestResult, VeriLinkEnforcementMode
from .client import VeriLinkClient
from .exceptions import VeriLinkAuthError

logger = logging.getLogger("verilink_plugin")

class VeriLinkGovernancePlugin:
    """Main integration plugin for AI Verify"""
    
    PLUGIN_ID = "verilink_os_governance"
    PLUGIN_VERSION = "1.0.0"
    
    def __init__(self, config_dict: Optional[Dict] = None):
        self.config = VeriLinkConfig(**(config_dict or {}))
        self.client = VeriLinkClient(self.config)
        self._aibom_cache: Dict[str, Any] = {}
        self._initialized = False
    
    async def verilink_setup(self):
        """Initialize the plugin and check connectivity"""
        try:
            if await self.client.verilink_health_check():
                self._initialized = True
                logger.info("VeriLinkOS connection established")
            else:
                logger.warning("VeriLinkOS API unreachable. Operating in fail-safe mode.")
                self._initialized = False
        except Exception as e:
            logger.error(f"VeriLink setup failed: {str(e)}")
            self._initialized = False
    
    async def run_test(self, test_config: Dict[str, Any], test_func: Callable) -> VeriLinkTestResult:
        """Run an AI test with VeriLinkOS governance"""
        try:
            if not self._initialized:
                await self.verilink_setup()
            
            # 1. Predictive enforcement
            if self.config.predictive_enabled:
                prediction = await self._verilink_predict_risk(test_config)
                if prediction > 0.8 and self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                    return VeriLinkTestResult(
                        passed=False, 
                        error="Predictive block: high risk detected",
                        prediction_score=prediction,
                        governance_status="blocked"
                    )
            
            # 2. Get trust token
            try:
                await self.client.verilink_get_token()
                logger.info("VeriLink trust token acquired")
            except Exception as e:
                if self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                    return VeriLinkTestResult(
                        passed=False,
                        error=f"Authentication failed: {str(e)}",
                        governance_status="blocked"
                    )
                return self._fail_open_result(str(e))
            
            # 3. Verify AI-BOM
            try:
                aibom_status = await self._verilink_check_aibom(test_config)
                if not aibom_status.get("valid") and self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                    return VeriLinkTestResult(
                        passed=False,
                        error="AI-BOM Verification Failed: Model not registered or tampered",
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
            
            # 4. Run the actual test
            test_start_time = asyncio.get_event_loop().time()
            test_raw_result = await test_func(test_config)
            test_duration = asyncio.get_event_loop().time() - test_start_time
            
            # 5. Generate VAP receipt
            evidence = {
                "test_config": test_config,
                "raw_result": test_raw_result,
                "duration": test_duration,
                "timestamp": asyncio.get_event_loop().time()
            }
            receipt_data = await self.client.verilink_generate_receipt(evidence)
            
            # 6. Verify the receipt
            verification = await self.client.verilink_verify_receipt(receipt_data["receipt_id"])
            is_verified = verification.get("verified", False)
            
            return VeriLinkTestResult(
                passed=test_raw_result.get("passed", False),
                receipt_id=receipt_data["receipt_id"],
                verification_url=f"{self.config.api_url}/verify/{receipt_data['receipt_id']}",
                merkle_root=receipt_data.get("merkle_root"),
                details={
                    "receipt_verified": is_verified,
                    "duration": test_duration,
                    "governance_mode": self.config.enforce_mode.value
                },
                artifacts=test_raw_result.get("artifacts", {}),
                governance_status="approved" if is_verified else "pending"
            )
            
        except VeriLinkAuthError as e:
            if self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                raise
            return self._fail_open_result(str(e))
            
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
        """Check AI-BOM with caching"""
        model_id = test_config.get("model_id", "default")
        
        if self.config.use_cache and model_id in self._aibom_cache:
            logger.debug(f"AI-BOM cache hit for {model_id}")
            return self._aibom_cache[model_id]
        
        res = await self.client.verilink_verify_aibom({"model_id": model_id})
        
        if self.config.use_cache:
            self._aibom_cache[model_id] = res
        
        return res
    
    async def _verilink_predict_risk(self, test_config: Dict) -> float:
        """Predict failure probability"""
        fingerprint = hashlib.sha256(
            json.dumps(test_config, sort_keys=True).encode()
        ).hexdigest()
        
        return await self.client.verilink_predict_outcome(fingerprint)
    
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
        """Return plugin metadata for AI Verify"""
        return {
            "name": "VeriLinkOS Governance Plugin",
            "version": self.PLUGIN_VERSION,
            "entry_point": "verilink_os",
            "description": "Active governance integration for AI Verify"
        }
    
    async def cleanup(self):
        """Clean up resources"""
        await self.client.close()
