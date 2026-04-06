@echo off
echo ============================================
echo   SvnTimestamp Uninstaller
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

echo [1/3] Removing context menu entries...
reg delete "HKCR\*\shell\SvnTimestampSave" /f >nul 2>&1
reg delete "HKCR\*\shell\SvnTimestampRestore" /f >nul 2>&1
reg delete "HKCR\Directory\shell\SvnTimestampSave" /f >nul 2>&1
reg delete "HKCR\Directory\shell\SvnTimestampRestore" /f >nul 2>&1
echo        Done.

echo [2/3] Uninstalling svnts Python package...
pip uninstall svnts -y >nul 2>&1
if %errorLevel% equ 0 (
    echo        Done.
) else (
    echo        svnts package not found, skipped.
)

echo [3/3] Cleaning pip cache...
pip cache remove svnts >nul 2>&1
echo        Done.

echo.
echo ============================================
echo   Uninstallation complete!
echo ============================================
echo.
echo NOTE: TortoiseSVN hook scripts were NOT removed automatically.
echo        If you configured hooks, please remove them manually:
echo        TortoiseSVN ^> Settings ^> Hook Scripts ^> select and Remove
echo.
pause
