"""
OnTrac MCP tools for package tracking.

Provides MCP tool functions for OnTrac package tracking operations.
"""

import json
import logging
from typing import Any, Dict, List

from ..models import TrackingCarrier, TrackingError
from ..tracking.ontrac_tracker import OnTracTracker

logger = logging.getLogger(__name__)


async def track_ontrac_package(tracking_number: str) -> Dict[str, Any]:
    """
    Track a single OnTrac package.

    Args:
        tracking_number: OnTrac tracking number

    Returns:
        Dict[str, Any]: Tracking result as dictionary
    """
    try:
        tracker = OnTracTracker()
        result = await tracker.track_package(tracking_number)
        
        # Reason: Convert to dict for MCP response
        return {
            "tracking_number": result.tracking_number,
            "carrier": result.carrier.value,
            "status": result.status.value,
            "estimated_delivery": result.estimated_delivery.isoformat() if result.estimated_delivery else None,
            "delivered_at": result.delivered_at.isoformat() if result.delivered_at else None,
            "origin": {
                "city": result.origin.city if result.origin else None,
                "state": result.origin.state if result.origin else None,
                "country": result.origin.country if result.origin else None,
                "postal_code": result.origin.postal_code if result.origin else None
            } if result.origin else None,
            "destination": {
                "city": result.destination.city if result.destination else None,
                "state": result.destination.state if result.destination else None,
                "country": result.destination.country if result.destination else None,
                "postal_code": result.destination.postal_code if result.destination else None
            } if result.destination else None,
            "service_type": result.service_type,
            "weight": result.weight,
            "reference_numbers": result.reference_numbers,
            "events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "description": event.description,
                    "location": {
                        "city": event.location.city if event.location else None,
                        "state": event.location.state if event.location else None,
                        "country": event.location.country if event.location else None,
                        "postal_code": event.location.postal_code if event.location else None
                    } if event.location else None,
                    "status_code": event.status_code
                }
                for event in result.events
            ],
            "error_message": result.error_message
        }
    except TrackingError as e:
        logger.error(f"OnTrac tracking failed: {e}")
        return {
            "tracking_number": tracking_number,
            "carrier": TrackingCarrier.ONTRAC.value,
            "status": "error",
            "error_message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error tracking OnTrac package {tracking_number}: {e}")
        return {
            "tracking_number": tracking_number,
            "carrier": TrackingCarrier.ONTRAC.value,
            "status": "error",
            "error_message": f"Unexpected error: {e}"
        }


async def track_multiple_ontrac_packages(tracking_numbers: List[str]) -> Dict[str, Any]:
    """
    Track multiple OnTrac packages.

    Args:
        tracking_numbers: List of OnTrac tracking numbers

    Returns:
        Dict[str, Any]: Tracking results as dictionary
    """
    try:
        tracker = OnTracTracker()
        results = await tracker.track_multiple_packages(tracking_numbers)
        
        # Reason: Convert results to dict format for MCP response
        return {
            "results": [
                {
                    "tracking_number": result.tracking_number,
                    "carrier": result.carrier.value,
                    "status": result.status.value,
                    "estimated_delivery": result.estimated_delivery.isoformat() if result.estimated_delivery else None,
                    "delivered_at": result.delivered_at.isoformat() if result.delivered_at else None,
                    "origin": {
                        "city": result.origin.city if result.origin else None,
                        "state": result.origin.state if result.origin else None,
                        "country": result.origin.country if result.origin else None,
                        "postal_code": result.origin.postal_code if result.origin else None
                    } if result.origin else None,
                    "destination": {
                        "city": result.destination.city if result.destination else None,
                        "state": result.destination.state if result.destination else None,
                        "country": result.destination.country if result.destination else None,
                        "postal_code": result.destination.postal_code if result.destination else None
                    } if result.destination else None,
                    "service_type": result.service_type,
                    "weight": result.weight,
                    "reference_numbers": result.reference_numbers,
                    "events": [
                        {
                            "timestamp": event.timestamp.isoformat(),
                            "description": event.description,
                            "location": {
                                "city": event.location.city if event.location else None,
                                "state": event.location.state if event.location else None,
                                "country": event.location.country if event.location else None,
                                "postal_code": event.location.postal_code if event.location else None
                            } if event.location else None,
                            "status_code": event.status_code
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
        logger.error(f"OnTrac batch tracking failed: {e}")
        return {
            "results": [],
            "total_count": len(tracking_numbers),
            "success_count": 0,
            "error_message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error tracking OnTrac packages: {e}")
        return {
            "results": [],
            "total_count": len(tracking_numbers),
            "success_count": 0,
            "error_message": f"Unexpected error: {e}"
        }


async def validate_ontrac_tracking_number(tracking_number: str) -> Dict[str, Any]:
    """
    Validate OnTrac tracking number format.

    Args:
        tracking_number: OnTrac tracking number to validate

    Returns:
        Dict[str, Any]: Validation result
    """
    try:
        tracker = OnTracTracker()
        is_valid = tracker.validate_tracking_number(tracking_number)
        
        return {
            "tracking_number": tracking_number,
            "carrier": TrackingCarrier.ONTRAC.value,
            "is_valid": is_valid,
            "message": "Valid OnTrac tracking number format" if is_valid else "Invalid OnTrac tracking number format"
        }
    except Exception as e:
        logger.error(f"Error validating OnTrac tracking number {tracking_number}: {e}")
        return {
            "tracking_number": tracking_number,
            "carrier": TrackingCarrier.ONTRAC.value,
            "is_valid": False,
            "error_message": f"Validation error: {e}"
        }


def get_ontrac_service_types() -> Dict[str, Any]:
    """
    Get available OnTrac service types.

    Returns:
        Dict[str, Any]: Available service types
    """
    return {
        "carrier": TrackingCarrier.ONTRAC.value,
        "service_types": [
            {
                "code": "GROUND",
                "name": "OnTrac Ground",
                "description": "Standard ground delivery"
            },
            {
                "code": "SUNRISE",
                "name": "OnTrac Sunrise",
                "description": "Early morning delivery"
            },
            {
                "code": "GOLD",
                "name": "OnTrac Gold",
                "description": "Time-definite delivery by 5 PM"
            },
            {
                "code": "PALLETIZED",
                "name": "OnTrac Palletized",
                "description": "Pallet shipping service"
            }
        ]
    }