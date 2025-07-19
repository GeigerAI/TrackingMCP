# Package Tracking MCP Server

A Model Context Protocol (MCP) server that enables AI agents to track packages using FedEx, UPS, and DHL APIs. This server provides standardized tracking tools that can be consumed by any MCP-compatible AI agent or application.

## Quick Start

**To run the MCP server:**
```bash
python -m src
```

**To configure with Claude Desktop, add this to your MCP settings:**
```json
{
  "mcpServers": {
    "tracking-rate-mcp": {
      "command": "python",
      "args": ["-m", "src"],
      "cwd": "/path/to/TrackingRateMCP"
    }
  }
}
```

## Features

- 🚚 **FedEx Package Tracking**: Real-time tracking with OAuth2 authentication and auto-refresh
- 📦 **UPS Package Tracking**: Complete tracking support with OAuth2 authorization flow
- 🟡 **DHL Package Tracking**: DHL eCommerce tracking with OAuth2 client credentials flow
- 🤖 **MCP Protocol**: Standard interface for AI agents via Model Context Protocol
- ⚡ **Batch Processing**: Track up to 30 FedEx packages, 10 UPS packages, or 10 DHL packages at once
- 🔄 **Auto-Retry**: Automatic retry logic for rate limits and network failures
- 📝 **Rich Logging**: Comprehensive logging with configurable levels
- 🔒 **Secure Authentication**: OAuth2 token management with automatic refresh
- 🎯 **Type Safety**: Full Pydantic model validation and type hints

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd TrackingRateMCP
   ```

2. **Create and activate virtual environment** (as specified in CLAUDE.md):
   ```bash
   python -m venv venv_linux
   source venv_linux/bin/activate  # On Linux/macOS
   # or
   venv_linux\\Scripts\\activate     # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

## Environment Configuration

Create a `.env` file based on `.env.example` with the following settings:

### Required Environment Variables

```bash
# FedEx Configuration (Production)
FEDEX_CLIENT_ID=your_fedex_client_id
FEDEX_CLIENT_SECRET=your_fedex_client_secret
FEDEX_SANDBOX=false

# UPS Configuration  
UPS_CLIENT_ID=your_ups_client_id
UPS_CLIENT_SECRET=your_ups_client_secret
UPS_REDIRECT_URI=http://localhost:8000/callback
UPS_SANDBOX=false

# DHL Configuration
DHL_CLIENT_ID=your_dhl_client_id
DHL_CLIENT_SECRET=your_dhl_client_secret
DHL_SANDBOX=true

# MCP Configuration
MCP_TRANSPORT=stdio
LOG_LEVEL=INFO
```

### Optional Environment Variables

```bash
# Custom timeout settings
REQUEST_TIMEOUT=30
TOKEN_REFRESH_BUFFER=60
```

### API Key Setup

#### FedEx API Setup
1. Visit [FedEx Developer Portal](https://developer.fedex.com/)
2. Create an account and new project
3. Obtain your Client ID and Client Secret
4. Enable production access for live tracking

#### UPS API Setup
1. Visit [UPS Developer Portal](https://developer.ups.com/)
2. Create an account and new application
3. Obtain your Client ID and Client Secret
4. No additional OAuth setup required - uses client credentials flow

#### DHL API Setup
1. Visit [DHL Developer Portal](https://developer.dhl.com/)
2. Create an account and new application for DHL eCommerce
3. Obtain your Client ID and Client Secret
4. Uses OAuth2 client credentials flow

## Usage

### As MCP Server (Recommended)

Start the MCP server for use with AI agents:

```bash
python -m src
```

Configure with Claude Desktop by adding to your MCP configuration:

```json
{
  "mcpServers": {
    "tracking-rate-mcp": {
      "command": "python",
      "args": ["-m", "src"],
      "cwd": "/path/to/TrackingRateMCP"
    }
  }
}
```

### As HTTP Server (Alternative)

Start the HTTP server for REST API access:

```bash
python -m src.server
```

### Command Line Interface

The package includes a CLI for testing and development:

#### Basic Package Tracking

```bash
# Track a FedEx package
python main.py --fedex 123456789012

# Track a UPS package  
python main.py --ups 1Z12345E0123456789

# Track a DHL package
python main.py --dhl GM60511234500000001

# Track multiple packages
python main.py --fedex 123456789012 987654321098
python main.py --ups 1Z12345E0123456789 1Z12345E9876543210
python main.py --dhl GM60511234500000001 GM60511234500000002
```

#### Validation and Testing

```bash
# Validate tracking numbers without tracking
python main.py --validate --fedex 123456789012
python main.py --validate --ups 1Z12345E0123456789
python main.py --validate --dhl GM60511234500000001

# Run test mode with sample tracking numbers
python main.py --test-mode

# Start MCP server
python main.py --server
```

### Integration with AI Agents

#### Pydantic AI Agent Example

```python
from pydantic_ai import Agent
from mcp import Client

# Configure MCP client to use tracking server
mcp_client = Client("stdio", command=["python", "-m", "src.server"])

# Create agent with tracking capabilities
agent = Agent(
    "gpt-4",
    tools=[mcp_client],
    system_prompt="You can track packages using FedEx and UPS."
)

# Use the agent
result = await agent.run("Track FedEx package 123456789012")
```

#### Available MCP Tools

The server exposes the following tools to AI agents:

- `track_fedex_package(tracking_number: str)` - Track single FedEx package
- `track_multiple_fedex_packages(tracking_numbers: List[str])` - Track multiple FedEx packages
- `validate_fedex_tracking_number(tracking_number: str)` - Validate FedEx tracking number format
- `track_ups_package(tracking_number: str)` - Track single UPS package
- `track_multiple_ups_packages(tracking_numbers: List[str])` - Track multiple UPS packages  
- `validate_ups_tracking_number(tracking_number: str)` - Validate UPS tracking number format
- `track_dhl_package(tracking_number: str)` - Track single DHL package
- `track_multiple_dhl_packages(tracking_numbers: List[str])` - Track multiple DHL packages
- `validate_dhl_tracking_number(tracking_number: str)` - Validate DHL tracking number format

#### Available MCP Resources

- `tracking://server/info` - Server capabilities and configuration
- `tracking://carriers/{carrier}/capabilities` - Carrier-specific features

## Project Structure

```
TrackingRateMCP/
├── src/
│   ├── __init__.py                    # Package initialization
│   ├── server.py                      # Main MCP server implementation
│   ├── models.py                      # Pydantic models for tracking data
│   ├── config.py                      # Configuration and environment management
│   ├── auth/
│   │   ├── __init__.py               # Auth package init
│   │   ├── fedex_auth.py             # FedEx OAuth token management
│   │   ├── ups_auth.py               # UPS OAuth token management
│   │   └── dhl_auth.py               # DHL OAuth token management
│   ├── tracking/
│   │   ├── __init__.py               # Tracking package init
│   │   ├── fedex_tracker.py          # FedEx tracking implementation
│   │   ├── ups_tracker.py            # UPS tracking implementation
│   │   ├── dhl_tracker.py            # DHL tracking implementation
│   │   └── base_tracker.py           # Abstract tracking interface
│   └── tools/
│       ├── __init__.py               # Tools package init
│       ├── fedex_tools.py            # FedEx MCP tools
│       ├── ups_tools.py              # UPS MCP tools
│       └── dhl_tools.py              # DHL MCP tools
├── tests/                             # Comprehensive test suite
├── venv_linux/                       # Virtual environment
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project configuration
├── .env.example                       # Environment variables template
├── README.md                          # This documentation
└── main.py                           # CLI entry point for testing
```

## Testing

Run the comprehensive test suite:

```bash
# Activate virtual environment
source venv_linux/bin/activate

# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test modules
pytest tests/test_models.py -v
pytest tests/test_fedex_auth.py -v
pytest tests/test_fedex_tracking.py -v

# Run with detailed output
pytest tests/ -v -s
```

## Development

### Code Quality

The project includes code quality tools configured in `pyproject.toml`:

```bash
# Format and lint code
ruff check src/ tests/ --fix

# Type checking
mypy src/ tests/

# Run all quality checks
ruff check src/ tests/ --fix && mypy src/ tests/
```

### Adding New Carriers

To add support for additional carriers:

1. Create authentication module in `src/auth/`
2. Implement tracking service extending `BaseTracker`
3. Create MCP tools in `src/tools/`
4. Register tools in `src/server.py`
5. Add comprehensive tests

## API Documentation

### Tracking Result Model

```python
class TrackingResult(BaseModel):
    tracking_number: str              # Package tracking number
    carrier: TrackingCarrier          # Shipping carrier (fedex/ups)
    status: TrackingStatus           # Current package status
    estimated_delivery: Optional[datetime]  # Estimated delivery time
    events: List[TrackingEvent]      # Tracking history
    delivery_address: Optional[str]  # Delivery location
    service_type: Optional[str]      # Shipping service type
    weight: Optional[str]            # Package weight
    error_message: Optional[str]     # Error details if tracking failed
```

### Tracking Status Values

- `in_transit` - Package is in transit
- `out_for_delivery` - Package is out for delivery
- `delivered` - Package has been delivered
- `exception` - Delivery exception occurred
- `pending` - Package processing pending
- `not_found` - Tracking number not found

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Verify API credentials in `.env` file
   - Check if using correct sandbox/production endpoints
   - Ensure OAuth flow completed for UPS

2. **Tracking Failures**:
   - Validate tracking number format
   - Check API rate limits
   - Verify network connectivity

3. **MCP Integration Issues**:
   - Ensure MCP client is properly configured
   - Check server logs for detailed error information
   - Verify tool registration in MCP client

### Logging

Enable debug logging for detailed troubleshooting:

```bash
LOG_LEVEL=DEBUG
```

Check logs for specific error details and API response information.

## Rate Limits and Best Practices

### FedEx API
- Maximum 30 tracking numbers per request
- Tokens expire every 60 minutes (auto-refreshed)
- Respect rate limits to avoid 429 errors

### UPS API
- Individual requests for each tracking number
- OAuth tokens may have longer validity
- Implement exponential backoff for retries

### DHL API
- Maximum 10 tracking numbers per request
- OAuth tokens expire based on API settings
- Supports both batch and individual tracking

### Best Practices
- Use batch tracking when possible
- Cache results to minimize API calls
- Implement proper error handling
- Monitor API usage and costs

## Contributing

1. Follow the project structure and coding conventions from `CLAUDE.md`
2. Add unit tests for new features using pytest
3. Update documentation as needed
4. Ensure all tests pass before submitting changes
5. Use type hints and Pydantic models for validation

## License

This project is for educational and development purposes. Please ensure compliance with FedEx and UPS API terms of service when using tracking functionality.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review test files for usage examples
- Examine log files for detailed error information