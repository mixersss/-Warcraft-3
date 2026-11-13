@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 src\audit_server.py
goto done
:use_python
python src\audit_server.py
:done
echo.
pause
