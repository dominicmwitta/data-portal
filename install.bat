@echo off
echo ============================================================
echo Economic Dashboard Installer
echo ============================================================
echo.

REM Check if wheel file exists
if not exist "*.whl" (
    echo ERROR: No .whl file found in this directory!
    echo Please place the .whl file here and run this script again.
    pause
    exit /b 1
)

REM Install dependencies for shortcut creation
echo Installing dependencies...
python -m pip install pywin32 winshell --quiet
if errorlevel 1 (
    echo Warning: Could not install dependencies for shortcut creation
)

REM Install the wheel file
echo.
echo Installing Economic Dashboard...
for %%f in (*.whl) do (
    python -m pip install "%%f"
    if errorlevel 1 (
        echo ERROR: Installation failed!
        pause
        exit /b 1
    )
    echo Installation successful!
)

REM Create desktop shortcut using VBScript
echo.
echo Creating desktop shortcut...

REM Create temporary VBScript to make shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Economic Dashboard.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "cmd.exe" >> CreateShortcut.vbs
echo oLink.Arguments = "/c economic-dashboard" >> CreateShortcut.vbs
echo oLink.Description = "Economic Indicators Dashboard" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%USERPROFILE%" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

REM Run the VBScript
cscript CreateShortcut.vbs //nologo
if errorlevel 1 (
    echo Warning: Could not create desktop shortcut
) else (
    echo Desktop shortcut created successfully!
)

REM Clean up VBScript
del CreateShortcut.vbs

echo.
echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo You can now:
echo 1. Double-click "Economic Dashboard" on your desktop
echo 2. Or run "economic-dashboard" from command line
echo.
pause