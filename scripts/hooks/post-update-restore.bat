@echo off
rem TortoiseSVN Post-update Hook
rem Restores file ctime/mtime from SVN properties after update/checkout
rem
rem TortoiseSVN passes: PATH DEPTH REVISION ERROR CWD RESULTPATH
rem RESULTPATH = temp file with newline-delimited list of updated files

setlocal

set "SVNTS_EXE=C:\Program Files\SvnTimestamp\svnts.exe"

if not exist "%SVNTS_EXE%" (
    set "SVNTS_EXE=%~dp0svnts.exe"
)

if not exist "%SVNTS_EXE%" (
    echo SvnTimestamp not found, skipping post-update hook
    exit /b 0
)

"%SVNTS_EXE%" hook-restore %1 %2 %3 %4 %5 %6

endlocal
