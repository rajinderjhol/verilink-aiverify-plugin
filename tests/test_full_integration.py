# test_full_integration.py
import asyncio
import os
import sys
from dotenv import load_dotenv
from verilink_plugin import VeriLinkGovernancePlugin

# Load .env file if it exists
load_dotenv()

async def main():
    # Default to localhost, but override via environment for live testing
    api_url = os.getenv("VERILINK_API_URL", "http://localhost:8000")

    # Validate required environment variables
    required_vars = ["VERILINK_API_KEY", "VERILINK_AGENT_ID", "VERILINK_ORG_ID"]
    missing_vars = [v for v in required_vars if not os.getenv(v)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("💡 Set them in a .env file or export them in your terminal to continue.")
        sys.exit(1)

    plugin = VeriLinkGovernancePlugin({
        "api_url": api_url,
        "api_key": os.getenv("VERILINK_API_KEY"),
        "agent_id": os.getenv("VERILINK_AGENT_ID"),
        "organization_id": os.getenv("VERILINK_ORG_ID")
    })
    
    try:
        print(f"📡 Connecting to VeriLinkOS at: {api_url}")
        print("🚀 Starting integration test...")

        # Test a simple action
        result = await plugin.run_test(
            {"model_id": "test-model"},
            lambda config: {"passed": True}
        )
        
        print(f"✅ Test result: {result.passed}")
        print(f"📋 Receipt ID: {result.receipt_id}")
        if result.verification_url:
            print(f"🔗 Verification URL: {result.verification_url}")

    except Exception as e:
        print(f"❌ Integration test failed!")
        print(f"📝 Error: {e}")
        sys.exit(1)
    finally:
        await plugin.cleanup()

asyncio.run(main())