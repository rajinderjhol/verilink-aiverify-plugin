#!/usr/bin/env python3
"""
Quick start example for VeriLinkOS AI Verify Plugin
"""
import asyncio
import os
from verilink_plugin import VeriLinkGovernancePlugin

async def main():
    plugin = VeriLinkGovernancePlugin({
        "api_url": os.getenv("VERILINK_API_URL", "https://api.verilink.os"),
        "api_key": os.getenv("VERILINK_API_KEY", "test_key"),
        "agent_id": os.getenv("VERILINK_AGENT_ID", "test_agent"),
        "organization_id": os.getenv("VERILINK_ORG_ID", "test_org")
    })
    
    result = await plugin.run_test(
        {"model_id": "test-model", "dataset": "test-data"},
        lambda config: {"passed": True, "artifacts": {"test": "result"}}
    )
    
    print(f"✅ Test passed: {result.passed}")
    print(f"📋 Receipt ID: {result.receipt_id}")
    
    await plugin.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
