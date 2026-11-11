@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
if not errorlevel 1 goto use_py
python -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
if not errorlevel 1 goto use_python
echo Python 3.9+ was not found. Install Python 3.12 for Windows:
echo https://www.python.org/downloads/windows/
echo Select "Add python.exe to PATH", then run this file again.
goto done
:use_py
py -3 src\auto_bots.py
goto done
:use_python
python src\auto_bots.py
:done
echo.
pause
