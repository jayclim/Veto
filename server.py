"""Dedalus Labs entry point for the Veto Budget MCP Server."""
import sys
import os

# Add backend to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Change to backend directory for SQLite path to work correctly
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

from mcp_server import mcp

if __name__ == "__main__":
    mcp.run()
