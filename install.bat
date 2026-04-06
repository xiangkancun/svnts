@echo off
echo ============================================
echo   SvnTimestamp Installer
echo ============================================
echo.

set "ROOT_DIR=%~dp0"

echo [1/3] Installing svnts Python package...
pip install -e "%ROOT_DIR%"
if %errorLevel% neq 0 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

echo [2/3] Installing context menu entries...
python "%ROOT_DIR%svnts\_install.py" install-menu
if %errorLevel% neq 0 (
    echo ERROR: context menu installation failed.
    pause
    exit /b 1
)

echo [3/3] Configuring TortoiseSVN hooks...
python "%ROOT_DIR%svnts\_install.py" install-hooks
if %errorLevel% neq 0 (
    echo ERROR: TortoiseSVN hook configuration failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Installation complete!
echo ============================================
echo.
echo   - pip package installed
echo   - Right-click context menu added
echo   - TortoiseSVN hooks configured:
echo     Pre-commit:  auto save timestamps
echo     Post-update: auto restore timestamps
echo.
pause
