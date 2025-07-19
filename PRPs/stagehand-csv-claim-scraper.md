name: "Stagehand CSV Claim Status Scraper PRP"
description: |

## Purpose
Comprehensive implementation guide for creating a Python-based Stagehand agent that automates claim status checking on u-pic.com by processing CSV files with tracking numbers and returning updated CSV files with claim status information.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create a production-ready Python script using Stagehand that loads a CSV file with tracking numbers, navigates to https://u-pic.com/claims, processes each tracking number by submitting it under the DHL Clients section, extracts the "Claim Status" from the "Claim Resolution" section, and exports an updated CSV file with the status information.

## Why
- **Automation Value**: Eliminates manual data entry and status checking for multiple tracking numbers
- **Data Processing**: Streamlines claim status reporting for business operations
- **Integration Example**: Demonstrates Stagehand integration with CSV processing and web scraping
- **Scalability**: Processes multiple tracking numbers efficiently with error handling

## What
A command-line Python application that:
- Loads CSV files containing tracking numbers
- Uses Stagehand to automate browser interactions on u-pic.com
- Extracts claim status information using AI-powered web scraping
- Exports results to CSV with original data plus status column
- Handles errors, retries, and rate limiting gracefully
- Provides logging and progress feedback

### Success Criteria
- [ ] Successfully loads CSV files with tracking numbers
- [ ] Navigates to https://u-pic.com/claims using Stagehand
- [ ] Submits tracking numbers in DHL Clients section
- [ ] Extracts claim status from Claim Resolution section
- [ ] Exports updated CSV with status column
- [ ] Handles errors and edge cases gracefully
- [ ] Includes comprehensive unit tests (>80% coverage)
- [ ] Provides clear CLI interface and logging
- [ ] Follows all CLAUDE.md conventions and patterns

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://docs.stagehand.dev/examples/best_practices
  why: Best practices for Stagehand automation, variables usage, and error handling
  
- url: https://docs.stagehand.dev/reference/initialization_config
  why: Configuration options for browser settings, timeouts, and environment setup
  
- url: https://docs.stagehand.dev/reference/act
  why: Web interaction patterns using natural language with variables for form submission
  
- url: https://docs.stagehand.dev/reference/extract
  why: Structured data extraction using pydantic schemas for claim status information
  
- url: https://docs.stagehand.dev/reference/observe
  why: Page exploration before taking actions, useful for understanding page structure

- file: examples/config.py
  why: Pydantic configuration patterns with environment variables and browser settings
  
- file: examples/page.py
  why: StagehandPage wrapper patterns for act(), extract(), and observe() methods
  
- file: examples/schemas.py
  why: Pydantic model patterns for Stagehand options and results with camelCase conversion
  
- file: examples/main.py
  why: Stagehand client initialization, session management, and cleanup patterns
  
- file: CLAUDE.md
  why: Project structure requirements, testing patterns, and code organization rules
```

### Current Codebase tree
```bash
/home/geiger/Claims/
├── CLAUDE.md
├── Claims.csv                    # Sample input file with tracking numbers
├── INITIAL.md                   # Feature requirements
├── README.md                    # Workshop documentation
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md
├── examples/                    # Stagehand example implementations
│   ├── README.md
│   ├── api.py                   # API communication patterns
│   ├── config.py                # Pydantic configuration models
│   ├── context.py               # Browser context management
│   ├── main.py                  # Main Stagehand class patterns
│   ├── page.py                  # Page automation methods
│   ├── schemas.py               # Pydantic schemas for Stagehand
│   └── utils.py                 # Utility functions
```

### Desired Codebase tree with files to be added and responsibility of file
```bash
/home/geiger/Claims/
├── src/                         # Main application code
│   ├── __init__.py              # Package initialization
│   ├── agent.py                 # ClaimScrapingAgent - main automation logic
│   ├── tools.py                 # CSV processing, retry logic, utilities
│   ├── prompts.py               # Stagehand prompts and pydantic schemas
│   └── config.py                # Configuration management with pydantic
├── tests/                       # Unit and integration tests
│   ├── __init__.py
│   ├── test_agent.py            # Agent functionality tests
│   ├── test_tools.py            # CSV and utility function tests
│   ├── test_config.py           # Configuration tests
│   └── fixtures/                # Test data and fixtures
│       └── sample_claims.csv    # Test CSV file
├── main.py                      # CLI entry point
├── requirements.txt             # Project dependencies
├── .env.example                 # Environment variable template
├── README.md                    # Updated with project documentation
└── pyproject.toml              # Python project configuration
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: Stagehand requires proper session management
# Sessions must be initialized and closed properly to avoid resource leaks

# CRITICAL: Use variables in act() to avoid exposing sensitive data to LLM
await page.act({
    "action": "Type %tracking_number% into the tracking field",
    "variables": {"tracking_number": "actual_tracking_number"}
})

# CRITICAL: u-pic.com may have rate limiting
# Implement delays between requests and retry logic

# CRITICAL: Browser automation requires proper error handling
# Network timeouts, element not found, and page load issues

# CRITICAL: CSV files may have different formats or encoding issues
# Use pandas with error handling and encoding detection

# CRITICAL: Follow CLAUDE.md - files must be under 500 lines
# Split large files into logical modules

# CRITICAL: Use python_dotenv and load_dotenv() for environment variables
# Don't hardcode API keys or sensitive configuration

# CRITICAL: Pydantic models for data validation
# All input/output should be validated with pydantic schemas
```

## Implementation Blueprint

### Data models and structure

Create the core data models for type safety and consistency:
```python
# src/config.py - Configuration management
class StagehandSettings(BaseModel):
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("STAGEHAND_API_KEY"))
    timeout_seconds: int = Field(default_factory=lambda: int(os.getenv("STAGEHAND_TIMEOUT", "30")))
    
class ProcessingSettings(BaseModel):
    batch_size: int = Field(default_factory=lambda: int(os.getenv("BATCH_SIZE", "5")))
    request_delay: float = Field(default_factory=lambda: float(os.getenv("REQUEST_DELAY", "2.0")))
    max_retries: int = Field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))

# src/prompts.py - Data extraction schemas
class ClaimStatus(BaseModel):
    tracking_number: str = Field(description="The tracking number being processed")
    claim_status: str = Field(description="The claim status from Claim Resolution section")
    resolution_details: Optional[str] = Field(description="Additional resolution information if available")
    
class ProcessingResult(BaseModel):
    tracking_number: str
    status: Literal["success", "error", "not_found"]
    claim_status: Optional[str] = None
    error_message: Optional[str] = None
```

### List of tasks to be completed to fulfill the PRP in the order they should be completed

```yaml
Task 1: Create project structure and dependencies
CREATE requirements.txt:
  - INCLUDE: stagehand-py, pandas, pydantic, python-dotenv, click, pytest
  - MIRROR pattern from: examples/ import statements
  - ADD: development dependencies (black, ruff, mypy)

CREATE .env.example:
  - TEMPLATE for environment variables
  - INCLUDE: STAGEHAND_API_KEY, browser settings, processing config

CREATE src/__init__.py and tests/__init__.py:
  - EMPTY files for package structure

Task 2: Configuration management
CREATE src/config.py:
  - MIRROR pattern from: examples/config.py
  - USE: Pydantic BaseModel with environment variable defaults
  - INCLUDE: StagehandSettings, ProcessingSettings, LoggingSettings
  - FOLLOW: CLAUDE.md pydantic usage patterns

Task 3: Data models and prompts
CREATE src/prompts.py:
  - MIRROR pattern from: examples/schemas.py
  - CREATE: Pydantic models for claim data extraction
  - INCLUDE: Stagehand extraction prompts with proper schemas
  - USE: Google-style docstrings for all models

Task 4: Utility functions and CSV processing
CREATE src/tools.py:
  - CREATE: CSV loading and saving functions with pandas
  - IMPLEMENT: Retry logic with exponential backoff
  - ADD: Data validation and error handling utilities
  - INCLUDE: Progress tracking and logging helpers
  - KEEP: Under 500 lines per CLAUDE.md rules

Task 5: Main agent implementation
CREATE src/agent.py:
  - MIRROR pattern from: examples/main.py and examples/page.py
  - CREATE: ClaimScrapingAgent class with async methods
  - IMPLEMENT: Stagehand session management
  - ADD: Navigation and data extraction workflow
  - INCLUDE: Error handling and retry logic
  - USE: Context managers for proper resource cleanup

Task 6: CLI interface
CREATE main.py:
  - USE: Click or argparse for command-line interface
  - IMPLEMENT: Input validation and file handling
  - ADD: Progress indicators and logging output
  - INCLUDE: Help text and usage examples
  - HANDLE: Error scenarios gracefully

Task 7: Unit tests
CREATE tests/test_config.py:
  - TEST: Configuration loading and validation
  - VERIFY: Environment variable handling
  - CHECK: Default values and edge cases

CREATE tests/test_tools.py:
  - TEST: CSV processing functions
  - VERIFY: Retry logic and error handling
  - CHECK: Data validation utilities

CREATE tests/test_agent.py:
  - TEST: Agent initialization and configuration
  - MOCK: Stagehand interactions for unit testing
  - VERIFY: Error handling and edge cases

CREATE tests/fixtures/sample_claims.csv:
  - SAMPLE: Test data for CSV processing
  - INCLUDE: Various tracking number formats

Task 8: Integration testing and validation
CREATE: Integration test script
  - TEST: End-to-end workflow with test data
  - VERIFY: Actual Stagehand integration (if credentials available)
  - CHECK: CSV input/output correctness

VALIDATE: All linting and type checking
  - RUN: ruff check and format
  - RUN: mypy type checking
  - FIX: Any errors or warnings

Task 9: Documentation updates
UPDATE README.md:
  - INCLUDE: Project description and setup instructions
  - ADD: Usage examples and CLI documentation
  - DOCUMENT: Configuration options and environment variables
  - PROVIDE: Troubleshooting guide
```

### Per task pseudocode as needed added to each task

```python
# Task 5 - Main agent implementation pseudocode
class ClaimScrapingAgent:
    def __init__(self, config: Config):
        # PATTERN: Initialize with configuration (see examples/main.py)
        self.config = config
        self.stagehand = None
        
    async def process_csv_file(self, input_path: str, output_path: str) -> List[ProcessingResult]:
        # PATTERN: Context manager for session management
        async with self._stagehand_session() as stagehand:
            # STEP 1: Load CSV file with pandas
            claims_data = self._load_csv(input_path)
            
            # STEP 2: Navigate to u-pic.com claims page
            await self._navigate_to_claims_page(stagehand)
            
            # STEP 3: Process each tracking number with retry logic
            results = []
            for claim in claims_data:
                result = await self._process_single_claim(stagehand, claim["tracking_number"])
                results.append(result)
                
                # GOTCHA: Rate limiting - add delay between requests
                await asyncio.sleep(self.config.processing.request_delay)
            
            # STEP 4: Export results to CSV
            self._export_results(results, output_path)
            return results
    
    async def _process_single_claim(self, stagehand, tracking_number: str) -> ProcessingResult:
        # PATTERN: Use observe() to understand page structure first
        elements = await stagehand.page.observe("Find the tracking number input field")
        
        # PATTERN: Use act() with variables to avoid exposing data to LLM
        await stagehand.page.act({
            "action": "Enter %tracking_number% in the tracking number field",
            "variables": {"tracking_number": tracking_number}
        })
        
        # PATTERN: Submit form and wait for results
        await stagehand.page.act("Click the submit button")
        
        # PATTERN: Use extract() with pydantic schema for structured data
        claim_data = await stagehand.page.extract({
            "instruction": "Extract the claim status from the Claim Resolution section",
            "schema": ClaimStatus
        })
        
        return ProcessingResult(
            tracking_number=tracking_number,
            status="success",
            claim_status=claim_data.claim_status
        )
```

### Integration Points
```yaml
ENVIRONMENT:
  - .env file: "STAGEHAND_API_KEY, BROWSER_TIMEOUT, BATCH_SIZE, REQUEST_DELAY"
  - pattern: "Use python_dotenv.load_dotenv() in config.py"
  
CSV_PROCESSING:
  - pandas: "Read CSV with encoding detection and error handling"
  - pattern: "df = pd.read_csv(path, encoding='utf-8-sig', on_bad_lines='skip')"
  
STAGEHAND_CONFIG:
  - browser settings: "Configure timeout, headless mode, user agent"
  - pattern: "Follow examples/config.py StagehandConfig patterns"
  
CLI_INTERFACE:
  - entry point: "main.py with click decorators for commands"
  - pattern: "@click.command() and @click.option() for arguments"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check src/ tests/ main.py --fix  # Auto-fix what's possible
ruff format src/ tests/ main.py       # Format code
mypy src/ tests/ main.py              # Type checking

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests each new feature/file/function use existing test patterns
```python
# CREATE test_agent.py with these test cases:
def test_agent_initialization():
    """Agent initializes with proper configuration"""
    config = Config()
    agent = ClaimScrapingAgent(config)
    assert agent.config == config

def test_csv_loading():
    """CSV files load correctly with proper validation"""
    agent = ClaimScrapingAgent(Config())
    data = agent._load_csv("tests/fixtures/sample_claims.csv")
    assert len(data) > 0
    assert "tracking_number" in data[0]

def test_retry_logic():
    """Retry logic handles failures gracefully"""
    with mock.patch('stagehand.page.act', side_effect=TimeoutError):
        result = process_with_retry(mock_function)
        assert result.status == "error"
        assert "timeout" in result.error_message
```

```bash
# Run and iterate until passing:
pytest tests/ -v --cov=src --cov-report=html
# If failing: Read error, understand root cause, fix code, re-run (never mock to pass)
```

### Level 3: Integration Test
```bash
# Test with sample data
python main.py tests/fixtures/sample_claims.csv output.csv --dry-run

# Test configuration loading
python -c "from src.config import Config; print(Config().dict())"

# Expected: No errors, proper configuration display
# If error: Check logs and configuration files
```

## Final validation Checklist
- [ ] All tests pass: `pytest tests/ -v --cov=src --cov-report=html`
- [ ] No linting errors: `ruff check src/ tests/ main.py`
- [ ] No type errors: `mypy src/ tests/ main.py`
- [ ] Manual test successful: `python main.py Claims.csv output.csv --dry-run`
- [ ] Error cases handled gracefully (missing files, invalid data, network errors)
- [ ] Logs are informative but not verbose
- [ ] Documentation updated with usage examples
- [ ] Environment variables properly configured
- [ ] CSV input/output formats validated
- [ ] Rate limiting and retry logic tested

---

## Anti-Patterns to Avoid
- ❌ Don't hardcode tracking numbers or credentials in code
- ❌ Don't skip proper session cleanup in Stagehand
- ❌ Don't use synchronous functions in async context
- ❌ Don't ignore CSV encoding issues or malformed data
- ❌ Don't create files over 500 lines (CLAUDE.md rule)
- ❌ Don't expose sensitive data to LLM in act() calls - use variables
- ❌ Don't skip rate limiting - u-pic.com may block aggressive requests
- ❌ Don't catch all exceptions - be specific about error types
- ❌ Don't skip input validation - use pydantic models
- ❌ Don't forget to test edge cases and error scenarios

## Success Confidence Score: 9/10

This PRP provides comprehensive context, follows established patterns, includes detailed validation loops, and addresses all requirements. The high confidence score is based on:
- Complete documentation references and best practices
- Detailed task breakdown with clear dependencies
- Specific code patterns from examples directory
- Comprehensive testing strategy
- Clear validation gates with executable commands
- Adherence to all CLAUDE.md requirements
- Proper error handling and edge case coverage