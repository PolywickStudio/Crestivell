@echo off
setlocal DisableDelayedExpansion
if "%~1"=="" goto usage
if "%~2"=="" goto usage
if not "%~4"=="" goto usage
rem Quoted paths may contain spaces. The CLI returns a failure status to the build.
rem The finder resolves paths relative to itself, never the current working directory.
call "%~dp0..\find-cli.cmd"
if errorlevel 1 exit /b 2
if "%~3"=="" goto environmentLabel
"%CRESTIVELL_CLI%" upload-sign --file "%~1" --output "%~2" --label "%~3"
exit /b %errorlevel%
:environmentLabel
"%CRESTIVELL_CLI%" upload-sign --file "%~1" --output "%~2"
exit /b %errorlevel%
:usage
echo Usage: sign-file.cmd "input.exe" "signed-output.exe" ["certificate-label"] 1>&2
exit /b 1
