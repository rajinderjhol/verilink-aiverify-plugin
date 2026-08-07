"""
VeriLinkOS AI Verify Plugin
"""
from .plugin import VeriLinkGovernancePlugin
from .client import VeriLinkClient
from .models import VeriLinkConfig, VeriLinkTestResult, VeriLinkEnforcementMode
from .exceptions import VeriLinkError

__version__ = "1.2.0"


__all__ = [
    "VeriLinkGovernancePlugin",
    "VeriLinkClient",
    "VeriLinkConfig",
    "VeriLinkTestResult",
    "VeriLinkEnforcementMode",
    "VeriLinkError"
]
