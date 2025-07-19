name: "Claims Processing Agent Web Frontend - Context-Rich Implementation PRP"
description: |

## Purpose
Complete web frontend implementation for the Claims Processing Agent with real-time progress tracking, file upload, and results display using FastAPI, WebSocket, and Jinja2Templates.

## Core Principles
1. **Context is King**: Leverage existing codebase patterns and FastAPI best practices
2. **Real-time Updates**: Use WebSocket for progress and log streaming
3. **User Experience**: Intuitive file upload with visual progress feedback
4. **Code Reuse**: Integrate with existing ClaimScrapingAgent and configuration
5. **Follow Rules**: Adhere to all CLAUDE.md guidelines

---

## Goal
Build a web frontend that allows users to upload CSV files with tracking numbers, process them through the existing Claims Processing Agent, and display real-time progress with downloadable results.

## Why
- **User Accessibility**: Provides web interface for non-technical users
- **Real-time Feedback**: Users see processing progress and logs in real-time
- **Enhanced Experience**: Visual progress bars and status updates
- **Integration**: Leverages existing robust CLI agent functionality
- **Scalability**: Web interface allows multiple users and concurrent processing

## What
Web application with the following features:
- File upload interface for CSV files
- Real-time progress bar during processing
- Live log display showing processing status
- Results display with download capability
- Status indicators and error handling
- Configuration management through web interface

### Success Criteria
- [ ] Users can upload CSV files through web interface
- [ ] Real-time progress bar shows processing status
- [ ] Live log display updates during processing
- [ ] Results are displayed in user-friendly format
- [ ] Users can download processed results as CSV
- [ ] Web interface handles errors gracefully
- [ ] All existing CLI functionality accessible through web
- [ ] WebSocket connections manage multiple concurrent users

## All Needed Context

### Documentation & References
```yaml
# MUST READ - FastAPI Integration Patterns
- url: https://fastapi.tiangolo.com/advanced/templates/
  why: Official FastAPI Jinja2Templates documentation
  
- url: https://fastapi.tiangolo.com/advanced/websockets/
  why: WebSocket implementation patterns in FastAPI
  
- url: https://fastapi.tiangolo.com/tutorial/request-files/
  why: File upload handling with FastAPI UploadFile
  
- url: https://blog.poespas.me/posts/2024/05/27/fastapi-async-websocket-realtime-data-processing/
  why: Real-time data processing with FastAPI WebSockets (2024)
  
- url: https://medium.com/@rajgpt630/beginners-guide-to-creating-asynchronous-progress-bars-with-fastapi-7368871a322b
  why: Async progress bars implementation guide
  
- url: https://stackoverflow.com/questions/70041336/how-can-i-use-a-websocket-to-report-the-progress-of-post-file-uploads-with-fasta
  why: Specific patterns for file upload progress via WebSocket

# MUST READ - Existing Codebase Patterns
- file: src/agent.py
  why: Core ClaimScrapingAgent class with async processing patterns
  
- file: src/config.py
  why: Pydantic configuration models and environment variable patterns
  
- file: src/tools.py
  why: ProcessingResult, ClaimStatus, CSVProcessor patterns
  
- file: main.py
  why: CLI argument parsing and configuration setup patterns
  
- file: requirements.txt
  why: Current dependencies and version constraints
```

### Current Codebase Tree
```bash
Claims/
├── main.py                    # CLI entry point
├── src/
│   ├── __init__.py
│   ├── agent.py              # ClaimScrapingAgent with async processing
│   ├── config.py             # Pydantic configuration models
│   ├── prompts.py            # AI prompts for web scraping
│   └── tools.py              # CSVProcessor, ProcessingResult, RetryHandler
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_config.py
│   └── test_tools.py
├── requirements.txt          # Python dependencies
├── .env.local-llm-example    # Environment configuration template
└── README.md
```

### Desired Codebase Tree with New Web Frontend
```bash
Claims/
├── main.py                    # CLI entry point
├── web_main.py               # Web application entry point
├── src/
│   ├── __init__.py
│   ├── agent.py              # Existing ClaimScrapingAgent
│   ├── config.py             # Existing configuration
│   ├── prompts.py            # Existing prompts
│   ├── tools.py              # Existing tools
│   └── web/                  # New web frontend module
│       ├── __init__.py
│       ├── app.py            # FastAPI application instance
│       ├── routes.py         # Web routes and file handling
│       ├── websocket.py      # WebSocket endpoints for real-time updates
│       ├── models.py         # Pydantic models for web requests/responses
│       └── static/           # Static files (CSS, JS, images)
│           ├── css/
│           │   └── main.css
│           └── js/
│               └── main.js
├── templates/                # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   └── results.html
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_config.py
│   ├── test_tools.py
│   └── test_web.py           # Web frontend tests
├── requirements.txt          # Updated with FastAPI dependencies
├── .env.local-llm-example
└── README.md
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: FastAPI WebSocket connection management
# WebSocket connections must be properly managed to avoid memory leaks
# Use ConnectionManager pattern for multiple concurrent connections

# CRITICAL: File upload handling with UploadFile
# UploadFile uses tempfile.SpooledTemporaryFile - must be read properly
# Use: contents = await file.read() for CSV processing

# CRITICAL: Async context in existing agent
# ClaimScrapingAgent uses async patterns - must maintain async context
# Use: await agent.process_csv_file() in web routes

# CRITICAL: Environment variable loading
# Existing code uses python-dotenv load_dotenv()
# Must call load_dotenv() before FastAPI app initialization

# CRITICAL: Pydantic v2 compatibility
# Existing code uses Pydantic v2 - ensure compatibility
# Use: model_validate() instead of parse_obj()

# CRITICAL: Rich console output in web context
# Existing CLI uses Rich console - won't work in web context
# Create web-specific logging handlers for WebSocket broadcasting
```

## Implementation Blueprint

### Data Models and Structure
```python
# Web-specific Pydantic models for API requests/responses
class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    task_id: str
    filename: str
    status: str

class ProcessingStatus(BaseModel):
    """Real-time processing status"""
    task_id: str
    progress: float  # 0.0 to 1.0
    current_step: str
    total_claims: int
    processed_claims: int
    successful_claims: int
    failed_claims: int
    logs: List[str]

class WebProcessingResult(BaseModel):
    """Web-optimized processing result"""
    task_id: str
    status: str
    results: List[ProcessingResult]
    summary: Dict[str, Any]
    download_url: Optional[str]
```

### Tasks to Complete (in order)
```yaml
Task 1: Update Dependencies
MODIFY requirements.txt:
  - ADD: fastapi>=0.104.0
  - ADD: uvicorn[standard]>=0.24.0
  - ADD: jinja2>=3.1.2
  - ADD: python-multipart>=0.0.6
  - ADD: websockets>=11.0.0
  - PRESERVE: All existing dependencies

Task 2: Create Web Module Structure
CREATE src/web/__init__.py:
  - EMPTY file for package initialization

CREATE src/web/app.py:
  - INITIALIZE FastAPI application
  - CONFIGURE Jinja2Templates
  - SET static files directory
  - LOAD environment variables using load_dotenv()
  - MIRROR pattern from: src/config.py for environment handling

CREATE src/web/models.py:
  - DEFINE web-specific Pydantic models
  - INHERIT from existing ProcessingResult in src/tools.py
  - FOLLOW pattern from: src/config.py for model structure

Task 3: Implement File Upload and Processing Routes
CREATE src/web/routes.py:
  - IMPORT existing ClaimScrapingAgent from src/agent.py
  - IMPORT CSVProcessor from src/tools.py
  - IMPLEMENT file upload endpoint with UploadFile
  - CREATE background task for processing
  - FOLLOW async patterns from: src/agent.py process_csv_file method
  - GENERATE unique task IDs for tracking

Task 4: Implement WebSocket for Real-time Updates
CREATE src/web/websocket.py:
  - IMPLEMENT ConnectionManager for multiple clients
  - CREATE WebSocket endpoint for progress updates
  - INTEGRATE with existing agent progress callbacks
  - BROADCAST processing status to connected clients
  - HANDLE WebSocket connection lifecycle

Task 5: Create HTML Templates
CREATE templates/base.html:
  - BASIC HTML structure with Bootstrap CSS
  - INCLUDE WebSocket JavaScript connection
  - DEFINE common layout elements

CREATE templates/index.html:
  - EXTEND base.html
  - CREATE file upload form
  - INCLUDE progress bar elements
  - ADD log display area

CREATE templates/results.html:
  - DISPLAY processing results
  - SHOW summary statistics
  - PROVIDE download links

Task 6: Implement Static Assets
CREATE src/web/static/css/main.css:
  - STYLE progress bars and status indicators
  - RESPONSIVE design for mobile compatibility

CREATE src/web/static/js/main.js:
  - HANDLE WebSocket connections
  - UPDATE progress bars in real-time
  - MANAGE file upload UI interactions
  - DISPLAY log messages

Task 7: Create Web Application Entry Point
CREATE web_main.py:
  - IMPORT FastAPI app from src/web/app.py
  - CONFIGURE uvicorn server
  - MIRROR pattern from: main.py for configuration setup
  - INCLUDE all routes and WebSocket endpoints

Task 8: Integrate with Existing Agent
MODIFY src/agent.py:
  - ADD optional progress_callback parameter to process_csv_file
  - IMPLEMENT callback mechanism for real-time updates
  - PRESERVE existing CLI functionality
  - MAINTAIN async context compatibility

Task 9: Add Web-specific Configuration
MODIFY src/config.py:
  - ADD WebSettings class for web-specific config
  - INCLUDE server host, port, and WebSocket settings
  - FOLLOW existing pattern for environment variables

Task 10: Create Web Tests
CREATE tests/test_web.py:
  - TEST file upload functionality
  - TEST WebSocket connections
  - TEST integration with existing agent
  - FOLLOW pattern from: tests/test_agent.py
  - INCLUDE async test patterns with pytest-asyncio
```

### Per Task Pseudocode

```python
# Task 1: Update Dependencies
# Add FastAPI and related dependencies to requirements.txt

# Task 2: Web Module Structure
# src/web/app.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()  # CRITICAL: Load before app initialization

app = FastAPI(title="Claims Processing Agent Web Frontend")
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
templates = Jinja2Templates(directory="templates")

# Task 3: File Upload Routes
# src/web/routes.py
from fastapi import UploadFile, File, BackgroundTasks
import uuid
from ..agent import ClaimScrapingAgent
from ..config import Config

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # PATTERN: Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # PATTERN: Save uploaded file temporarily
    temp_path = f"/tmp/{task_id}_{file.filename}"
    contents = await file.read()  # CRITICAL: Read UploadFile properly
    
    # PATTERN: Start background processing
    background_tasks.add_task(process_claims_task, task_id, temp_path)
    
    return {"task_id": task_id, "status": "started"}

# Task 4: WebSocket Implementation
# src/web/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

class ConnectionManager:
    """Manage WebSocket connections for multiple clients"""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
    
    async def broadcast_progress(self, task_id: str, data: dict):
        """Broadcast progress to all connections for a task"""
        if task_id in self.active_connections:
            for connection in self.active_connections[task_id]:
                await connection.send_text(json.dumps(data))

# Task 8: Agent Integration
# MODIFY src/agent.py - add progress callback
async def process_csv_file(
    self, 
    input_path: Union[str, Path], 
    output_path: Union[str, Path],
    progress_callback: Optional[Callable] = None  # NEW: Progress callback
) -> List[ProcessingResult]:
    """Process CSV with optional progress reporting"""
    
    # PATTERN: Report progress through callback
    if progress_callback:
        await progress_callback({
            "progress": 0.1,
            "current_step": "Loading CSV file",
            "total_claims": 0,
            "processed_claims": 0
        })
    
    # Continue with existing processing logic...
    # Call progress_callback at key points
```

### Integration Points
```yaml
DEPENDENCIES:
  - add to: requirements.txt
  - pattern: "fastapi>=0.104.0"
  - pattern: "uvicorn[standard]>=0.24.0"
  - pattern: "jinja2>=3.1.2"
  - pattern: "python-multipart>=0.0.6"
  - pattern: "websockets>=11.0.0"
  
CONFIGURATION:
  - extend: src/config.py
  - pattern: "class WebSettings(BaseModel):"
  - add: "host, port, websocket_settings"
  
AGENT_INTEGRATION:
  - modify: src/agent.py
  - pattern: "async def process_csv_file(..., progress_callback=None)"
  - preserve: "All existing CLI functionality"
  
TEMPLATES:
  - create: templates/ directory
  - pattern: "Jinja2Templates directory structure"
  - include: "Bootstrap CSS, WebSocket JavaScript"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
source venv_linux/bin/activate
ruff check src/web/ --fix
mypy src/web/
black src/web/

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE tests/test_web.py with these test cases:
import pytest
from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)

def test_upload_endpoint():
    """Test file upload functionality"""
    with open("tests/fixtures/sample_claims.csv", "rb") as f:
        response = client.post("/upload", files={"file": f})
    assert response.status_code == 200
    assert "task_id" in response.json()

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection"""
    with client.websocket_connect("/ws/test-task-id") as websocket:
        data = websocket.receive_json()
        assert "status" in data

def test_template_rendering():
    """Test HTML template rendering"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Claims Processing Agent" in response.text
```

```bash
# Run and iterate until passing:
source venv_linux/bin/activate
pytest tests/test_web.py -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start the web service
source venv_linux/bin/activate
python web_main.py

# Test the web interface
curl -X POST http://localhost:8000/upload \
  -F "file=@tests/fixtures/sample_claims.csv"

# Expected: {"task_id": "uuid", "status": "started"}
# Open browser to http://localhost:8000 and test UI
```

### Level 4: End-to-End Test
```bash
# Full workflow test
# 1. Start web server
python web_main.py

# 2. Open browser to http://localhost:8000
# 3. Upload CSV file
# 4. Verify real-time progress updates
# 5. Check log display updates
# 6. Verify results display and download
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check src/`
- [ ] No type errors: `mypy src/`
- [ ] Web server starts successfully: `python web_main.py`
- [ ] File upload works through web interface
- [ ] WebSocket connections established and working
- [ ] Real-time progress updates display correctly
- [ ] Log messages stream to web interface
- [ ] Results display properly formatted
- [ ] CSV download functionality works
- [ ] Multiple concurrent users supported
- [ ] Error handling graceful and informative
- [ ] All existing CLI functionality preserved

---

## Anti-Patterns to Avoid
- ❌ Don't create new configuration patterns - use existing Config class
- ❌ Don't bypass existing agent functionality - integrate with ClaimScrapingAgent
- ❌ Don't ignore WebSocket connection management - implement proper cleanup
- ❌ Don't hardcode paths - use environment variables and configuration
- ❌ Don't block async operations - maintain async context throughout
- ❌ Don't duplicate existing logic - reuse CSVProcessor and ProcessingResult
- ❌ Don't skip progress callback integration - users need real-time feedback
- ❌ Don't forget error handling - web users need clear error messages

## Confidence Score: 9/10

This PRP provides comprehensive context for one-pass implementation with:
- ✅ Complete integration with existing codebase patterns
- ✅ Specific FastAPI, WebSocket, and Jinja2 implementation details
- ✅ Real-world examples and documentation links
- ✅ Detailed task breakdown with pseudocode
- ✅ Proper validation loops and testing strategy
- ✅ Clear error handling and anti-patterns guidance

The high confidence score reflects the thorough research, existing codebase integration, and proven patterns from the FastAPI ecosystem. The implementation follows established patterns and leverages the robust existing agent functionality.