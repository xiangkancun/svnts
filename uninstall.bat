@echo off
echo ============================================
echo   SvnTimestamp Uninstaller
echo ============================================
echo.

set "ROOT_DIR=%~dp0"
rem Remove trailing backslash
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

echo [1/3] Removing context menu entries...
python "%ROOT_DIR%\svnts\_install.py" uninstall-menu
echo        Done.

echo [2/3] Removing TortoiseSVN hooks...
python "%ROOT_DIR%\svnts\_install.py" uninstall-hooks
echo        Done.

echo [3/3] Uninstalling svnts Python package...
pip uninstall svnts -y >nul 2>&1
echo        Done.

echo.
echo ============================================
echo   Uninstallation complete!
echo ============================================
echo.
pause
