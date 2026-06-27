import pytest
from verilink_plugin import VeriLinkGovernancePlugin

@pytest.mark.asyncio
async def test_plugin_metadata(mock_config):
    plugin = VeriLinkGovernancePlugin(mock_config)
    metadata = plugin.get_metadata()
    
    assert metadata["name"] == "VeriLinkOS Governance Plugin"
    assert metadata["version"] == "1.0.0"
    assert metadata["entry_point"] == "verilink_os"
