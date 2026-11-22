"""Transport-level tests: exact endpoint paths + fail-closed behavior.

These intercept httpx at the transport layer (not by patching
`_verilink_request`), so they prove the actual URL/method the client emits.
No network is used.
"""

import json

import httpx
import pytest

from verilink_plugin import VeriLinkGovernancePlugin


class Recorder:
    def __init__(self, responses):
        self.responses = responses  # list of (status, json_body)
        self.requests = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append({
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.url.params),
            "body": json.loads(request.content) if request.content else None,
        })
        status, body = self.responses[min(len(self.requests) - 1, len(self.responses) - 1)]
        return httpx.Response(status, json=body, request=request)


def _plugin_with(mock_config, responses):
    plugin = VeriLinkGovernancePlugin(mock_config)
    rec = Recorder(responses)
    plugin.client._client = httpx.AsyncClient(
        base_url="http://mock-api.test", transport=httpx.MockTransport(rec.handler)
    )
    return plugin, rec


@pytest.mark.asyncio
async def test_verify_receipt_exact_path_and_status(mock_config):
    plugin, rec = _plugin_with(mock_config, [(200, {"status": "permit_granted"})])
    result = await plugin.client.verilink_verify_receipt("VAP-123")
    assert rec.requests == [{
        "method": "GET", "path": "/v1/vap/receipt/VAP-123",
        "query": {}, "body": None,
    }]
    assert result["verified"] is True


@pytest.mark.asyncio
async def test_verify_receipt_unknown_status_fails_closed(mock_config):
    plugin, rec = _plugin_with(mock_config, [(200, {"status": "pending"})])
    result = await plugin.client.verilink_verify_receipt("VAP-123")
    assert rec.requests[0]["path"] == "/v1/vap/receipt/VAP-123"
    assert result["verified"] is False


@pytest.mark.asyncio
async def test_verify_receipt_server_error_fails_closed(mock_config):
    plugin, rec = _plugin_with(mock_config, [(500, {"detail": "down"})])
    result = await plugin.client.verilink_verify_receipt("VAP-123")
    assert rec.requests[0]["path"] == "/v1/vap/receipt/VAP-123"
    assert result["verified"] is False
    assert result["status"] is None


@pytest.mark.asyncio
async def test_mock_receipt_id_never_issues_request(mock_config):
    plugin, rec = _plugin_with(mock_config, [(200, {"status": "permit_granted"})])
    result = await plugin.client.verilink_verify_receipt("mock-123")
    assert rec.requests == []
    assert result["verified"] is False


@pytest.mark.asyncio
async def test_generate_receipt_exact_path(mock_config):
    plugin, rec = _plugin_with(mock_config, [(201, {"receipt_id": "VAP-REAL-1"})])
    result = await plugin.client.verilink_generate_receipt({"verdict": "allow"})
    assert rec.requests[0]["method"] == "POST"
    assert rec.requests[0]["path"] == "/v1/vap/receipt/generate"
    assert rec.requests[0]["body"]["decision"]["verdict"] == "allow"
    assert result["receipt_id"] == "VAP-REAL-1"


@pytest.mark.asyncio
async def test_evaluate_policy_exact_path(mock_config):
    plugin, rec = _plugin_with(mock_config, [(200, {"verdict": "allow"})])
    await plugin.client.verilink_evaluate_policy({"model_id": "m1", "test_type": "t"})
    req = rec.requests[0]
    assert req["method"] == "POST"
    assert req["path"] == "/v1/policy/evaluate"
    assert req["body"]["action"]["parameters"]["model_id"] == "m1"


@pytest.mark.asyncio
async def test_aibom_exact_path_and_fail_closed(mock_config):
    plugin, rec = _plugin_with(mock_config, [(500, {"detail": "down"})])
    result = await plugin.client.verilink_verify_aibom({"model_id": "m1", "hash": "ab" * 32})
    assert rec.requests[0]["method"] == "POST"
    assert rec.requests[0]["path"] == "/v1/bom/verify"
    assert result["valid"] is False
    assert result["degraded"] is True


@pytest.mark.asyncio
async def test_insurance_exact_path_and_query(mock_config):
    plugin, rec = _plugin_with(mock_config, [(200, {"is_valid": True, "status": "active"})])
    result = await plugin.client.verilink_verify_insurance_policy("POL-1")
    req = rec.requests[0]
    assert req["method"] == "POST"
    assert req["path"] == "/v1/insurance/partners/verify-policy"
    assert req["query"] == {"policy_id": "POL-1"}
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_insurance_fail_closed(mock_config):
    plugin, rec = _plugin_with(mock_config, [(503, {"detail": "down"})])
    result = await plugin.client.verilink_verify_insurance_policy("POL-1")
    assert rec.requests[0]["path"] == "/v1/insurance/partners/verify-policy"
    assert result["valid"] is False
    assert result["degraded"] is True


@pytest.mark.asyncio
async def test_trust_token_exact_path_and_signing_gate(mock_config):
    from verilink_plugin.exceptions import VeriLinkValidationError

    # No private key: fail closed before any HTTP call.
    plugin, rec = _plugin_with(mock_config, [(200, {"token": "t"})])
    with pytest.raises(VeriLinkValidationError):
        await plugin.client.verilink_get_token()
    assert rec.requests == []

    # With a real Ed25519 key, the exact path is used.
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization

    key = ed25519.Ed25519PrivateKey.generate()
    mock_config["private_key_hex"] = key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ).hex()
    plugin, rec = _plugin_with(mock_config, [(200, {"token": "tok-1"})])
    token = await plugin.client.verilink_get_token()
    req = rec.requests[0]
    assert req["method"] == "POST"
    assert req["path"] == "/v1/agents/trust/token"
    assert req["query"]["agent_id"] == str(mock_config["agent_id"])
    assert "signature" in req["query"]
    assert token == "tok-1"


@pytest.mark.asyncio
async def test_health_check_exact_path(mock_config):
    plugin, rec = _plugin_with(mock_config, [(200, {"status": "ok"})])
    assert await plugin.client.verilink_health_check() is True
    assert rec.requests[0] == {
        "method": "GET", "path": "/health", "query": {}, "body": None,
    }
