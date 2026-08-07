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

