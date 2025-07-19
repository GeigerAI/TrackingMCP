"""
Main MCP server for package tracking.

Implements a Model Context Protocol server that provides package tracking
tools for FedEx and UPS shipments to AI agents.
"""

import logging
import sys
from contextlib import asynccontextmanager

# NOTE: MCP package not available in current environment
# from mcp.server.fastmcp import FastMCP
# Using FastAPI as temporary alternative to demonstrate functionality
from fastapi import FastAPI
import uvicorn

from .config import settings
from .tools.fedex_tools import register_fedex_tools
from .tools.ups_tools import register_ups_tools

# Reason: Configure logging as specified in CLAUDE.md
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """
    FastAPI server lifespan manager.

    Handles server startup and shutdown operations.
    """
    logger.info("Starting Package Tracking MCP Server")

    try:
        # Reason: Validate configuration on startup
        settings.validate_api_credentials()
        logger.info("API credentials validated successfully")
    except ValueError as e:
        logger.warning(f"API credentials validation failed: {e}")
        logger.warning("Some tracking features may not work without proper credentials")

    yield

    logger.info("Shutting down Package Tracking MCP Server")


# Reason: Create FastAPI server instance as temporary alternative to MCP
app = FastAPI(
    title="Package Tracking Server",
    description="Provides package tracking for FedEx and UPS shipments",
    version="0.1.0",
    lifespan=lifespan
)


def setup_server():
    """
    Set up the MCP server by registering all tools and resources.
    """
    logger.info("Setting up Package Tracking MCP Server")

    # Reason: Register FedEx tracking tools
    try:
        register_fedex_tools(app)
        logger.info("Successfully registered FedEx tracking tools")
    except Exception as e:
        logger.error(f"Failed to register FedEx tools: {e}")

    # Reason: Register UPS tracking tools
    try:
        register_ups_tools(app)
        logger.info("Successfully registered UPS tracking tools")
    except Exception as e:
        logger.error(f"Failed to register UPS tools: {e}")

    # Reason: Add server information endpoint
    @app.get("/tracking/server/info")
    def server_info():
        """
        Provide information about the tracking server capabilities.

        Returns:
            dict: Server information and available carriers
        """
        return {
            "name": "Package Tracking MCP Server",
            "version": "0.1.0",
            "description": "Provides package tracking for FedEx and UPS shipments",
            "supported_carriers": ["fedex", "ups"],
            "features": [
                "Real-time package tracking",
                "Multiple package batch tracking",
                "Tracking number validation",
                "Delivery estimates",
                "Tracking history and events"
            ],
            "configuration": {
                "fedex_sandbox": settings.fedex_sandbox,
                "ups_sandbox": settings.ups_sandbox,
                "transport": settings.mcp_transport
            }
        }

    # Reason: Add carrier capabilities endpoint
    @app.get("/tracking/carriers/{carrier}/capabilities")
    def carrier_capabilities(carrier: str):
        """
        Provide capabilities for a specific carrier.

        Args:
            carrier: Carrier name (fedex or ups)

        Returns:
            dict: Carrier-specific capabilities
        """
        if carrier.lower() == "fedex":
            return {
                "carrier": "FedEx",
                "max_batch_size": 30,
                "tracking_number_formats": [
                    "12 digits (Express)",
                    "14 digits (Ground)",
                    "15 digits (SmartPost)",
                    "22 digits (Ground barcode)"
                ],
                "features": [
                    "Batch tracking",
                    "Detailed scan events",
                    "Estimated delivery",
                    "Service type information"
                ]
            }
        elif carrier.lower() == "ups":
            return {
                "carrier": "UPS",
                "max_batch_size": 10,
                "tracking_number_formats": [
                    "1Z + 16 characters (standard)",
                    "12 digits (reference)",
                    "18 digits",
                    "22-25 digits (Mail Innovations)"
                ],
                "features": [
                    "Individual tracking",
                    "Activity history",
                    "Delivery information",
                    "OAuth authorization flow"
                ]
            }
        else:
            return {"error": f"Unsupported carrier: {carrier}"}

    logger.info("Package Tracking MCP Server setup completed")


def main():
    """
    Main entry point for the MCP server.
    """
    try:
        # Reason: Set up server before running
        setup_server()

        # Reason: Run the FastAPI server as MCP alternative
        logger.info("Starting FastAPI server...")
        uvicorn.run(app, host="0.0.0.0", port=8566)

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
