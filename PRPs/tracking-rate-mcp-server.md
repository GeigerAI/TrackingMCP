name: "Package Tracking MCP Server for Pydantic AI Agents"
description: |

## Purpose
Build a production-ready Model Context Protocol (MCP) server that enables Pydantic AI agents to track packages using FedEx and UPS APIs. This server will provide standardized tracking tools that can be consumed by any MCP-compatible AI agent or application.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create a Model Context Protocol server that provides package tracking capabilities for FedEx and UPS shipments. The server should handle OAuth authentication, rate limiting, error handling, and return structured tracking data that Pydantic AI agents can easily consume and process.

## Why
- **Business value**: Enables AI agents to autonomously track shipments and provide real-time logistics updates
- **Integration**: Standardized MCP interface allows any AI agent to use tracking capabilities
- **Problems solved**: Eliminates manual tracking lookup and provides structured data for AI decision-making

## What
An MCP server that exposes tracking tools for:
- FedEx package tracking with OAuth2 authentication
- UPS package tracking with OAuth2 authentication  
- Structured responses with delivery status, location, and timing data
- Automatic token management and refresh
- Error handling for API rate limits and failures

### Success Criteria
- [ ] MCP server successfully registers tracking tools
- [ ] FedEx OAuth authentication and token refresh working
- [ ] UPS OAuth authentication and token refresh working
- [ ] Package tracking returns structured Pydantic models
- [ ] Error handling for invalid tracking numbers and API failures
- [ ] All tests pass and code meets quality standards
- [ ] Integration with Pydantic AI agents working

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://ai.pydantic.dev/
  why: Core Pydantic AI framework documentation for agent integration
  
- url: https://ai.pydantic.dev/agents/
  why: Agent creation patterns and tool usage with MCP servers
  
- url: https://modelcontextprotocol.io/
  why: Official MCP specification and protocol documentation
  
- url: https://github.com/modelcontextprotocol/python-sdk
  why: Python SDK for building MCP servers with tool registration patterns
  
- url: https://developer.fedex.com/api/en-us/catalog/track/v1/docs.html
  why: FedEx tracking API endpoints, request/response formats, rate limits
  
- url: https://developer.fedex.com/api/en-ca/catalog/authorization/v1/docs.html
  why: FedEx OAuth2 flow, token management (1-hour expiry), credentials
  
- file: Example/fedex_oauth.py
  why: Basic FedEx OAuth implementation pattern to build upon
  
- file: Example/fedex_tracking.py
  why: Basic FedEx tracking request pattern with headers and payload
  
- file: Example/ups_tracking.py
  why: UPS tracking API structure and request format
  
- file: Example/ups_oauth_token.py
  why: UPS OAuth implementation with authorization_code flow
  
- url: https://github.com/coleam00/mcp-mem0
  why: Reference MCP server implementation showing @mcp.tool() patterns, environment config
```

### Current Codebase tree
```bash
.
├── Example/
│   ├── README.md
│   ├── fedex_oauth.py        # Basic FedEx OAuth template
│   ├── fedex_tracking.py     # Basic FedEx tracking template  
│   ├── ups_oauth_token.py    # Basic UPS OAuth template
│   └── ups_tracking.py       # Basic UPS tracking template
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md
│   └── EXAMPLE_multi_agent_prp.md
├── INITIAL.md               # Feature specification
├── CLAUDE.md               # Project coding guidelines
└── .claude/                # Claude configuration
```

### Desired Codebase tree with files to be added
```bash
.
├── src/
│   ├── __init__.py                    # Package initialization
│   ├── server.py                      # Main MCP server implementation
│   ├── models.py                      # Pydantic models for tracking data
│   ├── config.py                      # Configuration and environment management
│   ├── auth/
│   │   ├── __init__.py               # Auth package init
│   │   ├── fedex_auth.py             # FedEx OAuth token management
│   │   └── ups_auth.py               # UPS OAuth token management
│   ├── tracking/
│   │   ├── __init__.py               # Tracking package init
│   │   ├── fedex_tracker.py          # FedEx tracking implementation
│   │   ├── ups_tracker.py            # UPS tracking implementation
│   │   └── base_tracker.py           # Abstract tracking interface
│   └── tools/
│       ├── __init__.py               # Tools package init
│       ├── fedex_tools.py            # FedEx MCP tools
│       └── ups_tools.py              # UPS MCP tools
├── tests/
│   ├── __init__.py                   # Test package init
│   ├── test_server.py                # MCP server tests
│   ├── test_models.py                # Model validation tests
│   ├── test_fedex_auth.py            # FedEx authentication tests
│   ├── test_ups_auth.py              # UPS authentication tests
│   ├── test_fedex_tracking.py        # FedEx tracking tests
│   └── test_ups_tracking.py          # UPS tracking tests
├── venv_linux/                       # Virtual environment (as specified in CLAUDE.md)
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project configuration
├── .env.example                       # Environment variables template
├── README.md                          # Comprehensive documentation
└── main.py                           # CLI entry point for testing
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: FedEx OAuth tokens expire every 60 minutes - implement auto-refresh
# CRITICAL: FedEx allows max 30 tracking numbers per request
# CRITICAL: UPS uses authorization_code flow with redirect_uri requirement
# CRITICAL: MCP servers require JSON-RPC 2.0 message format
# CRITICAL: Use async/await throughout for Pydantic AI compatibility
# CRITICAL: Store sensitive credentials in .env, never commit them
# CRITICAL: FedEx sandbox vs production URLs differ
# CRITICAL: Rate limits: respect API throttling to avoid 429 errors
# CRITICAL: Use python_dotenv and load_dotenv() per CLAUDE.md requirements
```

## Implementation Blueprint

### Data models and structure

Create core data models for type safety and API consistency.
```python
# models.py - Tracking data structures
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

class TrackingCarrier(str, Enum):
    FEDEX = "fedex"
    UPS = "ups"

class TrackingStatus(str, Enum):
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"  
    DELIVERED = "delivered"
    EXCEPTION = "exception"
    PENDING = "pending"

class TrackingEvent(BaseModel):
    timestamp: datetime
    status: str
    location: Optional[str] = None
    description: str

class TrackingResult(BaseModel):
    tracking_number: str
    carrier: TrackingCarrier
    status: TrackingStatus
    estimated_delivery: Optional[datetime] = None
    events: List[TrackingEvent] = []
    delivery_address: Optional[str] = None
    error_message: Optional[str] = None

class TrackingRequest(BaseModel):
    tracking_number: str = Field(..., description="Package tracking number")
    carrier: TrackingCarrier = Field(..., description="Shipping carrier")
```

### List of tasks to be completed

```yaml
Task 1: Setup Project Structure and Configuration
CREATE src/config.py:
  - PATTERN: Use pydantic-settings like CLAUDE.md specifies
  - Load environment variables with python_dotenv
  - Validate required API keys are present
  - Support both sandbox and production modes

CREATE requirements.txt:
  - Include: mcp, pydantic, httpx, python-dotenv, pytest
  - Follow exact versions for reproducibility

CREATE .env.example:
  - Include all required environment variables with descriptions
  - Follow pattern from CLAUDE.md

Task 2: Implement OAuth Authentication Modules
CREATE src/auth/fedex_auth.py:
  - PATTERN: Async class-based approach for token management
  - Implement auto-refresh for 1-hour token expiry
  - Handle client_credentials grant type
  - Store tokens securely in memory (not files)

CREATE src/auth/ups_auth.py:
  - PATTERN: Similar to FedEx but handle authorization_code flow
  - Implement token refresh mechanism
  - Handle redirect_uri requirements

Task 3: Implement Core Tracking Services
CREATE src/tracking/base_tracker.py:
  - PATTERN: Abstract base class for consistency
  - Define common interface for all carriers
  - Include error handling patterns

CREATE src/tracking/fedex_tracker.py:
  - PATTERN: Use httpx async client like mcp-mem0 examples
  - Handle up to 30 tracking numbers per request
  - Parse FedEx response format to TrackingResult models
  - Implement retry logic for rate limits

CREATE src/tracking/ups_tracker.py:
  - PATTERN: Similar structure to FedEx tracker
  - Handle UPS API response format
  - Implement inquiry number tracking

Task 4: Create MCP Tools Interface
CREATE src/tools/fedex_tools.py:
  - PATTERN: Use @mcp.tool() decorator like mcp-mem0
  - Register track_fedex_package tool
  - Include proper error handling and validation

CREATE src/tools/ups_tools.py:
  - PATTERN: Similar to FedEx tools structure
  - Register track_ups_package tool
  - Consistent error handling

Task 5: Implement Main MCP Server
CREATE src/server.py:
  - PATTERN: Follow mcp-mem0 server structure
  - Register all tracking tools
  - Support both stdio and SSE transport
  - Implement proper logging

CREATE main.py:
  - PATTERN: CLI entry point for testing
  - Allow testing tools directly
  - Support both carriers

Task 6: Add Comprehensive Tests
CREATE tests/:
  - PATTERN: Mirror src structure in tests
  - Mock HTTP requests for API calls
  - Test authentication flows
  - Test tracking result parsing
  - Ensure 80%+ coverage

Task 7: Create Documentation
CREATE README.md:
  - PATTERN: Follow Example/README.md structure
  - Include setup, installation, usage
  - API key configuration steps
  - MCP client integration examples
```

### Per task pseudocode

```python
# Task 2: FedEx Authentication
class FedExAuth:
    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True):
        # PATTERN: Store credentials securely
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://apis-sandbox.fedex.com" if sandbox else "https://apis.fedex.com"
        self.token = None
        self.expires_at = None
    
    async def get_access_token(self) -> str:
        # CRITICAL: Check if token needs refresh (expires every 60 min)
        if self.token and self.expires_at and datetime.now() < self.expires_at:
            return self.token
        
        # PATTERN: Use httpx like mcp-mem0
        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            # GOTCHA: FedEx requires application/x-www-form-urlencoded
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise AuthenticationError(f"FedEx auth failed: {response.text}")
            
            token_data = response.json()
            self.token = token_data["access_token"] 
            self.expires_at = datetime.now() + timedelta(seconds=token_data["expires_in"] - 60)  # 60s buffer
            
            return self.token

# Task 4: MCP Tool Registration  
@mcp.tool()
async def track_fedex_package(tracking_number: str) -> TrackingResult:
    """Track a FedEx package by tracking number."""
    # PATTERN: Validate input with Pydantic
    request = TrackingRequest(tracking_number=tracking_number, carrier=TrackingCarrier.FEDEX)
    
    # CRITICAL: Use dependency injection for auth
    auth = FedExAuth(
        client_id=config.FEDEX_CLIENT_ID,
        client_secret=config.FEDEX_CLIENT_SECRET,
        sandbox=config.FEDEX_SANDBOX
    )
    
    tracker = FedExTracker(auth)
    
    # PATTERN: Structured error handling
    try:
        result = await tracker.track_package(request.tracking_number)
        return result
    except TrackingError as e:
        return TrackingResult(
            tracking_number=tracking_number,
            carrier=TrackingCarrier.FEDEX,
            status=TrackingStatus.EXCEPTION,
            error_message=str(e)
        )
```

### Integration Points
```yaml
ENVIRONMENT:
  - add to: .env
  - vars: |
      # FedEx Configuration
      FEDEX_CLIENT_ID=your_fedex_client_id
      FEDEX_CLIENT_SECRET=your_fedex_client_secret
      FEDEX_SANDBOX=true
      
      # UPS Configuration  
      UPS_CLIENT_ID=your_ups_client_id
      UPS_CLIENT_SECRET=your_ups_client_secret
      UPS_REDIRECT_URI=http://localhost:8000/callback
      UPS_SANDBOX=true
      
      # MCP Configuration
      MCP_TRANSPORT=stdio
      LOG_LEVEL=INFO

DEPENDENCIES:
  - Update requirements.txt with:
    - mcp>=0.8.0
    - pydantic>=2.0.0  
    - httpx>=0.24.0
    - python-dotenv>=1.0.0
    - pytest>=7.0.0

MCP_CLIENT_INTEGRATION:
  - Server can be used with any MCP-compatible client
  - Register server in client configuration
  - Tools appear as available functions for AI agents
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check src/ tests/ --fix        # Auto-fix style issues
mypy src/ tests/                    # Type checking

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```python
# test_fedex_tracking.py
async def test_fedex_authentication():
    """Test FedEx OAuth flow"""
    auth = FedExAuth("test_id", "test_secret", sandbox=True)
    # Mock the HTTP response
    with httpx.MockTransport() as transport:
        token = await auth.get_access_token()
        assert token is not None
        assert auth.expires_at > datetime.now()

async def test_track_fedex_package():
    """Test FedEx package tracking"""
    # Mock successful tracking response
    result = await track_fedex_package("123456789012")
    assert result.tracking_number == "123456789012"
    assert result.carrier == TrackingCarrier.FEDEX
    assert result.status in TrackingStatus

async def test_invalid_tracking_number():
    """Test error handling for invalid tracking numbers"""
    result = await track_fedex_package("invalid")
    assert result.status == TrackingStatus.EXCEPTION
    assert result.error_message is not None

# test_mcp_server.py
async def test_mcp_tool_registration():
    """Test MCP server tool registration"""
    server = create_tracking_server()
    tools = server.list_tools()
    assert "track_fedex_package" in [tool.name for tool in tools]
    assert "track_ups_package" in [tool.name for tool in tools]
```

```bash
# Run tests iteratively until passing:
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# If failing: Debug specific test, fix code, re-run
```

### Level 3: Integration Test
```bash
# Test MCP server directly
python main.py --test-mode

# Expected interactions:
# 1. Server starts and registers tools
# 2. Test FedEx tracking with sample number
# 3. Test UPS tracking with sample number
# 4. Verify structured responses

# Test with Pydantic AI agent:
# 1. Start MCP server: python -m src.server
# 2. Configure Pydantic AI agent to use MCP server
# 3. Ask agent to track a package
# 4. Verify agent receives structured tracking data
```

## Final Validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `ruff check src/ tests/`
- [ ] No type errors: `mypy src/ tests/`
- [ ] FedEx OAuth authentication working
- [ ] UPS OAuth authentication working
- [ ] Package tracking returns valid structured data
- [ ] MCP server registers tools correctly
- [ ] Error cases handled gracefully (invalid tracking numbers, API failures)
- [ ] Token refresh working for both carriers
- [ ] README includes clear setup instructions
- [ ] .env.example has all required variables
- [ ] Integration with Pydantic AI agent tested

---

## Anti-Patterns to Avoid
- ❌ Don't hardcode API keys - use environment variables
- ❌ Don't ignore token expiration - implement auto-refresh
- ❌ Don't use sync functions - keep everything async for Pydantic AI
- ❌ Don't skip rate limit handling - implement backoff strategies
- ❌ Don't return raw API responses - always use structured Pydantic models
- ❌ Don't commit .env files with real credentials
- ❌ Don't skip error handling for network failures
- ❌ Don't use production APIs during development - use sandbox mode

## Confidence Score: 8/10

High confidence due to:
- Clear examples provided in the codebase
- Well-documented external APIs (FedEx, UPS)
- Established MCP server patterns from mcp-mem0
- Comprehensive validation gates and testing approach
- Detailed implementation blueprint with specific patterns

Minor uncertainty on:
- UPS OAuth authorization_code flow complexity
- API rate limiting specifics that may require runtime tuning
- Exact integration patterns with Pydantic AI agents (framework is new 2024)

The comprehensive context, reference implementations, and detailed validation approach provide strong foundation for successful implementation.