"""Absolute-path entry point: works without relying on the client's working directory."""
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent/"src"))
from mgsv_mcp.server import main

if __name__ == "__main__":
    main()
