# Claims Processing Agent

A Python-based web scraping agent that processes CSV files containing tracking numbers and extracts claim status information from u-pic.com. The agent uses AI-powered web automation to navigate the claims website and extract structured data.

## Features

- 🔍 **Automated Claim Scraping**: Extracts claim status from u-pic.com using AI-powered web automation
- 📊 **CSV Processing**: Batch process multiple tracking numbers from CSV files
- 🤖 **Local LLM Support**: Works with local LLM providers (Ollama, LM Studio, LocalAI)
- ⚡ **Concurrent Processing**: Configurable batch sizes and request delays
- 🔄 **Retry Logic**: Automatic retry for failed claims with configurable limits
- 📝 **Rich Logging**: Comprehensive logging with configurable levels
- 🎯 **Progress Tracking**: Visual progress bars and status updates
- 🛠️ **CLI Interface**: User-friendly command-line interface with rich output

## Installation

1. **Clone the repository** (or extract the project files)

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv_linux
   source venv_linux/bin/activate  # On Linux/macOS
   # or
   venv_linux\Scripts\activate     # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.local-llm-example .env
   ```

## Environment Configuration

Create a `.env` file based on `.env.local-llm-example` with the following settings:

### Required Environment Variables

```bash
# Local LLM Configuration
USE_LOCAL_LLM=true
LOCAL_LLM_BASE_URL=http://localhost:11434/v1  # Ollama example
LOCAL_LLM_API_KEY=local
MODEL_NAME=llama3.1

# Processing Configuration
BATCH_SIZE=5
REQUEST_DELAY=2.0
MAX_RETRIES=3
TIMEOUT_SECONDS=30

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=claims_processing.log
```

### Optional Environment Variables

```bash
# MCP Server Configuration (for MCP integration)
STAGEHAND_MCP_SERVER_URL=/stagehand/mcp-server-browserbase/stagehand/dist/index.js

# Stagehand API URL (for server mode)
STAGEHAND_API_URL=http://localhost:5000

# Browserbase Configuration (for cloud browser automation)
BROWSERBASE_API_KEY=your_api_key_here
BROWSERBASE_PROJECT_ID=your_project_id_here
```

### Local LLM Setup

The agent supports multiple local LLM providers:

- **Ollama**: `http://localhost:11434/v1`
- **LM Studio**: `http://localhost:1234/v1`
- **LocalAI**: `http://localhost:8080/v1`

Make sure your local LLM provider is running and accessible at the configured URL.

## Usage

### Basic Usage

```bash
# Process claims from input.csv and save results to output.csv
python main.py claims.csv results.csv
```

### Advanced Usage

```bash
# Custom batch size and delay
python main.py claims.csv results.csv --batch-size 3 --delay 3.0

# Custom retry and timeout settings
python main.py claims.csv results.csv --max-retries 5 --timeout 60

# Enable debug logging
python main.py claims.csv results.csv --log-level DEBUG

# Dry run (validate configuration without processing)
python main.py claims.csv results.csv --dry-run
```

### Create Sample Data

```bash
# Create a sample CSV file with test tracking numbers
python main.py --create-sample sample.csv
```

### Command Line Options

- `--batch-size`: Number of claims to process concurrently (default: 5)
- `--delay`: Delay between batches in seconds (default: 2.0)
- `--max-retries`: Maximum retry attempts for failed claims (default: 3)
- `--timeout`: Timeout for web operations in seconds (default: 30)
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--log-file`: Path to log file (default: claims_processing.log)
- `--create-sample`: Create a sample CSV file with test tracking numbers
- `--dry-run`: Validate inputs without processing
- `--version`: Show version information

## Input Format

The input CSV file should contain tracking numbers in the first column:

```csv
tracking_number
1234567890123
9876543210987
5555666677778
```

## Output Format

The output CSV file will contain the extracted claim information:

```csv
tracking_number,status,details,timestamp
1234567890123,approved,Claim approved for processing,2024-01-15 10:30:00
9876543210987,pending,Under review,2024-01-15 10:32:00
5555666677778,denied,Insufficient documentation,2024-01-15 10:34:00
```

## Project Structure

```
Claims/
├── main.py                 # CLI entry point
├── src/
│   ├── agent.py           # Main scraping agent
│   ├── config.py          # Configuration management
│   ├── prompts.py         # AI prompts
│   └── tools.py           # Utility functions
├── tests/                 # Unit tests
├── examples/              # Example implementations
└── requirements.txt       # Python dependencies
```

## Testing

Run the test suite:

```bash
# Activate virtual environment
source venv_linux/bin/activate

# Run tests
pytest tests/
```

## Troubleshooting

### Common Issues

1. **Local LLM Connection Issues**:
   - Ensure your local LLM provider is running
   - Check the `LOCAL_LLM_BASE_URL` in your `.env` file
   - Verify the model name matches your local provider

2. **Browser Automation Issues**:
   - Check that required browser dependencies are installed
   - Verify timeout settings are appropriate for your network speed

3. **CSV Processing Issues**:
   - Ensure input CSV has the correct format
   - Check file permissions for input and output files

### Logging

The agent provides comprehensive logging. Check the log file (default: `claims_processing.log`) for detailed error information.

## Contributing

1. Follow the project structure and coding conventions
2. Add unit tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting changes

## License

This project is for educational and research purposes. Please ensure compliance with website terms of service when using web scraping functionality.