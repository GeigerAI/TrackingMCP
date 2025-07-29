"""
OnTrac package tracking implementation.

Handles package tracking operations for OnTrac shipments using their REST API.
"""

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional

import httpx

from ..auth.ontrac_auth import OnTracAuth
from ..models import (
    PackageLocation,
    TrackingCarrier,
    TrackingError,
    TrackingEvent,
    TrackingResult,
    TrackingStatus,
)
from .base_tracker import BaseTracker

logger = logging.getLogger(__name__)


class OnTracTracker(BaseTracker):
    """
    OnTrac package tracking service.

    Implements package tracking for OnTrac shipments using their REST API.
    """

    def __init__(self, api_key: Optional[str] = None, account_number: Optional[str] = None,
                 sandbox: Optional[bool] = None):
        """
        Initialize OnTrac tracker.

        Args:
            api_key: OnTrac API key (defaults to config)
            account_number: OnTrac account number (defaults to config)
            sandbox: Use sandbox environment (defaults to config)
        """
        super().__init__(TrackingCarrier.ONTRAC)
        self.auth = OnTracAuth(api_key=api_key, account_number=account_number, sandbox=sandbox)

    def _get_max_batch_size(self) -> int:
        """
        Returns the maximum number of tracking numbers allowed in a single batch request.
        OnTrac does not support batch tracking, so this is 1.
        """
        return 1

    def validate_tracking_number(self, tracking_number: str) -> bool:
        """
        Validate OnTrac tracking number format.

        OnTrac tracking numbers are typically:
        - C + 14 digits (e.g., C10000012345678)
        - D + 14 digits (e.g., D10000012345678)

        Args:
            tracking_number: Tracking number to validate

        Returns:
            bool: True if format is valid
        """
        # Reason: OnTrac tracking numbers start with C or D followed by 14 digits
        pattern = r'^[CD]\d{14}$'
        return bool(re.match(pattern, tracking_number.strip().upper()))

    async def track_package(self, tracking_number: str) -> TrackingResult:
        """
        Track a single OnTrac package.

        Args:
            tracking_number: Package tracking number

        Returns:
            TrackingResult: Structured tracking information

        Raises:
            TrackingError: If tracking fails
        """
        tracking_number = tracking_number.strip().upper()

        if not self.validate_tracking_number(tracking_number):
            raise TrackingError(f"Invalid OnTrac tracking number format: {tracking_number}")

        # OnTrac uses URL parameters, not headers for auth
        account_number = self.auth.account_number or "37"  # Default test account
        
        # Build URL according to OnTrac API spec
        url = f"{self.auth.base_url}/V7/{account_number}/shipments"
        
        # Get authentication parameters and add tracking-specific params
        params = self.auth.get_auth_params()
        params.update({
            "tn": tracking_number,
            "requestType": "track"
        })

        try:
            # Get appropriate headers for OnTrac API
            headers = await self.auth.get_auth_headers()
            
            # OnTrac expects GET with query parameters, not headers
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                
                # Debug: Log response content
                logger.info(f"OnTrac API response status: {response.status_code}")
                logger.info(f"OnTrac API response headers: {response.headers}")
                logger.debug(f"OnTrac API response content (first 500 chars): {response.text[:500]}")
                
                response.raise_for_status()
                
                # OnTrac returns XML, not JSON
                return self._parse_xml_response(response.text, tracking_number)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise TrackingError(f"Tracking number not found: {tracking_number}")
            elif e.response.status_code == 401:
                raise TrackingError("Authentication failed. Please check your API key.")
            else:
                logger.error(f"OnTrac API error: {e.response.status_code} - {e.response.text}")
                raise TrackingError(f"OnTrac API error: {e.response.status_code}")

        except Exception as e:
            logger.error(f"Error tracking OnTrac package {tracking_number}: {e}")
            raise TrackingError(f"Failed to track package: {str(e)}")

    async def track_multiple_packages(self, tracking_numbers: List[str]) -> List[TrackingResult]:
        """
        Track multiple OnTrac packages.

        OnTrac doesn't support batch tracking, so we make concurrent requests.

        Args:
            tracking_numbers: List of tracking numbers

        Returns:
            List[TrackingResult]: List of tracking results

        Raises:
            TrackingError: If tracking fails
        """
        # Reason: OnTrac doesn't have batch tracking, use concurrent requests
        tasks = [self.track_package(tn) for tn in tracking_numbers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error tracking {tracking_numbers[i]}: {result}")
                # Create error result
                final_results.append(TrackingResult(
                    tracking_number=tracking_numbers[i],
                    carrier=self.carrier,
                    status=TrackingStatus.ERROR,
                    error_message=str(result),
                    events=[]
                ))
            else:
                final_results.append(result)

        return final_results

    def _parse_xml_response(self, xml_text: str, tracking_number: str) -> TrackingResult:
        """
        Parse OnTrac XML tracking API response.

        Args:
            xml_text: Raw XML response from OnTrac API
            tracking_number: Original tracking number

        Returns:
            TrackingResult: Parsed tracking information
        """
        try:
            root = ET.fromstring(xml_text)
            
            # Check for API errors first
            error_elem = root.find('.//Error')
            if error_elem is not None and error_elem.text:
                raise TrackingError(f"OnTrac API error: {error_elem.text}")
            
            # Find the shipment element
            shipment = root.find('.//Shipment')
            if shipment is None:
                raise TrackingError("No shipment data found in OnTrac response")
            
            # Parse tracking events
            events = []
            events_container = shipment.find('Events')
            if events_container is not None:
                for event_elem in events_container.findall('Event'):
                    event = self._parse_xml_event(event_elem)
                    if event:
                        events.append(event)
            
            # Sort events by timestamp (newest first)
            events.sort(key=lambda e: e.timestamp, reverse=True)
            
            # Determine current status
            delivered = shipment.findtext('Delivered', '').lower() == 'true'
            status = TrackingStatus.DELIVERED if delivered else self._determine_status_from_events(events)
            
            # Get delivery info
            delivered_at = None
            estimated_delivery = None
            
            # Parse expected delivery date
            exp_del_date = shipment.findtext('Exp_Del_Date')
            if exp_del_date:
                try:
                    estimated_delivery = datetime.fromisoformat(exp_del_date.rstrip('Z'))
                except (ValueError, AttributeError):
                    pass
            
            # Get destination info
            destination = PackageLocation(
                city=shipment.findtext('City'),
                state=shipment.findtext('State'),
                postal_code=shipment.findtext('Zip'),
                country="US"
            )
            
            # Get service type
            service_type = shipment.findtext('Service', 'OnTrac Ground')
            service_map = {'C': 'OnTrac Ground'}
            service_type = service_map.get(service_type, service_type)
            
            # Get weight
            weight = shipment.findtext('Weight')
            
            # Get reference numbers
            reference_numbers = []
            ref1 = shipment.findtext('Reference')
            ref2 = shipment.findtext('Reference2')
            if ref1:
                reference_numbers.append(ref1)
            if ref2:
                reference_numbers.append(ref2)
            
            return TrackingResult(
                tracking_number=tracking_number,
                carrier=self.carrier,
                status=status,
                events=events,
                origin=None,  # OnTrac tracking doesn't provide origin in response
                destination=destination,
                delivered_at=delivered_at,
                estimated_delivery=estimated_delivery,
                service_type=service_type,
                weight=weight,
                reference_numbers=reference_numbers,
                raw_data={"xml": xml_text}
            )
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse OnTrac XML response: {e}")
            raise TrackingError(f"Invalid XML response from OnTrac API: {e}")

    def _parse_xml_event(self, event_elem: ET.Element) -> Optional[TrackingEvent]:
        """
        Parse individual tracking event from XML.

        Args:
            event_elem: XML element containing event data

        Returns:
            Optional[TrackingEvent]: Parsed event or None if invalid
        """
        try:
            # Parse timestamp
            timestamp_str = event_elem.findtext('EventTime')
            if not timestamp_str:
                return None

            # OnTrac timestamps are in format: 2022-04-06T14:53:21.45
            timestamp = datetime.fromisoformat(timestamp_str.rstrip('Z'))

            # Parse location
            location = None
            city = event_elem.findtext('City')
            state = event_elem.findtext('State')
            zip_code = event_elem.findtext('Zip')
            
            if city or state or zip_code:
                location = PackageLocation(
                    city=city,
                    state=state,
                    country="US",
                    postal_code=zip_code
                )

            # Get description and status
            description = event_elem.findtext('Description', '')
            status_code = event_elem.findtext('Status', '')
            
            return TrackingEvent(
                timestamp=timestamp,
                description=description,
                location=location,
                status_code=status_code
            )

        except Exception as e:
            logger.warning(f"Failed to parse OnTrac event: {e}")
            return None

    def _parse_location(self, location_data: dict) -> Optional[PackageLocation]:
        """
        Parse location information.

        Args:
            location_data: Raw location data

        Returns:
            Optional[PackageLocation]: Parsed location or None
        """
        if not location_data:
            return None

        return PackageLocation(
            city=location_data.get("city"),
            state=location_data.get("state", location_data.get("stateProvince")),
            country=location_data.get("country", "US"),
            postal_code=location_data.get("postalCode", location_data.get("zip"))
        )

    def _determine_status_from_events(self, events: List[TrackingEvent]) -> TrackingStatus:
        """
        Determine tracking status from events.

        Args:
            events: List of tracking events

        Returns:
            TrackingStatus: Current package status
        """
        if not events:
            return TrackingStatus.UNKNOWN

        # Check latest event status code according to OnTrac status codes
        latest_event = events[0]
        status_code = latest_event.status_code.upper() if latest_event.status_code else ""
        description = latest_event.description.upper() if latest_event.description else ""

        # OnTrac status codes from documentation
        delivered_codes = ["CL", "DW", "OK", "DN"]  # Delivered status codes
        out_for_delivery_codes = ["OD"]  # Out for delivery
        exception_codes = ["CR", "DC", "DR", "UD", "UM", "RS"]  # Exception/return codes
        in_transit_codes = ["OS", "PS", "RD", "PU"]  # In transit codes
        label_created_codes = ["XX", "OE"]  # Order created/info transmitted
        
        if status_code in delivered_codes or "DELIVERED" in description:
            return TrackingStatus.DELIVERED
        elif status_code in out_for_delivery_codes or "OUT FOR DELIVERY" in description:
            return TrackingStatus.OUT_FOR_DELIVERY
        elif status_code in exception_codes or any(word in description for word in ["EXCEPTION", "RETURN", "REFUSED", "DAMAGE"]):
            return TrackingStatus.EXCEPTION
        elif status_code in label_created_codes or "DATA ENTRY" in description:
            return TrackingStatus.LABEL_CREATED
        elif status_code in in_transit_codes:
            return TrackingStatus.IN_TRANSIT
        else:
            return TrackingStatus.IN_TRANSIT  # Default to in transit
