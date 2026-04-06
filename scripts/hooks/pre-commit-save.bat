@echo off
rem TortoiseSVN Pre-commit Hook
rem Saves file ctime/mtime as SVN properties before commit
rem
rem TortoiseSVN passes: PATH DEPTH MESSAGEFILE CWD
rem PATH = temp file with newline-delimited list of files to commit

setlocal

set "SVNTS_EXE=C:\Program Files\SvnTimestamp\svnts.exe"

if not exist "%SVNTS_EXE%" (
    set "SVNTS_EXE=%~dp0svnts.exe"
)

if not exist "%SVNTS_EXE%" (
    echo SvnTimestamp not found, skipping pre-commit hook
    exit /b 0
)

"%SVNTS_EXE%" hook-save %1 %2 %3 %4

endlocal
