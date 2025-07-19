"""
Unit tests for DHL authentication module.

Tests OAuth2 authentication and token management for DHL API.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.auth.dhl_auth import DHLAuth
from src.models import AuthenticationError, AuthToken


class TestDHLAuth:
    """Test cases for DHL authentication."""
    
    def test_init_with_credentials(self):
        """Test initialization with valid credentials."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            sandbox=True
        )
        
        assert auth.client_id == "test_client_id"
        assert auth.client_secret == "test_client_secret"
        assert auth.sandbox is True
        assert auth.base_url == "https://api-sandbox.dhlecs.com"
    
    def test_init_production_url(self):
        """Test production URL configuration."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            sandbox=False
        )
        
        assert auth.base_url == "https://api.dhlecs.com"
    
    def test_init_missing_credentials(self):
        """Test initialization with missing credentials."""
        with pytest.raises(AuthenticationError, match="DHL client ID and secret are required"):
            DHLAuth(client_id="", client_secret="")
    
    def test_is_token_valid_no_token(self):
        """Test token validation with no token."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        assert auth.is_token_valid is False
    
    def test_is_token_valid_expired_token(self):
        """Test token validation with expired token."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        # Create an expired token
        expired_token = AuthToken(
            access_token="expired_token",
            token_type="Bearer",
            expires_in=3600,
            expires_at=datetime.now() - timedelta(minutes=5)
        )
        auth._token = expired_token
        
        assert auth.is_token_valid is False
    
    def test_is_token_valid_valid_token(self):
        """Test token validation with valid token."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        # Create a valid token
        valid_token = AuthToken(
            access_token="valid_token",
            token_type="Bearer",
            expires_in=3600,
            expires_at=datetime.now() + timedelta(minutes=30)
        )
        auth._token = valid_token
        
        assert auth.is_token_valid is True
    
    @pytest.mark.asyncio
    async def test_get_access_token_existing_valid(self):
        """Test getting access token when valid token exists."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        # Set up a valid token
        valid_token = AuthToken(
            access_token="existing_token",
            token_type="Bearer",
            expires_in=3600,
            expires_at=datetime.now() + timedelta(minutes=30)
        )
        auth._token = valid_token
        
        token = await auth.get_access_token()
        assert token == "existing_token"
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            await auth._refresh_token()
            
            assert auth._token.access_token == "new_access_token"
            assert auth._token.token_type == "Bearer"
            assert auth._token.expires_in == 3600
    
    @pytest.mark.asyncio
    async def test_refresh_token_401_error(self):
        """Test token refresh with 401 error."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        # Mock HTTP response with 401 error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(AuthenticationError, match="Invalid client credentials"):
                await auth._refresh_token()
    
    @pytest.mark.asyncio
    async def test_refresh_token_429_error(self):
        """Test token refresh with rate limit error."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        # Mock HTTP response with 429 error
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limited"
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(AuthenticationError, match="rate limited"):
                await auth._refresh_token()
    
    @pytest.mark.asyncio
    async def test_refresh_token_timeout(self):
        """Test token refresh with timeout error."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            
            with pytest.raises(AuthenticationError, match="timed out"):
                await auth._refresh_token()
    
    @pytest.mark.asyncio
    async def test_get_auth_headers(self):
        """Test getting authentication headers."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        # Set up a valid token
        valid_token = AuthToken(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
            expires_at=datetime.now() + timedelta(minutes=30)
        )
        auth._token = valid_token
        
        headers = await auth.get_auth_headers()
        
        expected_headers = {
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json",
            "User-Agent": "eCOMv4 DHLeC Developer portal"
        }
        
        assert headers == expected_headers
    
    def test_clear_token(self):
        """Test clearing stored token."""
        auth = DHLAuth(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        # Set up a token
        auth._token = AuthToken(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
            expires_at=datetime.now() + timedelta(minutes=30)
        )
        
        auth.clear_token()
        assert auth._token is None