"""
FedEx package tracking service.

Implements package tracking for FedEx shipments using the FedEx Track API.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..auth.fedex_auth import FedExAuth
from ..models import (
    TrackingCarrier,
    TrackingError,
    TrackingEvent,
    TrackingResult,
    TrackingStatus,
)
from .base_tracker import BaseTracker

logger = logging.getLogger(__name__)


class FedExTracker(BaseTracker):
    """
    FedEx package tracking implementation.

    Handles tracking requests for FedEx shipments with automatic authentication
    and response parsing.
    """

    def __init__(self, auth: Optional[FedExAuth] = None):
        """
        Initialize FedEx tracker.

        Args:
            auth: FedEx authentication instance (creates new if None)
        """
        super().__init__(TrackingCarrier.FEDEX)
        self.auth = auth or FedExAuth()
        self.api_url = f"{self.auth.base_url}/track/v1/trackingnumbers"

    def validate_tracking_number(self, tracking_number: str) -> bool:
        """
        Validate FedEx tracking number format.

        FedEx tracking numbers can be:
        - 12 digits: Express tracking number
        - 14 digits: Ground tracking number
        - 15 digits: SmartPost tracking number
        - 22 digits: FedEx Ground barcode

        Args:
            tracking_number: Tracking number to validate

        Returns:
            bool: True if format is valid
        """
        if not tracking_number or not isinstance(tracking_number, str):
            return False

        # Reason: Remove any spaces or special characters
        clean_number = re.sub(r'[^a-zA-Z0-9]', '', tracking_number.upper())

        # Reason: Check common FedEx tracking number patterns
        fedex_patterns = [
            r'^\d{12}$',        # 12 digit Express
            r'^\d{14}$',        # 14 digit Ground
            r'^\d{15}$',        # 15 digit SmartPost
            r'^\d{22}$',        # 22 digit Ground barcode
            r'^[0-9]{4}[0-9]{4}[0-9]{4}$',  # 12 digit with spacing
        ]

        return any(re.match(pattern, clean_number) for pattern in fedex_patterns)

    def _get_max_batch_size(self) -> int:
        """
        Get maximum batch size for FedEx API.

        Returns:
            int: Maximum 30 tracking numbers per request (FedEx limit)
        """
        return 30

    async def track_package(self, tracking_number: str) -> TrackingResult:
        """
        Track a single FedEx package.

        Args:
            tracking_number: FedEx tracking number

        Returns:
            TrackingResult: Tracking information

        Raises:
            TrackingError: If tracking fails
        """
        results = await self.track_multiple_packages([tracking_number])
        return results[0]

    async def track_multiple_packages(self, tracking_numbers: List[str]) -> List[TrackingResult]:
        """
        Track multiple FedEx packages in a single request.

        Args:
            tracking_numbers: List of FedEx tracking numbers (max 30)

        Returns:
            List[TrackingResult]: List of tracking results

        Raises:
            TrackingError: If tracking fails
        """
        # Reason: Validate batch before making API call
        self._validate_tracking_numbers_batch(tracking_numbers)

        payload = {
            "includeDetailedScans": True,
            "trackingInfo": [
                {
                    "trackingNumberInfo": {
                        "trackingNumber": tracking_number
                    }
                }
                for tracking_number in tracking_numbers
            ]
        }

        try:
            headers = await self.auth.get_auth_headers()

            logger.info(f"Tracking {len(tracking_numbers)} FedEx packages")
            response = await self._make_request("POST", self.api_url, headers, data=payload)

            if response.status_code == 200:
                response_data = response.json()
                return self._parse_tracking_response(response_data, tracking_numbers)
            elif response.status_code == 401:
                # Reason: Clear token and retry once for authentication issues
                self.auth.clear_token()
                headers = await self.auth.get_auth_headers()
                response = await self._make_request("POST", self.api_url, headers, data=payload)

                if response.status_code == 200:
                    response_data = response.json()
                    return self._parse_tracking_response(response_data, tracking_numbers)
                else:
                    raise TrackingError(f"FedEx authentication failed: {response.text}", carrier=self.carrier)
            else:
                raise TrackingError(
                    f"FedEx tracking request failed: HTTP {response.status_code} - {response.text}",
                    carrier=self.carrier
                )

        except Exception as e:
            if isinstance(e, TrackingError):
                raise

            logger.error(f"FedEx tracking failed: {e}")
            raise TrackingError(f"FedEx tracking failed: {e}", carrier=self.carrier)

    def _parse_tracking_response(self, response_data: Dict[str, Any],
                                requested_numbers: List[str]) -> List[TrackingResult]:
        """
        Parse FedEx tracking response into TrackingResult objects.

        Args:
            response_data: Raw FedEx API response
            requested_numbers: List of requested tracking numbers

        Returns:
            List[TrackingResult]: Parsed tracking results
        """
        results = []

        # Reason: FedEx response contains "output" with "completeTrackResults"
        complete_track_results = response_data.get("output", {}).get("completeTrackResults", [])

        # Reason: Create a mapping of tracking numbers to results
        results_map = {}
        for track_result in complete_track_results:
            tracking_number = track_result.get("trackingNumber", "")
            results_map[tracking_number] = track_result

        # Reason: Ensure we return results for all requested numbers
        for tracking_number in requested_numbers:
            if tracking_number in results_map:
                track_data = results_map[tracking_number]
                result = self._parse_single_tracking_result(track_data, tracking_number)
            else:
                result = self._create_error_result(
                    tracking_number,
                    "Tracking number not found in FedEx response"
                )

            results.append(result)

        return results

    def _parse_single_tracking_result(self, track_data: Dict[str, Any],
                                    tracking_number: str) -> TrackingResult:
        """
        Parse a single FedEx tracking result.

        Args:
            track_data: Single tracking result from FedEx response
            tracking_number: The tracking number

        Returns:
            TrackingResult: Parsed tracking result
        """
        try:
            # Reason: Extract basic tracking information
            track_results = track_data.get("trackResults", [])
            if not track_results:
                return self._create_error_result(tracking_number, "No tracking results found")

            # Reason: Use the first (most recent) tracking result
            track_info = track_results[0]

            # Reason: Extract status information
            latest_status_detail = track_info.get("latestStatusDetail", {})
            status_code = latest_status_detail.get("code", "")
            status_description = latest_status_detail.get("description", "Unknown")

            # Reason: Map FedEx status to our standard status
            mapped_status = self._map_fedex_status(status_code, status_description)

            # Reason: Extract delivery information
            estimated_delivery = None
            delivery_address = None

            delivery_details = track_info.get("deliveryDetails", {})
            if delivery_details:
                delivery_address = delivery_details.get("deliveryLocation", "")

                # Reason: Parse estimated delivery date
                estimated_delivery_str = delivery_details.get("estimatedDeliveryTimeWindow", {}).get("window", {}).get("ends")
                if estimated_delivery_str:
                    try:
                        estimated_delivery = datetime.fromisoformat(estimated_delivery_str.replace("Z", "+00:00"))
                    except ValueError:
                        logger.warning(f"Could not parse delivery date: {estimated_delivery_str}")

            # Reason: Extract tracking events
            events = self._parse_tracking_events(track_info.get("scanEvents", []))

            # Reason: Extract service information
            service_detail = track_info.get("serviceDetail", {})
            service_type = service_detail.get("description", "")

            # Reason: Extract package weight
            package_details = track_info.get("packageDetails", {})
            weight_info = package_details.get("weight", {})
            weight = f"{weight_info.get('value', '')} {weight_info.get('unit', '')}" if weight_info else None

            return TrackingResult(
                tracking_number=tracking_number,
                carrier=self.carrier,
                status=mapped_status,
                estimated_delivery=estimated_delivery,
                events=events,
                delivery_address=delivery_address,
                service_type=service_type,
                weight=weight
            )

        except Exception as e:
            logger.error(f"Error parsing FedEx tracking result for {tracking_number}: {e}")
            return self._create_error_result(
                tracking_number,
                f"Error parsing tracking data: {e}"
            )

    def _parse_tracking_events(self, scan_events: List[Dict[str, Any]]) -> List[TrackingEvent]:
        """
        Parse FedEx scan events into TrackingEvent objects.

        Args:
            scan_events: List of scan events from FedEx response

        Returns:
            List[TrackingEvent]: Parsed tracking events
        """
        events = []

        for event in scan_events:
            try:
                # Reason: Extract event timestamp
                date_str = event.get("date", "")
                timestamp = None
                if date_str:
                    try:
                        timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except ValueError:
                        logger.warning(f"Could not parse event date: {date_str}")
                        continue  # Skip events with invalid dates

                # Reason: Extract event details
                event_description = event.get("eventDescription", "")
                event_type = event.get("eventType", "")

                # Reason: Extract location information
                location_detail = event.get("scanLocation", {})
                location = ""
                if location_detail:
                    city = location_detail.get("city", "")
                    state = location_detail.get("stateOrProvinceCode", "")
                    country = location_detail.get("countryCode", "")
                    location = f"{city}, {state} {country}".strip(", ")

                if timestamp and event_description:
                    events.append(TrackingEvent(
                        timestamp=timestamp,
                        status=event_type,
                        location=location or None,
                        description=event_description
                    ))

            except Exception as e:
                logger.warning(f"Could not parse tracking event: {e}")
                continue

        # Reason: Sort events by timestamp (earliest first for chronological order)
        events.sort(key=lambda x: x.timestamp, reverse=False)
        return events

    def _map_fedex_status(self, status_code: str, status_description: str) -> TrackingStatus:
        """
        Map FedEx status codes to standardized tracking status.

        Args:
            status_code: FedEx status code
            status_description: FedEx status description

        Returns:
            TrackingStatus: Mapped status
        """
        status_lower = status_description.lower()

        if "delivered" in status_lower:
            return TrackingStatus.DELIVERED
        elif "out for delivery" in status_lower:
            return TrackingStatus.OUT_FOR_DELIVERY
        elif any(term in status_lower for term in ["in transit", "departed", "arrived", "scanned"]):
            return TrackingStatus.IN_TRANSIT
        elif any(term in status_lower for term in ["exception", "delayed", "weather", "unable"]):
            return TrackingStatus.EXCEPTION
        elif "pending" in status_lower or not status_description:
            return TrackingStatus.PENDING
        else:
            return TrackingStatus.IN_TRANSIT  # Default to in transit
