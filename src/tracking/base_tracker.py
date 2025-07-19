"""
Base tracking interface for all shipping carriers.

Defines the common interface and error handling patterns for package tracking services.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

import httpx

from ..config import settings
from ..models import RateLimitError, TrackingCarrier, TrackingError, TrackingResult

logger = logging.getLogger(__name__)


class BaseTracker(ABC):
    """
    Abstract base class for package tracking services.

    Defines the common interface and provides shared functionality for all carriers.
    """

    def __init__(self, carrier: TrackingCarrier):
        """
        Initialize base tracker.

        Args:
            carrier: The shipping carrier this tracker handles
        """
        self.carrier = carrier
        self.timeout = int(settings.request_timeout)

    @abstractmethod
    async def track_package(self, tracking_number: str) -> TrackingResult:
        """
        Track a single package by tracking number.

        Args:
            tracking_number: Package tracking number

        Returns:
            TrackingResult: Structured tracking information

        Raises:
            TrackingError: If tracking fails
        """
        pass

    @abstractmethod
    async def track_multiple_packages(self, tracking_numbers: List[str]) -> List[TrackingResult]:
        """
        Track multiple packages in a single request.

        Args:
            tracking_numbers: List of tracking numbers

        Returns:
            List[TrackingResult]: List of tracking results

        Raises:
            TrackingError: If tracking fails
        """
        pass

    @abstractmethod
    def validate_tracking_number(self, tracking_number: str) -> bool:
        """
        Validate tracking number format for this carrier.

        Args:
            tracking_number: Tracking number to validate

        Returns:
            bool: True if format is valid
        """
        pass

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: dict,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        max_retries: int = 3
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            data: Request body data
            params: URL parameters
            max_retries: Maximum retry attempts

        Returns:
            httpx.Response: HTTP response

        Raises:
            TrackingError: If request fails after retries
            RateLimitError: If rate limited
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")

                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=data,
                        params=params
                    )

                    # Reason: Handle rate limiting with exponential backoff
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited by {self.carrier.value}. Retrying after {retry_after}s")

                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise RateLimitError(
                                f"Rate limited by {self.carrier.value} API",
                                carrier=self.carrier
                            )

                    # Reason: Handle server errors with exponential backoff
                    if 500 <= response.status_code < 600:
                        wait_time = (2 ** attempt) + 1  # Exponential backoff
                        logger.warning(
                            f"Server error {response.status_code} from {self.carrier.value}. "
                            f"Retrying in {wait_time}s"
                        )

                        if attempt < max_retries - 1:
                            await asyncio.sleep(wait_time)
                            continue

                    return response

            except httpx.TimeoutException as e:
                last_exception = e
                wait_time = (2 ** attempt) + 1
                logger.warning(f"Request timeout to {self.carrier.value}. Retrying in {wait_time}s")

                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                    continue

            except httpx.RequestError as e:
                last_exception = e
                logger.error(f"Request error to {self.carrier.value}: {e}")
                break  # Don't retry on client errors

        # Reason: If we get here, all retries failed
        if last_exception:
            raise TrackingError(
                f"Request to {self.carrier.value} failed after {max_retries} attempts: {last_exception}",
                carrier=self.carrier
            )
        else:
            raise TrackingError(
                f"Request to {self.carrier.value} failed after {max_retries} attempts",
                carrier=self.carrier
            )

    def _create_error_result(self, tracking_number: str, error_message: str) -> TrackingResult:
        """
        Create a TrackingResult for error cases.

        Args:
            tracking_number: The tracking number that failed
            error_message: Error description

        Returns:
            TrackingResult: Error result
        """
        return TrackingResult(
            tracking_number=tracking_number,
            carrier=self.carrier,
            status="exception",
            error_message=error_message
        )

    def _validate_tracking_numbers_batch(self, tracking_numbers: List[str]) -> None:
        """
        Validate a batch of tracking numbers.

        Args:
            tracking_numbers: List of tracking numbers to validate

        Raises:
            TrackingError: If validation fails
        """
        if not tracking_numbers:
            raise TrackingError("No tracking numbers provided", carrier=self.carrier)

        if len(tracking_numbers) > self._get_max_batch_size():
            raise TrackingError(
                f"Too many tracking numbers. Maximum allowed: {self._get_max_batch_size()}",
                carrier=self.carrier
            )

        for tracking_number in tracking_numbers:
            if not self.validate_tracking_number(tracking_number):
                raise TrackingError(
                    f"Invalid tracking number format: {tracking_number}",
                    carrier=self.carrier,
                    tracking_number=tracking_number
                )

    @abstractmethod
    def _get_max_batch_size(self) -> int:
        """
        Get maximum batch size for this carrier.

        Returns:
            int: Maximum number of tracking numbers per request
        """
        pass
