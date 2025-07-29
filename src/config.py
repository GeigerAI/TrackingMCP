"""
Configuration management for the package tracking MCP server.

Uses pydantic-settings for environment variable management as specified in CLAUDE.md.
"""


from dotenv import load_dotenv
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings

# Reason: Load environment variables from .env file per CLAUDE.md requirements
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings have defaults for development and can be overridden via environment variables.
    """

    # FedEx Configuration
    fedex_client_id: str = Field(
        default="",
        description="FedEx API client ID"
    )
    fedex_client_secret: str = Field(
        default="",
        description="FedEx API client secret"
    )
    fedex_sandbox: bool = Field(
        default=True,
        description="Use FedEx sandbox environment"
    )

    # UPS Configuration
    ups_client_id: str = Field(
        default="",
        description="UPS API client ID"
    )
    ups_client_secret: str = Field(
        default="",
        description="UPS API client secret"
    )
    ups_redirect_uri: str = Field(
        default="http://localhost:8000/callback",
        description="UPS OAuth redirect URI"
    )
    ups_sandbox: bool = Field(
        default=True,
        description="Use UPS sandbox environment"
    )

    # DHL Configuration
    dhl_client_id: str = Field(
        default="",
        description="DHL API client ID"
    )
    dhl_client_secret: str = Field(
        default="",
        description="DHL API client secret"
    )
    dhl_sandbox: bool = Field(
        default=True,
        description="Use DHL sandbox environment"
    )

    # OnTrac Configuration
    ontrac_api_key: str = Field(
        default="",
        description="OnTrac API key"
    )
    ontrac_account_number: str = Field(
        default="",
        description="OnTrac account number"
    )
    ontrac_sandbox: bool = Field(
        default=True,
        description="Use OnTrac sandbox environment"
    )

    # MCP Configuration
    mcp_transport: str = Field(
        default="stdio",
        description="MCP transport method (stdio or sse)"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # API Settings
    request_timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
        validation_alias=AliasChoices("REQUEST_TIMEOUT", "request_timeout")
    )
    token_refresh_buffer: int = Field(
        default=60,
        description="Token refresh buffer in seconds",
        validation_alias=AliasChoices("TOKEN_REFRESH_BUFFER", "token_refresh_buffer")
    )

    @property
    def fedex_base_url(self) -> str:
        """
        Get FedEx API base URL based on sandbox setting.

        Returns:
            str: FedEx API base URL
        """
        if self.fedex_sandbox:
            return "https://apis-sandbox.fedex.com"
        return "https://apis.fedex.com"

    @property
    def ups_base_url(self) -> str:
        """
        Get UPS API base URL based on sandbox setting.

        Returns:
            str: UPS API base URL
        """
        if self.ups_sandbox:
            return "https://wwwcie.ups.com"
        return "https://onlinetools.ups.com"

    @property
    def dhl_base_url(self) -> str:
        """
        Get DHL API base URL based on sandbox setting.

        Returns:
            str: DHL API base URL
        """
        if self.dhl_sandbox:
            return "https://api-sandbox.dhlecs.com"
        return "https://api.dhlecs.com"

    @property
    def ontrac_base_url(self) -> str:
        """
        Get OnTrac API base URL based on sandbox setting.

        Returns:
            str: OnTrac API base URL
        """
        if self.ontrac_sandbox:
            return "https://www.shipontrac.net/OnTracTestWebServices/OnTracServices.svc"
        return "https://www.shipontrac.net/OnTracWebServices/OnTracServices.svc"

    def validate_api_credentials(self) -> None:
        """
        Validate that required API credentials are present.

        Raises:
            ValueError: If required credentials are missing
        """
        if not self.fedex_client_id or not self.fedex_client_secret:
            raise ValueError("FedEx API credentials are required")

        if not self.ups_client_id or not self.ups_client_secret:
            raise ValueError("UPS API credentials are required")

        if not self.dhl_client_id or not self.dhl_client_secret:
            raise ValueError("DHL API credentials are required")

        if not self.ontrac_api_key:
            raise ValueError("OnTrac API key is required")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
