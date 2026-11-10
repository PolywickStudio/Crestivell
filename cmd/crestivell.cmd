@echo off
setlocal DisableDelayedExpansion
rem The finder resolves paths relative to itself, never the current working directory.
call "%~dp0..\find-cli.cmd"
if errorlevel 1 exit /b 2
"%CRESTIVELL_CLI%" %*
exit /b %errorlevel%
