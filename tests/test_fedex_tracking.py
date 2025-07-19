"""
Tests for FedEx tracking functionality.

Tests tracking number validation, API interaction, and response parsing.
"""



import httpx
import pytest
import respx

from src.auth.fedex_auth import FedExAuth
from src.models import TrackingCarrier, TrackingError, TrackingStatus
from src.tracking.fedex_tracker import FedExTracker


class TestFedExTracker:
    """Test FedEx tracking functionality."""

    @pytest.fixture
    def mock_tracker(self):
        """Create tracker with mock auth."""
        auth = FedExAuth("test_client_id", "test_client_secret", sandbox=True)
        return FedExTracker(auth=auth)

    def test_init(self, mock_tracker):
        """Test tracker initialization."""
        tracker = mock_tracker
        assert tracker.carrier == TrackingCarrier.FEDEX
        assert tracker.auth is not None
        assert "track/v1/trackingnumbers" in tracker.api_url

    def test_init_with_auth(self):
        """Test tracker initialization with custom auth."""
        from src.auth.fedex_auth import FedExAuth
        auth = FedExAuth("test_id", "test_secret", sandbox=True)
        tracker = FedExTracker(auth=auth)
        assert tracker.auth == auth

    def test_validate_tracking_number_valid(self, mock_tracker):
        """Test validation of valid tracking numbers."""
        tracker = mock_tracker

        # Test various valid FedEx formats
        valid_numbers = [
            "123456789012",        # 12 digit
            "12345678901234",      # 14 digit
            "123456789012345",     # 15 digit
            "1234567890123456789012",  # 22 digit
        ]

        for number in valid_numbers:
            assert tracker.validate_tracking_number(number) is True

    def test_validate_tracking_number_invalid(self, mock_tracker):
        """Test validation of invalid tracking numbers."""
        tracker = mock_tracker

        # Test invalid formats
        invalid_numbers = [
            "",                    # Empty
            "123",                 # Too short
            "123456789",           # Wrong length
            "12345678901",         # Wrong length
            "abc123def456",        # Contains letters
            None,                  # None type
        ]

        for number in invalid_numbers:
            assert tracker.validate_tracking_number(number) is False

    def test_get_max_batch_size(self, mock_tracker):
        """Test maximum batch size."""
        tracker = mock_tracker
        assert tracker._get_max_batch_size() == 30

    def test_map_fedex_status(self, mock_tracker):
        """Test status mapping from FedEx to standard status."""
        tracker = mock_tracker

        # Test delivered status
        assert tracker._map_fedex_status("DL", "Delivered") == TrackingStatus.DELIVERED

        # Test out for delivery
        assert tracker._map_fedex_status("OD", "Out for delivery") == TrackingStatus.OUT_FOR_DELIVERY

        # Test in transit
        assert tracker._map_fedex_status("IT", "In transit") == TrackingStatus.IN_TRANSIT
        assert tracker._map_fedex_status("DP", "Departed facility") == TrackingStatus.IN_TRANSIT

        # Test exception
        assert tracker._map_fedex_status("EX", "Weather delay") == TrackingStatus.EXCEPTION
        assert tracker._map_fedex_status("DE", "Delivery exception") == TrackingStatus.EXCEPTION

        # Test pending
        assert tracker._map_fedex_status("PU", "Pending") == TrackingStatus.PENDING
        assert tracker._map_fedex_status("", "") == TrackingStatus.PENDING

        # Test default
        assert tracker._map_fedex_status("UK", "Unknown status") == TrackingStatus.IN_TRANSIT

    def test_parse_tracking_events(self, mock_tracker):
        """Test parsing of tracking events."""
        tracker = mock_tracker

        sample_events = [
            {
                "date": "2024-01-15T10:30:00Z",
                "eventDescription": "Package picked up",
                "eventType": "PU",
                "scanLocation": {
                    "city": "Memphis",
                    "stateOrProvinceCode": "TN",
                    "countryCode": "US"
                }
            },
            {
                "date": "2024-01-16T14:45:00Z",
                "eventDescription": "In transit",
                "eventType": "IT",
                "scanLocation": {
                    "city": "Atlanta",
                    "stateOrProvinceCode": "GA",
                    "countryCode": "US"
                }
            }
        ]

        events = tracker._parse_tracking_events(sample_events)

        assert len(events) == 2
        # Events should be sorted by timestamp (most recent first)
        assert events[0].description == "In transit"
        assert events[0].location == "Atlanta, GA US"
        assert events[1].description == "Package picked up"
        assert events[1].location == "Memphis, TN US"

    def test_parse_tracking_events_malformed(self, mock_tracker):
        """Test parsing of malformed tracking events."""
        tracker = mock_tracker

        malformed_events = [
            {
                "date": "invalid-date",
                "eventDescription": "Valid event",
                "eventType": "PU"
            },
            {
                # Missing required fields
                "eventType": "IT"
            },
            {
                "date": "2024-01-15T10:30:00Z",
                "eventDescription": "Valid event 2",
                "eventType": "DL"
            }
        ]

        events = tracker._parse_tracking_events(malformed_events)

        # Should only get the valid event
        assert len(events) == 1
        assert events[0].description == "Valid event 2"

    @respx.mock
    @pytest.mark.asyncio
    async def test_track_package_success(self, mock_tracker):
        """Test successful package tracking."""
        # Mock authentication
        respx.post("https://apis-sandbox.fedex.com/oauth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_token",
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            )
        )

        # Mock tracking response
        respx.post("https://apis-sandbox.fedex.com/track/v1/trackingnumbers").mock(
            return_value=httpx.Response(
                200,
                json={
                    "output": {
                        "completeTrackResults": [
                            {
                                "trackingNumber": "123456789012",
                                "trackResults": [
                                    {
                                        "latestStatusDetail": {
                                            "code": "DL",
                                            "description": "Delivered"
                                        },
                                        "deliveryDetails": {
                                            "deliveryLocation": "Front door"
                                        },
                                        "serviceDetail": {
                                            "description": "FedEx Ground"
                                        },
                                        "scanEvents": [
                                            {
                                                "date": "2024-01-15T10:30:00Z",
                                                "eventDescription": "Delivered",
                                                "eventType": "DL"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                }
            )
        )

        tracker = mock_tracker
        result = await tracker.track_package("123456789012")

        assert result.tracking_number == "123456789012"
        assert result.carrier == TrackingCarrier.FEDEX
        assert result.status == TrackingStatus.DELIVERED
        assert result.delivery_address == "Front door"
        assert result.service_type == "FedEx Ground"
        assert len(result.events) == 1
        assert result.events[0].description == "Delivered"

    @respx.mock
    @pytest.mark.asyncio
    async def test_track_package_not_found(self, mock_tracker):
        """Test tracking package not found."""
        # Mock authentication
        respx.post("https://apis-sandbox.fedex.com/oauth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_token",
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            )
        )

        # Mock empty tracking response
        respx.post("https://apis-sandbox.fedex.com/track/v1/trackingnumbers").mock(
            return_value=httpx.Response(
                200,
                json={
                    "output": {
                        "completeTrackResults": []
                    }
                }
            )
        )

        tracker = mock_tracker
        result = await tracker.track_package("999999999999")

        assert result.tracking_number == "999999999999"
        assert result.carrier == TrackingCarrier.FEDEX
        assert result.error_message == "Tracking number not found in FedEx response"

    @respx.mock
    @pytest.mark.asyncio
    async def test_track_package_auth_error(self, mock_tracker):
        """Test tracking with authentication error."""
        # Mock authentication failure
        respx.post("https://apis-sandbox.fedex.com/oauth/token").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )

        tracker = mock_tracker

        with pytest.raises(TrackingError):
            await tracker.track_package("123456789012")

    @respx.mock
    @pytest.mark.asyncio
    async def test_track_multiple_packages(self, mock_tracker):
        """Test tracking multiple packages."""
        # Mock authentication
        respx.post("https://apis-sandbox.fedex.com/oauth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_token",
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            )
        )

        # Mock tracking response for multiple packages
        respx.post("https://apis-sandbox.fedex.com/track/v1/trackingnumbers").mock(
            return_value=httpx.Response(
                200,
                json={
                    "output": {
                        "completeTrackResults": [
                            {
                                "trackingNumber": "123456789012",
                                "trackResults": [
                                    {
                                        "latestStatusDetail": {
                                            "code": "DL",
                                            "description": "Delivered"
                                        }
                                    }
                                ]
                            },
                            {
                                "trackingNumber": "123456789013",
                                "trackResults": [
                                    {
                                        "latestStatusDetail": {
                                            "code": "IT",
                                            "description": "In transit"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                }
            )
        )

        tracker = mock_tracker
        results = await tracker.track_multiple_packages(["123456789012", "123456789013"])

        assert len(results) == 2
        assert results[0].tracking_number == "123456789012"
        assert results[0].status == TrackingStatus.DELIVERED
        assert results[1].tracking_number == "123456789013"
        assert results[1].status == TrackingStatus.IN_TRANSIT

    @pytest.mark.asyncio
    async def test_track_package_invalid_number(self, mock_tracker):
        """Test tracking with invalid tracking number."""
        tracker = mock_tracker

        with pytest.raises(TrackingError):
            await tracker.track_multiple_packages([""])  # Invalid empty number
