@echo off
setlocal DisableDelayedExpansion
if "%~1"=="" goto usage
if "%~2"=="" goto usage
if not "%~4"=="" goto usage
rem Receipt is written to stdout; this does not embed a signature in a file.
rem The finder resolves paths relative to itself, never the current working directory.
call "%~dp0..\find-cli.cmd"
if errorlevel 1 exit /b 2
if "%~3"=="" goto environmentLabel
"%CRESTIVELL_CLI%" sign --digest "%~1" --name "%~2" --label "%~3"
exit /b %errorlevel%
:environmentLabel
"%CRESTIVELL_CLI%" sign --digest "%~1" --name "%~2"
exit /b %errorlevel%
:usage
echo Usage: sign-digest.cmd "sha256" "file-name" ["certificate-label"] 1>&2
exit /b 1
