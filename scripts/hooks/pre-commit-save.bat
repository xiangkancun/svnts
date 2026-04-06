@echo off
rem TortoiseSVN Pre-commit Hook
rem Saves file ctime/mtime as SVN properties before commit
rem
rem TortoiseSVN passes: PATH DEPTH MESSAGEFILE CWD
rem PATH = temp file with newline-delimited list of files to commit

setlocal

rem Try pip-installed svnts command first, then python -m fallback
where svnts >nul 2>&1
if %errorLevel% equ 0 (
    svnts hook-save %1 %2 %3 %4
    endlocal
    exit /b 0
)

where python >nul 2>&1
if %errorLevel% equ 0 (
    python -m svnts hook-save %1 %2 %3 %4
    endlocal
    exit /b 0
)

echo SvnTimestamp not found, skipping pre-commit hook
endlocal
exit /b 0
