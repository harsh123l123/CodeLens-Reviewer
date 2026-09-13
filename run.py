#!/usr/bin/env python3
"""
CodeLens AI - One-Click Launcher
Starts the backend server and opens the browser interface.
"""

import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.server import run_server
from backend.config import HOST, PORT

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def open_browser(url):
    time.sleep(1.2)
    print(f"Opening browser at {url}...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

def main():
    print("===================================================================")
    print("                 [+] LAUNCHING CODELENS AI REVIEWER                ")
    print("===================================================================")
    print(f"Server URL: http://{HOST}:{PORT}/")
    print("Press Ctrl+C in this terminal to stop the server at any time.\n")

    # Start browser opener in background thread
    threading.Thread(target=open_browser, args=(f"http://{HOST}:{PORT}/",), daemon=True).start()

    # Start server (blocking)
    try:
        run_server(HOST, PORT)
    except KeyboardInterrupt:
        print("\nServer stopped. Thank you for using CodeLens AI!")

if __name__ == "__main__":
    main()
