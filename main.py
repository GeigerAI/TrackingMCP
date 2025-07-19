"""
CLI entry point for testing the package tracking MCP server.

Provides command-line interface for testing tracking functionality
without requiring an MCP client.
"""

import asyncio
import argparse
import logging
import sys
from typing import List

from src.config import settings
from src.tracking.fedex_tracker import FedExTracker
from src.tracking.ups_tracker import UPSTracker
from src.models import TrackingCarrier, TrackingResult

# Reason: Configure logging for CLI usage
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_fedex_tracking(tracking_numbers: List[str]) -> None:
    """
    Test FedEx tracking functionality.
    
    Args:
        tracking_numbers: List of FedEx tracking numbers to test
    """
    print("\\n=== Testing FedEx Tracking ===")
    
    try:
        tracker = FedExTracker()
        
        if len(tracking_numbers) == 1:
            result = await tracker.track_package(tracking_numbers[0])
            print_tracking_result(result)
        else:
            results = await tracker.track_multiple_packages(tracking_numbers)
            for result in results:
                print_tracking_result(result)
                print("-" * 50)
                
    except Exception as e:
        print(f"FedEx tracking test failed: {e}")


async def test_ups_tracking(tracking_numbers: List[str]) -> None:
    """
    Test UPS tracking functionality.
    
    Args:
        tracking_numbers: List of UPS tracking numbers to test
    """
    print("\\n=== Testing UPS Tracking ===")
    
    try:
        tracker = UPSTracker()
        
        if len(tracking_numbers) == 1:
            result = await tracker.track_package(tracking_numbers[0])
            print_tracking_result(result)
        else:
            results = await tracker.track_multiple_packages(tracking_numbers)
            for result in results:
                print_tracking_result(result)
                print("-" * 50)
                
    except Exception as e:
        print(f"UPS tracking test failed: {e}")


def print_tracking_result(result: TrackingResult) -> None:
    """
    Print tracking result in a formatted way.
    
    Args:
        result: TrackingResult to display
    """
    print(f"Tracking Number: {result.tracking_number}")
    print(f"Carrier: {result.carrier.value.upper()}")
    print(f"Status: {result.status.value}")
    
    if result.error_message:
        print(f"Error: {result.error_message}")
        return
    
    if result.estimated_delivery:
        print(f"Estimated Delivery: {result.estimated_delivery}")
    
    if result.delivery_address:
        print(f"Delivery Address: {result.delivery_address}")
    
    if result.service_type:
        print(f"Service Type: {result.service_type}")
    
    if result.weight:
        print(f"Weight: {result.weight}")
    
    if result.events:
        print(f"\\nTracking Events ({len(result.events)} total):")
        for i, event in enumerate(result.events[:5]):  # Show first 5 events
            print(f"  {i+1}. {event.timestamp} - {event.description}")
            if event.location:
                print(f"     Location: {event.location}")
        
        if len(result.events) > 5:
            print(f"     ... and {len(result.events) - 5} more events")


def validate_tracking_numbers(tracking_numbers: List[str], carrier: str) -> bool:
    """
    Validate tracking numbers for the specified carrier.
    
    Args:
        tracking_numbers: List of tracking numbers to validate
        carrier: Carrier name (fedex or ups)
        
    Returns:
        bool: True if all numbers are valid
    """
    print(f"\\n=== Validating {carrier.upper()} Tracking Numbers ===")
    
    if carrier.lower() == "fedex":
        tracker = FedExTracker()
    elif carrier.lower() == "ups":
        tracker = UPSTracker()
    else:
        print(f"Unsupported carrier: {carrier}")
        return False
    
    all_valid = True
    for tracking_number in tracking_numbers:
        is_valid = tracker.validate_tracking_number(tracking_number)
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"  {tracking_number}: {status}")
        if not is_valid:
            all_valid = False
    
    return all_valid


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Test package tracking functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --fedex 123456789012
  python main.py --ups 1Z12345E0123456789
  python main.py --fedex 123456789012 987654321098
  python main.py --validate --fedex 123456789012
  python main.py --test-mode
        """
    )
    
    parser.add_argument(
        "--fedex", 
        nargs="+", 
        help="FedEx tracking number(s) to track"
    )
    parser.add_argument(
        "--ups", 
        nargs="+", 
        help="UPS tracking number(s) to track"
    )
    parser.add_argument(
        "--validate", 
        action="store_true", 
        help="Only validate tracking numbers without tracking"
    )
    parser.add_argument(
        "--test-mode", 
        action="store_true", 
        help="Run in test mode with sample tracking numbers"
    )
    parser.add_argument(
        "--server", 
        action="store_true", 
        help="Start MCP server"
    )
    
    args = parser.parse_args()
    
    # Reason: Start MCP server if requested
    if args.server:
        from src.server import main as server_main
        server_main()
        return
    
    # Reason: Show configuration info
    print("=== Package Tracking CLI ===")
    print(f"FedEx Sandbox: {settings.fedex_sandbox}")
    print(f"UPS Sandbox: {settings.ups_sandbox}")
    print(f"Log Level: {settings.log_level}")
    
    try:
        # Reason: Validate credentials
        settings.validate_api_credentials()
        print("✓ API credentials configured")
    except ValueError as e:
        print(f"⚠ Warning: {e}")
        print("Some features may not work without proper credentials")
    
    # Reason: Test mode with sample tracking numbers
    if args.test_mode:
        print("\\n=== Running in Test Mode ===")
        # Note: These are example tracking numbers for testing format validation
        sample_fedex = ["123456789012", "12345678901234"]
        sample_ups = ["1Z12345E0123456789", "1Z12345E1234567890"]
        
        validate_tracking_numbers(sample_fedex, "fedex")
        validate_tracking_numbers(sample_ups, "ups")
        
        print("\\nNote: Use real tracking numbers with --fedex or --ups for actual tracking")
        return
    
    # Reason: Validate tracking numbers if requested
    if args.validate:
        if args.fedex:
            validate_tracking_numbers(args.fedex, "fedex")
        if args.ups:
            validate_tracking_numbers(args.ups, "ups")
        return
    
    # Reason: Track packages
    if args.fedex:
        await test_fedex_tracking(args.fedex)
    
    if args.ups:
        await test_ups_tracking(args.ups)
    
    if not args.fedex and not args.ups and not args.test_mode:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())