"""Create desktop shortcut for Windows"""

import os
import sys
from pathlib import Path
import winshell
from win32com.client import Dispatch

def create_windows_shortcut():
    """Create a desktop shortcut on Windows"""
    
    # Get desktop path
    desktop = Path(winshell.desktop())
    
    # Shortcut path
    shortcut_path = desktop / "Economic Dashboard.lnk"
    
    # Get Python executable
    python_exe = sys.executable
    
    # Get the package installation path
    import macro_database
    package_path = Path(macro_database.__file__).parent
    
    # Create shortcut
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.Targetpath = python_exe
    shortcut.Arguments = f'-m macro_database.run'
    shortcut.WorkingDirectory = str(package_path)
    shortcut.IconLocation = python_exe
    shortcut.Description = "Economic Indicators Dashboard"
    shortcut.save()
    
    print(f"✅ Shortcut created at: {shortcut_path}")

if __name__ == "__main__":
    try:
        create_windows_shortcut()
    except Exception as e:
        print(f"❌ Error creating shortcut: {e}")
        print("\nYou may need to install: pip install pywin32 winshell")


