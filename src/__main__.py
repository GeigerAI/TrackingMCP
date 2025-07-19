"""
Entry point for running MCP server as a module.
"""

import sys
import os

# Reason: Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.mcp_server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())