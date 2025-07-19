"""
Unit tests for DHL tracking module.

Tests package tracking functionality for DHL eCommerce API.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.models import TrackingCarrier, TrackingStatus, TrackingError, InvalidTrackingNumberError
from src.tracking.dhl_tracker import DHLTracker


class TestDHLTracker:
    """Test cases for DHL tracking functionality."""
    
    def test_init(self):
        """Test tracker initialization."""
        tracker = DHLTracker()
        
        assert tracker.carrier == TrackingCarrier.DHL
        assert tracker.auth is not None
        assert "tracking/v4/package/open" in tracker.base_api_url
    
    def test_validate_tracking_number_valid(self):
        """Test tracking number validation with valid numbers."""
        tracker = DHLTracker()
        
        # Test various valid DHL tracking number formats
        valid_numbers = [
            "GM60511234500000001",  # GM prefix format
            "3387191106122423",     # Numeric format
            "420300249374869903500011805718",  # USPS format
            "1234567890123456",     # Generic numeric
            "AB123456789US",        # DHL Express format
        ]
        
        for number in valid_numbers:
            assert tracker.validate_tracking_number(number) is True
    
    def test_validate_tracking_number_invalid(self):
        """Test tracking number validation with invalid numbers."""
        tracker = DHLTracker()
        
        # Test invalid tracking numbers
        invalid_numbers = [
            "",                    # Empty string
            None,                  # None value
            "123",                 # Too short
            "a" * 35,              # Too long
            "invalid-format",      # Invalid format
        ]
        
        for number in invalid_numbers:
            assert tracker.validate_tracking_number(number) is False
    
    def test_get_max_batch_size(self):
        """Test maximum batch size."""
        tracker = DHLTracker()
        assert tracker._get_max_batch_size() == 10
    
    @pytest.mark.asyncio
    async def test_track_package_invalid_number(self):
        """Test tracking with invalid tracking number."""
        tracker = DHLTracker()
        
        with pytest.raises(InvalidTrackingNumberError):
            await tracker.track_package("invalid")
    
    @pytest.mark.asyncio
    async def test_track_package_success(self):
        """Test successful package tracking."""
        tracker = DHLTracker()
        
        # Mock response data
        mock_response_data = {
            "packages": [
                {
                    "package": {
                        "trackingId": "GM60511234500000001",
                        "expectedDelivery": "2024-01-15",
                        "productName": "DHL eCommerce Ground",
                        "weight": {
                            "value": 2.5,
                            "unitOfMeasure": "lb"
                        }
                    },
                    "recipient": {
                        "city": "New York",
                        "state": "NY",
                        "postalCode": "10001",
                        "country": "US"
                    },
                    "events": [
                        {
                            "date": "2024-01-10",
                            "time": "14:30:00",
                            "location": "New York, NY, US",
                            "primaryEventDescription": "PROCESSED",
                            "secondaryEventDescription": "Package processed at facility"
                        }
                    ]
                }
            ]
        }
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch.object(tracker, '_make_request', return_value=mock_response):
            result = await tracker.track_package("GM60511234500000001")
            
            assert result.tracking_number == "GM60511234500000001"
            assert result.carrier == TrackingCarrier.DHL
            assert result.status == TrackingStatus.IN_TRANSIT
            assert result.service_type == "DHL eCommerce Ground"
            assert result.weight == "2.5 lb"
            assert result.delivery_address == "New York, NY, 10001, US"
            assert len(result.events) == 1
            assert result.events[0].description == "Package processed at facility"
    
    @pytest.mark.asyncio
    async def test_track_package_not_found(self):
        """Test tracking package not found."""
        tracker = DHLTracker()
        
        # Mock HTTP response with 404
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch.object(tracker, '_make_request', return_value=mock_response):
            result = await tracker.track_package("GM60511234500000001")
            
            assert result.tracking_number == "GM60511234500000001"
            assert result.carrier == TrackingCarrier.DHL
            assert result.status == TrackingStatus.NOT_FOUND
            assert result.error_message == "Tracking number not found"
    
    @pytest.mark.asyncio
    async def test_track_package_auth_retry(self):
        """Test tracking with authentication retry."""
        tracker = DHLTracker()
        
        # Mock response data for successful retry
        mock_response_data = {
            "packages": [
                {
                    "package": {
                        "trackingId": "GM60511234500000001",
                        "expectedDelivery": "2024-01-15"
                    },
                    "recipient": {},
                    "events": []
                }
            ]
        }
        
        # Mock first 401 response, then successful response
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = mock_response_data
        
        with patch.object(tracker, '_make_request', side_effect=[mock_response_401, mock_response_200]):
            with patch.object(tracker.auth, 'clear_token') as mock_clear:
                result = await tracker.track_package("GM60511234500000001")
                
                assert result.tracking_number == "GM60511234500000001"
                assert result.carrier == TrackingCarrier.DHL
                mock_clear.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_multiple_packages_success(self):
        """Test successful multiple package tracking."""
        tracker = DHLTracker()
        
        tracking_numbers = ["GM60511234500000001", "GM60511234500000002"]
        
        # Mock response data
        mock_response_data = {
            "packages": [
                {
                    "package": {
                        "trackingId": "GM60511234500000001",
                        "expectedDelivery": "2024-01-15"
                    },
                    "recipient": {},
                    "events": []
                },
                {
                    "package": {
                        "trackingId": "GM60511234500000002",
                        "expectedDelivery": "2024-01-16"
                    },
                    "recipient": {},
                    "events": []
                }
            ]
        }
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch.object(tracker, '_make_request', return_value=mock_response):
            results = await tracker.track_multiple_packages(tracking_numbers)
            
            assert len(results) == 2
            assert results[0].tracking_number == "GM60511234500000001"
            assert results[1].tracking_number == "GM60511234500000002"
            assert all(result.carrier == TrackingCarrier.DHL for result in results)
    
    @pytest.mark.asyncio
    async def test_track_multiple_packages_missing_response(self):
        """Test multiple package tracking with missing packages in response."""
        tracker = DHLTracker()
        
        tracking_numbers = ["GM60511234500000001", "GM60511234500000002"]
        
        # Mock response data with only one package
        mock_response_data = {
            "packages": [
                {
                    "package": {
                        "trackingId": "GM60511234500000001",
                        "expectedDelivery": "2024-01-15"
                    },
                    "recipient": {},
                    "events": []
                }
            ]
        }
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch.object(tracker, '_make_request', return_value=mock_response):
            results = await tracker.track_multiple_packages(tracking_numbers)
            
            assert len(results) == 2
            assert results[0].tracking_number == "GM60511234500000001"
            assert results[1].tracking_number == "GM60511234500000002"
            assert results[1].error_message == "Package not found in response"
    
    def test_determine_status_from_events(self):
        """Test status determination from events."""
        tracker = DHLTracker()
        
        # Test delivered status
        from src.models import TrackingEvent
        delivered_event = TrackingEvent(
            timestamp=datetime.now(),
            status="DELIVERED",
            location="New York, NY",
            description="Package delivered"
        )
        
        status = tracker._determine_status_from_events([delivered_event])
        assert status == TrackingStatus.DELIVERED
        
        # Test out for delivery status
        out_for_delivery_event = TrackingEvent(
            timestamp=datetime.now(),
            status="OUT_FOR_DELIVERY",
            location="New York, NY",
            description="Out for delivery"
        )
        
        status = tracker._determine_status_from_events([out_for_delivery_event])
        assert status == TrackingStatus.OUT_FOR_DELIVERY
        
        # Test in transit status
        in_transit_event = TrackingEvent(
            timestamp=datetime.now(),
            status="PROCESSED",
            location="New York, NY",
            description="Package processed at facility"
        )
        
        status = tracker._determine_status_from_events([in_transit_event])
        assert status == TrackingStatus.IN_TRANSIT
        
        # Test exception status
        exception_event = TrackingEvent(
            timestamp=datetime.now(),
            status="EXCEPTION",
            location="New York, NY",
            description="Delivery exception occurred"
        )
        
        status = tracker._determine_status_from_events([exception_event])
        assert status == TrackingStatus.EXCEPTION
    
    def test_format_delivery_address(self):
        """Test delivery address formatting."""
        tracker = DHLTracker()
        
        # Test complete address
        recipient = {
            "city": "New York",
            "state": "NY",
            "postalCode": "10001",
            "country": "US"
        }
        
        address = tracker._format_delivery_address(recipient)
        assert address == "New York, NY, 10001, US"
        
        # Test partial address
        partial_recipient = {
            "city": "New York",
            "country": "US"
        }
        
        address = tracker._format_delivery_address(partial_recipient)
        assert address == "New York, US"
        
        # Test empty recipient
        address = tracker._format_delivery_address({})
        assert address is None
        
        # Test None recipient
        address = tracker._format_delivery_address(None)
        assert address is None