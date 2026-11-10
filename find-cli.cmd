@echo off
rem Shared finder. CALL this without arguments; it sets CRESTIVELL_CLI for the caller.
rem An explicit override must name an existing executable or one on PATH.
if defined CRESTIVELL_CLI goto override
for %%I in ("%~dp0..\CrestivellCli.exe") do if exist "%%~fI" (
    set "CRESTIVELL_CLI=%%~fI"
    exit /b 0
)
for %%I in (CrestivellCli.exe) do if not "%%~$PATH:I"=="" (
    set "CRESTIVELL_CLI=%%~$PATH:I"
    exit /b 0
)
if defined ProgramW6432 if exist "%ProgramW6432%\PolywickStudio\Crestivell\CrestivellCli.exe" (
    set "CRESTIVELL_CLI=%ProgramW6432%\PolywickStudio\Crestivell\CrestivellCli.exe"
    exit /b 0
)
if defined ProgramFiles if exist "%ProgramFiles%\PolywickStudio\Crestivell\CrestivellCli.exe" (
    set "CRESTIVELL_CLI=%ProgramFiles%\PolywickStudio\Crestivell\CrestivellCli.exe"
    exit /b 0
)
echo CrestivellCli.exe was not found. Install the Client component, add it to PATH, or set CRESTIVELL_CLI. 1>&2
exit /b 2
:override
if exist "%CRESTIVELL_CLI%" exit /b 0
for %%I in ("%CRESTIVELL_CLI%") do if not "%%~$PATH:I"=="" (
    set "CRESTIVELL_CLI=%%~$PATH:I"
    exit /b 0
)
echo CRESTIVELL_CLI does not identify an existing executable. 1>&2
exit /b 2
