"""
Main VeriLinkOS Governance Plugin for AI Verify
"""
import inspect
import logging
import os
import asyncio
import hashlib
import threading
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
from .exceptions import (
    VeriLinkAuthError,
    VeriLinkConfigError,
    VeriLinkReceiptError,
    VeriLinkValidationError,
)

logger = logging.getLogger("verilink_plugin")

class VeriLinkGovernancePlugin:
    """Main integration plugin for AI Verify"""
    
    PLUGIN_ID = "verilink_os_governance"
    PLUGIN_VERSION = "1.2.0"
    
    def __init__(self, config_dict: Optional[Dict] = None):
        """Initialize plugin with validated configuration.

        Explicit values win; remaining fields fall back to VERILINK_* env vars.
        """
        env_config = {}
        env_map = {
            "api_url": "VERILINK_API_URL",
            "api_key": "VERILINK_API_KEY",
            "agent_id": "VERILINK_AGENT_ID",
            "organization_id": "VERILINK_ORG_ID",
            "private_key_hex": "VERILINK_PRIVATE_KEY_HEX",
        }
        for field, key in env_map.items():
            value = os.getenv(key)
            if value:
                env_config[field] = value
        env_config.update(config_dict or {})
        try:
            self.config = VeriLinkConfig(**env_config)
            logger.info("Configuration validated successfully")
            
            if self.config.predictive_enabled and not self.config.private_key_hex:
                logger.warning(
                    "No Ed25519 private key configured: JIT trust tokens cannot "
                    "be issued. Block mode will refuse to govern tests."
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
    
    def run_test_sync(self, test_config: Dict[str, Any], test_func: Callable) -> VeriLinkTestResult:
        """Synchronous wrapper that works even inside a running event loop.

        Uses a dedicated thread with its own loop, avoiding the undeclared
        `nest_asyncio` dependency.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run_test(test_config, test_func))

        box: Dict[str, Any] = {}

        def worker():
            box["result"] = asyncio.run(self.run_test(test_config, test_func))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        thread.join()
        return box["result"]

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
            
            # 3. Evaluate the action against live policy (real governance)
            try:
                decision = await self.client.verilink_evaluate_policy(test_config)
                effect = str(decision.get("effect", "")).upper()
                if effect in {"DENY", "BLOCK"} and self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                    return VeriLinkTestResult(
                        passed=False,
                        error=f"Policy denied the test action: {decision.get('block_reason') or effect}",
                        governance_status="blocked",
                    )
                if effect == "REQUIRE_HUMAN_APPROVAL" and self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                    return VeriLinkTestResult(
                        passed=False,
                        error="Policy requires human approval before this test may run",
                        governance_status="blocked",
                    )
            except Exception as e:
                if self.config.enforce_mode == VeriLinkEnforcementMode.BLOCK:
                    return VeriLinkTestResult(
                        passed=False, error=f"Policy evaluation failed: {e}",
                        governance_status="blocked",
                    )
                logger.warning(f"Policy evaluation degraded: {e}")

            # 4. Verify AI-BOM
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
            
            # 5. Run the test (sync or async callbacks are both supported)
            test_start = time.time()
            raw = test_func(test_config)
            test_raw_result = await raw if inspect.isawaitable(raw) else raw
            if not isinstance(test_raw_result, dict):
                raise VeriLinkValidationError("test callback must return a dict")
            test_duration = time.time() - test_start

            passed = bool(test_raw_result.get("passed", False))

            # 6. Generate VAP receipt with the verdict derived from the result
            evidence = {
                "test_config": test_config,
                "raw_result": test_raw_result,
                "duration": test_duration,
                "timestamp": datetime.now().isoformat(),
                "verdict": "allow" if passed else "block",
                "confidence": 100 if passed else 0,
            }

            receipt_data = await self.client.verilink_generate_receipt(evidence)
            receipt_id = receipt_data.get("receipt_id")
            if not receipt_id:
                raise VeriLinkReceiptError("receipt response contained no receipt_id")

            # 7. Verify the receipt against the real ledger
            verification = await self.client.verilink_verify_receipt(receipt_id)
            is_verified = verification.get("verified", False)
            
            return VeriLinkTestResult(
                passed=passed,
                receipt_id=receipt_id,
                verification_url=f"{self.config.api_url}/verify/{receipt_id}",
                merkle_root=receipt_data.get("merkle_root"),
                details={
                    "receipt_verified": is_verified,
                    "duration": test_duration,
                    "governance_mode": self.config.enforce_mode.value,
                },
                artifacts=test_raw_result.get("artifacts", {}),
                governance_status="approved" if is_verified else "degraded",
                prediction_score=prediction,
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
            cached_at, cached = self._aibom_cache[model_id]
            if time.time() - cached_at < self.config.cache_ttl:
                return cached

        res = await self.client.verilink_verify_aibom({
            "model_id": model_id,
            "hash": model_hash
        })

        if self.config.use_cache:
            self._aibom_cache[model_id] = (time.time(), res)

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
        """Advisory-mode result: never claim a pass when governance failed."""
        logger.warning(f"VeriLink governance degraded: {error_msg}")
        return VeriLinkTestResult(
            passed=False,
            error=error_msg,
            governance_status="degraded",
            details={"mode": "advisory_degraded"}
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
