"""
Core data models for package tracking.

Provides Pydantic models for type safety and API consistency across all tracking operations.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TrackingCarrier(str, Enum):
    """Supported shipping carriers."""
    FEDEX = "fedex"
    UPS = "ups"
    DHL = "dhl"


class TrackingStatus(str, Enum):
    """Standard tracking status codes."""
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"
    PENDING = "pending"
    NOT_FOUND = "not_found"


class TrackingEvent(BaseModel):
    """
    Individual tracking event/scan.

    Represents a single update in the package's journey.
    """
    timestamp: datetime = Field(..., description="When the event occurred")
    status: str = Field(..., description="Status code or description")
    location: Optional[str] = Field(None, description="Location where event occurred")
    description: str = Field(..., description="Human-readable event description")


class TrackingResult(BaseModel):
    """
    Complete tracking information for a package.

    Main response model returned by tracking services.
    """
    tracking_number: str = Field(..., description="Package tracking number")
    carrier: TrackingCarrier = Field(..., description="Shipping carrier")
    status: TrackingStatus = Field(..., description="Current package status")
    estimated_delivery: Optional[datetime] = Field(
        None,
        description="Estimated delivery date and time"
    )
    events: List[TrackingEvent] = Field(
        default_factory=list,
        description="Chronological list of tracking events"
    )
    delivery_address: Optional[str] = Field(
        None,
        description="Delivery address if available"
    )
    service_type: Optional[str] = Field(
        None,
        description="Shipping service type (e.g., Ground, Express)"
    )
    weight: Optional[str] = Field(
        None,
        description="Package weight if available"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if tracking failed"
    )


class TrackingRequest(BaseModel):
    """
    Request to track a package.

    Input model for tracking operations.
    """
    tracking_number: str = Field(
        ...,
        description="Package tracking number",
        min_length=1,
        max_length=50
    )
    carrier: TrackingCarrier = Field(..., description="Shipping carrier")


class AuthToken(BaseModel):
    """
    OAuth authentication token.

    Used for managing API authentication across carriers.
    """
    access_token: str = Field(..., description="OAuth access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifetime in seconds")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    refresh_token: Optional[str] = Field(None, description="Refresh token if available")


class TrackingError(Exception):
    """
    Custom exception for tracking-related errors.

    Used for structured error handling across the application.
    """

    def __init__(self, message: str, carrier: Optional[TrackingCarrier] = None,
                 tracking_number: Optional[str] = None):
        """
        Initialize tracking error.

        Args:
            message: Error description
            carrier: Carrier where error occurred
            tracking_number: Tracking number if relevant
        """
        super().__init__(message)
        self.message = message
        self.carrier = carrier
        self.tracking_number = tracking_number


class AuthenticationError(TrackingError):
    """Authentication-specific error."""
    pass


class RateLimitError(TrackingError):
    """Rate limiting error."""
    pass


class InvalidTrackingNumberError(TrackingError):
    """Invalid tracking number error."""
    pass
