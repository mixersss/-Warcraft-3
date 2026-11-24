@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 world_expansion.py --restore-spawns-only --apply %*
goto done
:use_python
python world_expansion.py --restore-spawns-only --apply %*
:done
set "result=%errorlevel%"
pause
exit /b %result%
