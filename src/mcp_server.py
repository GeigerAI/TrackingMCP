"""
MCP server implementation for package tracking.

Implements Model Context Protocol for package tracking tools and resources.
Compatible with Python 3.9+ by implementing MCP protocol manually.
"""

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
# Reason: Add current directory to path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.auth.fedex_auth import FedExAuth
from src.auth.ups_auth import UPSAuth
from src.auth.dhl_auth import DHLAuth
from src.config import settings
from src.models import TrackingCarrier, TrackingResult
from src.tracking.fedex_tracker import FedExTracker
from src.tracking.ups_tracker import UPSTracker
from src.tracking.dhl_tracker import DHLTracker

logger = logging.getLogger(__name__)


class MCPServer:
    """
    Model Context Protocol server for package tracking.
    
    Implements MCP protocol manually for compatibility with Python 3.9.
    """
    
    def __init__(self):
        """Initialize MCP server."""
        self.tools = {}
        self.resources = {}
        self.ups_auth = UPSAuth()
        self.dhl_auth = DHLAuth()
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self):
        """Register all tracking tools."""
        
        # FedEx tools
        self.tools["track_fedex_package"] = {
            "name": "track_fedex_package",
            "description": "Track a FedEx package by tracking number",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tracking_number": {
                        "type": "string",
                        "description": "FedEx tracking number"
                    }
                },
                "required": ["tracking_number"]
            }
        }
        
        self.tools["track_multiple_fedex_packages"] = {
            "name": "track_multiple_fedex_packages", 
            "description": "Track multiple FedEx packages (up to 30)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tracking_numbers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of FedEx tracking numbers (max 30)"
                    }
                },
                "required": ["tracking_numbers"]
            }
        }
        
        self.tools["validate_fedex_tracking_number"] = {
            "name": "validate_fedex_tracking_number",
            "description": "Validate FedEx tracking number format",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "tracking_number": {
                        "type": "string",
                        "description": "Tracking number to validate"
                    }
                },
                "required": ["tracking_number"]
            }
        }
        
        # UPS tools
        self.tools["track_ups_package"] = {
            "name": "track_ups_package",
            "description": "Track a UPS package by tracking number",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tracking_number": {
                        "type": "string", 
                        "description": "UPS tracking number"
                    }
                },
                "required": ["tracking_number"]
            }
        }
        
        self.tools["track_multiple_ups_packages"] = {
            "name": "track_multiple_ups_packages",
            "description": "Track multiple UPS packages",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tracking_numbers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of UPS tracking numbers"
                    }
                },
                "required": ["tracking_numbers"]
            }
        }
        
        self.tools["validate_ups_tracking_number"] = {
            "name": "validate_ups_tracking_number",
            "description": "Validate UPS tracking number format",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tracking_number": {
                        "type": "string",
                        "description": "Tracking number to validate"
                    }
                },
                "required": ["tracking_number"]
            }
        }

        # DHL tools
        self.tools["track_dhl_package"] = {
            "name": "track_dhl_package",
            "description": "Track a DHL package by tracking number",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tracking_number": {
                        "type": "string",
                        "description": "DHL tracking number"
                    }
                },
                "required": ["tracking_number"]
            }
        }
        
        self.tools["track_multiple_dhl_packages"] = {
            "name": "track_multiple_dhl_packages",
            "description": "Track multiple DHL packages (up to 10)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tracking_numbers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of DHL tracking numbers (max 10)"
                    }
                },
                "required": ["tracking_numbers"]
            }
        }
        
        self.tools["validate_dhl_tracking_number"] = {
            "name": "validate_dhl_tracking_number",
            "description": "Validate DHL tracking number format",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tracking_number": {
                        "type": "string",
                        "description": "Tracking number to validate"
                    }
                },
                "required": ["tracking_number"]
            }
        }

    
    def _setup_resources(self):
        """Register all resources."""
        
        self.resources["tracking://server/info"] = {
            "uri": "tracking://server/info",
            "name": "Server Information",
            "description": "Information about the tracking server capabilities",
            "mimeType": "application/json"
        }
        
        self.resources["tracking://carriers/fedex/capabilities"] = {
            "uri": "tracking://carriers/fedex/capabilities", 
            "name": "FedEx Capabilities",
            "description": "FedEx carrier capabilities and limits",
            "mimeType": "application/json"
        }
        
        self.resources["tracking://carriers/ups/capabilities"] = {
            "uri": "tracking://carriers/ups/capabilities",
            "name": "UPS Capabilities", 
            "description": "UPS carrier capabilities and limits",
            "mimeType": "application/json"
        }
        
        self.resources["tracking://carriers/dhl/capabilities"] = {
            "uri": "tracking://carriers/dhl/capabilities",
            "name": "DHL Capabilities",
            "description": "DHL carrier capabilities and limits",
            "mimeType": "application/json"
        }
    
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming MCP message."""
        
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        try:
            if method == "initialize":
                return self._handle_initialize(msg_id, params)
            elif method == "tools/list":
                return self._handle_tools_list(msg_id)
            elif method == "tools/call":
                return await self._handle_tools_call(msg_id, params)
            elif method == "resources/list":
                return self._handle_resources_list(msg_id)
            elif method == "resources/read":
                return self._handle_resources_read(msg_id, params)
            else:
                return self._error_response(msg_id, -32601, f"Method not found: {method}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return self._error_response(msg_id, -32603, f"Internal error: {str(e)}")
    
    def _handle_initialize(self, msg_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": "Package Tracking MCP Server",
                    "version": "0.1.0"
                }
            }
        }
    
    def _handle_tools_list(self, msg_id: Any) -> Dict[str, Any]:
        """Handle tools/list request."""
        return {
            "jsonrpc": "2.0", 
            "id": msg_id,
            "result": {
                "tools": list(self.tools.values())
            }
        }
    
    async def _handle_tools_call(self, msg_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return self._error_response(msg_id, -32602, f"Unknown tool: {tool_name}")
        
        try:
            if tool_name == "track_fedex_package":
                result = await self._track_fedex_package(arguments["tracking_number"])
            elif tool_name == "track_multiple_fedex_packages":
                result = await self._track_multiple_fedex_packages(arguments["tracking_numbers"])
            elif tool_name == "validate_fedex_tracking_number":
                result = await self._validate_fedex_tracking_number(arguments["tracking_number"])
            elif tool_name == "track_ups_package":
                result = await self._track_ups_package(arguments["tracking_number"])
            elif tool_name == "track_multiple_ups_packages":
                result = await self._track_multiple_ups_packages(arguments["tracking_numbers"])
            elif tool_name == "validate_ups_tracking_number":
                result = await self._validate_ups_tracking_number(arguments["tracking_number"])
            elif tool_name == "track_dhl_package":
                result = await self._track_dhl_package(arguments["tracking_number"])
            elif tool_name == "track_multiple_dhl_packages":
                result = await self._track_multiple_dhl_packages(arguments["tracking_numbers"])
            elif tool_name == "validate_dhl_tracking_number":
                result = await self._validate_dhl_tracking_number(arguments["tracking_number"])
            else:
                return self._error_response(msg_id, -32602, f"Tool not implemented: {tool_name}")
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, default=str, indent=2)
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return self._error_response(msg_id, -32603, f"Tool execution failed: {str(e)}")
    
    def _handle_resources_list(self, msg_id: Any) -> Dict[str, Any]:
        """Handle resources/list request."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "resources": list(self.resources.values())
            }
        }
    
    def _handle_resources_read(self, msg_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        
        uri = params.get("uri")
        
        if uri not in self.resources:
            return self._error_response(msg_id, -32602, f"Unknown resource: {uri}")
        
        try:
            if uri == "tracking://server/info":
                content = {
                    "name": "Package Tracking MCP Server",
                    "version": "0.1.0",
                    "description": "Provides package tracking for FedEx, UPS, and DHL shipments",
                    "supported_carriers": ["fedex", "ups", "dhl"],
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
                        "dhl_sandbox": settings.dhl_sandbox
                    }
                }
            elif uri == "tracking://carriers/fedex/capabilities":
                content = {
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
            elif uri == "tracking://carriers/ups/capabilities":
                content = {
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
            elif uri == "tracking://carriers/dhl/capabilities":
                content = {
                    "carrier": "DHL",
                    "max_batch_size": 10,
                    "tracking_number_formats": [
                        "DHL Express (2 letters + 9 digits + 2 letters)",
                        "DHL eCommerce (10-30 alphanumeric)",
                        "Package ID (GM + 17 digits)",
                        "USPS format (420 + 27 digits)"
                    ],
                    "features": [
                        "Batch tracking",
                        "Event history",
                        "Delivery estimates",
                        "OAuth2 authentication"
                    ]
                }
            else:
                return self._error_response(msg_id, -32602, f"Resource not implemented: {uri}")
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(content, indent=2)
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            return self._error_response(msg_id, -32603, f"Resource read failed: {str(e)}")
    
    def _error_response(self, msg_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    # Tool implementations
    async def _track_fedex_package(self, tracking_number: str) -> Dict[str, Any]:
        """Track a FedEx package."""
        tracker = FedExTracker()
        result = await tracker.track_package(tracking_number)
        return result.model_dump()
    
    async def _track_multiple_fedex_packages(self, tracking_numbers: List[str]) -> List[Dict[str, Any]]:
        """Track multiple FedEx packages."""
        tracker = FedExTracker()
        results = await tracker.track_multiple_packages(tracking_numbers)
        return [result.model_dump() for result in results]
    
    async def _validate_fedex_tracking_number(self, tracking_number: str) -> bool:
        """Validate FedEx tracking number."""
        tracker = FedExTracker()
        return tracker.validate_tracking_number(tracking_number)
    
    async def _track_ups_package(self, tracking_number: str) -> Dict[str, Any]:
        """Track a UPS package."""
        tracker = UPSTracker(auth=self.ups_auth)
        result = await tracker.track_package(tracking_number)
        return result.model_dump()
    
    async def _track_multiple_ups_packages(self, tracking_numbers: List[str]) -> List[Dict[str, Any]]:
        """Track multiple UPS packages."""
        tracker = UPSTracker(auth=self.ups_auth)
        results = await tracker.track_multiple_packages(tracking_numbers)
        return [result.model_dump() for result in results]
    
    async def _validate_ups_tracking_number(self, tracking_number: str) -> bool:
        """Validate UPS tracking number (doesn't require authentication)."""
        # Reason: Validation doesn't need OAuth, just format checking
        tracker = UPSTracker()
        return tracker.validate_tracking_number(tracking_number)
    
    async def _track_dhl_package(self, tracking_number: str) -> Dict[str, Any]:
        """Track a DHL package."""
        tracker = DHLTracker(auth=self.dhl_auth)
        result = await tracker.track_package(tracking_number)
        return result.model_dump()
    
    async def _track_multiple_dhl_packages(self, tracking_numbers: List[str]) -> List[Dict[str, Any]]:
        """Track multiple DHL packages."""
        tracker = DHLTracker(auth=self.dhl_auth)
        results = await tracker.track_multiple_packages(tracking_numbers)
        return [result.model_dump() for result in results]
    
    async def _validate_dhl_tracking_number(self, tracking_number: str) -> bool:
        """Validate DHL tracking number (doesn't require authentication)."""
        # Reason: Validation doesn't need OAuth, just format checking
        tracker = DHLTracker()
        return tracker.validate_tracking_number(tracking_number)


async def main():
    """Main entry point for MCP server."""
    
    # Reason: Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)]  # Use stderr to avoid interfering with stdio
    )
    
    logger.info("Starting Package Tracking MCP Server")
    
    try:
        # Reason: Validate configuration on startup
        settings.validate_api_credentials()
        logger.info("API credentials validated successfully")
    except ValueError as e:
        logger.warning(f"API credentials validation failed: {e}")
        logger.warning("Some tracking features may not work without proper credentials")
    
    server = MCPServer()
    
    logger.info("MCP server started, listening for messages...")
    
    try:
        # Reason: Simple line-by-line processing of stdin
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # Reason: Read line from stdin synchronously
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                    
                message = json.loads(line)
                logger.debug(f"Received message: {message}")
                
                response = await server.handle_message(message)
                
                if response:
                    response_json = json.dumps(response) + "\n"
                    # Reason: Write directly as string to stdout
                    sys.stdout.write(response_json)
                    sys.stdout.flush()
                    logger.debug(f"Sent response: {response}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)
    finally:
        logger.info("MCP server shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
