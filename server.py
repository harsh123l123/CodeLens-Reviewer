#!/usr/bin/env python3
"""
Root Server Entrypoint for Cloud Deployment (Render, Railway, Heroku, Docker).
"""
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.server import run_server
from backend.config import HOST, PORT

if __name__ == "__main__":
    run_server(HOST, PORT)
