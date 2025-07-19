"""
DHL MCP tools for package tracking.

Provides MCP tool functions for DHL package tracking operations.
"""

import json
import logging
from typing import Any, Dict, List

from ..models import TrackingCarrier, TrackingError
from ..tracking.dhl_tracker import DHLTracker

logger = logging.getLogger(__name__)


async def track_dhl_package(tracking_number: str) -> Dict[str, Any]:
    """
    Track a single DHL package.

    Args:
        tracking_number: DHL tracking number

    Returns:
        Dict[str, Any]: Tracking result as dictionary
    """
    try:
        tracker = DHLTracker()
        result = await tracker.track_package(tracking_number)
        
        # Reason: Convert to dict for MCP response
        return {
            "tracking_number": result.tracking_number,
            "carrier": result.carrier.value,
            "status": result.status.value,
            "estimated_delivery": result.estimated_delivery.isoformat() if result.estimated_delivery else None,
            "delivery_address": result.delivery_address,
            "service_type": result.service_type,
            "weight": result.weight,
            "events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "status": event.status,
                    "location": event.location,
                    "description": event.description
                }
                for event in result.events
            ],
            "error_message": result.error_message
        }
    except TrackingError as e:
        logger.error(f"DHL tracking failed: {e}")
        return {
            "tracking_number": tracking_number,
            "carrier": TrackingCarrier.DHL.value,
            "status": "error",
            "error_message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error tracking DHL package {tracking_number}: {e}")
        return {
            "tracking_number": tracking_number,
            "carrier": TrackingCarrier.DHL.value,
            "status": "error",
            "error_message": f"Unexpected error: {e}"
        }


async def track_multiple_dhl_packages(tracking_numbers: List[str]) -> Dict[str, Any]:
    """
    Track multiple DHL packages.

    Args:
        tracking_numbers: List of DHL tracking numbers

    Returns:
        Dict[str, Any]: Tracking results as dictionary
    """
    try:
        tracker = DHLTracker()
        results = await tracker.track_multiple_packages(tracking_numbers)
        
        # Reason: Convert results to dict format for MCP response
        return {
            "results": [
                {
                    "tracking_number": result.tracking_number,
                    "carrier": result.carrier.value,
                    "status": result.status.value,
                    "estimated_delivery": result.estimated_delivery.isoformat() if result.estimated_delivery else None,
                    "delivery_address": result.delivery_address,
                    "service_type": result.service_type,
                    "weight": result.weight,
                    "events": [
                        {
                            "timestamp": event.timestamp.isoformat(),
                            "status": event.status,
                            "location": event.location,
                            "description": event.description
                        }
                        for event in result.events
                    ],
                    "error_message": result.error_message
                }
                for result in results
            ],
            "total_count": len(results),
            "success_count": len([r for r in results if not r.error_message])
        }
    except TrackingError as e:
        logger.error(f"DHL batch tracking failed: {e}")
        return {
            "results": [],
            "total_count": len(tracking_numbers),
            "success_count": 0,
            "error_message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error tracking DHL packages: {e}")
        return {
            "results": [],
            "total_count": len(tracking_numbers),
            "success_count": 0,
            "error_message": f"Unexpected error: {e}"
        }


async def validate_dhl_tracking_number(tracking_number: str) -> Dict[str, Any]:
    """
    Validate DHL tracking number format.

    Args:
        tracking_number: DHL tracking number to validate

    Returns:
        Dict[str, Any]: Validation result
    """
    try:
        tracker = DHLTracker()
        is_valid = tracker.validate_tracking_number(tracking_number)
        
        return {
            "tracking_number": tracking_number,
            "carrier": TrackingCarrier.DHL.value,
            "is_valid": is_valid,
            "message": "Valid DHL tracking number format" if is_valid else "Invalid DHL tracking number format"
        }
    except Exception as e:
        logger.error(f"Error validating DHL tracking number {tracking_number}: {e}")
        return {
            "tracking_number": tracking_number,
            "carrier": TrackingCarrier.DHL.value,
            "is_valid": False,
            "message": f"Validation error: {e}"
        }


# Reason: Define DHL MCP tools for registration
DHL_TOOLS = {
    "track_dhl_package": {
        "description": "Track a single DHL package by tracking number",
        "parameters": {
            "type": "object",
            "properties": {
                "tracking_number": {
                    "type": "string",
                    "description": "DHL tracking number"
                }
            },
            "required": ["tracking_number"]
        },
        "handler": track_dhl_package
    },
    "track_multiple_dhl_packages": {
        "description": "Track multiple DHL packages by tracking numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "tracking_numbers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of DHL tracking numbers"
                }
            },
            "required": ["tracking_numbers"]
        },
        "handler": track_multiple_dhl_packages
    },
    "validate_dhl_tracking_number": {
        "description": "Validate DHL tracking number format",
        "parameters": {
            "type": "object",
            "properties": {
                "tracking_number": {
                    "type": "string",
                    "description": "DHL tracking number to validate"
                }
            },
            "required": ["tracking_number"]
        },
        "handler": validate_dhl_tracking_number
    }
}