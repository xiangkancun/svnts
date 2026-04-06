@echo off
echo ============================================
echo   SvnTimestamp Installer
echo ============================================
echo.

rem Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Administrator privileges required.
    echo Please right-click and select "Run as administrator".
    pause
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"

rem Install Python package
echo Installing svnts Python package...
pip install -e "%SCRIPT_DIR%.."
if %errorLevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python and pip are available.
    pause
    exit /b 1
)

rem Install context menu entries
echo Installing context menu entries...
call "%SCRIPT_DIR%registry\install-context-menu.bat"

echo.
echo ============================================
echo   Installation complete!
echo ============================================
echo.
echo Next steps:
echo   1. Configure TortoiseSVN hooks:
echo      Right-click ^> TortoiseSVN ^> Settings ^> Hook Scripts ^> Add
echo.
echo      Pre-commit hook:
echo        Working Copy Path: [your working copy root]
echo        Command: %SCRIPT_DIR%hooks\pre-commit-save.bat
echo.
echo      Post-update hook:
echo        Working Copy Path: [your working copy root]
echo        Command: %SCRIPT_DIR%hooks\post-update-restore.bat
echo.
echo   2. Right-click any file to see "Save/Restore Timestamps" options.
echo.
pause
