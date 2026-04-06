@echo off
echo ============================================
echo   SvnTimestamp Installer
echo ============================================
echo.

set "ROOT_DIR=%~dp0"

rem Install Python package
echo [1/2] Installing svnts Python package...
pip install -e "%ROOT_DIR%"
if %errorLevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python and pip are available.
    pause
    exit /b 1
)

rem Install context menu entries
echo [2/2] Installing context menu entries...
set "CMD=python -m svnts"

reg add "HKCR\*\shell\SvnTimestampSave" /ve /t REG_SZ /d "Save Timestamps to SVN" /f >nul
reg add "HKCR\*\shell\SvnTimestampSave\command" /ve /t REG_SZ /d "%CMD% save \"%%1\"" /f >nul
reg add "HKCR\*\shell\SvnTimestampSave" /v "Icon" /t REG_SZ /d "shell32.dll,43" /f >nul

reg add "HKCR\*\shell\SvnTimestampRestore" /ve /t REG_SZ /d "Restore Timestamps from SVN" /f >nul
reg add "HKCR\*\shell\SvnTimestampRestore\command" /ve /t REG_SZ /d "%CMD% restore \"%%1\"" /f >nul
reg add "HKCR\*\shell\SvnTimestampRestore" /v "Icon" /t REG_SZ /d "shell32.dll,43" /f >nul

reg add "HKCR\Directory\shell\SvnTimestampSave" /ve /t REG_SZ /d "Save Timestamps to SVN" /f >nul
reg add "HKCR\Directory\shell\SvnTimestampSave\command" /ve /t REG_SZ /d "%CMD% save \"%%1\"" /f >nul
reg add "HKCR\Directory\shell\SvnTimestampSave" /v "Icon" /t REG_SZ /d "shell32.dll,43" /f >nul

reg add "HKCR\Directory\shell\SvnTimestampRestore" /ve /t REG_SZ /d "Restore Timestamps from SVN" /f >nul
reg add "HKCR\Directory\shell\SvnTimestampRestore\command" /ve /t REG_SZ /d "%CMD% restore \"%%1\"" /f >nul
reg add "HKCR\Directory\shell\SvnTimestampRestore" /v "Icon" /t REG_SZ /d "shell32.dll,43" /f >nul

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
echo        Command: %ROOT_DIR%scripts\hooks\pre-commit-save.bat
echo.
echo      Post-update hook:
echo        Working Copy Path: [your working copy root]
echo        Command: %ROOT_DIR%scripts\hooks\post-update-restore.bat
echo.
echo   2. Right-click any file to see "Save/Restore Timestamps" options.
echo.
pause
