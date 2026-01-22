"""
Launcher script for Economic Indicators Dashboard
"""

import os
import sys
import subprocess
import webbrowser
import threading
import time
from pathlib import Path


def open_browser(url, delay=2):
    """Open browser after a short delay to allow server to start"""
    time.sleep(delay)
    webbrowser.open(url)


def main():
    """Launch the Streamlit dashboard"""

    # Get the path to app.py
    app_path = Path(__file__).parent / "app.py"

    if not app_path.exists():
        print(f"[ERROR] Could not find app.py at {app_path}")
        sys.exit(1)

    port = 8501
    url = f"http://localhost:{port}"

    # Set up Streamlit configuration
    streamlit_args = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false"
    ]

    print("Launching Chota Data Dashboard...")
    print(f"App location: {app_path}")
    print(f"Opening browser at: {url}")
    print("\n" + "="*60)
    print("Press Ctrl+C to stop the dashboard")
    print("="*60 + "\n")

    # Open browser automatically after server starts
    browser_thread = threading.Thread(target=open_browser, args=(url,))
    browser_thread.daemon = True
    browser_thread.start()

    try:
        subprocess.run(streamlit_args)
    except KeyboardInterrupt:
        print("\n\nDashboard stopped. Goodbye!")
    except Exception as e:
        print(f"\n[ERROR] Error launching dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()