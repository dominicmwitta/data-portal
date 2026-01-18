"""
Launcher script for Economic Indicators Dashboard
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Launch the Streamlit dashboard"""
    
    # Get the path to app.py
    app_path = Path(__file__).parent / "app.py"
    
    if not app_path.exists():
        print(f"❌ Error: Could not find app.py at {app_path}")
        sys.exit(1)
    
    # Set up Streamlit configuration
    streamlit_args = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8501",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false"
    ]
    
    print("🚀 Launching Economic Indicators Dashboard...")
    print(f"📂 App location: {app_path}")
    print(f"🌐 Opening browser at: http://localhost:8501")
    print("\n" + "="*60)
    print("Press Ctrl+C to stop the dashboard")
    print("="*60 + "\n")
    
    try:
        subprocess.run(streamlit_args)
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error launching dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()