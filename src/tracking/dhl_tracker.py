"""
DHL package tracking service.

Implements package tracking for DHL eCommerce shipments using the DHL Tracking API.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..auth.dhl_auth import DHLAuth
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


class DHLTracker(BaseTracker):
    """
    DHL package tracking implementation.

    Handles tracking requests for DHL eCommerce shipments with automatic authentication
    and response parsing.
    """

    def __init__(self, auth: Optional[DHLAuth] = None):
        """
        Initialize DHL tracker.

        Args:
            auth: DHL authentication instance (creates new if None)
        """
        super().__init__(TrackingCarrier.DHL)
        self.auth = auth or DHLAuth()
        self.base_api_url = f"{self.auth.base_url}/tracking/v4/package/open"

    def validate_tracking_number(self, tracking_number: str) -> bool:
        """
        Validate DHL tracking number format.

        DHL tracking numbers can be:
        - Package ID: Various alphanumeric formats
        - DHL Package ID: Numeric format
        - Tracking ID: Long numeric format (like USPS)
        - Manifest ID: Numeric format

        Args:
            tracking_number: Tracking number to validate

        Returns:
            bool: True if format is valid
        """
        if not tracking_number or not isinstance(tracking_number, str):
            return False

        # Reason: Remove any spaces or special characters
        clean_number = re.sub(r'[^a-zA-Z0-9]', '', tracking_number.upper())

        # Reason: Check common DHL tracking number patterns
        dhl_patterns = [
            r'^[A-Z]{2}[0-9]{9}[A-Z]{2}$',        # Standard DHL Express format
            r'^[0-9]{10,30}$',                      # DHL eCommerce numeric formats
            r'^[A-Z0-9]{10,30}$',                   # Alphanumeric package IDs
            r'^GM[0-9]{17}$',                       # GM prefix format
            r'^420[0-9]{27}$',                      # USPS tracking format
        ]

        # Reason: Basic length check - DHL tracking numbers are typically 10-30 chars
        if len(clean_number) < 10 or len(clean_number) > 30:
            return False

        return any(re.match(pattern, clean_number) for pattern in dhl_patterns)

    def _get_max_batch_size(self) -> int:
        """
        Get maximum batch size for DHL API.

        Returns:
            int: DHL allows up to 10 tracking numbers per request
        """
        return 10

    async def track_package(self, tracking_number: str) -> TrackingResult:
        """
        Track a single DHL package.

        Args:
            tracking_number: DHL tracking number

        Returns:
            TrackingResult: Tracking information

        Raises:
            TrackingError: If tracking fails
        """
        if not self.validate_tracking_number(tracking_number):
            raise InvalidTrackingNumberError(
                f"Invalid DHL tracking number format: {tracking_number}",
                carrier=self.carrier,
                tracking_number=tracking_number
            )

        # Reason: Use trackingId parameter for most tracking numbers
        params = {
            "trackingId": tracking_number,
            "limit": 1
        }

        try:
            headers = await self.auth.get_auth_headers()

            logger.info(f"Tracking DHL package: {tracking_number}")
            response = await self._make_request("GET", self.base_api_url, headers, params=params)

            if response.status_code == 200:
                response_data = response.json()
                return self._parse_tracking_response(response_data, tracking_number)
            elif response.status_code == 401:
                # Reason: Clear token and retry once for authentication issues
                self.auth.clear_token()
                headers = await self.auth.get_auth_headers()
                response = await self._make_request("GET", self.base_api_url, headers, params=params)

                if response.status_code == 200:
                    response_data = response.json()
                    return self._parse_tracking_response(response_data, tracking_number)
                else:
                    raise TrackingError(f"DHL authentication failed: {response.text}", carrier=self.carrier)
            elif response.status_code == 404:
                return TrackingResult(
                    tracking_number=tracking_number,
                    carrier=self.carrier,
                    status=TrackingStatus.NOT_FOUND,
                    error_message="Tracking number not found"
                )
            else:
                raise TrackingError(
                    f"DHL tracking request failed: HTTP {response.status_code} - {response.text}",
                    carrier=self.carrier
                )

        except Exception as e:
            if isinstance(e, TrackingError):
                raise

            logger.error(f"DHL tracking failed: {e}")
            raise TrackingError(f"DHL tracking failed: {e}", carrier=self.carrier)

    async def track_multiple_packages(self, tracking_numbers: List[str]) -> List[TrackingResult]:
        """
        Track multiple DHL packages.

        Args:
            tracking_numbers: List of DHL tracking numbers

        Returns:
            List[TrackingResult]: List of tracking results

        Raises:
            TrackingError: If tracking fails
        """
        # Reason: Validate batch before making API calls
        self._validate_tracking_numbers_batch(tracking_numbers)

        # Reason: DHL API supports multiple tracking numbers via comma-separated values
        tracking_ids = ",".join(tracking_numbers)
        params = {
            "trackingId": tracking_ids,
            "limit": min(len(tracking_numbers), self._get_max_batch_size())
        }

        try:
            headers = await self.auth.get_auth_headers()

            logger.info(f"Tracking {len(tracking_numbers)} DHL packages")
            response = await self._make_request("GET", self.base_api_url, headers, params=params)

            if response.status_code == 200:
                response_data = response.json()
                return self._parse_multiple_tracking_response(response_data, tracking_numbers)
            elif response.status_code == 401:
                # Reason: Clear token and retry once for authentication issues
                self.auth.clear_token()
                headers = await self.auth.get_auth_headers()
                response = await self._make_request("GET", self.base_api_url, headers, params=params)

                if response.status_code == 200:
                    response_data = response.json()
                    return self._parse_multiple_tracking_response(response_data, tracking_numbers)
                else:
                    raise TrackingError(f"DHL authentication failed: {response.text}", carrier=self.carrier)
            else:
                raise TrackingError(
                    f"DHL tracking request failed: HTTP {response.status_code} - {response.text}",
                    carrier=self.carrier
                )

        except Exception as e:
            if isinstance(e, TrackingError):
                raise

            logger.error(f"DHL batch tracking failed: {e}")
            raise TrackingError(f"DHL batch tracking failed: {e}", carrier=self.carrier)

    def _parse_tracking_response(self, response_data: Dict[str, Any],
                                tracking_number: str) -> TrackingResult:
        """
        Parse DHL tracking response into TrackingResult object.

        Args:
            response_data: Raw DHL API response
            tracking_number: The tracking number

        Returns:
            TrackingResult: Parsed tracking result
        """
        try:
            # Reason: DHL response contains "packages" array
            packages = response_data.get("packages", [])

            if not packages:
                return self._create_error_result(tracking_number, "No package data found")

            # Reason: Use the first package (should match our tracking number)
            package_data = packages[0]
            package_info = package_data.get("package", {})

            # Reason: Extract tracking information
            tracking_id = package_info.get("trackingId", tracking_number)
            expected_delivery = package_info.get("expectedDelivery")
            
            # Reason: Parse expected delivery date
            estimated_delivery = None
            if expected_delivery:
                try:
                    estimated_delivery = datetime.strptime(expected_delivery, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Could not parse DHL delivery date: {expected_delivery}")

            # Reason: Extract events and determine status
            events = self._parse_tracking_events(package_data.get("events", []))
            status = self._determine_status_from_events(events)

            # Reason: Extract recipient information
            recipient = package_data.get("recipient", {})
            delivery_address = self._format_delivery_address(recipient)

            # Reason: Extract service information
            service_type = package_info.get("productName", "")
            
            # Reason: Extract weight information
            weight = None
            weight_info = package_info.get("weight", {})
            if weight_info:
                weight_value = weight_info.get("value")
                weight_unit = weight_info.get("unitOfMeasure")
                if weight_value and weight_unit:
                    weight = f"{weight_value} {weight_unit}"

            return TrackingResult(
                tracking_number=tracking_number,
                carrier=self.carrier,
                status=status,
                estimated_delivery=estimated_delivery,
                events=events,
                delivery_address=delivery_address,
                service_type=service_type,
                weight=weight
            )

        except Exception as e:
            logger.error(f"Error parsing DHL tracking result for {tracking_number}: {e}")
            return self._create_error_result(
                tracking_number,
                f"Error parsing tracking data: {e}"
            )

    def _parse_multiple_tracking_response(self, response_data: Dict[str, Any],
                                        tracking_numbers: List[str]) -> List[TrackingResult]:
        """
        Parse DHL multiple tracking response into list of TrackingResult objects.

        Args:
            response_data: Raw DHL API response
            tracking_numbers: List of tracking numbers requested

        Returns:
            List[TrackingResult]: List of parsed tracking results
        """
        results = []
        packages = response_data.get("packages", [])

        # Reason: Create mapping of tracking numbers to results
        tracking_map = {}
        for package_data in packages:
            package_info = package_data.get("package", {})
            tracking_id = package_info.get("trackingId", "")
            if tracking_id:
                result = self._parse_tracking_response({"packages": [package_data]}, tracking_id)
                tracking_map[tracking_id] = result

        # Reason: Ensure we have results for all requested tracking numbers
        for tracking_number in tracking_numbers:
            if tracking_number in tracking_map:
                results.append(tracking_map[tracking_number])
            else:
                results.append(self._create_error_result(tracking_number, "Package not found in response"))

        return results

    def _parse_tracking_events(self, events: List[Dict[str, Any]]) -> List[TrackingEvent]:
        """
        Parse DHL events into TrackingEvent objects.

        Args:
            events: List of event data from DHL response

        Returns:
            List[TrackingEvent]: Parsed tracking events
        """
        parsed_events = []

        for event in events:
            try:
                # Reason: Extract event timestamp
                date_str = event.get("date", "")
                time_str = event.get("time", "")
                timestamp = None

                if date_str and time_str:
                    try:
                        # Reason: DHL uses YYYY-MM-DD date format and HH:MM:SS time format
                        datetime_str = f"{date_str} {time_str}"
                        timestamp = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        logger.warning(f"Could not parse DHL event date/time: {date_str} {time_str}")
                        timestamp = datetime.now()

                # Reason: Extract event details
                primary_desc = event.get("primaryEventDescription", "")
                secondary_desc = event.get("secondaryEventDescription", "")
                description = secondary_desc if secondary_desc else primary_desc

                # Reason: Extract location information
                location = event.get("location", "")

                if timestamp and description:
                    parsed_events.append(TrackingEvent(
                        timestamp=timestamp,
                        status=primary_desc,
                        location=location or None,
                        description=description
                    ))

            except Exception as e:
                logger.warning(f"Could not parse DHL tracking event: {e}")
                continue

        # Reason: Sort events by timestamp (earliest first for chronological order)
        parsed_events.sort(key=lambda x: x.timestamp, reverse=False)
        return parsed_events

    def _determine_status_from_events(self, events: List[TrackingEvent]) -> TrackingStatus:
        """
        Determine package status from tracking events.

        Args:
            events: List of tracking events

        Returns:
            TrackingStatus: Determined status
        """
        if not events:
            return TrackingStatus.PENDING

        # Reason: Use most recent event to determine status
        latest_event = events[0]
        status_lower = latest_event.status.lower()
        description_lower = latest_event.description.lower()

        if "delivered" in description_lower:
            return TrackingStatus.DELIVERED
        elif "out for delivery" in description_lower:
            return TrackingStatus.OUT_FOR_DELIVERY
        elif any(term in description_lower for term in ["processed", "departed", "arrived", "in transit"]):
            return TrackingStatus.IN_TRANSIT
        elif any(term in description_lower for term in ["exception", "delayed", "returned", "unable"]):
            return TrackingStatus.EXCEPTION
        else:
            return TrackingStatus.IN_TRANSIT  # Default to in transit

    def _format_delivery_address(self, recipient: Dict[str, Any]) -> Optional[str]:
        """
        Format delivery address from recipient information.

        Args:
            recipient: Recipient information from DHL response

        Returns:
            Optional[str]: Formatted delivery address
        """
        if not recipient:
            return None

        address_parts = []
        
        city = recipient.get("city", "")
        state = recipient.get("state", "")
        postal_code = recipient.get("postalCode", "")
        country = recipient.get("country", "")

        if city:
            address_parts.append(city)
        if state:
            address_parts.append(state)
        if postal_code:
            address_parts.append(postal_code)
        if country:
            address_parts.append(country)

        return ", ".join(address_parts) if address_parts else None