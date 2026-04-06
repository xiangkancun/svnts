@echo off
rem TortoiseSVN Post-update Hook
rem Restores file ctime/mtime from SVN properties after update/checkout
rem
rem TortoiseSVN passes: PATH DEPTH REVISION ERROR CWD RESULTPATH
rem RESULTPATH = temp file with newline-delimited list of updated files

setlocal

rem Try pip-installed svnts command first, then python -m fallback
where svnts >nul 2>&1
if %errorLevel% equ 0 (
    svnts hook-restore %1 %2 %3 %4 %5 %6
    endlocal
    exit /b 0
)

where python >nul 2>&1
if %errorLevel% equ 0 (
    python -m svnts hook-restore %1 %2 %3 %4 %5 %6
    endlocal
    exit /b 0
)

echo SvnTimestamp not found, skipping post-update hook
endlocal
exit /b 0
