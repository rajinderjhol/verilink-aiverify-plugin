import pytest
from verilink_plugin import VeriLinkGovernancePlugin

@pytest.mark.asyncio
async def test_plugin_metadata(mock_config):
    plugin = VeriLinkGovernancePlugin(mock_config)
    metadata = plugin.get_metadata()
    
    assert metadata["name"] == "VeriLinkOS Governance Plugin"
    assert metadata["entry_point"] == "verilink_os"

@pytest.mark.asyncio
async def test_client_insurance_verification(mock_config):
    plugin = VeriLinkGovernancePlugin(mock_config)
    res = await plugin.client.verilink_verify_insurance_policy("POL-12345")
    assert "valid" in res
    assert res["valid"] is False, "failed verification must fail closed"


@pytest.mark.asyncio
async def test_aibom_failure_fails_closed(mock_config, monkeypatch):
    plugin = VeriLinkGovernancePlugin(mock_config)

    async def fail(*args, **kwargs):
        raise Exception("404 endpoint not found")

    monkeypatch.setattr(plugin.client, "_verilink_request", fail)
    result = await plugin.client.verilink_verify_aibom({"model_id": "m"})
    assert result["valid"] is False


@pytest.mark.asyncio
async def test_receipt_accepts_real_ledger_statuses(mock_config, monkeypatch):
    plugin = VeriLinkGovernancePlugin(mock_config)

    async def ok(method, endpoint, data=None):
        return {"status": "permit_granted"}

    monkeypatch.setattr(plugin.client, "_verilink_request", ok)
    result = await plugin.client.verilink_verify_receipt("VAP-123")
    assert result["verified"] is True


@pytest.mark.asyncio
async def test_receipt_missing_fails_closed(mock_config, monkeypatch):
    plugin = VeriLinkGovernancePlugin(mock_config)

    async def missing(*args, **kwargs):
        raise Exception("404 not found")

    monkeypatch.setattr(plugin.client, "_verilink_request", missing)
    result = await plugin.client.verilink_verify_receipt("VAP-missing")
    assert result["verified"] is False

