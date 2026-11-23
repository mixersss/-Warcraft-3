@echo off
setlocal
cd /d "%~dp0"
set "resource_path=%~1"
if not defined resource_path set /p "resource_path=Path to GameServer resource: "
set "resource_path=%resource_path:"=%"
if not defined resource_path exit /b 1
where py >nul 2>nul
if errorlevel 1 (
  python "%~dp0src\spawn_sources.py" "%resource_path%"
) else (
  py -3 "%~dp0src\spawn_sources.py" "%resource_path%"
)
set "result=%errorlevel%"
pause
exit /b %result%
