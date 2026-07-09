# VeriLinkOS AI Verify Plugin

[![PyPI version](https://badge.fury.io/py/verilink-aiverify-plugin.svg)](https://badge.fury.io/py/verilink-aiverify-plugin)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/pypi/pyversions/verilink-aiverify-plugin.svg)](https://pypi.org/project/verilink-aiverify-plugin)
[![Downloads](https://img.shields.io/pypi/dm/verilink-aiverify-plugin.svg)](https://pypi.org/project/verilink-aiverify-plugin)

## 📖 Introduction

VeriLinkOS AI Verify Plugin integrates **active governance capabilities** from [VeriLinkOS](https://verilink.io) into the [AI Verify](https://github.com/aiverify-foundation/aiverify) testing framework. It provides real-time enforcement, cryptographic evidence, and compliance guardrails for AI testing.

By bridging testing with governance, this plugin ensures that AI models are not only accurate but also ethically aligned and legally compliant throughout their evaluation lifecycle.

### 🎯 Key Capabilities

- **🛡️ Active Governance**: Prevent unauthorized AI actions **before** they occur
- **🔐 Cryptographic Receipts**: Tamper-evident VAP receipts with Merkle-tree batching
- **✅ AI-BOM Verification**: Ensure model integrity and provenance
- **🔑 Trust Tokens**: JIT authentication for each test session
- **🧠 Predictive Enforcement**: ML-based risk prediction to preemptively block risky tests

For a deep dive into the technical architecture, please refer to the [Technical Specification](./SPECIFICATION.md).

---

## ⚙️ Setup

### Installation

```bash
pip install verilink-aiverify-plugin
```

### Configuration

The plugin can be configured using environment variables or by passing a dictionary directly to the constructor.

#### Option 1: Environment Variables

```bash
export VERILINK_API_URL=https://api.verilink.os
export VERILINK_API_KEY=your_api_key
export VERILINK_AGENT_ID=your_agent_id
export VERILINK_ORG_ID=your_organization_id
export VERILINK_ENFORCE_MODE=block  # Optional: block, warn, log, observe
```

#### Option 2: Inline Dictionary

```python
from verilink_plugin import VeriLinkGovernancePlugin

config = {
    "api_url": "https://api.verilink.os",
    "api_key": "your_api_key",
    "agent_id": "agent_001",
    "organization_id": "org_001"
}
plugin = VeriLinkGovernancePlugin(config)
```

---

## 🚀 Quick Start

```python
import asyncio
from verilink_plugin import VeriLinkGovernancePlugin, VeriLinkError

async def my_ai_test(config):
    """Your AI Verify test logic here."""
    # Simulate test execution
    await asyncio.sleep(0.1)
    return {"passed": True, "artifacts": {"accuracy": 0.98}}

async def test_model():
    # Initialize plugin
    plugin = VeriLinkGovernancePlugin({
        "api_url": "http://localhost:8000",  # Your VeriLinkOS URL
        "api_key": "your_api_key",
        "agent_id": "your_agent_id",
        "organization_id": "your_org_id"
    })
    
    try:
        # Run test with governance
        result = await plugin.run_test(
            {"model_id": "model-001", "dataset": "test-data"},
            my_ai_test
        )
        
        print(f"✅ Test Result: {'PASSED' if result.passed else 'FAILED'}")
        print(f"📋 Receipt ID: {result.receipt_id}")
        print(f"🔗 Verification: {result.verification_url}")
        
    except VeriLinkError as e:
        print(f"❌ Governance Error: {e}")
    finally:
        await plugin.cleanup()

asyncio.run(test_model())
```

---

## 🔧 Error Handling

The plugin raises specific exceptions for different error scenarios:

| Exception | Description |
|-----------|-------------|
| `VeriLinkConnectionError` | Cannot connect to VeriLinkOS API |
| `VeriLinkAuthError` | Invalid API credentials or signature |
| `VeriLinkTimeoutError` | Request timed out |
| `VeriLinkValidationError` | Invalid configuration |
| `VeriLinkConfigError` | Configuration validation failed |

```python
from verilink_plugin import (
    VeriLinkGovernancePlugin,
    VeriLinkConnectionError,
    VeriLinkAuthError
)

try:
    plugin = VeriLinkGovernancePlugin(config)
    result = await plugin.run_test(test_config, test_func)
except VeriLinkConnectionError:
    print("⚠️ Cannot reach VeriLinkOS. Check your connection.")
except VeriLinkAuthError:
    print("🔒 Authentication failed. Check your API key.")
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details on our code of conduct and development process.

---

## 📄 License

Apache 2.0 - See [LICENSE](./LICENSE) for details.

---

## 🔗 Links

- **PyPI**: https://pypi.org/project/verilink-aiverify-plugin/
- **GitHub**: https://github.com/rajinderjhol/verilink-aiverify-plugin
- **Issues**: https://github.com/rajinderjhol/verilink-aiverify-plugin/issues
- **Specification**: [SPECIFICATION.md](./SPECIFICATION.md)

---

This plug-in is currently unplugged from VeriLinkOS core Trust Infrastructure. We will be carefully release more code for open-source development.

To set up full demo, please contact rajinderjhol@gmail.com  



**Made with ❤️ for the AI governance community**
