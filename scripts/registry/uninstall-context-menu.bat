@echo off
rem Remove context menu entries for SvnTimestamp
rem Requires admin privileges

reg delete "HKCR\*\shell\SvnTimestampSave" /f
reg delete "HKCR\*\shell\SvnTimestampRestore" /f
reg delete "HKCR\Directory\shell\SvnTimestampSave" /f
reg delete "HKCR\Directory\shell\SvnTimestampRestore" /f

echo Context menu entries removed successfully.
