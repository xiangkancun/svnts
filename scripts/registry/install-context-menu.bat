@echo off
rem Install context menu entries for SvnTimestamp
rem Requires admin privileges

set "EXE_PATH=C:\Program Files\SvnTimestamp\svnts.exe"

rem Context menu for FILES (right-click on file)
reg add "HKCR\*\shell\SvnTimestampSave" /ve /t REG_SZ /d "Save Timestamps to SVN" /f
reg add "HKCR\*\shell\SvnTimestampSave\command" /ve /t REG_SZ /d "\"%EXE_PATH%\" save \"%%1\"" /f
reg add "HKCR\*\shell\SvnTimestampSave" /v "Icon" /t REG_SZ /d "shell32.dll,43" /f

reg add "HKCR\*\shell\SvnTimestampRestore" /ve /t REG_SZ /d "Restore Timestamps from SVN" /f
reg add "HKCR\*\shell\SvnTimestampRestore\command" /ve /t REG_SZ /d "\"%EXE_PATH%\" restore \"%%1\"" /f
reg add "HKCR\*\shell\SvnTimestampRestore" /v "Icon" /t REG_SZ /d "shell32.dll,43" /f

rem Context menu for DIRECTORIES (right-click on folder)
reg add "HKCR\Directory\shell\SvnTimestampSave" /ve /t REG_SZ /d "Save Timestamps to SVN" /f
reg add "HKCR\Directory\shell\SvnTimestampSave\command" /ve /t REG_SZ /d "\"%EXE_PATH%\" save \"%%1\"" /f
reg add "HKCR\Directory\shell\SvnTimestampSave" /v "Icon" /t REG_SZ /d "shell32.dll,43" /f

reg add "HKCR\Directory\shell\SvnTimestampRestore" /ve /t REG_SZ /d "Restore Timestamps from SVN" /f
reg add "HKCR\Directory\shell\SvnTimestampRestore\command" /ve /t REG_SZ /d "\"%EXE_PATH%\" restore \"%%1\"" /f
reg add "HKCR\Directory\shell\SvnTimestampRestore" /v "Icon" /t REG_SZ /d "shell32.dll,43" /f

echo Context menu entries installed successfully.
