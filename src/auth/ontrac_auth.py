"""
OnTrac API key authentication module.

Handles API key authentication for OnTrac tracking API access.
"""

import logging
from typing import Optional

from ..config import settings
from ..models import AuthenticationError

logger = logging.getLogger(__name__)


class OnTracAuth:
    """
    OnTrac API key authentication manager.

    Handles API key authentication for OnTrac tracking API access.
    OnTrac uses a simple API key header-based authentication.
    """

    def __init__(self, api_key: Optional[str] = None, account_number: Optional[str] = None,
                 sandbox: Optional[bool] = None):
        """
        Initialize OnTrac authentication.

        Args:
            api_key: OnTrac API key (defaults to config)
            account_number: OnTrac account number (defaults to config)
            sandbox: Use sandbox environment (defaults to config)
        """
        self.api_key = api_key or settings.ontrac_api_key
        self.account_number = account_number or settings.ontrac_account_number
        self.sandbox = sandbox if sandbox is not None else settings.ontrac_sandbox

        if not self.api_key:
            raise AuthenticationError("OnTrac API key is required")

        # Reason: OnTrac uses the same URL for sandbox and production
        self.base_url = settings.ontrac_base_url

    async def get_auth_headers(self) -> dict:
        """
        Get HTTP headers for OnTrac API requests.
        
        OnTrac uses query parameters for authentication, not headers.
        Returns basic headers for XML content.

        Returns:
            dict: Basic headers for OnTrac API
        """
        headers = {
            "Content-Type": "application/xml",
            "Accept": "application/xml",
            "User-Agent": "TrackingMCP/1.0"
        }
        
        logger.debug("OnTrac auth headers: Content-Type=application/xml")
        
        return headers

    def get_auth_params(self) -> dict:
        """
        Get query parameters for OnTrac API authentication.
        
        OnTrac uses the 'pw' parameter for API authentication.

        Returns:
            dict: Query parameters including API password

        Raises:
            AuthenticationError: If API key is not configured
        """
        if not self.api_key:
            raise AuthenticationError("OnTrac API key is not configured")

        params = {
            "pw": self.api_key
        }
        
        # Log params for debugging (without exposing the full API key)
        logger.debug(f"OnTrac auth params: pw={self.api_key[:8]}...")
        
        return params

    def clear_token(self) -> None:
        """Clear token method for compatibility with other auth modules."""
        # Reason: OnTrac uses API key, not tokens, so nothing to clear
        logger.info("OnTrac uses API key authentication, no token to clear")