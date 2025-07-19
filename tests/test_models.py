"""
Tests for core data models.

Tests Pydantic model validation, serialization, and custom exceptions.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models import (
    AuthenticationError,
    AuthToken,
    InvalidTrackingNumberError,
    RateLimitError,
    TrackingCarrier,
    TrackingError,
    TrackingEvent,
    TrackingRequest,
    TrackingResult,
    TrackingStatus,
)


class TestTrackingCarrier:
    """Test TrackingCarrier enum."""

    def test_valid_carriers(self):
        """Test valid carrier values."""
        assert TrackingCarrier.FEDEX == "fedex"
        assert TrackingCarrier.UPS == "ups"

    def test_carrier_string_representation(self):
        """Test carrier string representation."""
        assert TrackingCarrier.FEDEX.value == "fedex"
        assert TrackingCarrier.UPS.value == "ups"


class TestTrackingStatus:
    """Test TrackingStatus enum."""

    def test_valid_statuses(self):
        """Test valid status values."""
        assert TrackingStatus.IN_TRANSIT == "in_transit"
        assert TrackingStatus.OUT_FOR_DELIVERY == "out_for_delivery"
        assert TrackingStatus.DELIVERED == "delivered"
        assert TrackingStatus.EXCEPTION == "exception"
        assert TrackingStatus.PENDING == "pending"
        assert TrackingStatus.NOT_FOUND == "not_found"


class TestTrackingEvent:
    """Test TrackingEvent model."""

    def test_valid_event(self):
        """Test creating valid tracking event."""
        timestamp = datetime.now()
        event = TrackingEvent(
            timestamp=timestamp,
            status="in_transit",
            location="Memphis, TN",
            description="Package scanned at facility"
        )

        assert event.timestamp == timestamp
        assert event.status == "in_transit"
        assert event.location == "Memphis, TN"
        assert event.description == "Package scanned at facility"

    def test_event_without_location(self):
        """Test event without location (optional field)."""
        event = TrackingEvent(
            timestamp=datetime.now(),
            status="pending",
            description="Order processed"
        )

        assert event.location is None
        assert event.description == "Order processed"

    def test_event_validation_error(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError):
            TrackingEvent(status="invalid")  # Missing timestamp and description


class TestTrackingResult:
    """Test TrackingResult model."""

    def test_valid_result(self):
        """Test creating valid tracking result."""
        result = TrackingResult(
            tracking_number="123456789012",
            carrier=TrackingCarrier.FEDEX,
            status=TrackingStatus.DELIVERED
        )

        assert result.tracking_number == "123456789012"
        assert result.carrier == TrackingCarrier.FEDEX
        assert result.status == TrackingStatus.DELIVERED
        assert result.events == []  # Default empty list
        assert result.error_message is None

    def test_result_with_events(self):
        """Test result with tracking events."""
        events = [
            TrackingEvent(
                timestamp=datetime.now(),
                status="delivered",
                description="Package delivered"
            )
        ]

        result = TrackingResult(
            tracking_number="123456789012",
            carrier=TrackingCarrier.FEDEX,
            status=TrackingStatus.DELIVERED,
            events=events
        )

        assert len(result.events) == 1
        assert result.events[0].description == "Package delivered"

    def test_error_result(self):
        """Test result with error message."""
        result = TrackingResult(
            tracking_number="invalid",
            carrier=TrackingCarrier.UPS,
            status=TrackingStatus.EXCEPTION,
            error_message="Invalid tracking number"
        )

        assert result.error_message == "Invalid tracking number"
        assert result.status == TrackingStatus.EXCEPTION


class TestTrackingRequest:
    """Test TrackingRequest model."""

    def test_valid_request(self):
        """Test creating valid tracking request."""
        request = TrackingRequest(
            tracking_number="123456789012",
            carrier=TrackingCarrier.FEDEX
        )

        assert request.tracking_number == "123456789012"
        assert request.carrier == TrackingCarrier.FEDEX

    def test_request_validation(self):
        """Test request validation for tracking number length."""
        # Valid tracking number
        request = TrackingRequest(
            tracking_number="123456789012",
            carrier=TrackingCarrier.FEDEX
        )
        assert request.tracking_number == "123456789012"

        # Empty tracking number should fail
        with pytest.raises(ValidationError):
            TrackingRequest(
                tracking_number="",
                carrier=TrackingCarrier.FEDEX
            )

        # Too long tracking number should fail
        with pytest.raises(ValidationError):
            TrackingRequest(
                tracking_number="a" * 51,  # Over 50 character limit
                carrier=TrackingCarrier.FEDEX
            )


class TestAuthToken:
    """Test AuthToken model."""

    def test_valid_token(self):
        """Test creating valid auth token."""
        expires_at = datetime.now()
        token = AuthToken(
            access_token="sample_token",
            expires_in=3600,
            expires_at=expires_at
        )

        assert token.access_token == "sample_token"
        assert token.token_type == "Bearer"  # Default value
        assert token.expires_in == 3600
        assert token.expires_at == expires_at
        assert token.refresh_token is None  # Optional field

    def test_token_with_refresh(self):
        """Test token with refresh token."""
        token = AuthToken(
            access_token="access_token",
            expires_in=3600,
            expires_at=datetime.now(),
            refresh_token="refresh_token"
        )

        assert token.refresh_token == "refresh_token"


class TestTrackingExceptions:
    """Test custom tracking exceptions."""

    def test_tracking_error(self):
        """Test basic TrackingError."""
        error = TrackingError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.carrier is None
        assert error.tracking_number is None

    def test_tracking_error_with_context(self):
        """Test TrackingError with carrier and tracking number."""
        error = TrackingError(
            "API error",
            carrier=TrackingCarrier.FEDEX,
            tracking_number="123456789012"
        )

        assert error.message == "API error"
        assert error.carrier == TrackingCarrier.FEDEX
        assert error.tracking_number == "123456789012"

    def test_authentication_error(self):
        """Test AuthenticationError subclass."""
        error = AuthenticationError("Auth failed")
        assert isinstance(error, TrackingError)
        assert str(error) == "Auth failed"

    def test_rate_limit_error(self):
        """Test RateLimitError subclass."""
        error = RateLimitError("Rate limited")
        assert isinstance(error, TrackingError)
        assert str(error) == "Rate limited"

    def test_invalid_tracking_number_error(self):
        """Test InvalidTrackingNumberError subclass."""
        error = InvalidTrackingNumberError("Invalid format")
        assert isinstance(error, TrackingError)
        assert str(error) == "Invalid format"
