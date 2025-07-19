"""
Tests for FedEx authentication module.

Tests OAuth token acquisition, refresh, and error handling.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import httpx
import pytest
import respx

from src.auth.fedex_auth import FedExAuth
from src.models import AuthenticationError


class TestFedExAuth:
    """Test FedEx authentication functionality."""

    def test_init_with_credentials(self):
        """Test initialization with explicit credentials."""
        auth = FedExAuth(
            client_id="test_id",
            client_secret="test_secret",
            sandbox=True
        )

        assert auth.client_id == "test_id"
        assert auth.client_secret == "test_secret"
        assert auth.sandbox is True
        assert "sandbox" in auth.base_url

    def test_init_production_mode(self):
        """Test initialization in production mode."""
        auth = FedExAuth(
            client_id="test_id",
            client_secret="test_secret",
            sandbox=False
        )

        assert auth.sandbox is False
        assert "sandbox" not in auth.base_url
        assert "apis.fedex.com" in auth.base_url

    def test_init_missing_credentials(self):
        """Test initialization with missing credentials."""
        with pytest.raises(AuthenticationError, match="FedEx client ID and secret are required"):
            FedExAuth(client_id="", client_secret="")

    def test_is_token_valid_no_token(self):
        """Test token validity check with no token."""
        auth = FedExAuth("test_id", "test_secret")
        assert auth.is_token_valid is False

    def test_is_token_valid_expired(self):
        """Test token validity check with expired token."""
        auth = FedExAuth("test_id", "test_secret")

        # Mock an expired token
        from src.models import AuthToken
        auth._token = AuthToken(
            access_token="expired_token",
            expires_in=3600,
            expires_at=datetime.now() - timedelta(hours=1)  # Expired 1 hour ago
        )

        assert auth.is_token_valid is False

    def test_is_token_valid_current(self):
        """Test token validity check with current token."""
        auth = FedExAuth("test_id", "test_secret")

        # Mock a current token
        from src.models import AuthToken
        auth._token = AuthToken(
            access_token="current_token",
            expires_in=3600,
            expires_at=datetime.now() + timedelta(hours=1)  # Expires in 1 hour
        )

        assert auth.is_token_valid is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh."""
        # Mock successful token response
        respx.post("https://apis-sandbox.fedex.com/oauth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "new_access_token",
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            )
        )

        auth = FedExAuth("test_id", "test_secret")
        await auth._refresh_token()

        assert auth._token is not None
        assert auth._token.access_token == "new_access_token"
        assert auth._token.token_type == "Bearer"
        assert auth._token.expires_in == 3600

    @respx.mock
    @pytest.mark.asyncio
    async def test_refresh_token_auth_failure(self):
        """Test token refresh with authentication failure."""
        # Mock authentication failure
        respx.post("https://apis-sandbox.fedex.com/oauth/token").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )

        auth = FedExAuth("test_id", "test_secret")

        with pytest.raises(AuthenticationError, match="FedEx authentication failed: Invalid client credentials"):
            await auth._refresh_token()

    @respx.mock
    @pytest.mark.asyncio
    async def test_refresh_token_rate_limit(self):
        """Test token refresh with rate limiting."""
        # Mock rate limit response
        respx.post("https://apis-sandbox.fedex.com/oauth/token").mock(
            return_value=httpx.Response(429, text="Rate limited")
        )

        auth = FedExAuth("test_id", "test_secret")

        with pytest.raises(AuthenticationError, match="FedEx authentication rate limited"):
            await auth._refresh_token()

    @respx.mock
    @pytest.mark.asyncio
    async def test_refresh_token_server_error(self):
        """Test token refresh with server error."""
        # Mock server error
        respx.post("https://apis-sandbox.fedex.com/oauth/token").mock(
            return_value=httpx.Response(500, text="Internal server error")
        )

        auth = FedExAuth("test_id", "test_secret")

        with pytest.raises(AuthenticationError, match="FedEx authentication failed: HTTP 500"):
            await auth._refresh_token()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_access_token_valid_cached(self):
        """Test getting access token when cached token is valid."""
        auth = FedExAuth("test_id", "test_secret")

        # Mock a valid cached token
        from src.models import AuthToken
        auth._token = AuthToken(
            access_token="cached_token",
            expires_in=3600,
            expires_at=datetime.now() + timedelta(hours=1)
        )

        token = await auth.get_access_token()
        assert token == "cached_token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_access_token_refresh_needed(self):
        """Test getting access token when refresh is needed."""
        # Mock successful token response
        respx.post("https://apis-sandbox.fedex.com/oauth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "refreshed_token",
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            )
        )

        auth = FedExAuth("test_id", "test_secret")
        token = await auth.get_access_token()

        assert token == "refreshed_token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_auth_headers(self):
        """Test getting authentication headers."""
        # Mock successful token response
        respx.post("https://apis-sandbox.fedex.com/oauth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "header_token",
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            )
        )

        auth = FedExAuth("test_id", "test_secret")
        headers = await auth.get_auth_headers()

        expected_headers = {
            "Authorization": "Bearer header_token",
            "Content-Type": "application/json",
            "X-locale": "en_US"
        }

        assert headers == expected_headers

    def test_clear_token(self):
        """Test clearing stored token."""
        auth = FedExAuth("test_id", "test_secret")

        # Set a token first
        from src.models import AuthToken
        auth._token = AuthToken(
            access_token="test_token",
            expires_in=3600,
            expires_at=datetime.now() + timedelta(hours=1)
        )

        # Clear the token
        auth.clear_token()
        assert auth._token is None

    @pytest.mark.asyncio
    async def test_refresh_token_timeout(self):
        """Test token refresh with timeout."""
        auth = FedExAuth("test_id", "test_secret")

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises(AuthenticationError, match="FedEx authentication request timed out"):
                await auth._refresh_token()

    @pytest.mark.asyncio
    async def test_refresh_token_request_error(self):
        """Test token refresh with request error."""
        auth = FedExAuth("test_id", "test_secret")

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.RequestError("Connection failed")

            with pytest.raises(AuthenticationError, match="FedEx authentication request failed"):
                await auth._refresh_token()
