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

set "INSTALL_DIR=C:\Program Files\SvnTimestamp"
set "SCRIPT_DIR=%~dp0"

rem Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\hooks" mkdir "%INSTALL_DIR%\hooks"

rem Copy svnts.exe
echo Installing svnts.exe...
set "PUBLISH_DIR=%SCRIPT_DIR%..\src\SvnTimestamp.CLI\bin\Release\net8.0\win-x64\publish\"
if exist "%PUBLISH_DIR%svnts.exe" (
    copy /Y "%PUBLISH_DIR%svnts.exe" "%INSTALL_DIR%\" >nul
) else (
    echo WARNING: svnts.exe not found in publish directory.
    echo Please build first: dotnet publish src\SvnTimestamp.CLI -c Release
    echo Then re-run this installer.
    pause
    exit /b 1
)

rem Copy hook scripts
echo Installing hook scripts...
copy /Y "%SCRIPT_DIR%hooks\pre-commit-save.bat" "%INSTALL_DIR%\hooks\" >nul
copy /Y "%SCRIPT_DIR%hooks\post-update-restore.bat" "%INSTALL_DIR%\hooks\" >nul

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
echo        Command: %INSTALL_DIR%\hooks\pre-commit-save.bat
echo.
echo      Post-update hook:
echo        Working Copy Path: [your working copy root]
echo        Command: %INSTALL_DIR%\hooks\post-update-restore.bat
echo.
echo   2. Right-click any file to see "Save/Restore Timestamps" options.
echo.
pause
