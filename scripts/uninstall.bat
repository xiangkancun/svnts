@echo off
echo ============================================
echo   SvnTimestamp Uninstaller
echo ============================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Administrator privileges required.
    pause
    exit /b 1
)

set "INSTALL_DIR=C:\Program Files\SvnTimestamp"
set "SCRIPT_DIR=%~dp0"

rem Remove context menu entries
echo Removing context menu entries...
call "%SCRIPT_DIR%registry\uninstall-context-menu.bat" 2>nul

rem Remove installed files
echo Removing installed files...
if exist "%INSTALL_DIR%" rmdir /S /Q "%INSTALL_DIR%"

echo.
echo Uninstallation complete.
pause
