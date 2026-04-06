@echo off
setlocal
python "%~dp0..\svnts.py" hook-restore %1 %2 %3 %4 %5
endlocal
exit /b 0
