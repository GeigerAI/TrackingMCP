"""
FedEx MCP tools for package tracking.

Exposes FedEx tracking functionality as MCP tools for AI agents.
"""

import logging
from typing import List

from ..models import TrackingCarrier, TrackingResult
from ..tracking.fedex_tracker import FedExTracker

logger = logging.getLogger(__name__)


def register_fedex_tools(app):
    """
    Register FedEx tracking tools with the FastAPI server.

    Args:
        app: FastAPI app instance to register tools with
    """

    @app.post("/tracking/fedex/track")
    async def track_fedex_package(tracking_number: str) -> TrackingResult:
        """
        Track a FedEx package by tracking number.

        Provides real-time tracking information for FedEx shipments including
        current status, location, delivery estimates, and tracking history.

        Args:
            tracking_number: FedEx tracking number (12-22 digits)

        Returns:
            TrackingResult: Complete tracking information including:
                - Current package status
                - Estimated delivery date
                - Tracking events with timestamps and locations
                - Service type and package details
        """
        try:
            logger.info(f"Tracking FedEx package: {tracking_number}")

            # Reason: Create tracker with automatic authentication
            tracker = FedExTracker()
            result = await tracker.track_package(tracking_number)

            logger.info(f"Successfully tracked FedEx package {tracking_number}: {result.status}")
            return result

        except Exception as e:
            logger.error(f"Failed to track FedEx package {tracking_number}: {e}")
            # Reason: Return structured error result instead of raising exception
            return TrackingResult(
                tracking_number=tracking_number,
                carrier=TrackingCarrier.FEDEX,
                status="exception",
                error_message=f"Tracking failed: {str(e)}"
            )

    @app.post("/tracking/fedex/track_multiple")
    async def track_multiple_fedex_packages(tracking_numbers: List[str]) -> List[TrackingResult]:
        """
        Track multiple FedEx packages in a single request.

        Efficiently tracks up to 30 FedEx packages at once using batch API calls.
        Useful for processing multiple shipments simultaneously.

        Args:
            tracking_numbers: List of FedEx tracking numbers (max 30)

        Returns:
            List[TrackingResult]: List of tracking results for each package
        """
        try:
            logger.info(f"Tracking {len(tracking_numbers)} FedEx packages")

            # Reason: Create tracker with automatic authentication
            tracker = FedExTracker()
            results = await tracker.track_multiple_packages(tracking_numbers)

            successful_tracks = len([r for r in results if not r.error_message])
            logger.info(f"Successfully tracked {successful_tracks}/{len(results)} FedEx packages")

            return results

        except Exception as e:
            logger.error(f"Failed to track multiple FedEx packages: {e}")
            # Reason: Return error results for all tracking numbers
            return [
                TrackingResult(
                    tracking_number=tn,
                    carrier=TrackingCarrier.FEDEX,
                    status="exception",
                    error_message=f"Batch tracking failed: {str(e)}"
                )
                for tn in tracking_numbers
            ]

    @app.post("/tracking/fedex/validate")
    async def validate_fedex_tracking_number(tracking_number: str) -> bool:
        """
        Validate if a tracking number matches FedEx format.

        Checks if the provided tracking number follows standard FedEx
        tracking number patterns without making an API call.

        Args:
            tracking_number: Tracking number to validate

        Returns:
            bool: True if the format is valid for FedEx
        """
        try:
            tracker = FedExTracker()
            is_valid = tracker.validate_tracking_number(tracking_number)

            logger.debug(f"FedEx tracking number validation for {tracking_number}: {is_valid}")
            return is_valid

        except Exception as e:
            logger.error(f"Error validating FedEx tracking number {tracking_number}: {e}")
            return False

    logger.info("Registered FedEx tracking tools with FastAPI server")
