"""
UPS OAuth authentication module.

Handles OAuth2 authorization_code flow for UPS API access with automatic token refresh.
"""

import asyncio
import base64
import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

import httpx

from ..config import settings
from ..models import AuthenticationError, AuthToken

logger = logging.getLogger(__name__)


class UPSAuth:
    """
    UPS OAuth2 authentication manager.

    Handles token acquisition, storage, and automatic refresh for UPS API access.
    Uses authorization_code flow with PKCE (Proof Key for Code Exchange).
    """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None,
                 redirect_uri: Optional[str] = None, sandbox: Optional[bool] = None):
        """
        Initialize UPS authentication.

        Args:
            client_id: UPS API client ID (defaults to config)
            client_secret: UPS API client secret (defaults to config)
            redirect_uri: OAuth redirect URI (defaults to config)
            sandbox: Use sandbox environment (defaults to config)
        """
        self.client_id = client_id or settings.ups_client_id
        self.client_secret = client_secret or settings.ups_client_secret
        self.redirect_uri = redirect_uri or settings.ups_redirect_uri
        self.sandbox = sandbox if sandbox is not None else settings.ups_sandbox

        if not self.client_id or not self.client_secret:
            raise AuthenticationError("UPS client ID and secret are required")

        self.base_url = settings.ups_base_url
        self._token: Optional[AuthToken] = None
        self._refresh_lock = asyncio.Lock()
        self._code_verifier: Optional[str] = None

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
        buffer_time = timedelta(seconds=settings.token_refresh_buffer)
        return datetime.now() < (self._token.expires_at - buffer_time)

    def _generate_pkce_pair(self) -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge for OAuth flow.

        Returns:
            tuple: (code_verifier, code_challenge)
        """
        # Reason: Generate cryptographically secure random string for PKCE
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

        # Reason: Create SHA256 challenge from verifier
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')

        return code_verifier, code_challenge

    def get_authorization_url(self) -> str:
        """
        Generate UPS OAuth authorization URL for user consent.

        Returns:
            str: Authorization URL for user to visit
        """
        self._code_verifier, code_challenge = self._generate_pkce_pair()

        # Reason: Build OAuth authorization URL with PKCE parameters
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "tracking",  # UPS tracking scope
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{self.base_url}/security/v1/oauth/authorize?{query_string}"

        logger.info(f"Generated UPS authorization URL: {auth_url}")
        return auth_url

    async def exchange_code_for_token(self, authorization_code: str) -> None:
        """
        Exchange authorization code for access token.

        Args:
            authorization_code: Authorization code from OAuth callback

        Raises:
            AuthenticationError: If token exchange fails
        """
        if not self._code_verifier:
            raise AuthenticationError("No code verifier available. Call get_authorization_url() first.")

        url = f"{self.base_url}/security/v1/oauth/token"

        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": self._code_verifier,
            "client_id": self.client_id
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                logger.debug(f"Exchanging UPS authorization code for token at {url}")

                # Reason: UPS requires basic auth with client credentials
                auth = (self.client_id, self.client_secret)
                response = await client.post(url, data=data, headers=headers, auth=auth)

                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("Successfully obtained UPS OAuth token")

                    # Reason: Calculate exact expiration time for proactive refresh
                    expires_at = datetime.now() + timedelta(
                        seconds=token_data["expires_in"]
                    )

                    self._token = AuthToken(
                        access_token=token_data["access_token"],
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_in=token_data["expires_in"],
                        expires_at=expires_at,
                        refresh_token=token_data.get("refresh_token")
                    )

                    logger.debug(f"Token expires at: {expires_at}")

                elif response.status_code == 401:
                    logger.error("UPS authentication failed: Invalid credentials or code")
                    raise AuthenticationError(
                        "UPS authentication failed: Invalid client credentials or authorization code"
                    )
                elif response.status_code == 400:
                    logger.error(f"UPS bad request: {response.text}")
                    raise AuthenticationError(f"UPS authentication failed: {response.text}")
                else:
                    logger.error(f"UPS auth failed with status {response.status_code}: {response.text}")
                    raise AuthenticationError(
                        f"UPS authentication failed: HTTP {response.status_code}"
                    )

        except httpx.TimeoutException:
            logger.error("UPS authentication request timed out")
            raise AuthenticationError("UPS authentication request timed out")
        except httpx.RequestError as e:
            logger.error(f"UPS authentication request failed: {e}")
            raise AuthenticationError(f"UPS authentication request failed: {e}")

    async def get_access_token(self) -> str:
        """
        Get valid OAuth access token, refreshing if necessary.

        Returns:
            str: Valid OAuth access token

        Raises:
            AuthenticationError: If authentication fails or no token available
        """
        if not self._token:
            raise AuthenticationError(
                "No UPS token available. Complete OAuth flow first using get_authorization_url()"
            )

        if self.is_token_valid:
            return self._token.access_token

        # Reason: Use lock to prevent multiple simultaneous token refresh attempts
        async with self._refresh_lock:
            # Double-check pattern: another coroutine might have refreshed the token
            if self.is_token_valid:
                return self._token.access_token

            if self._token.refresh_token:
                logger.info("Refreshing UPS OAuth token using refresh token")
                await self._refresh_token()
                return self._token.access_token
            else:
                raise AuthenticationError(
                    "UPS token expired and no refresh token available. Re-authorize required."
                )

    async def _refresh_token(self) -> None:
        """
        Refresh the OAuth token using refresh token.

        Raises:
            AuthenticationError: If token refresh fails
        """
        if not self._token or not self._token.refresh_token:
            raise AuthenticationError("No refresh token available")

        url = f"{self.base_url}/security/v1/oauth/token"

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._token.refresh_token,
            "client_id": self.client_id
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                logger.debug(f"Refreshing UPS token at {url}")

                # Reason: UPS requires basic auth with client credentials
                auth = (self.client_id, self.client_secret)
                response = await client.post(url, data=data, headers=headers, auth=auth)

                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("Successfully refreshed UPS OAuth token")

                    # Reason: Calculate exact expiration time for proactive refresh
                    expires_at = datetime.now() + timedelta(
                        seconds=token_data["expires_in"]
                    )

                    self._token = AuthToken(
                        access_token=token_data["access_token"],
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_in=token_data["expires_in"],
                        expires_at=expires_at,
                        refresh_token=token_data.get("refresh_token", self._token.refresh_token)
                    )

                else:
                    logger.error(f"UPS token refresh failed with status {response.status_code}: {response.text}")
                    raise AuthenticationError(f"UPS token refresh failed: HTTP {response.status_code}")

        except httpx.TimeoutException:
            logger.error("UPS token refresh request timed out")
            raise AuthenticationError("UPS token refresh request timed out")
        except httpx.RequestError as e:
            logger.error(f"UPS token refresh request failed: {e}")
            raise AuthenticationError(f"UPS token refresh request failed: {e}")

    async def get_auth_headers(self) -> dict:
        """
        Get HTTP headers with valid OAuth token.

        Returns:
            dict: Headers including Authorization bearer token

        Raises:
            AuthenticationError: If unable to obtain valid token
        """
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "transId": "tracking",
            "transactionSrc": "mcp-server"
        }

    def clear_token(self) -> None:
        """Clear stored token, forcing re-authorization on next request."""
        self._token = None
        self._code_verifier = None
        logger.info("UPS token cleared")
