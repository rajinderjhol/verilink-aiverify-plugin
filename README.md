# VeriLinkOS AI Verify Plugin

[![PyPI version](https://badge.fury.io/py/verilink-aiverify-plugin.svg)](https://badge.fury.io/py/verilink-aiverify-plugin)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

VeriLinkOS AI Verify Plugin integrates active governance capabilities from VeriLinkOS into the AI Verify testing framework.

### Features

- ✅ Active Governance: Real-time policy enforcement during AI tests
- ✅ VAP Receipts: Cryptographic evidence for compliance audits
- ✅ AI-BOM Verification: Ensure model integrity and provenance
- ✅ Trust Tokens: JIT authentication for each test run
- ✅ Predictive Enforcement: ML-based risk prediction

## Installation

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