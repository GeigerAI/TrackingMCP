"""
UPS package tracking service.

Implements package tracking for UPS shipments using the UPS Track API.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..auth.ups_auth import UPSAuth
from ..models import (
    InvalidTrackingNumberError,
    TrackingCarrier,
    TrackingError,
    TrackingEvent,
    TrackingResult,
    TrackingStatus,
)
from .base_tracker import BaseTracker

logger = logging.getLogger(__name__)


class UPSTracker(BaseTracker):
    """
    UPS package tracking implementation.

    Handles tracking requests for UPS shipments with automatic authentication
    and response parsing.
    """

    def __init__(self, auth: Optional[UPSAuth] = None):
        """
        Initialize UPS tracker.

        Args:
            auth: UPS authentication instance (creates new if None)
        """
        super().__init__(TrackingCarrier.UPS)
        self.auth = auth or UPSAuth()
        self.base_api_url = f"{self.auth.base_url}/api/track/v1/details"

    def validate_tracking_number(self, tracking_number: str) -> bool:
        """
        Validate UPS tracking number format.

        UPS tracking numbers can be:
        - 18 digits: 1Z tracking number (most common)
        - Mail Innovations: 22-25 digits
        - Reference numbers: Various formats

        Args:
            tracking_number: Tracking number to validate

        Returns:
            bool: True if format is valid
        """
        if not tracking_number or not isinstance(tracking_number, str):
            return False

        # Reason: Remove any spaces or special characters
        clean_number = re.sub(r'[^a-zA-Z0-9]', '', tracking_number.upper())

        # Reason: Check common UPS tracking number patterns
        ups_patterns = [
            r'^1Z[0-9A-Z]{16}$',       # Standard 1Z tracking number
            r'^[0-9]{12}$',            # 12 digit reference
            r'^[0-9]{18}$',            # 18 digit tracking
            r'^[0-9]{22,25}$',         # Mail Innovations
            r'^T[0-9]{10}$',           # UPS InfoNotice
        ]

        return any(re.match(pattern, clean_number) for pattern in ups_patterns)

    def _get_max_batch_size(self) -> int:
        """
        Get maximum batch size for UPS API.

        Returns:
            int: UPS typically allows fewer tracking numbers per request than FedEx
        """
        return 10  # Conservative estimate for UPS

    async def track_package(self, tracking_number: str) -> TrackingResult:
        """
        Track a single UPS package.

        Args:
            tracking_number: UPS tracking number

        Returns:
            TrackingResult: Tracking information

        Raises:
            TrackingError: If tracking fails
        """
        if not self.validate_tracking_number(tracking_number):
            raise InvalidTrackingNumberError(
                f"Invalid UPS tracking number format: {tracking_number}",
                carrier=self.carrier,
                tracking_number=tracking_number
            )

        url = f"{self.base_api_url}/{tracking_number}"

        # Reason: UPS API query parameters
        params = {
            "locale": "en_US",
            "returnSignature": "false",
            "returnMilestones": "false",
            "returnPOD": "false"
        }

        try:
            headers = await self.auth.get_auth_headers()

            logger.info(f"Tracking UPS package: {tracking_number}")
            response = await self._make_request("GET", url, headers, params=params)

            if response.status_code == 200:
                response_data = response.json()
                return self._parse_tracking_response(response_data, tracking_number)
            elif response.status_code == 401:
                # Reason: Clear token and retry once for authentication issues
                self.auth.clear_token()
                headers = await self.auth.get_auth_headers()
                response = await self._make_request("GET", url, headers, params=params)

                if response.status_code == 200:
                    response_data = response.json()
                    return self._parse_tracking_response(response_data, tracking_number)
                else:
                    raise TrackingError(f"UPS authentication failed: {response.text}", carrier=self.carrier)
            elif response.status_code == 404:
                return TrackingResult(
                    tracking_number=tracking_number,
                    carrier=self.carrier,
                    status=TrackingStatus.NOT_FOUND,
                    error_message="Tracking number not found"
                )
            else:
                raise TrackingError(
                    f"UPS tracking request failed: HTTP {response.status_code} - {response.text}",
                    carrier=self.carrier
                )

        except Exception as e:
            if isinstance(e, TrackingError):
                raise

            logger.error(f"UPS tracking failed: {e}")
            raise TrackingError(f"UPS tracking failed: {e}", carrier=self.carrier)

    async def track_multiple_packages(self, tracking_numbers: List[str]) -> List[TrackingResult]:
        """
        Track multiple UPS packages.

        Note: UPS API doesn't support bulk tracking, so we make individual requests.

        Args:
            tracking_numbers: List of UPS tracking numbers

        Returns:
            List[TrackingResult]: List of tracking results

        Raises:
            TrackingError: If tracking fails
        """
        # Reason: Validate batch before making API calls
        self._validate_tracking_numbers_batch(tracking_numbers)

        results = []

        # Reason: UPS doesn't support bulk tracking, make individual requests
        for tracking_number in tracking_numbers:
            try:
                result = await self.track_package(tracking_number)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to track UPS package {tracking_number}: {e}")
                error_result = self._create_error_result(
                    tracking_number,
                    f"Tracking failed: {e}"
                )
                results.append(error_result)

        return results

    def _parse_tracking_response(self, response_data: Dict[str, Any],
                                tracking_number: str) -> TrackingResult:
        """
        Parse UPS tracking response into TrackingResult object.

        Args:
            response_data: Raw UPS API response
            tracking_number: The tracking number

        Returns:
            TrackingResult: Parsed tracking result
        """
        try:
            # Reason: UPS response contains "trackResponse" with "shipment" array
            track_response = response_data.get("trackResponse", {})
            shipments = track_response.get("shipment", [])

            if not shipments:
                return self._create_error_result(tracking_number, "No shipment data found")

            # Reason: Use the first shipment (should only be one for single tracking number)
            shipment = shipments[0]

            # Reason: Extract package information
            packages = shipment.get("package", [])
            if not packages:
                return self._create_error_result(tracking_number, "No package data found")

            # Reason: Use the first package
            package = packages[0]

            # Reason: Extract status information
            current_status = package.get("currentStatus", {})
            status_description = current_status.get("description", "Unknown")
            status_code = current_status.get("code", "")

            # Reason: Map UPS status to our standard status
            mapped_status = self._map_ups_status(status_code, status_description)

            # Reason: Extract delivery information
            estimated_delivery = None
            delivery_address = None

            delivery_date = package.get("deliveryDate", [])
            if delivery_date:
                # Reason: Parse delivery date from UPS format
                delivery_info = delivery_date[0]
                date_str = delivery_info.get("date", "")
                if date_str:
                    try:
                        estimated_delivery = datetime.strptime(date_str, "%Y%m%d")
                    except ValueError:
                        logger.warning(f"Could not parse UPS delivery date: {date_str}")

            # Reason: Extract delivery location
            delivery_location = package.get("deliveryInformation", {})
            if delivery_location:
                location = delivery_location.get("location", "")
                delivery_address = location

            # Reason: Extract tracking events
            events = self._parse_tracking_events(package.get("activity", []))

            # Reason: Extract service information
            service = shipment.get("service", {})
            service_type = service.get("description", "")

            # Reason: Extract package weight
            package_weight = package.get("packageWeight", {})
            weight = None
            if package_weight:
                weight_value = package_weight.get("weight", "")
                weight_unit = package_weight.get("unitOfMeasurement", {}).get("description", "")
                if weight_value and weight_unit:
                    weight = f"{weight_value} {weight_unit}"

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
            logger.error(f"Error parsing UPS tracking result for {tracking_number}: {e}")
            return self._create_error_result(
                tracking_number,
                f"Error parsing tracking data: {e}"
            )

    def _parse_tracking_events(self, activities: List[Dict[str, Any]]) -> List[TrackingEvent]:
        """
        Parse UPS activity events into TrackingEvent objects.

        Args:
            activities: List of activity events from UPS response

        Returns:
            List[TrackingEvent]: Parsed tracking events
        """
        events = []

        for activity in activities:
            try:
                # Reason: Extract event timestamp
                date_str = activity.get("date", "")
                time_str = activity.get("time", "")
                timestamp = None

                if date_str and time_str:
                    try:
                        # Reason: UPS uses YYYYMMDD date format and HHMMSS time format
                        datetime_str = f"{date_str}{time_str}"
                        timestamp = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
                    except ValueError:
                        logger.warning(f"Could not parse UPS activity date/time: {date_str} {time_str}")
                        timestamp = datetime.now()

                # Reason: Extract event details
                status_info = activity.get("status", {})
                event_description = status_info.get("description", "")
                event_type = status_info.get("type", "")

                # Reason: Extract location information
                location_info = activity.get("location", {})
                location = ""
                if location_info:
                    address = location_info.get("address", {})
                    city = address.get("city", "")
                    state = address.get("stateProvinceCode", "")
                    country = address.get("countryCode", "")
                    location = f"{city}, {state} {country}".strip(", ")

                if timestamp and event_description:
                    events.append(TrackingEvent(
                        timestamp=timestamp,
                        status=event_type,
                        location=location or None,
                        description=event_description
                    ))

            except Exception as e:
                logger.warning(f"Could not parse UPS tracking event: {e}")
                continue

        # Reason: Sort events by timestamp (earliest first for chronological order)
        events.sort(key=lambda x: x.timestamp, reverse=False)
        return events

    def _map_ups_status(self, status_code: str, status_description: str) -> TrackingStatus:
        """
        Map UPS status codes to standardized tracking status.

        Args:
            status_code: UPS status code
            status_description: UPS status description

        Returns:
            TrackingStatus: Mapped status
        """
        status_lower = status_description.lower()

        if "delivered" in status_lower:
            return TrackingStatus.DELIVERED
        elif "out for delivery" in status_lower:
            return TrackingStatus.OUT_FOR_DELIVERY
        elif any(term in status_lower for term in ["in transit", "departed", "arrived", "origin scan"]):
            return TrackingStatus.IN_TRANSIT
        elif any(term in status_lower for term in ["exception", "delayed", "weather", "unable", "returned"]):
            return TrackingStatus.EXCEPTION
        elif "order processed" in status_lower or not status_description:
            return TrackingStatus.PENDING
        else:
            return TrackingStatus.IN_TRANSIT  # Default to in transit
