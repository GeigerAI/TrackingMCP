"""
UPS OAuth authentication module using client credentials flow.

Simplified approach matching the official UPS MCP implementation.
Uses client_credentials flow instead of authorization_code flow.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

from ..config import settings
from ..models import AuthenticationError, AuthToken

logger = logging.getLogger(__name__)


class UPSAuth:
    """
    UPS OAuth2 authentication manager using client credentials flow.
    
    Simplified approach that matches the official UPS MCP implementation.
    Uses client_credentials grant type instead of authorization_code flow.
    """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None,
                 sandbox: Optional[bool] = None):
        """
        Initialize UPS authentication.
        
        Args:
            client_id: UPS API client ID (defaults to config)
            client_secret: UPS API client secret (defaults to config) 
            sandbox: Use sandbox environment (defaults to config)
        """
        self.client_id = client_id or settings.ups_client_id
        self.client_secret = client_secret or settings.ups_client_secret
        self.sandbox = sandbox if sandbox is not None else settings.ups_sandbox

        if not self.client_id or not self.client_secret:
            raise AuthenticationError("UPS client ID and secret are required")

        # Reason: Use sandbox or production URLs based on environment
        if self.sandbox:
            self.base_url = "https://wwwcie.ups.com"
        else:
            self.base_url = "https://onlinetools.ups.com"
            
        self._token: Optional[AuthToken] = None
        self._refresh_lock = asyncio.Lock()

    @property
    def is_token_valid(self) -> bool:
        """
        Check if current token is valid and not expired.
        
        Returns:
            bool: True if token exists and is not expired
        """
        if not self._token:
            return False

        # Reason: Add buffer to ensure token doesn't expire during request
        buffer_time = timedelta(seconds=int(settings.token_refresh_buffer))
        return datetime.now() < (self._token.expires_at - buffer_time)

    async def get_access_token(self) -> str:
        """
        Get valid OAuth access token, refreshing if necessary.
        
        Returns:
            str: Valid OAuth access token
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if self.is_token_valid:
            return self._token.access_token

        # Reason: Use lock to prevent multiple simultaneous token refresh attempts
        async with self._refresh_lock:
            # Double-check pattern: another coroutine might have refreshed the token
            if self.is_token_valid:
                return self._token.access_token

            logger.info("Refreshing UPS OAuth token")
            await self._refresh_token()
            return self._token.access_token

    async def _refresh_token(self) -> None:
        """
        Refresh the OAuth token using client_credentials flow.
        
        Raises:
            AuthenticationError: If token refresh fails
        """
        url = f"{self.base_url}/security/v1/oauth/token"

        # Reason: UPS requires client_credentials flow for service-to-service auth
        data = {
            "grant_type": "client_credentials"
        }

        # Reason: UPS requires basic auth with client credentials
        auth = (self.client_id, self.client_secret)

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            async with httpx.AsyncClient(timeout=int(settings.request_timeout)) as client:
                logger.debug(f"Requesting UPS token from {url}")

                response = await client.post(url, data=data, headers=headers, auth=auth)

                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("Successfully obtained UPS OAuth token")

                    # Reason: Calculate exact expiration time for proactive refresh
                    expires_in_seconds = int(token_data["expires_in"])
                    expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)

                    self._token = AuthToken(
                        access_token=token_data["access_token"],
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_in=expires_in_seconds,
                        expires_at=expires_at
                    )

                    logger.debug(f"Token expires at: {expires_at}")

                elif response.status_code == 401:
                    logger.error("UPS authentication failed: Invalid credentials")
                    raise AuthenticationError(
                        "UPS authentication failed: Invalid client credentials"
                    )
                elif response.status_code == 429:
                    logger.error("UPS authentication rate limited")
                    raise AuthenticationError(
                        "UPS authentication rate limited. Please try again later."
                    )
                else:
                    logger.error(f"UPS auth failed with status {response.status_code}: {response.text}")
                    raise AuthenticationError(
                        f"UPS authentication failed: HTTP {response.status_code}"
                    )

        except httpx.TimeoutException:
            logger.error("UPS authentication request timed out")
            raise AuthenticationError("UPS authentication request timed out") from None
        except httpx.RequestError as e:
            logger.error(f"UPS authentication request failed: {e}")
            raise AuthenticationError(f"UPS authentication request failed: {e}") from None

    async def get_auth_headers(self) -> dict:
        """
        Get HTTP headers with valid OAuth token.
        
        Returns:
            dict: Headers including Authorization bearer token and required UPS headers
            
        Raises:
            AuthenticationError: If unable to obtain valid token
        """
        import uuid
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "transId": str(uuid.uuid4()),
            "transactionSrc": "testing"
        }

    def clear_token(self) -> None:
        """Clear stored token, forcing refresh on next request."""
        self._token = None
        logger.info("UPS token cleared")