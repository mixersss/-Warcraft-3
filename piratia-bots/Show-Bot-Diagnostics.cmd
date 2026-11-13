@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 src\show_diagnostics.py
goto done
:use_python
python src\show_diagnostics.py
:done
echo.
pause
