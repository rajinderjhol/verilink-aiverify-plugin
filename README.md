# VeriLinkOS AI Verify Plugin

[![PyPI version](https://badge.fury.io/py/verilink-aiverify-plugin.svg)](https://badge.fury.io/py/verilink-aiverify-plugin)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/pypi/pyversions/verilink-aiverify-plugin.svg)](https://pypi.org/project/verilink-aiverify-plugin)
[![Downloads](https://img.shields.io/pypi/dm/verilink-aiverify-plugin.svg)](https://pypi.org/project/verilink-aiverify-plugin)

## 📖 Overview

VeriLinkOS AI Verify Plugin integrates **active governance capabilities** from [VeriLinkOS](https://verilink.io) into the [AI Verify](https://github.com/aiverify-foundation/aiverify) testing framework. It provides real-time enforcement, cryptographic evidence, and compliance guardrails for AI testing.

### 🎯 Why Use This Plugin?

- **🛡️ Active Governance**: Prevent unauthorized AI actions **before** they occur
- **🔐 Cryptographic Receipts**: Tamper-evident VAP receipts with Merkle-tree batching
- **✅ AI-BOM Verification**: Ensure model integrity and provenance
- **🔑 Trust Tokens**: JIT authentication for each test session
- **🧠 Predictive Enforcement**: ML-based risk prediction to preemptively block risky tests
- **⚖️ Constitutional AI**: Ethical and legal guardrails via MetaRuleSet
- **👥 Multi-Agent Arbitration**: Conflict resolution for resource contention

---

## 🚀 Installation

### From PyPI (Recommended)
```bash
pip install verilink-aiverify-plugin
```

## Configuration
Set environment variables:

```bash
export VERILINK_API_URL=https://api.verilink.os
export VERILINK_API_KEY=your_api_key
export VERILINK_AGENT_ID=your_agent_id
export VERILINK_ORG_ID=your_org_id
```

## Quick Start
```python
import asyncio
from verilink_plugin import VeriLinkGovernancePlugin

async def test_model():
    plugin = VeriLinkGovernancePlugin()
    
    result = await plugin.run_test(
        {"model_id": "model-001", "dataset": "test-data"},
        lambda config: {"passed": True, "artifacts": {}}
    )
    
    print(f"Passed: {result.passed}")
    print(f"Receipt: {result.receipt_id}")
    
    await plugin.cleanup()

asyncio.run(test_model())
```

## License
Apache 2.0