"""
UPS MCP tools for package tracking.

Exposes UPS tracking functionality as MCP tools for AI agents.
"""

import logging
from typing import List

from ..auth.ups_auth import UPSAuth
from ..models import TrackingCarrier, TrackingResult
from ..tracking.ups_tracker import UPSTracker

logger = logging.getLogger(__name__)


def register_ups_tools(app):
    """
    Register UPS tracking tools with the FastAPI server.

    Args:
        app: FastAPI app instance to register tools with
    """

    @app.post("/tracking/ups/track")
    async def track_ups_package(tracking_number: str) -> TrackingResult:
        """
        Track a UPS package by tracking number.

        Provides real-time tracking information for UPS shipments including
        current status, location, delivery estimates, and tracking history.

        Args:
            tracking_number: UPS tracking number (typically starts with 1Z)

        Returns:
            TrackingResult: Complete tracking information including:
                - Current package status
                - Estimated delivery date
                - Tracking events with timestamps and locations
                - Service type and package details
        """
        try:
            logger.info(f"Tracking UPS package: {tracking_number}")

            # Reason: Create tracker with automatic authentication
            tracker = UPSTracker()
            result = await tracker.track_package(tracking_number)

            logger.info(f"Successfully tracked UPS package {tracking_number}: {result.status}")
            return result

        except Exception as e:
            logger.error(f"Failed to track UPS package {tracking_number}: {e}")
            # Reason: Return structured error result instead of raising exception
            return TrackingResult(
                tracking_number=tracking_number,
                carrier=TrackingCarrier.UPS,
                status="exception",
                error_message=f"Tracking failed: {str(e)}"
            )

    @app.post("/tracking/ups/track_multiple")
    async def track_multiple_ups_packages(tracking_numbers: List[str]) -> List[TrackingResult]:
        """
        Track multiple UPS packages.

        Tracks multiple UPS packages using individual API calls since UPS
        doesn't support bulk tracking. Processes requests efficiently with
        proper error handling for each package.

        Args:
            tracking_numbers: List of UPS tracking numbers (max 10 recommended)

        Returns:
            List[TrackingResult]: List of tracking results for each package
        """
        try:
            logger.info(f"Tracking {len(tracking_numbers)} UPS packages")

            # Reason: Create tracker with automatic authentication
            tracker = UPSTracker()
            results = await tracker.track_multiple_packages(tracking_numbers)

            successful_tracks = len([r for r in results if not r.error_message])
            logger.info(f"Successfully tracked {successful_tracks}/{len(results)} UPS packages")

            return results

        except Exception as e:
            logger.error(f"Failed to track multiple UPS packages: {e}")
            # Reason: Return error results for all tracking numbers
            return [
                TrackingResult(
                    tracking_number=tn,
                    carrier=TrackingCarrier.UPS,
                    status="exception",
                    error_message=f"Batch tracking failed: {str(e)}"
                )
                for tn in tracking_numbers
            ]

    @app.post("/tracking/ups/validate")
    async def validate_ups_tracking_number(tracking_number: str) -> bool:
        """
        Validate if a tracking number matches UPS format.

        Checks if the provided tracking number follows standard UPS
        tracking number patterns without making an API call.

        Args:
            tracking_number: Tracking number to validate

        Returns:
            bool: True if the format is valid for UPS
        """
        try:
            tracker = UPSTracker()
            is_valid = tracker.validate_tracking_number(tracking_number)

            logger.debug(f"UPS tracking number validation for {tracking_number}: {is_valid}")
            return is_valid

        except Exception as e:
            logger.error(f"Error validating UPS tracking number {tracking_number}: {e}")
            return False

    @app.get("/tracking/ups/oauth_url")
    async def get_ups_authorization_url() -> str:
        """
        Get UPS OAuth authorization URL for initial setup.

        Returns the URL that users need to visit to authorize the application
        to access UPS tracking data. This is required for the initial OAuth flow.

        Returns:
            str: Authorization URL for user to visit
        """
        try:
            auth = UPSAuth()
            auth_url = auth.get_authorization_url()

            logger.info("Generated UPS authorization URL")
            return auth_url

        except Exception as e:
            logger.error(f"Failed to generate UPS authorization URL: {e}")
            return f"Error generating authorization URL: {str(e)}"

    logger.info("Registered UPS tracking tools with FastAPI server")
