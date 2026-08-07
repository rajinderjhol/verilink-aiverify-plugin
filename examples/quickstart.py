"""
VeriLinkOS AI Verify Plugin - Developer Quickstart Example
Demonstrates active AI governance, AI insurance policy verification, and receipt generation.
"""
import asyncio
import os
from verilink_plugin import VeriLinkGovernancePlugin, VeriLinkError

async def evaluate_clinical_ai_model(test_config):
    """Simulated AI model test logic."""
    print(f"🤖 Executing AI test for model '{test_config.get('model_id')}'...")
    await asyncio.sleep(0.1)
    
    return {
        "passed": True,
        "artifacts": {
            "model_accuracy": 0.984,
            "demographic_bias_score": 0.008,
            "latency_ms": 42
        }
    }

async def main():
    print("==================================================")
    print("🚀 VeriLinkOS v3.0.0 AI Governance Quickstart")
    print("==================================================")

    # 1. Initialize plugin
    plugin = VeriLinkGovernancePlugin({
        "api_url": os.getenv("VERILINK_API_URL", "http://localhost:8000"),
        "api_key": os.getenv("VERILINK_API_KEY", "test_admin_key"),
        "agent_id": os.getenv("VERILINK_AGENT_ID", "agent-quickstart-001"),
        "organization_id": os.getenv("VERILINK_ORG_ID", "org-quickstart-001"),
        "enforce_mode": "block",
        "predictive_enabled": True
    })

    try:
        # 2. Check server health
        healthy = await plugin.client.verilink_health_check()
        print(f"📡 Connectivity Status: {'ONLINE' if healthy else 'DEGRADED/MOCK'}")

        # 3. Check AI Insurance coverage
        policy_id = "POL-2026-CLINICAL-001"
        print(f"🛡️ Checking AI Insurance Policy: {policy_id}...")
        ins_status = await plugin.client.verilink_verify_insurance_policy(policy_id)
        print(f"   Status: {'ACTIVE' if ins_status.get('valid') else 'UNVERIFIED'}")

        # 4. Run test with VeriLinkOS kernel governance
        test_config = {
            "model_id": "med-llm-v3",
            "model_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "test_type": "clinical_bias_audit"
        }

        result = await plugin.run_test(test_config, evaluate_clinical_ai_model)

        print("\n--------------------------------------------------")
        print(f"✅ Governance Result: {'PASSED' if result.passed else 'BLOCKED'}")
        print(f"📋 VAP Receipt ID: {result.receipt_id}")
        if result.verification_url:
            print(f"🔗 Verification URL: {result.verification_url}")
        print("--------------------------------------------------")

    except VeriLinkError as err:
        print(f"❌ Governance Block / Error: {err}")
    finally:
        await plugin.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
