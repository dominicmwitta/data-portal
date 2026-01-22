"""Create desktop shortcut for Linux"""

import os
import sys
from pathlib import Path

def create_linux_shortcut():
    """Create a .desktop file on Linux"""
    
    # Get desktop path
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        desktop = Path.home() / ".local" / "share" / "applications"
    
    # Desktop file path
    desktop_file = desktop / "economic-dashboard.desktop"
    
    # Get Python executable
    python_exe = sys.executable
    
    # Create .desktop file content
    content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Economic Dashboard
Comment=CPI and Balance of Payments Data Explorer
Exec={python_exe} -m macro_database.run
Icon=utilities-terminal
Terminal=false
Categories=Office;Finance;
"""
    
    # Write file
    desktop_file.write_text(content)
    
    # Make executable
    os.chmod(desktop_file, 0o755)
    
    print(f"✅ Shortcut created at: {desktop_file}")

if __name__ == "__main__":
    try:
        create_linux_shortcut()
    except Exception as e:
        print(f"❌ Error creating shortcut: {e}")