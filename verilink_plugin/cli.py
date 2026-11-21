"""
VeriLinkOS AI Verify Plugin CLI Tool
Command line developer utility for testing connectivity, receipts, and insurance policies.
"""
import sys
import argparse
import asyncio
import json
from .plugin import VeriLinkGovernancePlugin

def main():
    parser = argparse.ArgumentParser(
        description="VeriLinkOS AI Verify Plugin Developer CLI"
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--api-url", default="http://localhost:8000", help="VeriLinkOS API endpoint URL")
    common.add_argument("--api-key", default="test_admin_key", help="VeriLinkOS API Key")
    common.add_argument("--agent-id", default="00000000-0000-0000-0000-000000000001", help="Agent UUID")
    common.add_argument("--org-id", default="00000000-0000-0000-0000-000000000000", help="Organization UUID")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands", parser_class=lambda **kw: argparse.ArgumentParser(parents=[common], **kw))

    # Command: health
    subparsers.add_parser("health", help="Check VeriLinkOS server health status")

    # Command: check-policy
    policy_parser = subparsers.add_parser("check-policy", help="Verify active AI Insurance policy")
    policy_parser.add_argument("policy_id", help="Insurance Policy ID")

    # Command: verify-receipt
    receipt_parser = subparsers.add_parser("verify-receipt", help="Verify a VAP receipt ID")
    receipt_parser.add_argument("receipt_id", help="VAP Receipt ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    plugin = VeriLinkGovernancePlugin({
        "api_url": args.api_url,
        "api_key": args.api_key,
        "agent_id": args.agent_id,
        "organization_id": args.org_id
    })

    async def run_cli():
        try:
            if args.command == "health":
                is_healthy = await plugin.client.verilink_health_check()
                if is_healthy:
                    print(f"✅ VeriLinkOS API at '{args.api_url}' is ONLINE & HEALTHY.")
                else:
                    print(f"❌ VeriLinkOS API at '{args.api_url}' is UNREACHABLE or DEGRADED.")
                    sys.exit(1)

            elif args.command == "check-policy":
                print(f"📡 Querying AI Insurance Policy: {args.policy_id}...")
                res = await plugin.client.verilink_verify_insurance_policy(args.policy_id)
                print(json.dumps(res, indent=2))

            elif args.command == "verify-receipt":
                print(f"📡 Verifying VAP Receipt: {args.receipt_id}...")
                res = await plugin.client.verilink_verify_receipt(args.receipt_id)
                print(json.dumps(res, indent=2))

        finally:
            await plugin.cleanup()

    asyncio.run(run_cli())

if __name__ == "__main__":
    main()
