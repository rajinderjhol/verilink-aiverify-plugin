"""
Custom exceptions for VeriLinkOS plugin
"""

class VeriLinkError(Exception):
    """Base exception for all VeriLink plugin errors."""
    pass

class VeriLinkConnectionError(VeriLinkError):
    """Raised when the plugin cannot connect to VeriLinkOS API."""
    pass

class VeriLinkAuthError(VeriLinkError):
    """Raised on authentication failures."""
    pass

class VeriLinkValidationError(VeriLinkError):
    """Raised when configuration or payload validation fails."""
    pass

class VeriLinkTimeoutError(VeriLinkError):
    """Raised when a VeriLinkOS operation times out."""
    pass

class VeriLinkConfigError(VeriLinkError):
    """Raised when configuration is invalid."""
    pass

class VeriLinkReceiptError(VeriLinkError):
    """Raised when receipt generation or verification fails."""
    pass
