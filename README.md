# VeriLinkOS AI Verify Plugin v1.2.0

[![PyPI version](https://badge.fury.io/py/verilink-aiverify-plugin.svg)](https://badge.fury.io/py/verilink-aiverify-plugin)
[![VeriLinkOS Compatibility](https://img.shields.io/badge/VeriLinkOS-v3.7.0-purple.svg)](https://github.com/rajinderjhol/VeriLinkOS)
[![VAP Protocol](https://img.shields.io/badge/protocol-Open_VAP_v3.0-blue.svg)](https://github.com/rajinderjhol/VeriLinkOS)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

## 📖 Introduction

VeriLinkOS AI Verify Plugin (v1.2.0) integrates **active governance and cryptographic insurance verification** from [VeriLinkOS v3.7.0](https://github.com/rajinderjhol/VeriLinkOS) into the [AI Verify](https://github.com/aiverify-foundation/aiverify) testing framework. It provides real-time enforcement, cryptographic VAP receipts, AI-BOM integrity checks, and parametric AI insurance policy verification.

By bridging testing with governance and insurance underwriting, this plugin ensures that AI models are not only accurate but also ethically aligned, cryptographically bound, and insured throughout their evaluation lifecycle.

### 🎯 Key Capabilities (v1.2.0)

- **🛡️ Active Governance**: Intercept and evaluate AI testing actions **before** execution occurs.
- **🔐 Open VAP v3.0 Receipts**: Server-issued Ed25519-signed receipts with a local Merkle commitment. Multi-hash batching is available server-side via `/v1/anchoring/batches`.
- **🔥 VeriLink Assurance AI Insurance**: Verify active underwriting policy status (`/v1/insurance/partners/verify-policy`).
- **🧰 Developer CLI Utility (`verilink-verify`)**: Test connection health, policies, and receipts directly from the command line.
- **⚡ Synchronous Wrapper (`run_test_sync`)**: Execute governance tests in non-`async` test runners without event loop boilerplate.
- **✅ AI-BOM 2.0 & CycloneDX Verification**: Ensure model weight integrity with SHA-256 checksums and SBOM provenance.
- **🔑 JIT Trust Tokens**: Cryptographically signed JIT authentication for test sessions.
- **🧠 Predictive Risk Enforcement**: Preemptively block high-risk tests based on ML failure prediction.

For a deep dive into the technical architecture, refer to the [Technical Specification](./SPECIFICATION.md).

---

## ⚙️ Setup & Installation

```bash
pip install verilink-aiverify-plugin
```

---

## 🧰 Developer CLI (`verilink-verify`)

The plugin includes a command-line tool for debugging and diagnostic checks:

```bash
# Check server connectivity and health status
verilink-verify health --api-url http://localhost:8000

# Verify active AI Assurance policy status
verilink-verify check-policy POL-2026-SG-001 --api-url http://localhost:8000

# Verify a VAP receipt ID
verilink-verify verify-receipt VAP-RECEIPT-ID
```

---

## 🚀 Quick Start

### Option A: Asynchronous (`async/await`)

```python
import asyncio
from verilink_plugin import VeriLinkGovernancePlugin, VeriLinkError

async def my_ai_test(config):
    """AI Verify test logic execution."""
    await asyncio.sleep(0.1)
    return {"passed": True, "artifacts": {"accuracy": 0.98, "bias_score": 0.01}}

async def main():
    # Initialize plugin for VeriLinkOS v3.7.0
    plugin = VeriLinkGovernancePlugin({
        "api_url": "http://localhost:8000",
        "api_key": "test_admin_key",
        "agent_id": "agent-verify-001",
        "organization_id": "org-verify-001"
    })
    
    try:
        # 1. Verify active AI Insurance policy
        insurance_check = await plugin.client.verilink_verify_insurance_policy("POL-2026-SG-001")
        print(f"🛡️ Insurance Coverage Active: {insurance_check.get('valid')}")

        # 2. Run test with VeriLinkOS active governance
        result = await plugin.run_test(
            {"model_id": "model-001", "dataset": "clinical-eval-v1"},
            my_ai_test
        )
        
        print(f"✅ Test Result: {'PASSED' if result.passed else 'FAILED'}")
        print(f"📋 Receipt ID: {result.receipt_id}")
        
    except VeriLinkError as e:
        print(f"❌ Governance Error: {e}")
    finally:
        await plugin.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### Option B: Synchronous (`run_test_sync`)

For synchronous testing environments (e.g. standard `unittest` or sync scripts):

```python
from verilink_plugin import VeriLinkGovernancePlugin

plugin = VeriLinkGovernancePlugin(config)

# Run test synchronously
result = plugin.run_test_sync(
    {"model_id": "model-001"},
    my_sync_test_func
)
print(f"Status: {result.governance_status}")
```

---

## 🔧 Error Handling

| Exception | Description |
|-----------|-------------|
| `VeriLinkConnectionError` | Cannot connect to VeriLinkOS API |
| `VeriLinkAuthError` | Invalid API credentials or signature |
| `VeriLinkTimeoutError` | Request timed out |
| `VeriLinkValidationError` | Missing Ed25519 key or invalid signing payload |
| `VeriLinkConfigError` | Invalid configuration values (agent IDs must be UUIDs) |

---

## 📄 License

Apache 2.0 - See [LICENSE](./LICENSE) for details.

---

## 🔗 Links

- **VeriLinkOS Kernel Repository**: https://github.com/rajinderjhol/VeriLinkOS
- **PyPI**: https://pypi.org/project/verilink-aiverify-plugin/
- **Quickstart Demo**: [`examples/quickstart.py`](./examples/quickstart.py)
---

To set up full demo, please contact rajinderjhol@gmail.com

**Made with ❤️ for the AI governance community**

